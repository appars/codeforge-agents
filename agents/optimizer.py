"""Optimizer Agent — proposes concrete, safe improvements.
Its key rule is intellectual honesty: if there is nothing worth
improving, it must say so instead of inventing changes."""

from agents.base import Agent


class Optimizer(Agent):
    name = "Optimizer Agent"
    emoji = "⚡"
    system = (
        "You are a performance and code-quality optimizer. Rules: "
        "(1) NEVER break correctness. "
        "(2) Only suggest improvements you are confident about. "
        "(3) If the code is already fine, reply exactly: "
        "'No meaningful optimization needed.' "
        "(4) Keep suggestions short and concrete — show a small code "
        "snippet only when it genuinely helps."
    )

    def build_prompt(self, ctx: dict) -> str:
        return f"""Language: {ctx['language']}

USER REQUEST:
{ctx['prompt']}

TOOL RESULT (ground truth — fix errors before optimizing):
{ctx['tool_output']}

KNOWLEDGE BASE EXTRACTS (may include team standards):
{ctx['rag_context'] or '(nothing relevant retrieved)'}

Suggest optimizations now."""
