"""
🔨 CodeForge Agents — Streamlit UI
==================================
This file contains ONLY user interface code. All intelligence lives in:

    core/    config, llm provider, router, memory, demo scenarios
    agents/  reviewer, optimizer, synthesizer
    tools/   python_runner, java_checker, yaml_validator
    rag/     ingest, retrieve

Run:    streamlit run app.py
"""

import streamlit as st

from core import config, memory, router, ui
from core.llm import LLMClient, LLMUnavailableError, get_status
from core.scenarios import SCENARIOS
from agents.reviewer import Reviewer
from agents.optimizer import Optimizer
from agents.synthesizer import Synthesizer
from tools import python_runner, java_checker, yaml_validator
from rag import retrieve as rag

# ---------------------------------------------------------------- Page

st.set_page_config(page_title=config.APP_NAME, page_icon=config.APP_ICON,
                   layout="wide")
ui.inject_css()
ui.hero()

# ---------------------------------------------------------------- Cache
# TEACHING NOTE: Streamlit re-runs this whole script on EVERY interaction.
# @st.cache_resource makes expensive objects (API clients, the health
# check) survive re-runs instead of being rebuilt each time.


@st.cache_resource(show_spinner="Checking LLM backends…")
def get_llm():
    status = get_status()
    return LLMClient(status) if status.ok else None, status


llm, status = get_llm()

# ---------------------------------------------------------------- State

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "context_window" not in st.session_state:
    st.session_state.context_window = config.DEFAULT_CONTEXT_WINDOW


# ---------------------------------------------------------------- Gate
# Optional access gate for public deployments (APP_PASSWORD secret).
# TEACHING NOTE: a public LLM app without any gate lets strangers spend
# your API quota — cost protection is part of deployment design.

if config.APP_PASSWORD:
    if not st.session_state.get("authed", False):
        st.markdown("#### 🔐 This deployment is protected")
        entered = st.text_input("Access passphrase", type="password")
        if entered:
            if entered == config.APP_PASSWORD:
                st.session_state.authed = True
                st.rerun()
            else:
                st.error("Wrong passphrase.")
        st.stop()

# ---------------------------------------------------------------- Sidebar

with st.sidebar:
    st.header("⚙️ Control Center")

    # Real health status — never a hardcoded green light
    ui.status_badge(status)

    if status.provider == "none":
        with st.expander("🔑 How to connect an LLM", expanded=True):
            st.markdown(
                "**Option A — Groq (recommended, free):**\n"
                "1. Get a key at [console.groq.com/keys](https://console.groq.com/keys)\n"
                "2. Copy `.env.example` to `.env`\n"
                "3. Paste the key: `GROQ_API_KEY=gsk_...`\n"
                "4. Restart the app\n\n"
                "**Option B — Ollama (local):** install Ollama, then\n"
                "`ollama pull mistral` and `ollama serve`.")
        if st.button("🔄 Re-check connection"):
            get_llm.clear()
            st.rerun()

    # Knowledge base status / build button
    st.markdown("### 📚 Knowledge Base")
    if rag.index_ready():
        st.caption("✅ Index ready")
    else:
        st.caption("⚠️ Not built yet")
        if st.button("📚 Build Knowledge Base"):
            from rag.ingest import build_index
            with st.spinner("Indexing knowledge files…"):
                result = build_index(progress=lambda m: None)
            (st.success if result["ok"] else st.error)(result["message"])
            st.rerun()

    st.session_state.context_window = st.slider(
        "🧠 Memory window (messages)", 2, 12,
        st.session_state.context_window)

    # Demo scenarios stay reachable after the chat starts
    if st.session_state.messages:
        with st.expander("🎯 Demo Scenarios"):
            for i, sc in enumerate(SCENARIOS):
                if st.button(sc["label"], key=f"side_sc_{i}",
                             use_container_width=True):
                    st.session_state.pending_prompt = sc["prompt"]
                    st.rerun()

    if st.session_state.messages and st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------- Input
# (resolved early so the welcome cards hide the instant a prompt exists)

typed = st.chat_input("💬 Paste code or ask a question…")
prompt = typed or st.session_state.pending_prompt
st.session_state.pending_prompt = None

# ---------------------------------------------------------------- Welcome

if not st.session_state.messages and not prompt:
    st.markdown("#### Click a scenario to watch the agents work")
    cols = st.columns(3)
    for i, sc in enumerate(SCENARIOS):
        with cols[i % 3]:
            if ui.scenario_card(sc, key=f"main_sc_{i}"):
                st.session_state.pending_prompt = sc["prompt"]
                st.rerun()
    if status.provider == "none":
        st.info("💡 No LLM connected — the app still works in **Tools-Only "
                "Mode**: code execution, YAML validation, Java checks and "
                "knowledge retrieval all run without an LLM. Connect Groq "
                "or Ollama (sidebar) for the full agent pipeline.")

# ---------------------------------------------------------------- History

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ---------------------------------------------------------------- Pipeline

if prompt and prompt.strip():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        # ---- 1. Router -------------------------------------------------
        with st.spinner("🧭 Routing…"):
            route = router.classify(prompt, llm)
        with st.expander(f"🧭 Router — `{route['language']}` / "
                         f"`{route['intent']}` "
                         f"(via {route['method']})", expanded=False):
            st.markdown(
                f"**Language:** `{route['language']}`  \n"
                f"**Intent:** `{route['intent']}`  \n"
                f"**Method:** `{route['method']}` "
                + ("(LLM classifier)" if route["method"] == "llm"
                   else "(keyword fallback — no LLM needed)"))

        # ---- 2. RAG ------------------------------------------------------
        with st.spinner("📚 Retrieving knowledge…"):
            retrieval = rag.retrieve(prompt, route["language"])
        with st.expander(f"📚 RAG — {len(retrieval['hits'])} chunk(s) "
                         "retrieved", expanded=False):
            st.caption(retrieval["note"])
            for hit in retrieval["hits"]:
                st.markdown(f"**{hit['source']}** › *{hit['section']}* "
                            f"— similarity `{hit['score']}`")
                st.code(hit["preview"], language=None)

        # ---- 3. Deterministic tool ----------------------------------------
        tool_fn = {"python": python_runner.run,
                   "java": java_checker.run,
                   "yaml": yaml_validator.run}.get(route["language"])
        if tool_fn and route["intent"] != "explain":
            with st.spinner("⚙️ Running tool…"):
                tool = tool_fn(prompt)
        else:
            tool = {"ok": True, "title": "⚙️ No tool needed",
                    "output": "This request goes straight to the agents.",
                    "code": ""}
        with st.expander(tool["title"], expanded=not tool["ok"]):
            st.text(tool["output"])

        ctx = {
            "prompt": prompt,
            "language": route["language"],
            "intent": route["intent"],
            "tool_output": f"{tool['title']}\n{tool['output']}",
            "rag_context": retrieval["context"],
            "memory": memory.build_memory(st.session_state.messages,
                                          st.session_state.context_window),
        }

        # ---- 4-6. LLM agents (or Tools-Only Mode) ---------------------------
        if llm is None:
            final = (
                "⚠️ **Tools-Only Mode** (no LLM connected)\n\n"
                f"**{tool['title']}**\n```\n{tool['output']}\n```\n"
                + (f"\n**📚 Retrieved knowledge:**\n\n{retrieval['context']}\n"
                   if retrieval["context"] else "")
                + "\n*Connect Groq or Ollama (sidebar) to get the full "
                  "Reviewer → Optimizer → Synthesizer analysis.*")
            st.markdown(final)
        else:
            try:
                with st.spinner("🔍 Reviewer Agent…"):
                    ctx["reviewer"] = Reviewer(llm).run(ctx)
                with st.expander("🔍 Reviewer Agent"):
                    st.markdown(ctx["reviewer"])

                with st.spinner("⚡ Optimizer Agent…"):
                    ctx["optimizer"] = Optimizer(llm).run(ctx)
                with st.expander("⚡ Optimizer Agent"):
                    st.markdown(ctx["optimizer"])

                st.markdown("**✅ Final Answer**")
                final = st.write_stream(Synthesizer(llm).stream(ctx))
            except LLMUnavailableError as e:
                final = (f"{e}\n\n**The deterministic tool still worked:**\n"
                         f"```\n{tool['output']}\n```")
                st.markdown(final)

    st.session_state.messages.append({"role": "assistant",
                                      "content": str(final)})
