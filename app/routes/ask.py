# app/routes/ask.py

from fastapi import APIRouter, HTTPException
from app.models import AskRequest, AskResponse
from app.core.rag import ask

router = APIRouter()

@router.post("/ask", response_model=AskResponse, tags=["RAG Assistant"])
def ask_assistant(request: AskRequest):
    """
    RAG-powered automotive Q&A grounded in Ford's knowledge base.

    ## What is RAG?
    Retrieval-Augmented Generation (RAG) combines a **retrieval system**
    (semantic search over a vector database) with a **generative LLM**.
    Instead of relying on the LLM's parametric memory (which can hallucinate),
    RAG injects verified, retrieved context directly into the prompt —
    forcing the model to answer from facts, not assumptions.

    ## Why grounding matters in automotive
    Incorrect service intervals, wrong torque specs, or hallucinated safety
    features can cause real-world vehicle damage or driver harm.
    Every answer must be traceable to a verified data source.

    ## Hallucination mitigation strategy
    - **System prompt rules**: LLM is explicitly forbidden from using outside knowledge
    - **Low temperature (0.2)**: Reduces creative drift, keeps answers factual
    - **Source citation**: Every answer references the chunk it came from
    - **Fallback response**: If context is insufficient, the system admits it
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    result = ask(question=request.question, top_k=request.top_k)

    return AskResponse(
        question=request.question,
        answer=result["answer"],
        sources_used=result["sources_used"]
    )