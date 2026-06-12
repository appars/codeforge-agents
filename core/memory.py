"""
CodeForge Agents — Conversation Memory
======================================
A deliberately simple sliding-window memory: the last N messages are
formatted into a text block that the Synthesizer agent can read.

TEACHING NOTE: Real systems add summarization ("compress old turns into
a paragraph") and vector recall. The window below is the honest first
step — and its limitation (old context falls off the edge) is visible
in class: ask about something from 10 messages ago and watch it forget.
"""

from core import config


def build_memory(messages: list[dict],
                 window: int = config.DEFAULT_CONTEXT_WINDOW) -> str:
    """Format the last `window` messages as a readable transcript."""
    recent = messages[-window:]
    if not recent:
        return "(no prior conversation)"
    lines = []
    for msg in recent:
        content = msg["content"]
        if len(content) > 600:                     # keep prompts lean
            content = content[:600] + " …[truncated]"
        lines.append(f"{msg['role'].upper()}: {content}")
    return "\n".join(lines)
