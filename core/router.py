"""
CodeForge Agents — Intent Router
================================
Classifies every user prompt along two axes:

    language : python | java | yaml | general
    intent   : debug | explain | refactor | optimize | review | general

Strategy (a professional pattern worth teaching):
    1. PRIMARY  — ask a small, fast LLM to classify (cheap + accurate)
    2. FALLBACK — score-based keyword heuristics (works with no LLM at all)

The old v3 router matched single characters like "=" which misrouted
almost everything. The fallback below uses weighted SCORES instead of
first-match keywords — compare both in class as a before/after lesson.
"""

import json
import re

from core import config
from core.llm import LLMClient, LLMUnavailableError

LANGUAGES = ("python", "java", "yaml", "general")
INTENTS = ("debug", "explain", "refactor", "optimize", "review", "general")

_CLASSIFY_PROMPT = """You are a strict classifier. Read the user message and
respond with ONLY a JSON object, no prose, no markdown fences:

{{"language": "<python|java|yaml|general>", "intent": "<debug|explain|refactor|optimize|review|general>"}}

Rules:
- "yaml" covers YAML and Kubernetes manifests.
- If the message contains code with an error or asks to fix something -> "debug".
- If no programming content is present -> language "general", intent "general".

User message:
---
{prompt}
---"""


def classify(prompt: str, llm: LLMClient | None) -> dict:
    """Returns {"language": ..., "intent": ..., "method": "llm"|"keywords"}."""
    if llm is not None and llm.provider != "none":
        try:
            raw = llm.chat(
                [{"role": "user",
                  "content": _CLASSIFY_PROMPT.format(prompt=prompt[:4000])}],
                model=config.ROUTER_MODEL, temperature=0.0, max_tokens=100)
            data = json.loads(_extract_json(raw))
            lang = data.get("language", "general").lower()
            intent = data.get("intent", "general").lower()
            if lang in LANGUAGES and intent in INTENTS:
                return {"language": lang, "intent": intent, "method": "llm"}
        except (LLMUnavailableError, json.JSONDecodeError, AttributeError):
            pass  # fall through to keywords
    return keyword_classify(prompt)


def _extract_json(text: str) -> str:
    """LLMs sometimes wrap JSON in ``` fences or prose — dig it out."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else "{}"


# ------------------------------------------------------------ Fallback

def keyword_classify(prompt: str) -> dict:
    """No-LLM fallback. Scores each language; highest score wins,
    'general' wins if nothing scores."""
    text = prompt.lower()

    scores = {"python": 0, "java": 0, "yaml": 0}

    python_signals = ["def ", "print(", "import ", "elif", "lambda",
                      "self.", "python", "pip ", "range(", "f\"", "f'"]
    java_signals = ["public class", "public static void main",
                    "system.out.println", "private ", "void ", "extends ",
                    "implements ", "new ", "java", ";"]
    yaml_signals = ["apiversion", "kind:", "metadata:", "spec:",
                    "containers:", "kubernetes", "k8s", "yaml",
                    "kubectl", "deployment", "replicas:"]

    for sig in python_signals:
        if sig in text:
            scores["python"] += 2
    for sig in java_signals:
        if sig in text:
            scores["java"] += 2 if len(sig) > 2 else 1   # ";" is weak evidence
    for sig in yaml_signals:
        if sig in text:
            scores["yaml"] += 2

    # Indented "key: value" lines are strong YAML evidence
    if re.search(r"^\s+\w[\w.-]*:\s", prompt, re.MULTILINE):
        scores["yaml"] += 2
    # Braces + semicolons together lean Java
    if "{" in prompt and ";" in prompt:
        scores["java"] += 1

    best_lang, best_score = max(scores.items(), key=lambda kv: kv[1])
    language = best_lang if best_score >= 2 else "general"

    intent_map = {
        "debug": ["debug", "fix", "error", "broken", "wrong", "fail",
                  "issue", "bug", "not work"],
        "explain": ["explain", "what does", "what is", "understand",
                    "describe", "how does"],
        "refactor": ["refactor", "rewrite", "clean", "restructure"],
        "optimize": ["optimi", "faster", "performance", "speed up",
                     "efficient"],
        "review": ["review", "feedback", "best practice", "standards",
                   "quality"],
    }
    intent = "general"
    for name, words in intent_map.items():
        if any(w in text for w in words):
            intent = name
            break
    # Code present but no explicit ask? Assume the user wants debugging.
    if intent == "general" and language != "general":
        intent = "debug"

    return {"language": language, "intent": intent, "method": "keywords"}
