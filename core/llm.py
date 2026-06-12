"""
CodeForge Agents — LLM Provider Abstraction
===========================================
ONE interface, TWO backends:

    * Groq cloud  (fast, free tier, needs GROQ_API_KEY in .env)
    * Ollama      (fully local, needs `ollama serve` + a pulled model)

TEACHING NOTE: Agent logic should never care WHICH model answers.
This file is the only place that talks to a provider. Swap providers
with one env variable and zero changes anywhere else in the codebase.
"""

from dataclasses import dataclass

from core import config


class LLMUnavailableError(Exception):
    """Raised when no LLM backend can answer."""


# --------------------------------------------------------------- Status

@dataclass
class LLMStatus:
    provider: str          # "groq" | "ollama" | "none"
    ok: bool
    detail: str            # human-readable explanation for the sidebar

    @property
    def emoji(self) -> str:
        return {"groq": "🟢", "ollama": "🟡"}.get(self.provider, "🔴")


def _check_groq() -> LLMStatus:
    if not config.GROQ_API_KEY:
        return LLMStatus("none", False, "No GROQ_API_KEY found in .env")
    try:
        from groq import Groq
        client = Groq(api_key=config.GROQ_API_KEY, timeout=10)
        client.models.list()  # cheap authenticated ping
        return LLMStatus("groq", True, f"Groq connected · {config.AGENT_MODEL}")
    except Exception as exc:  # invalid key, network down, etc.
        return LLMStatus("none", False, f"Groq error: {_short(exc)}")


def _check_ollama() -> LLMStatus:
    try:
        import ollama
        client = ollama.Client(host=config.OLLAMA_HOST)
        client.list()
        return LLMStatus("ollama", True,
                         f"Ollama (local) · {config.OLLAMA_MODEL}")
    except Exception as exc:
        return LLMStatus("none", False, f"Ollama not reachable: {_short(exc)}")


def _short(exc: Exception, limit: int = 120) -> str:
    text = str(exc).replace("\n", " ")
    return text[:limit] + ("…" if len(text) > limit else "")


def get_status() -> LLMStatus:
    """Health check used by the sidebar. Decides which backend is live."""
    if config.LLM_PROVIDER in ("auto", "groq"):
        status = _check_groq()
        if status.ok:
            return status
        if config.LLM_PROVIDER == "groq":
            return status                      # user forced Groq; report why
    if config.LLM_PROVIDER in ("auto", "ollama"):
        status = _check_ollama()
        if status.ok:
            return status
    return LLMStatus(
        "none", False,
        "No LLM available — add GROQ_API_KEY to .env or start Ollama. "
        "Running in Tools-Only Mode."
    )


# --------------------------------------------------------------- Client

class LLMClient:
    """Unified chat interface. Use .chat() for full responses
    and .stream() for token-by-token output."""

    def __init__(self, status: LLMStatus):
        self.status = status
        self.provider = status.provider
        if self.provider == "groq":
            from groq import Groq
            self._client = Groq(api_key=config.GROQ_API_KEY,
                                timeout=config.REQUEST_TIMEOUT)
        elif self.provider == "ollama":
            import ollama
            self._client = ollama.Client(host=config.OLLAMA_HOST)

    # -- helpers -------------------------------------------------------
    def _resolve(self, model: str | None) -> str:
        """Map requested cloud model to local model when on Ollama."""
        if self.provider == "ollama":
            return config.OLLAMA_MODEL
        return model or config.AGENT_MODEL

    # -- public API ----------------------------------------------------
    def chat(self, messages: list[dict], model: str | None = None,
             temperature: float = 0.3, max_tokens: int = 1024) -> str:
        """Return the assistant's full reply as a string."""
        if self.provider == "none":
            raise LLMUnavailableError(self.status.detail)
        mdl = self._resolve(model)
        try:
            if self.provider == "groq":
                resp = self._client.chat.completions.create(
                    model=mdl, messages=messages,
                    temperature=temperature, max_tokens=max_tokens)
                return resp.choices[0].message.content or ""
            resp = self._client.chat(model=mdl, messages=messages,
                                     options={"temperature": temperature})
            return resp["message"]["content"]
        except Exception as exc:
            raise LLMUnavailableError(_friendly(exc)) from exc

    def stream(self, messages: list[dict], model: str | None = None,
               temperature: float = 0.3, max_tokens: int = 2048):
        """Yield the reply token by token (for st.write_stream)."""
        if self.provider == "none":
            raise LLMUnavailableError(self.status.detail)
        mdl = self._resolve(model)
        try:
            if self.provider == "groq":
                chunks = self._client.chat.completions.create(
                    model=mdl, messages=messages, temperature=temperature,
                    max_tokens=max_tokens, stream=True)
                for chunk in chunks:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
            else:
                for chunk in self._client.chat(model=mdl, messages=messages,
                                               stream=True):
                    yield chunk["message"]["content"]
        except Exception as exc:
            raise LLMUnavailableError(_friendly(exc)) from exc


def _friendly(exc: Exception) -> str:
    """Turn raw API errors into messages a student can act on."""
    text = str(exc)
    if "401" in text or "invalid_api_key" in text.lower():
        return ("❌ Invalid API key (401). Check GROQ_API_KEY in your .env — "
                "create a free key at console.groq.com/keys")
    if "429" in text:
        return ("⏳ Rate limit hit (429). The free tier allows limited "
                "requests/minute. Wait a moment, or create your own key "
                "instead of sharing one.")
    if "404" in text and "model" in text.lower():
        return ("❌ Model not found (404). It may have been deprecated — "
                "check console.groq.com/docs/models and update .env")
    if "timeout" in text.lower() or "timed out" in text.lower():
        return "⏳ The LLM request timed out. Check your network and retry."
    return f"❌ LLM error: {_short(exc, 200)}"
