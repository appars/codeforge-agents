"""
Tests for the runtime LLM fallback chain (core/llm.py).

These prove the behavior the app depends on in a classroom:
  * Groq 429 mid-session  -> falls through to Ollama (chat + stream)
  * both providers down   -> raises LLMUnavailableError (Tools-Only Mode)
  * mid-stream failure     -> does NOT silently switch providers
  * last_provider / last_fellback report the truth for the UI
"""
import pytest

from core import config, llm as llm_mod
from core.llm import LLMClient, LLMUnavailableError


@pytest.fixture(autouse=True)
def _fake_key(monkeypatch):
    # Pretend a Groq key exists so "groq" stays in the chain.
    monkeypatch.setattr(config, "GROQ_API_KEY", "gsk_test")
    monkeypatch.setattr(config, "LLM_PROVIDER", "auto")


def _client_with(monkeypatch, chat_once=None, stream_once=None):
    c = LLMClient(providers=["groq", "ollama"])
    if chat_once:
        monkeypatch.setattr(c, "_chat_once", chat_once)
    if stream_once:
        monkeypatch.setattr(c, "_stream_once", stream_once)
    return c


# --------------------------------------------------------------- chat()

def test_chat_falls_back_on_groq_429(monkeypatch):
    def chat_once(name, *a, **k):
        if name == "groq":
            raise Exception("Error code: 429 - rate_limit_exceeded")
        return "local answer from ollama"
    c = _client_with(monkeypatch, chat_once=chat_once)
    out = c.chat([{"role": "user", "content": "hi"}])
    assert out == "local answer from ollama"
    assert c.last_provider == "ollama"
    assert c.last_fellback is True          # UI should flag the failover


def test_chat_uses_groq_when_healthy(monkeypatch):
    def chat_once(name, *a, **k):
        if name == "groq":
            return "groq answer"
        raise AssertionError("should not reach ollama")
    c = _client_with(monkeypatch, chat_once=chat_once)
    assert c.chat([{"role": "user", "content": "hi"}]) == "groq answer"
    assert c.last_provider == "groq"
    assert c.last_fellback is False


def test_chat_both_down_raises(monkeypatch):
    def chat_once(name, *a, **k):
        raise Exception("boom " + name)
    c = _client_with(monkeypatch, chat_once=chat_once)
    with pytest.raises(LLMUnavailableError) as exc:
        c.chat([{"role": "user", "content": "hi"}])
    assert "groq" in str(exc.value) and "ollama" in str(exc.value)


# --------------------------------------------------------------- stream()

def test_stream_falls_back_before_first_token(monkeypatch):
    def stream_once(name, *a, **k):
        if name == "groq":
            raise Exception("429 rate limit")   # fails before yielding
            yield  # pragma: no cover
        else:
            yield "local "
            yield "stream"
    c = _client_with(monkeypatch, stream_once=stream_once)
    out = "".join(c.stream([{"role": "user", "content": "hi"}]))
    assert out == "local stream"
    assert c.last_provider == "ollama"
    assert c.last_fellback is True


def test_stream_midstream_failure_does_not_switch(monkeypatch):
    """If Groq emits tokens THEN dies, we must NOT splice Ollama on top."""
    def stream_once(name, *a, **k):
        if name == "groq":
            yield "half a "
            raise Exception("connection dropped mid-stream")
        else:
            yield "FULL OLLAMA ANSWER"   # must never appear
    c = _client_with(monkeypatch, stream_once=stream_once)
    collected = []
    with pytest.raises(LLMUnavailableError):
        for tok in c.stream([{"role": "user", "content": "hi"}]):
            collected.append(tok)
    assert "".join(collected) == "half a "          # only Groq's partial
    assert "FULL OLLAMA ANSWER" not in "".join(collected)


# --------------------------------------------------------------- chain config

def test_provider_order_respects_forced_ollama(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "ollama")
    c = LLMClient()
    assert c.providers == ["ollama"]
    assert c.provider == "ollama"


def test_groq_dropped_when_no_key(monkeypatch):
    monkeypatch.setattr(config, "GROQ_API_KEY", "")
    monkeypatch.setattr(config, "LLM_PROVIDER", "auto")
    c = LLMClient()
    assert "groq" not in c.providers          # can't use Groq without a key
    assert c.providers == ["ollama"]
