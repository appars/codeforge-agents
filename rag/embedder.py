"""
CodeForge Agents — Embedding Backend
====================================
ONE place that turns text into vectors, so ingest and retrieve always
agree on the model.

WHY ONNX, NOT sentence-transformers (the deployment lesson):
sentence-transformers pulls in PyTorch + the CUDA stack — gigabytes that
overwhelm a small cloud container (Streamlit Cloud's ~1 GB box) and make
the app fail to boot. ChromaDB ships the SAME model, all-MiniLM-L6-v2,
as a lightweight ONNX runtime build (onnxruntime, ~100 MB, no torch).
Same embeddings, same quality, a fraction of the weight — and it runs
identically on a laptop, in Docker, in Kubernetes, and on Streamlit Cloud.

If even ONNX cannot load, embeddings are UNAVAILABLE and the caller
disables RAG. We deliberately do NOT fake embeddings: irrelevant
"context" is worse than no context.
"""

_embedder = None
_failed = False


class EmbeddingsUnavailable(Exception):
    """The embedding model could not be loaded."""


def get_embedder():
    """Return a cached ChromaDB-compatible embedding function.
    Raises EmbeddingsUnavailable if it cannot be built."""
    global _embedder, _failed
    if _embedder is not None:
        return _embedder
    if _failed:
        raise EmbeddingsUnavailable("embedding model previously failed to load")
    try:
        # Bundled with chromadb; downloads the ONNX model once, then caches.
        from chromadb.utils import embedding_functions
        _embedder = embedding_functions.ONNXMiniLM_L6_V2()
        return _embedder
    except Exception as exc:
        _failed = True
        raise EmbeddingsUnavailable(str(exc)) from exc


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts → list of vectors."""
    return get_embedder()(texts)


def available() -> bool:
    """True if embeddings can be produced (used to gate RAG)."""
    try:
        get_embedder()
        return True
    except EmbeddingsUnavailable:
        return False
