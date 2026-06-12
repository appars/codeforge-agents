"""
CodeForge Agents — Java Tool
============================
Java can't be executed as easily as Python on a student laptop, so this
tool degrades gracefully through THREE levels:

    Level 1 (always)     — static structure checks in pure Python
                           (brace balance, missing semicolons, class name)
    Level 2 (if JDK)     — real `javac` compilation in a temp dir
    Level 3 (LLM agents) — deep reasoning, grounded by the results above

TEACHING NOTE: tools should report capability honestly. If javac is
missing we SAY so instead of pretending we compiled.
"""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from tools.extract import extract_java

_STMT_RE = re.compile(
    r"^(return\b|break\b|continue\b|throw\b|"
    r"(int|long|double|float|boolean|char|byte|short|String|var)\s+\w+.*|"
    r"[\w.\[\]<>]+\s*=\s*.+|"
    r"System\.out\.print.*|\w[\w.]*\(.*\))$"
)


def _static_checks(code: str) -> list[str]:
    findings = []

    # Brace balance ------------------------------------------------------
    opens, closes = code.count("{"), code.count("}")
    if opens != closes:
        findings.append(f"Unbalanced braces: {opens} '{{' vs {closes} '}}'.")

    # Missing semicolons (heuristic on statement-looking lines) ----------
    for n, line in enumerate(code.split("\n"), 1):
        s = line.strip()
        if not s or s.startswith(("//", "*", "/*", "@", "import ", "package ")):
            continue
        if s.endswith(("{", "}", ";", ",", "(", "&&", "||", "+")):
            continue
        if _STMT_RE.match(s):
            findings.append(f"Line {n} may be missing a ';' → `{s[:60]}`")

    # Public class / filename rule ----------------------------------------
    m = re.search(r"public\s+class\s+(\w+)", code)
    if m:
        findings.append(f"Reminder: public class `{m.group(1)}` must live in "
                        f"`{m.group(1)}.java` (class name = filename).")

    # main method present? -------------------------------------------------
    if "class" in code and "static void main" not in code:
        findings.append("No `public static void main(String[] args)` found — "
                        "fine for a library class, but it won't run directly.")
    return findings


def _try_javac(code: str) -> str | None:
    """Compile with the real JDK if available. Returns report or None."""
    javac = shutil.which("javac")
    if not javac:
        return None
    m = re.search(r"public\s+class\s+(\w+)", code)
    cls = m.group(1) if m else (re.search(r"class\s+(\w+)", code) or [None, "Main"])[1]
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"{cls}.java"
        src.write_text(code)
        try:
            proc = subprocess.run([javac, str(src)], capture_output=True,
                                  text=True, timeout=20)
        except subprocess.TimeoutExpired:
            return "⏱️ javac timed out."
        if proc.returncode == 0:
            return "✅ javac: compiled successfully (no errors)."
        return f"❌ javac errors:\n{proc.stderr.strip()[-1500:]}"


def run(text: str) -> dict:
    code = extract_java(text)
    if not code:
        return {"ok": False, "title": "☕ Java Tool",
                "output": "No Java code block found — passing the text "
                          "straight to the agents.",
                "code": ""}

    parts = []

    findings = _static_checks(code)
    if findings:
        parts.append("🔎 Static checks (pure Python, no JDK needed):\n"
                     + "\n".join(f"  • {f}" for f in findings))
    else:
        parts.append("🔎 Static checks: no structural problems spotted.")

    javac_report = _try_javac(code)
    if javac_report is None:
        parts.append("ℹ️ `javac` not found on this machine — skipped real "
                     "compilation. Install a JDK for Level-2 checking.")
        ok = not findings
    else:
        parts.append(javac_report)
        ok = javac_report.startswith("✅")

    return {"ok": ok, "title": "☕ Java Tool", "output": "\n\n".join(parts),
            "code": code}
