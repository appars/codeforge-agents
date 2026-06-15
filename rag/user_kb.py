"""
CodeForge Agents — Bring-Your-Own Knowledge (session-scoped)
============================================================
Lets a user add their OWN notes / standards for the CURRENT session only.

WHY EPHEMERAL + PER SESSION (the deployment lesson):
the baked `codeforge_knowledge` collection is process-global and, in
Kubernetes, per-pod. Writing user uploads into it would leak one user's
docs into another's retrieval and, with >1 replica, behave differently on
each pod. So each browser session gets its OWN in-memory ChromaDB
collection: isolated, written to no disk, gone when the session ends —
which in multi-replica k8s is exactly the right behavior (nothing to sync).

It reuses the SAME chunker (chunk_document) and embedder (rag.embedder)
as the baked index, so all vectors live in one space and retrieve() can
merge results from both collections by similarity score.

Stored in st.session_state (per session), NEVER @st.cache_resource
(process-global, would be shared across users).
"""

import hashlib

import streamlit as st

from rag.chunking import chunk_document
from rag.embedder import embed, available

MAX_FILE_BYTES = 1_000_000        # 1 MB per upload — keeps memory bounded
MAX_SESSION_CHUNKS = 200          # cap across ALL of a session's uploads

_COLL_KEY = "user_kb"             # the EphemeralClient collection handle
_SEEN_KEY = "user_kb_seen"        # content hashes already ingested (dedup)
_DOCS_KEY = "user_kb_docs"        # [{name, chunks}] for the sidebar list


def _collection():
    """Return this session's ephemeral collection, creating it once."""
    if _COLL_KEY not in st.session_state:
        import chromadb
        from chromadb.config import Settings
        client = chromadb.EphemeralClient(
            settings=Settings(anonymized_telemetry=False))
        st.session_state[_COLL_KEY] = client.create_collection(
            "user_knowledge", metadata={"hnsw:space": "cosine"})
        st.session_state[_SEEN_KEY] = set()
        st.session_state[_DOCS_KEY] = []
    return st.session_state[_COLL_KEY]


def collection_or_none():
    """The collection IF it has content, else None — for retrieve()."""
    coll = st.session_state.get(_COLL_KEY)
    try:
        return coll if coll is not None and coll.count() > 0 else None
    except Exception:
        return None


def docs() -> list[dict]:
    """[{name, chunks}] of what the user has added, for the sidebar."""
    return st.session_state.get(_DOCS_KEY, [])


def _chunks_used() -> int:
    coll = st.session_state.get(_COLL_KEY)
    try:
        return coll.count() if coll is not None else 0
    except Exception:
        return 0


def add_text(name: str, raw) -> dict:
    """Add one document — bytes from an upload, or a pasted string.

    Returns {"ok": bool, "message": str, ...}. SAFE to call on every
    Streamlit rerun: a content hash makes re-adding identical text a
    no-op, so file_uploader handing back the same files each rerun does
    not duplicate anything.
    """
    if not available():
        return {"ok": False, "message": "Embedding model unavailable — "
                "knowledge upload is disabled."}

    # Decode tolerantly. Word / Windows exports are frequently NOT clean
    # UTF-8 (smart quotes, a BOM, cp1252). utf-8-sig strips a BOM;
    # errors='replace' means a stray byte never crashes the upload.
    if isinstance(raw, (bytes, bytearray)):
        if len(raw) > MAX_FILE_BYTES:
            return {"ok": False,
                    "message": f"{name} is larger than 1 MB — please trim it."}
        text = bytes(raw).decode("utf-8-sig", errors="replace")
    else:
        text = str(raw)
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return {"ok": False, "message": f"No readable text found in {name}."}

    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    coll = _collection()
    if digest in st.session_state[_SEEN_KEY]:
        return {"ok": True, "duplicate": True,
                "message": f"{name} is already added."}

    chunks = chunk_document(text, source=name)
    if not chunks:
        return {"ok": False, "message": f"No readable text found in {name}."}

    budget = MAX_SESSION_CHUNKS - _chunks_used()
    if budget <= 0:
        return {"ok": False, "message": "Session knowledge is full "
                f"({MAX_SESSION_CHUNKS} chunks). Clear it to add more."}
    truncated = len(chunks) > budget
    if truncated:
        chunks = chunks[:budget]

    texts = [c["text"] for c in chunks]
    try:
        embeddings = embed(texts)
        # Namespace ids by content hash so two files with the SAME name
        # (or a re-edit) can never collide on chunk id.
        coll.add(
            ids=[f"{digest}:{c['id']}" for c in chunks],
            documents=texts,
            embeddings=embeddings,
            metadatas=[{"source": name, "section": c["section"],
                        "language": "user", "origin": "user"}
                       for c in chunks],
        )
    except Exception as exc:                  # never let an upload crash the app
        return {"ok": False, "message": f"Could not index {name}: {exc}"}

    st.session_state[_SEEN_KEY].add(digest)
    st.session_state[_DOCS_KEY].append({"name": name, "chunks": len(chunks)})
    msg = f"{name} → {len(chunks)} chunk(s) indexed."
    if truncated:
        msg += " (truncated to fit the session limit)"
    return {"ok": True, "message": msg}


def clear():
    """Drop all of this session's uploaded knowledge."""
    for k in (_COLL_KEY, _SEEN_KEY, _DOCS_KEY):
        st.session_state.pop(k, None)
