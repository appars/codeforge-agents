"""
CodeForge Agents — Agent Base Class
===================================
Every agent is the same simple shape:

    name + emoji      -> what the UI shows
    system prompt     -> the agent's PERSONA and rules
    build_prompt()    -> turns shared context into this agent's input
    run(context)      -> one LLM call, returns text

TEACHING NOTE: "Multi-agent" here means specialised prompts run in a
pipeline — each agent sees the previous agents' output. That IS a
legitimate agent pattern (sequential / pipeline). Frameworks like
LangGraph add branching and loops on top of exactly this idea.
"""

from core.llm import LLMClient, LLMUnavailableError


class Agent:
    name = "Agent"
    emoji = "🤖"
    system = "You are a helpful assistant."

    def __init__(self, llm: LLMClient):
        self.llm = llm

    # Subclasses override this -------------------------------------------
    def build_prompt(self, ctx: dict) -> str:
        raise NotImplementedError

    # Shared plumbing ------------------------------------------------------
    def run(self, ctx: dict) -> str:
        try:
            return self.llm.chat(
                [{"role": "system", "content": self.system},
                 {"role": "user", "content": self.build_prompt(ctx)}])
        except LLMUnavailableError as e:
            return f"⚠️ {self.name} could not run: {e}"

    @property
    def label(self) -> str:
        return f"{self.emoji} {self.name}"
