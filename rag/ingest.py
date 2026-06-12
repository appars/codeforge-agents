"""
CodeForge Agents — Knowledge Ingestion
======================================
Builds the vector index:   knowledge/*.md  ->  ChromaDB

    * splits each file into per-section chunks      (rag/chunking.py)
    * attaches metadata {language, topic, source}   (enables filtering)
    * IDEMPOTENT: the collection is rebuilt from scratch every run, so
      re-ingesting never duplicates or errors (the old v3 bug)

Run from the project root:        python -m rag.ingest
Or click "📚 Build Knowledge Base" in the app sidebar.
"""

from core import config
from rag.chunking import chunk_markdown

# filename (without extension) -> metadata
_FILE_META = {
    "python_debug":        {"language": "python",  "topic": "debug"},
    "python_optimization": {"language": "python",  "topic": "optimize"},
    "java_debug":          {"language": "java",    "topic": "debug"},
    "yaml_k8s_debug":      {"language": "yaml",    "topic": "debug"},
    "k8s_best_practices":  {"language": "yaml",    "topic": "review"},
    "team_standards":      {"language": "general", "topic": "review"},
}


def _embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(config.EMBEDDING_MODEL)


def build_index(progress=print) -> dict:
    """(Re)build the entire index. Returns a summary dict."""
    import chromadb

    files = sorted(config.KNOWLEDGE_DIR.glob("*.md"))
    if not files:
        return {"ok": False,
                "message": f"No .md files found in {config.KNOWLEDGE_DIR}"}

    try:
        model = _embedder()
    except Exception as e:
        return {"ok": False,
                "message": "Could not load the embedding model "
                           f"({config.EMBEDDING_MODEL}). First run needs "
                           f"internet to download it once. Error: {e}"}

    # anonymized_telemetry=False: keeps everything local AND silences the
    # harmless "Failed to send telemetry event" warnings from chromadb.
    from chromadb.config import Settings
    client = chromadb.PersistentClient(
        path=config.CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False))

    # Idempotency: drop and recreate — re-running is always safe.
    try:
        client.delete_collection(config.COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        config.COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    total_chunks = 0
    for path in files:
        meta = _FILE_META.get(path.stem,
                              {"language": "general", "topic": "general"})
        chunks = chunk_markdown(path.read_text(encoding="utf-8"), path.stem)
        if not chunks:
            continue
        texts = [c["text"] for c in chunks]
        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        collection.add(
            ids=[c["id"] for c in chunks],
            documents=texts,
            embeddings=embeddings,
            metadatas=[{**meta, "source": path.name,
                        "section": c["section"]} for c in chunks],
        )
        total_chunks += len(chunks)
        progress(f"  • {path.name}: {len(chunks)} chunks")

    msg = f"Indexed {len(files)} files → {total_chunks} chunks ✅"
    progress(msg)
    return {"ok": True, "message": msg,
            "files": len(files), "chunks": total_chunks}


if __name__ == "__main__":
    print("🔨 CodeForge Agents — building knowledge index…")
    result = build_index()
    if not result["ok"]:
        print("❌ " + result["message"])
        raise SystemExit(1)
