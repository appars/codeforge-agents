"""Reviewer Agent — judges correctness, quality, risk and best practices.
It is grounded by the deterministic tool result: it reviews FACTS, it
does not guess whether the code ran."""

from agents.base import Agent


class Reviewer(Agent):
    name = "Reviewer Agent"
    emoji = "🔍"
    system = (
        "You are a senior code reviewer. Be factual and concise. "
        "Base your review on the tool result provided — never claim code "
        "ran or failed unless the tool says so. Cover: correctness, "
        "code quality, risks, and best practices. Use short bullet points. "
        "Do not rewrite the code; that is another agent's job."
    )

    def build_prompt(self, ctx: dict) -> str:
        return f"""Language: {ctx['language']} | User intent: {ctx['intent']}

USER REQUEST:
{ctx['prompt']}

DETERMINISTIC TOOL RESULT (ground truth):
{ctx['tool_output']}

RELEVANT KNOWLEDGE BASE EXTRACTS (may be empty):
{ctx['rag_context'] or '(nothing relevant retrieved)'}

Write your review now."""
