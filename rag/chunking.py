"""
CodeForge Agents — Chunking
===========================
Splits a markdown knowledge file into retrieval-sized chunks.

Strategy: split on `## ` section headings. Each section is one chunk —
small enough to be precise, large enough to carry a full
error → cause → fix story. The H1 title is prepended to every chunk so
each one stays self-describing after it leaves its file.

TEACHING NOTE: chunking strategy is one of the highest-impact RAG
decisions. Whole-file embedding (the old v3 approach) averages many
topics into one fuzzy vector; per-section chunks give sharp matches.

This module is PURE PYTHON on purpose — it can be unit-tested without
installing chromadb or sentence-transformers.
"""

import re


def chunk_markdown(text: str, source: str) -> list[dict]:
    """Returns [{"id", "text", "section"}] — one entry per `## ` section."""
    lines = text.split("\n")

    title = ""
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    chunks, current, section = [], [], "intro"

    def flush():
        body = "\n".join(current).strip()
        if body:
            chunk_text = f"{title} — {section}\n\n{body}" if title else body
            safe = re.sub(r"[^a-z0-9]+", "-", section.lower()).strip("-")
            chunks.append({
                "id": f"{source}::{safe or 'intro'}::{len(chunks)}",
                "text": chunk_text,
                "section": section,
            })

    for line in lines:
        if line.startswith("## "):
            flush()
            current, section = [], line[3:].strip()
        elif line.startswith("# "):
            continue                      # title already captured
        else:
            current.append(line)
    flush()
    return chunks
