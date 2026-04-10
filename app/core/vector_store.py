# app/core/vector_store.py

import faiss
import numpy as np
from app.core.embedder import embed_texts, embed_query
from app.core.data_loader import load_all_chunks

# ── Globals (built once at startup) ──────────────────────────────────────────
_index: faiss.IndexFlatIP | None = None   # Inner Product index (cosine after normalisation)
_chunks: list[dict] = []                  # Parallel list — index i ↔ _chunks[i]


def _build_index():
    """
    Loads all chunks, embeds them, L2-normalises the vectors, then
    stores them in a FAISS IndexFlatIP.

    Why IndexFlatIP on L2-normalised vectors = cosine similarity:
        cos(a, b) = (a · b) / (|a| |b|)
        If |a| = |b| = 1  →  cos(a, b) = a · b  (inner product)
    So normalising first lets us use the fast inner-product index as
    a drop-in cosine similarity search.
    """
    global _index, _chunks

    print("[VectorStore] Loading chunks...")
    _chunks = load_all_chunks()

    texts = [c["text"] for c in _chunks]
    print(f"[VectorStore] Embedding {len(texts)} chunks...")
    embeddings = embed_texts(texts)

    # L2-normalise so inner product == cosine similarity
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]           # 384 for MiniLM
    _index = faiss.IndexFlatIP(dimension)
    _index.add(embeddings)

    print(f"[VectorStore] Index ready — {_index.ntotal} vectors, dim={dimension}")


def get_index():
    """Lazy initialiser — builds index on first call, reuses after."""
    global _index
    if _index is None:
        _build_index()
    return _index


def search(query: str, top_k: int = 5, source_filter: str = None) -> list[dict]:
    """
    Semantic search over the FAISS index.

    Args:
        query        : Natural language question from the user.
        top_k        : Number of results to return.
        source_filter: Optional — restrict results to one source type.
                       Values: 'vehicle_specs' | 'service_data' | 'owner_manual'

    Returns:
        List of chunk dicts, each with an added 'score' (cosine similarity 0-1).
    """
    get_index()   # ensure index is ready

    query_vec = embed_query(query)
    faiss.normalize_L2(query_vec)             # same normalisation as index

    # Search more candidates if we're going to filter afterwards
    fetch_k = top_k * 4 if source_filter else top_k
    scores, indices = _index.search(query_vec, fetch_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:                         # FAISS returns -1 for empty slots
            continue
        chunk = dict(_chunks[idx])            # copy so we don't mutate the store
        chunk["score"] = round(float(score), 4)

        if source_filter and chunk["source"] != source_filter:
            continue

        results.append(chunk)
        if len(results) == top_k:
            break

    return results