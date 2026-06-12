# 🔨 CodeForge Agents

**Watch AI agents debug, review and optimize your code — live.**

CodeForge Agents is a teaching-first **multi-agent AI engineering assistant** for **Python, Java and Kubernetes YAML**. Every step of the agent pipeline — routing, knowledge retrieval, tool execution, review, optimization, synthesis — is visible in the UI, so students see *how* agentic AI works, not just *that* it works.

Built with **Streamlit + Groq (or local Ollama) + ChromaDB**.

---

## Architecture

```text
User Prompt
    ↓
🧭 Router            small fast LLM classifies language + intent
    ↓                (keyword fallback works with no LLM at all)
📚 RAG Retrieval     ChromaDB · per-section chunks · metadata filter
    ↓                · relevance threshold · scores shown in UI
⚙️ Deterministic Tool python: safe subprocess exec · java: static
    ↓                checks + optional javac · yaml: K8s validation
🔍 Reviewer Agent    grounded by the tool result (the ground truth)
    ↓
⚡ Optimizer Agent   honest: says "no optimization needed" when true
    ↓
✅ Final Synthesizer streams the merged answer token by token
```

The folder structure mirrors this diagram — each module is a lecture:

```text
codeforge-agents/
├── app.py              # Streamlit UI only — no business logic
├── core/
│   ├── config.py       # ALL settings in one place; secrets from .env
│   ├── llm.py          # provider abstraction: Groq ⇄ Ollama ⇄ offline
│   ├── router.py       # LLM classifier + keyword fallback
│   ├── memory.py       # sliding-window conversation memory
│   └── scenarios.py    # the six clickable demo scenarios
├── agents/             # base class + Reviewer / Optimizer / Synthesizer
├── tools/              # python_runner / java_checker / yaml_validator
├── rag/                # chunking / ingest / retrieve
├── knowledge/          # 6 markdown knowledge files (see below)
├── tests/              # 18 unit tests — run with no API key needed
├── Dockerfile · .dockerignore
├── k8s/                # Deployment + Service manifests (secret via kubectl)
├── DEPLOYMENT.md       # Docker / Kubernetes / Streamlit Cloud guide
├── DEMO_GUIDE.md       # 12 verified classroom demos in 5 acts
└── Makefile · LICENSE · .github/workflows/ci.yml
```

---

## Quick Start

```bash
# 1. Clone and enter
git clone <your-repo-url> && cd codeforge-agents

# 2. Virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install
pip install -r requirements.txt

# 4. Configure (free Groq key from https://console.groq.com/keys)
cp .env.example .env
#    → edit .env and paste: GROQ_API_KEY=gsk_...

# 5. Build the knowledge index (first run downloads a small embedding model)
python -m rag.ingest

# 6. Launch
streamlit run app.py
```

**No API key? No problem.** The app boots into **Tools-Only Mode**: code execution, YAML validation, Java checks and knowledge retrieval all work without any LLM, with a banner explaining how to connect one. With **Ollama** installed locally (`ollama pull mistral`, `ollama serve`) the app falls back to it automatically.

---

## The LLM strategy (a lesson in itself)

| Job | Model | Why |
|---|---|---|
| Router (classification) | `llama-3.1-8b-instant` | tiny task → tiny, fast, cheap model |
| Agents (reasoning) | `openai/gpt-oss-120b` | review/optimization need real reasoning |
| Local fallback | `mistral` via Ollama | zero-cost, fully offline |

Change any of these in `.env` — agent code never changes. That is the point of `core/llm.py`.

---

## Knowledge base & RAG

Six markdown files in `knowledge/`, chunked **per `##` section** with metadata (`language`, `topic`, `source`):

- `python_debug.md`, `python_optimization.md`, `java_debug.md`, `yaml_k8s_debug.md`, `k8s_best_practices.md` — real *error → cause → fix* references
- **`team_standards.md`** — fictional internal engineering rules. This is the RAG showpiece: no LLM can know these from training, so when a student asks *"does this code follow our team standards?"*, the correct answer can ONLY come from retrieval. **Instructors:** replace these rules with your own course's grading standards and re-run `python -m rag.ingest` to make the lesson personal.

Retrieval applies a **relevance threshold** — if nothing scores high enough, it retrieves *nothing* (watch the RAG expander say so), avoiding context pollution. The Router's language decision **filters** retrieval by metadata.

---

## Classroom demo script (the six buttons)

| # | Scenario | Pipeline path it demonstrates |
|---|---|---|
| 1 | 🐍 Debug broken Python | tool catches SyntaxError *before* any LLM reasoning |
| 2 | ☸️ Fix a Kubernetes YAML | structure validation finds the missing `metadata.name` |
| 3 | ☕ Review a Java class | static checks: missing `;`, `==` vs `.equals()` |
| 4 | 📚 Team standards check | **RAG**: answerable only via `team_standards.md` |
| 5 | ⚡ Optimize a nested loop | Optimizer turns O(n²) into a set/dict O(n) |
| 6 | 📖 Explain code | router picks `explain` → no tool fires (correct restraint) |

Six clicks = a complete tour of the architecture.

---

## Module → lecture mapping

| Module | Teaching topic |
|---|---|
| `core/llm.py` | provider abstraction, graceful degradation, friendly errors |
| `core/router.py` | LLM-as-classifier vs heuristics (before/after demo) |
| `tools/python_runner.py` | tool guardrails: subprocess, timeout, why not `exec()` |
| `tools/java_checker.py` | capability honesty: degrade through levels, never pretend |
| `rag/chunking.py` + `ingest.py` | chunking strategy, metadata, idempotent indexing |
| `rag/retrieve.py` | relevance thresholds, context pollution, filtered search |
| `agents/base.py` | the agent abstraction: persona + context → output |
| `agents/synthesizer.py` | grounding, synthesis, streaming UX |
| `tests/test_all.py` | what is testable in an agentic system (and what isn't) |

---

## Tests

```bash
python tests/test_all.py        # or: python -m pytest tests/ -v
```

18 tests covering all three tools, the router fallback, extraction and chunking — **no API key or internet needed**, by design.

---

## Honest security note (read this with your students)

`subprocess` + isolated mode + timeout makes Python execution far safer than the naive `exec()` it replaces — infinite loops are killed, the app process is protected. **It is still not a true sandbox**: the child process runs with your OS permissions. Production systems use containers, gVisor or Firecracker microVMs. Knowing exactly where the residual risk lives is part of the lesson.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| 🔴 "No LLM available" | add `GROQ_API_KEY` to `.env`, or start Ollama — app still works in Tools-Only Mode meanwhile |
| 401 invalid key | re-copy the key from console.groq.com/keys into `.env` |
| 429 rate limit | each student should create their **own** free key rather than sharing |
| "Knowledge base is empty" | run `python -m rag.ingest` or just reload the app (it auto-builds) |
| Model not found (404) | model deprecated — update `AGENT_MODEL` in `.env` (see console.groq.com/docs/models) |
| `javac` skipped | install a JDK for Level-2 Java checking (static checks still run) |

---

## Deployment

See **DEPLOYMENT.md** for Docker, Kubernetes and Streamlit Community Cloud,
including how secrets are injected per platform and why the knowledge index
is baked into the Docker image at build time. Quick taste:

```bash
make docker-build && make docker-run
```

For public URLs, set the optional `APP_PASSWORD` secret to gate access and
protect your Groq quota.

## Author

**Apparsamy Perumal**
Professor of Practice | AI | DevOps | Cloud | Agentic AI Research
GitHub: https://github.com/appars

Part of the **Forge** teaching series, alongside InsightForge.

---

*"From code assistant to engineering co-pilot — with the hood open."*
