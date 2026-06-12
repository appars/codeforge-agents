"""
CodeForge Agents — Central Configuration
========================================
All settings live here. Secrets come from the .env file (never hardcoded!).

TEACHING NOTE: Keeping configuration in ONE place is a core professional
practice. Students should never see API keys inside application code.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Disable ChromaDB's anonymous telemetry globally — keeps everything local
# and silences harmless "Failed to send telemetry event" warnings caused by
# posthog version mismatches. Must be set BEFORE chromadb is imported, and
# config.py is imported first everywhere, so this is the right place.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY_DISABLED", "1")

# Load .env from the project root (silently does nothing if missing)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------- App
APP_NAME = "CodeForge Agents"
APP_ICON = "🔨"
APP_VERSION = "4.0"
APP_TAGLINE = "Watch AI agents debug, review and optimize your code — live."

# ---------------------------------------------------------------- LLM
# Provider preference: "auto" tries Groq first, then Ollama, then tools-only.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")          # auto | groq | ollama
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Two-model strategy (a professional pattern):
#   * small + fast model for classification (the Router)
#   * large reasoning model for the agent pipeline
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "llama-3.1-8b-instant")
AGENT_MODEL = os.getenv("AGENT_MODEL", "openai/gpt-oss-120b")

# Local fallback (Ollama)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))  # seconds per LLM call

# ---------------------------------------------------------------- Tools
PYTHON_EXEC_TIMEOUT = int(os.getenv("PYTHON_EXEC_TIMEOUT", "5"))  # seconds

# ---------------------------------------------------------------- RAG
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
CHROMA_DIR = str(PROJECT_ROOT / "chroma_db")
COLLECTION_NAME = "codeforge_knowledge"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RAG_TOP_K = 3
# Similarity threshold (cosine similarity, 0..1). Below this we retrieve
# NOTHING — better no context than wrong context ("context pollution").
RAG_MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.25"))

# ---------------------------------------------------------------- Memory
DEFAULT_CONTEXT_WINDOW = 6   # number of recent messages given to agents
