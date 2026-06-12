"""Final Synthesizer — merges everything (memory, knowledge, tool result,
reviewer, optimizer) into ONE clear answer for the user.

This is the only agent that streams: the user watches the final answer
being written token by token."""

from agents.base import Agent


class Synthesizer(Agent):
    name = "Final Synthesizer"
    emoji = "✅"
    system = (
        "You are the final answer writer of a multi-agent system. "
        "Merge the tool result, reviewer notes and optimizer notes into "
        "one clear, concise answer. Rules: "
        "(1) If the code is broken, show the corrected code in a fenced "
        "block and explain the fix in one or two sentences. "
        "(2) If team standards from the knowledge base apply, check the "
        "code against them explicitly. "
        "(3) Do not repeat the other agents verbatim — synthesize. "
        "(4) Answer in the user's language of conversation."
    )

    def build_prompt(self, ctx: dict) -> str:
        return f"""CONVERSATION MEMORY:
{ctx['memory']}

LANGUAGE: {ctx['language']} | INTENT: {ctx['intent']}

USER REQUEST:
{ctx['prompt']}

TOOL RESULT (ground truth):
{ctx['tool_output']}

KNOWLEDGE BASE EXTRACTS:
{ctx['rag_context'] or '(nothing relevant retrieved)'}

REVIEWER AGENT SAID:
{ctx['reviewer']}

OPTIMIZER AGENT SAID:
{ctx['optimizer']}

Write the final answer for the user now."""

    def stream(self, ctx: dict):
        """Yield the final answer token by token (for st.write_stream)."""
        yield from self.llm.stream(
            [{"role": "system", "content": self.system},
             {"role": "user", "content": self.build_prompt(ctx)}])
