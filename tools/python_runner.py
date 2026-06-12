"""
CodeForge Agents — Python Tool
==============================
1. Extract Python code from the user message
2. Syntax-check it with compile()  (instant, free, deterministic)
3. If syntax is OK, run it in a SEPARATE PROCESS with a hard timeout

WHY subprocess instead of exec()?
    * exec() runs in OUR process — an infinite loop freezes the whole app,
      and the code can touch our variables.
    * subprocess + timeout: infinite loops get killed after N seconds.

HONEST LIMITATION (tell your students!): this is NOT a real sandbox.
The child process still has the user's OS permissions. Production
systems use containers, gVisor, or Firecracker. Knowing where the
remaining risk lives is part of the lesson.
"""

import subprocess
import sys

from core import config
from tools.extract import extract_python


def run(text: str) -> dict:
    """Returns {ok, title, output, code} for the Executor expander."""
    code = extract_python(text)
    if not code:
        return {"ok": False, "title": "🐍 Python Tool",
                "output": "No runnable Python code found — passing the text "
                          "straight to the agents for analysis.",
                "code": ""}

    # ---- Step 1: deterministic syntax check (no LLM needed!) ----------
    try:
        compile(code, "<user_code>", "exec")
    except SyntaxError as e:
        pointer = f"line {e.lineno}: {e.text.strip() if e.text else ''}"
        return {"ok": False, "title": "🐍 Python Tool — Syntax Error",
                "output": f"❌ SyntaxError: {e.msg}\n   at {pointer}\n\n"
                          "The tool caught this BEFORE any LLM reasoning — "
                          "deterministic checks are fast, free and exact.",
                "code": code}

    # ---- Step 2: run in an isolated process with a timeout ------------
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", code],   # -I = isolated mode
            capture_output=True, text=True,
            timeout=config.PYTHON_EXEC_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "title": "🐍 Python Tool — Timeout",
                "output": f"⏱️ Execution killed after "
                          f"{config.PYTHON_EXEC_TIMEOUT}s (infinite loop?). "
                          "This is the timeout guardrail doing its job.",
                "code": code}
    except Exception as e:                         # extremely rare
        return {"ok": False, "title": "🐍 Python Tool — Error",
                "output": f"Could not launch Python subprocess: {e}",
                "code": code}

    if proc.returncode == 0:
        out = proc.stdout.strip() or "(no output — code ran without printing)"
        return {"ok": True, "title": "🐍 Python Tool — Executed OK",
                "output": f"✅ Exit code 0\n\n--- stdout ---\n{out}",
                "code": code}

    return {"ok": False, "title": "🐍 Python Tool — Runtime Error",
            "output": f"❌ Exit code {proc.returncode}\n\n--- stderr ---\n"
                      f"{proc.stderr.strip()[-1500:]}",
            "code": code}
