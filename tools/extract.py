"""
CodeForge Agents — Code Extraction Helpers
==========================================
Users paste code mixed with questions ("why is this broken? for i in...").
Tools need just the code. Strategy, in priority order:

    1. Markdown fences  ```python ... ```   (explicit, always wins)
    2. Heuristic line scan (looks-like-code lines + their indented bodies)

TEACHING NOTE: The old v3 extractor matched lines containing "=" which
swallowed normal English ("x = my question"). The heuristics below are
stricter — and the markdown-fence path shows students why structured
input beats guessing.
"""

import re

_FENCE_RE = re.compile(r"```[a-zA-Z0-9_+-]*\n(.*?)```", re.DOTALL)

_PY_STARTS = ("def ", "class ", "import ", "from ", "print(", "for ",
              "while ", "if ", "elif ", "else:", "try:", "except",
              "with ", "return ", "@", "async def ")

_YAML_KEYS = ("apiVersion", "kind:", "metadata:", "spec:", "containers:",
              "image:", "name:", "labels:", "replicas:", "ports:")


def extract_fenced(text: str) -> str:
    """Return the contents of all ``` fenced blocks joined together."""
    blocks = _FENCE_RE.findall(text)
    return "\n".join(b.strip("\n") for b in blocks)


def extract_python(text: str) -> str:
    fenced = extract_fenced(text)
    if fenced:
        return fenced
    out, in_code = [], False
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            if in_code:
                out.append(line)
            continue
        starts_like_code = stripped.startswith(_PY_STARTS)
        # assignment heuristic: identifier = value (NOT "==", not prose)
        is_assign = bool(re.match(r"^[A-Za-z_][\w.\[\]'\"]*\s*=[^=]", stripped))
        if starts_like_code or is_assign:
            out.append(line)
            in_code = True
        elif in_code and line[:1] in (" ", "\t"):
            out.append(line)          # indented continuation of a block
        else:
            in_code = False
    return "\n".join(out).strip()


def extract_java(text: str) -> str:
    fenced = extract_fenced(text)
    if fenced:
        return fenced
    # Heuristic: grab from the first 'class'/'import'/annotation line to
    # the last closing brace.
    lines = text.split("\n")
    start = end = None
    for i, line in enumerate(lines):
        s = line.strip()
        if start is None and (
                re.match(r"^(public |private |protected )?(final )?(abstract )?class\s", s)
                or s.startswith(("import ", "package ", "@"))):
            start = i
        if "}" in s:
            end = i
    if start is None or end is None or end < start:
        return ""
    return "\n".join(lines[start:end + 1]).strip()


def extract_yaml(text: str) -> str:
    fenced = extract_fenced(text)
    if fenced:
        return fenced
    out, in_yaml = [], False
    for line in text.split("\n"):
        s = line.strip()
        if any(s.startswith(k) for k in _YAML_KEYS) or s == "---":
            out.append(line)
            in_yaml = True
        elif in_yaml and (line[:1] in (" ", "\t") or s.startswith("- ")
                          or re.match(r"^[\w.-]+:(\s|$)", s)):
            out.append(line)
        elif in_yaml and not s:
            out.append(line)
        else:
            in_yaml = False
    return "\n".join(out).strip()
