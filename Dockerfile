# 🔨 CodeForge Agents — Dockerfile
# ---------------------------------------------------------------
# Build:   docker build -t codeforge-agents .
# Run:     docker run -p 8501:8501 --env-file .env codeforge-agents
#    or:   docker run -p 8501:8501 -e GROQ_API_KEY=$GROQ_API_KEY codeforge-agents
#    or:   leave the key out entirely and paste it in the app UI sidebar.
#
# SECURITY: the API key is injected at RUNTIME only (or typed into the UI).
# The image never contains it (.env is excluded via .dockerignore).
# Prefer --env-file over -e: a key passed with -e is visible in shell
# history and in `docker inspect`.
#
# TEACHING NOTE — why the index is baked at BUILD time:
#   `python -m rag.ingest` needs NO API key (chunking + embeddings are
#   100% local), so we run it while building. Containers then start
#   with the knowledge base ready: fast startup, no volumes, offline-ready.
#
# THE FIX (v4.x): the model + index are now baked AS THE forge USER.
#   ChromaDB's ONNX embedder downloads to `Path.home()/.cache/chroma/...`,
#   ignoring XDG_CACHE_HOME. Previously ingest ran as root (home=/root)
#   but the container ran as forge (home=/home/forge), so the baked model
#   was unreadable and got re-downloaded (79 MB) on EVERY start. Creating
#   forge first and running ingest as forge bakes it into the SAME home
#   the runtime reads. HOME is pinned too, so it survives even if k8s
#   overrides the UID.
# ---------------------------------------------------------------

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ANONYMIZED_TELEMETRY=False \
    # Pin HOME so Path.home() resolves to /home/forge at BUILD and RUN time,
    # regardless of which UID actually runs the container.
    HOME=/home/forge

# Create the non-root runtime user FIRST (numeric UID 10001 — Kubernetes'
# runAsNonRoot check cannot verify named users). The model + index will
# bake into THIS user's home, which is exactly what runs at startup.
RUN useradd -m -u 10001 forge

# Dependency layer first — Docker caches it, so code changes don't trigger
# a full reinstall.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code (filtered by .dockerignore: no .env, no venv, no .git)
COPY . .
RUN chown -R forge:forge /app /home/forge

# Switch to forge BEFORE baking the index, so the ONNX model lands in
# /home/forge/.cache and chroma_db in /app — both owned and readable by
# the runtime user. No secrets involved; no download at container start.
USER 10001
RUN python -m rag.ingest

EXPOSE 8501

# Healthcheck via Streamlit's built-in endpoint (no curl in slim image).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", \
     "--server.headless=true"]
