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

_collection = None

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
    global _collection
    _collection = None


def index_ready() -> bool:
    """True if the knowledge base has been built."""
    try:
        return _get_collection().count() > 0
    except Exception:
        return False


def retrieve(query: str, language: str = "general",
             user_collection=None) -> dict:
    """
    Returns:
        {
          "context":  str,   # text to inject into agent prompts ('' if none)
          "hits":     list,  # [{source, section, score, origin, preview}]
          "note":     str,   # human-readable status for the RAG expander
        }

    `user_collection` is an OPTIONAL per-session ephemeral collection of
    the user's own uploaded knowledge (see rag/user_kb.py). When present,
    its chunks compete with the baked index on similarity alone.
    """
    empty = {"context": "", "hits": []}
    from rag.embedder import embed, EmbeddingsUnavailable
    try:
        base = _get_collection()
        if base.count() == 0 and user_collection is None:
            return {**empty, "note": "Knowledge base is empty — it will be "
                    "auto-built on the next app load."}
        embedding = embed([query])[0]
    except EmbeddingsUnavailable as e:
        return {**empty, "note": "RAG disabled — the embedding model could "
                f"not load ({e}). The app continues without retrieval; "
                "better no context than wrong context."}
    except Exception as e:
        return {**empty, "note": f"Retrieval unavailable: {e}"}

    # Router-driven filter applies to the BAKED index only: language-specific
    # chunks + general ones. The user's own uploads are queried WITHOUT a
    # language filter — if they bothered to add it, they want it considered.
    where = None
    if language in ("python", "java", "yaml"):
        where = {"language": {"$in": [language, "general"]}}

    # Gather candidates from BOTH collections into ONE scored list, then
    # apply a single relevance bar + top-k. Source never beats relevance
    # (pure-rank merge — the honest RAG behavior).
    #
    # MERGE-POLICY SWITCH: to instead GUARANTEE an uploaded chunk shows
    # whenever it clears the threshold (handy for a nervous live demo),
    # after sorting `candidates`, pop the best origin=="user" entry and
    # prepend it before the top-k trim below. Three lines, no other change.
    candidates = []

    def collect(coll, use_filter):
        try:
            if coll is None or coll.count() == 0:
                return
            res = coll.query(
                query_embeddings=[embedding],
                n_results=min(config.RAG_TOP_K, coll.count()),
                where=where if use_filter else None)
            for doc, meta, dist in zip(res["documents"][0],
                                       res["metadatas"][0],
                                       res["distances"][0]):
                candidates.append((1.0 - dist, doc, meta))   # cosine: 0=identical
        except Exception:
            return

    collect(base, use_filter=True)
    collect(user_collection, use_filter=False)

    candidates.sort(key=lambda c: c[0], reverse=True)

    hits, kept = [], []
    for similarity, doc, meta in candidates:
        if similarity < config.RAG_MIN_SIMILARITY:
            continue                      # the threshold doing its job
        if len(kept) >= config.RAG_TOP_K:
            break
        kept.append(doc)
        hits.append({
            "source": meta.get("source", "?"),
            "section": meta.get("section", "?"),
            "score": round(similarity, 3),
            "origin": meta.get("origin", "base"),
            "preview": doc[:220] + ("…" if len(doc) > 220 else ""),
        })

    if not kept:
        return {**empty,
                "note": "No knowledge chunk passed the relevance threshold "
                        f"(min similarity {config.RAG_MIN_SIMILARITY}). "
                        "Retrieving nothing is the CORRECT behavior here — "
                        "irrelevant context would only pollute the prompt."}

    n_user = sum(1 for h in hits if h["origin"] == "user")
    note = (f"Retrieved {len(kept)} relevant chunk(s) "
            f"(language filter: {language}")
    note += f"; {n_user} from your upload)." if n_user else ")."
    return {"context": "\n\n---\n\n".join(kept), "hits": hits, "note": note}
