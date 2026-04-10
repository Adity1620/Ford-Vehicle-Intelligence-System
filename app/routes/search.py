# app/routes/search.py

from fastapi import APIRouter, HTTPException
from app.models import SearchRequest, SearchResponse, SearchResult
from app.core.vector_store import search

router = APIRouter()

@router.post("/search", response_model=SearchResponse, tags=["Semantic Search"])
def semantic_search(request: SearchRequest):
    """
    Performs semantic search over Ford vehicle knowledge base.

    ## How it works
    1. The query is embedded using **all-MiniLM-L6-v2** (384-dim vector).
    2. The vector is **L2-normalised** so that FAISS inner-product search
       is equivalent to **cosine similarity**.
    3. The top-k most similar chunks are returned with their scores.

    ## Cosine Similarity
    Measures the angle between two vectors in high-dimensional space.
    A score of **1.0** = identical meaning, **0.0** = unrelated.
    Unlike Euclidean distance, it is length-invariant — only direction matters,
    making it ideal for comparing sentence embeddings.

    ## Source Filter Options
    - `vehicle_specs` — engine, seats, fuel, price, safety
    - `service_data`  — oil change, tire rotation, warranty
    - `owner_manual`  — warning lights, troubleshooting
    """
    if request.source_filter and request.source_filter not in (
        "vehicle_specs", "service_data", "owner_manual"
    ):
        raise HTTPException(
            status_code=400,
            detail="source_filter must be one of: vehicle_specs, service_data, owner_manual"
        )

    raw_results = search(
        query=request.query,
        top_k=request.top_k,
        source_filter=request.source_filter
    )

    results = [
        SearchResult(
            model=r.get("model", "N/A"),
            source=r["source"],
            score=r["score"],
            text=r["text"]
        )
        for r in raw_results
    ]

    return SearchResponse(
        query=request.query,
        results=results,
        total_results=len(results)
    )