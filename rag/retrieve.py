"""
CodeForge Agents — Knowledge Retrieval
======================================
Query-time RAG with three professional habits the old v3 lacked:

    1. RELEVANCE THRESHOLD — if nothing scores above RAG_MIN_SIMILARITY,
       we retrieve NOTHING. Irrelevant context injected into prompts
       ("context pollution") makes answers WORSE, not better.
    2. METADATA FILTERING — the Router's language decision narrows the
       search: a Java question searches Java chunks (+ general ones,
       so team_standards.md is always reachable).
    3. TRANSPARENCY — we return scores and sources so the UI can show
       students exactly WHAT was retrieved and WHY.
"""

from core import config

_model = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        import chromadb
        from chromadb.config import Settings
        client = chromadb.PersistentClient(
            path=config.CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False))
        _collection = client.get_or_create_collection(
            config.COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    return _collection


def reset_cache():
    """Forget cached Chroma handles. MUST be called after a rebuild:
    ingest deletes + recreates the collection, so any cached handle
    points at a dead collection and count() reports stale results."""
    global _model, _collection
    _collection = None


def index_ready() -> bool:
    """True if the knowledge base has been built."""
    try:
        return _get_collection().count() > 0
    except Exception:
        return False


def retrieve(query: str, language: str = "general") -> dict:
    """
    Returns:
        {
          "context":  str,   # text to inject into agent prompts ('' if none)
          "hits":     list,  # [{source, section, score, preview}] for the UI
          "note":     str,   # human-readable status for the RAG expander
        }
    """
    empty = {"context": "", "hits": []}
    try:
        collection = _get_collection()
        if collection.count() == 0:
            return {**empty, "note": "Knowledge base is empty — it will be "
                    "auto-built on the next app load."}
        embedding = _get_model().encode(query).tolist()
    except Exception as e:
        return {**empty, "note": f"Retrieval unavailable: {e}"}

    # Router-driven filter: language-specific chunks + general ones
    where = None
    if language in ("python", "java", "yaml"):
        where = {"language": {"$in": [language, "general"]}}

    res = collection.query(query_embeddings=[embedding],
                           n_results=config.RAG_TOP_K, where=where)

    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]          # cosine distance: 0 = identical

    hits, kept = [], []
    for doc, meta, dist in zip(docs, metas, dists):
        similarity = 1.0 - dist
        if similarity < config.RAG_MIN_SIMILARITY:
            continue                      # the threshold doing its job
        kept.append(doc)
        hits.append({
            "source": meta.get("source", "?"),
            "section": meta.get("section", "?"),
            "score": round(similarity, 3),
            "preview": doc[:220] + ("…" if len(doc) > 220 else ""),
        })

    if not kept:
        return {**empty,
                "note": "No knowledge chunk passed the relevance threshold "
                        f"(min similarity {config.RAG_MIN_SIMILARITY}). "
                        "Retrieving nothing is the CORRECT behavior here — "
                        "irrelevant context would only pollute the prompt."}

    return {
        "context": "\n\n---\n\n".join(kept),
        "hits": hits,
        "note": f"Retrieved {len(kept)} relevant chunk(s) "
                f"(language filter: {language}).",
    }
