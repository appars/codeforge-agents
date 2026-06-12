"""
CodeForge Agents — Unit Tests
=============================
Tests everything that runs WITHOUT an API key or internet:
deterministic tools, the keyword router fallback, and RAG chunking.

Run from the project root:    python -m pytest tests/ -v
(or simply:                   python tests/test_all.py)

TEACHING NOTE: notice what is testable — the deterministic parts.
LLM outputs need evaluation, not assertion. That split is itself a
lesson in agentic system design.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.router import keyword_classify
from rag.chunking import chunk_markdown
from tools import python_runner, java_checker, yaml_validator
from tools.extract import extract_python, extract_yaml


# ------------------------------------------------------------- Python tool

def test_python_syntax_error_caught():
    res = python_runner.run("debug this:\n```python\nfor i in range(5)\n    print(i)\n```")
    assert not res["ok"]
    assert "SyntaxError" in res["output"]


def test_python_executes_ok():
    res = python_runner.run("```python\nprint(2 + 2)\n```")
    assert res["ok"]
    assert "4" in res["output"]


def test_python_runtime_error():
    res = python_runner.run("```python\nprint(1 / 0)\n```")
    assert not res["ok"]
    assert "ZeroDivisionError" in res["output"]


def test_python_infinite_loop_killed():
    res = python_runner.run("```python\nwhile True:\n    pass\n```")
    assert not res["ok"]
    assert "Timeout" in res["title"]


def test_python_no_code():
    res = python_runner.run("what is a variable?")
    assert "No runnable Python" in res["output"]


# ------------------------------------------------------------- Java tool

def test_java_missing_semicolon_flagged():
    code = ('```java\npublic class Greeter {\n'
            '    public static void main(String[] args) {\n'
            '        System.out.println("hi")\n    }\n}\n```')
    res = java_checker.run(code)
    assert any("';'" in line or "semicolon" in line.lower()
               for line in res["output"].split("\n"))


def test_java_unbalanced_braces():
    res = java_checker.run("```java\npublic class A {\n  void f() {\n}\n```")
    assert "Unbalanced braces" in res["output"]


# ------------------------------------------------------------- YAML tool

def test_yaml_valid_k8s():
    yml = """```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test
spec:
  containers:
    - name: app
      image: nginx:1.25
      resources: {}
      livenessProbe: {}
```"""
    res = yaml_validator.run(yml)
    assert res["ok"]


def test_yaml_missing_name():
    yml = "```yaml\napiVersion: v1\nkind: Pod\nmetadata:\n  labels:\n    a: b\nspec: {}\n```"
    res = yaml_validator.run(yml)
    assert not res["ok"]
    assert "metadata.name" in res["output"]


def test_yaml_tab_error():
    res = yaml_validator.run("```yaml\napiVersion: v1\nkind: Pod\nmetadata:\n\tname: x\n```")
    assert not res["ok"]
    assert "Syntax Error" in res["title"]


# --------------------------------------------------------- Router fallback

def test_router_python():
    r = keyword_classify("debug this: def f():\n    print('x')")
    assert r["language"] == "python" and r["intent"] == "debug"


def test_router_yaml():
    r = keyword_classify("fix my yaml:\napiVersion: v1\nkind: Pod")
    assert r["language"] == "yaml"


def test_router_java():
    r = keyword_classify("public class A { public static void main(String[] a){;} }")
    assert r["language"] == "java"


def test_router_chitchat_is_general():
    r = keyword_classify("hello, how are you today?")
    assert r["language"] == "general" and r["intent"] == "general"


def test_router_prose_with_equals_not_python():
    # The old v3 router misrouted this because it matched "="
    r = keyword_classify("my favourite equation is E = mc squared, explain it")
    assert r["language"] == "general"


# -------------------------------------------------------------- Chunking

def test_chunk_markdown_sections():
    md = "# Title\n\nintro text\n\n## First\nbody one\n\n## Second\nbody two"
    chunks = chunk_markdown(md, "demo")
    sections = [c["section"] for c in chunks]
    assert sections == ["intro", "First", "Second"]
    assert all(c["text"].startswith("Title — ") for c in chunks)
    assert len({c["id"] for c in chunks}) == 3      # ids unique


# -------------------------------------------------------------- Extraction

def test_extract_prefers_fences():
    text = "Fix this please\n```python\nprint('hi')\n```\nthanks!"
    assert extract_python(text) == "print('hi')"


def test_extract_yaml_heuristic():
    text = "my manifest:\napiVersion: v1\nkind: Pod\nmetadata:\n  name: x"
    out = extract_yaml(text)
    assert "apiVersion: v1" in out and "my manifest" not in out


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ✅ {name}")
            except AssertionError as e:
                failures += 1
                print(f"  ❌ {name}: {e}")
    print(f"\n{'❌ FAILURES: ' + str(failures) if failures else '✅ All tests passed'}")
    sys.exit(1 if failures else 0)
