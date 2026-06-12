"""
CodeForge Agents — UI Design System
===================================
All visual identity lives here so app.py stays logic-only.

Design direction ("the forge"):
    * gunmetal steel surfaces, ONE ember-orange accent (#FF6B35)
    * Space Grotesk for display, Inter for body, IBM Plex Mono for
      the engineering details (paths, chips, scores)
    * signature element: the agent pipeline rendered as a glowing
      production line — the pipeline IS the product being taught

TEACHING NOTE: Streamlit's class names change between releases, so the
CSS targets stable `data-testid` attributes and element tags wherever
possible. Theme colors come from .streamlit/config.toml; this file adds
typography, the hero, and component polish on top.
"""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* ---------- base ---------- */
html, body, [data-testid="stAppViewContainer"] * {
    font-family: 'Inter', sans-serif;
}
code, pre, .cf-mono { font-family: 'IBM Plex Mono', monospace !important; }

.block-container { padding-top: 2.2rem; max-width: 1080px; }

/* ---------- hero ---------- */
.cf-hero h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem; font-weight: 700; letter-spacing: -0.02em;
    margin: 0 0 0.2rem 0; line-height: 1.1;
}
.cf-hero .forge { color: #FF6B35; }
.cf-hero .tagline {
    color: #9aa0ab; font-size: 1.02rem; margin: 0 0 1.1rem 0;
}
.cf-rule {
    height: 3px; width: 72px; border-radius: 2px; margin: 0 0 1.2rem 0;
    background: linear-gradient(90deg, #FF6B35, rgba(255,107,53,0));
}

/* ---------- pipeline strip (the signature) ---------- */
.cf-pipe {
    display: flex; flex-wrap: wrap; align-items: center;
    gap: 0.45rem; margin: 0 0 1.6rem 0;
}
.cf-stage {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
    padding: 0.28rem 0.65rem; border-radius: 999px;
    border: 1px solid #2a2f39; background: #1C2027; color: #c9cdd5;
    transition: border-color .15s, box-shadow .15s;
    white-space: nowrap;
}
.cf-stage:hover {
    border-color: #FF6B35; box-shadow: 0 0 12px rgba(255,107,53,.25);
}
.cf-arrow { color: #FF6B35; font-size: 0.8rem; }

/* ---------- scenario cards ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px;
    transition: border-color .15s, box-shadow .15s, transform .15s;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #FF6B35 !important;
    box-shadow: 0 4px 22px rgba(255,107,53,.12);
    transform: translateY(-2px);
}
.cf-path {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
    color: #8a909c; line-height: 1.5; margin-top: 0.35rem;
}
.cf-path b { color: #FF6B35; font-weight: 500; }

/* ---------- buttons ---------- */
.stButton button {
    border-radius: 9px; font-weight: 600;
    transition: border-color .15s, color .15s;
}
.stButton button:hover { border-color: #FF6B35; color: #FF6B35; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {
    border-right: 1px solid #232833;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.01em;
}
.cf-badge {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.86rem; padding: 0.55rem 0.7rem; border-radius: 9px;
    border: 1px solid #2a2f39; background: #1C2027; line-height: 1.45;
}
.cf-dot { font-size: 0.7rem; }
.cf-badge.ok     { border-color: rgba(61,220,132,.4); }
.cf-badge.warn   { border-color: rgba(255,196,61,.4); }
.cf-badge.down   { border-color: rgba(255,93,93,.4); }

/* ---------- expanders (agent steps) ---------- */
details[data-testid="stExpander"] {
    border: 1px solid #232833; border-radius: 10px; background: #181B21;
}
details[data-testid="stExpander"] summary {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem;
}

/* ---------- chat ---------- */
[data-testid="stChatInput"] { border-radius: 12px; }
h3, h4 { font-family: 'Space Grotesk', sans-serif; }
</style>
"""

PIPELINE_STAGES = ["🧭 Router", "📚 RAG", "⚙️ Tool",
                   "🔍 Reviewer", "⚡ Optimizer", "✅ Synthesizer"]


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def hero():
    """Title + tagline + the signature pipeline strip."""
    stages = '<span class="cf-arrow">→</span>'.join(
        f'<span class="cf-stage">{s}</span>' for s in PIPELINE_STAGES)
    st.markdown(
        f"""
        <div class="cf-hero">
          <h1>🔨 Code<span class="forge">Forge</span> Agents</h1>
          <p class="tagline">Watch AI agents debug, review and optimize
          your code — live, with the hood open.</p>
          <div class="cf-rule"></div>
          <div class="cf-pipe">{stages}</div>
        </div>
        """, unsafe_allow_html=True)


def status_badge(status):
    """Sidebar connection badge with state-colored border."""
    cls = {"groq": "ok", "ollama": "warn"}.get(status.provider, "down")
    st.markdown(
        f'<div class="cf-badge {cls}"><span class="cf-dot">'
        f'{status.emoji}</span><span>{status.detail}</span></div>',
        unsafe_allow_html=True)


def scenario_card(scenario, key):
    """One bordered, hover-glowing card: button + mono pipeline path.
    Returns True when clicked."""
    with st.container(border=True):
        clicked = st.button(scenario["label"], key=key,
                            use_container_width=True)
        path = scenario["path"].replace("→", '<b>→</b>')
        st.markdown(f'<div class="cf-path">{path}</div>',
                    unsafe_allow_html=True)
    return clicked
