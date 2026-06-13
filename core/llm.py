"""
CodeForge Agents — LLM Provider Abstraction (with runtime fallback)
===================================================================
ONE interface, TWO backends, tried IN ORDER on EVERY call:

    * Groq cloud  (fast, free tier, needs GROQ_API_KEY)
    * Ollama      (fully local, needs `ollama serve` + a pulled model)

WHY A PER-CALL CHAIN (the important lesson):
A previous version picked ONE provider at startup and froze it. That
breaks exactly when it matters: Groq is healthy at launch, then returns
HTTP 429 (rate limit) mid-session — and a frozen client just errors
instead of using the local model sitting right there. Here, every
chat()/stream() call walks the chain and falls through on failure, so
the app keeps answering as long as ANY backend is alive.

FALLBACK RULES:
  * chat()   — try each provider in order; on failure, try the next.
  * stream() — try each provider, BUT only fall back if it fails BEFORE
    the first token. Once tokens are flowing we must not switch, or the
    user would see half a Groq answer spliced onto a full Ollama answer.
  * Which provider actually answered is recorded on `.last_provider`
    so the UI can show the failover honestly.

Order is configurable: LLM_PROVIDER = auto | groq | ollama.
"""

from dataclasses import dataclass

from core import config


class LLMUnavailableError(Exception):
    """Raised when NO backend in the chain could answer."""


# --------------------------------------------------------------- Status

@dataclass
class LLMStatus:
    provider: str          # "groq" | "ollama" | "none"
    ok: bool
    detail: str            # human-readable explanation for the sidebar

    @property
    def emoji(self) -> str:
        return {"groq": "🟢", "ollama": "🟡"}.get(self.provider, "🔴")


def _short(exc: Exception, limit: int = 120) -> str:
    text = str(exc).replace("\n", " ")
    return text[:limit] + ("…" if len(text) > limit else "")


def _check_groq() -> LLMStatus:
    if not config.GROQ_API_KEY:
        return LLMStatus("none", False, "No GROQ_API_KEY found")
    try:
        from groq import Groq
        client = Groq(api_key=config.GROQ_API_KEY, timeout=10)
        client.models.list()  # cheap authenticated ping
        return LLMStatus("groq", True, f"Groq connected · {config.AGENT_MODEL}")
    except Exception as exc:
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


def _ordered_providers() -> list[str]:
    """The chain to try, honouring the LLM_PROVIDER preference."""
    if config.LLM_PROVIDER == "groq":
        return ["groq"]
    if config.LLM_PROVIDER == "ollama":
        return ["ollama"]
    return ["groq", "ollama"]            # "auto": Groq first, Ollama fallback


def get_status() -> LLMStatus:
    """Health check for the sidebar: reports the FIRST live backend in the
    chain (the one a request would hit first), or 'none'."""
    checks = {"groq": _check_groq, "ollama": _check_ollama}
    first_error = None
    for name in _ordered_providers():
        status = checks[name]()
        if status.ok:
            return status
        first_error = first_error or status
    if first_error and config.LLM_PROVIDER != "auto":
        return first_error              # user forced one provider; report why
    return LLMStatus(
        "none", False,
        "No LLM available — add GROQ_API_KEY or start Ollama. "
        "Running in Tools-Only Mode.")


# --------------------------------------------------------------- Client

class LLMClient:
    """Unified chat interface with a runtime fallback chain.

    Build it once with the available backends; it lazily constructs each
    underlying SDK client the first time that provider is used.
    """

    def __init__(self, providers: list[str] | None = None):
        # Which backends are even possible (Groq needs a key).
        possible = providers if providers is not None else _ordered_providers()
        self.providers = [p for p in possible
                          if p != "groq" or config.GROQ_API_KEY]
        self._clients: dict[str, object] = {}
        self.last_provider: str | None = None      # who answered last call
        self.last_fellback: bool = False           # did we fall through?

    # -- introspection used by the sidebar/UI --------------------------
    @property
    def provider(self) -> str:
        """The PRIMARY (first) provider, for display."""
        return self.providers[0] if self.providers else "none"

    def available(self) -> bool:
        return bool(self.providers)

    # -- lazy client construction --------------------------------------
    def _client_for(self, name: str):
        if name not in self._clients:
            if name == "groq":
                from groq import Groq
                self._clients[name] = Groq(
                    api_key=config.GROQ_API_KEY, timeout=config.REQUEST_TIMEOUT)
            elif name == "ollama":
                import ollama
                self._clients[name] = ollama.Client(host=config.OLLAMA_HOST)
        return self._clients[name]

    def _model_for(self, name: str, requested: str | None) -> str:
        if name == "ollama":
            return config.OLLAMA_MODEL
        return requested or config.AGENT_MODEL

    # -- one provider's raw calls --------------------------------------
    def _chat_once(self, name, messages, model, temperature, max_tokens) -> str:
        client = self._client_for(name)
        mdl = self._model_for(name, model)
        if name == "groq":
            resp = client.chat.completions.create(
                model=mdl, messages=messages,
                temperature=temperature, max_tokens=max_tokens)
            return resp.choices[0].message.content or ""
        resp = client.chat(model=mdl, messages=messages,
                            options={"temperature": temperature})
        return resp["message"]["content"]

    def _stream_once(self, name, messages, model, temperature, max_tokens):
        client = self._client_for(name)
        mdl = self._model_for(name, model)
        if name == "groq":
            chunks = client.chat.completions.create(
                model=mdl, messages=messages, temperature=temperature,
                max_tokens=max_tokens, stream=True)
            for chunk in chunks:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        else:
            for chunk in client.chat(model=mdl, messages=messages, stream=True):
                yield chunk["message"]["content"]

    # -- public API: full reply, with fallback -------------------------
    def chat(self, messages: list[dict], model: str | None = None,
             temperature: float = 0.3, max_tokens: int = 1024) -> str:
        if not self.providers:
            raise LLMUnavailableError("No LLM backend configured.")
        errors = []
        for i, name in enumerate(self.providers):
            try:
                out = self._chat_once(name, messages, model,
                                      temperature, max_tokens)
                self.last_provider = name
                self.last_fellback = i > 0
                return out
            except Exception as exc:
                errors.append(f"{name}: {_friendly(exc)}")
                continue                       # try the next provider
        raise LLMUnavailableError(" | ".join(errors))

    # -- public API: streaming, with PRE-FIRST-TOKEN fallback ----------
    def stream(self, messages: list[dict], model: str | None = None,
               temperature: float = 0.3, max_tokens: int = 2048):
        """Yield tokens. Falls back to the next provider ONLY if a provider
        fails before producing its first token. A mid-stream failure is
        re-raised (we never splice two providers' partial answers)."""
        if not self.providers:
            raise LLMUnavailableError("No LLM backend configured.")
        errors = []
        for i, name in enumerate(self.providers):
            gen = self._stream_once(name, messages, model,
                                    temperature, max_tokens)
            started = False
            try:
                for token in gen:
                    started = True
                    yield token
                self.last_provider = name
                self.last_fellback = i > 0
                return                          # finished cleanly
            except Exception as exc:
                if started:
                    # Already emitted tokens — cannot safely switch.
                    raise LLMUnavailableError(
                        f"{name} failed mid-stream: {_friendly(exc)}") from exc
                errors.append(f"{name}: {_friendly(exc)}")
                continue                        # nothing emitted yet → fall back
        raise LLMUnavailableError(" | ".join(errors))


def _friendly(exc: Exception) -> str:
    """Turn raw API errors into messages a student can act on."""
    text = str(exc)
    if "401" in text or "invalid_api_key" in text.lower():
        return ("Invalid API key (401). Check GROQ_API_KEY — "
                "create a free key at console.groq.com/keys")
    if "429" in text:
        return ("Rate limit hit (429). Free tier allows limited "
                "requests/minute — falling back to local model if available.")
    if "404" in text and "model" in text.lower():
        return ("Model not found (404). It may be deprecated — "
                "check console.groq.com/docs/models")
    if "timeout" in text.lower() or "timed out" in text.lower():
        return "Request timed out."
    return f"{_short(exc, 200)}"
