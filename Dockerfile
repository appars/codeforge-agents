# 🔨 CodeForge Agents — Dockerfile
# ---------------------------------------------------------------
# Build:   docker build -t codeforge-agents .
# Run:     docker run -p 8501:8501 -e GROQ_API_KEY=$GROQ_API_KEY codeforge-agents
#    or:   docker run -p 8501:8501 --env-file .env codeforge-agents
#
# SECURITY: the API key is injected at RUNTIME only. The image never
# contains it (.env is excluded via .dockerignore) — anyone can pull
# this image safely.
#
# TEACHING NOTE — why the index is baked at BUILD time:
#   `python -m rag.ingest` needs NO API key (chunking + embeddings are
#   100% local), so we run it while building. Containers then start
#   with the knowledge base ready: fast startup, no volumes, and the
#   image works even on an airgapped network.
# ---------------------------------------------------------------

FROM python:3.11-slim

WORKDIR /app

# System layer: keep it minimal (slim image, no compilers needed —
# all our wheels are prebuilt)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ANONYMIZED_TELEMETRY=False \
    # ONNX embedding model caches here; baked into the image at build time
    # (see `python -m rag.ingest` below) so containers start offline-ready
    XDG_CACHE_HOME=/app/.cache

# Dependency layer first — Docker caches it, so code changes don't
# trigger a full reinstall (a classic Dockerfile optimization lesson)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code (filtered by .dockerignore: no .env, no venv, no .git)
COPY . .

# Bake the knowledge index: downloads the MiniLM embedding model once
# and builds chroma_db into the image. No secrets involved.
RUN python -m rag.ingest

EXPOSE 8501

# Healthcheck via Streamlit's built-in endpoint (no curl in slim image,
# so we use Python's stdlib)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Non-root user with a NUMERIC UID — Kubernetes' runAsNonRoot check
# cannot verify named users (the pod would fail with
# CreateContainerConfigError), so we pin UID 10001 explicitly.
RUN useradd -m -u 10001 forge && chown -R forge:forge /app
USER 10001

CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", \
     "--server.headless=true"]
