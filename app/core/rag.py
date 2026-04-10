# app/core/rag.py

import os
from openai import OpenAI
from dotenv import load_dotenv
from app.core.vector_store import search

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://models.inference.ai.azure.com"
)


# ── Prompt Template ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are FVIS (Ford Vehicle Intelligence System), an expert automotive assistant 
built to help users with Ford vehicle specifications, service schedules, and owner manual guidance.

KNOWLEDGE SOURCES AVAILABLE TO YOU:
- Vehicle Specifications: engine specs, fuel type, seating, drivetrain, safety features, pricing
- Service & Maintenance Data: oil change intervals, tire rotation, brake inspection, warranty
- Owner Manual: dashboard warnings, troubleshooting procedures, maintenance reminders

RESPONSE RULES:
1. GROUNDING: Base all answers on the retrieved context provided. Never invent specs, 
   features, prices, or intervals that are not explicitly stated in the context.

2. REASONING ALLOWED: You may reason and infer on top of the context. Examples:
   - If a user says they serviced a year ago and the interval is 12000 km, infer service is due.
   - If asked for the "best" vehicle for a use case, compare retrieved options and recommend 
     with clear reasoning from their specs.

3. COMPARISONS ALLOWED: When multiple vehicles appear in context, you may compare them 
   directly using only the attributes present in the context.

4. HONEST FALLBACK: If the retrieved context contains no relevant information to answer 
   the question, respond exactly with:
   "I don't have enough information in my knowledge base to answer that accurately."
   Do not guess. Do not use outside knowledge.

5. SAFETY-CRITICAL QUESTIONS: For questions involving warning lights, brake failures, 
   overheating, or any safety system — always provide the context-based answer AND 
   append: "For safety-critical issues, please consult a certified Ford technician immediately."

6. CITATIONS: Always mention which vehicle model, service record, or manual section 
   your answer is drawn from.

7. SCOPE: You only answer questions about Ford vehicles. For unrelated questions, 
   politely state that you are scoped to Ford automotive assistance only.

IMPORTANT — WHY THIS MATTERS:
In the automotive domain, a hallucinated brake inspection interval, a fabricated towing 
capacity, or a misidentified warning light are not just wrong answers — they are safety risks. 
This system is designed to be trustworthy above all else.
"""

def build_context(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a numbered context block
    injected into the prompt.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_label = {
            "vehicle_specs": "Vehicle Specifications",
            "service_data": "Service & Maintenance Data",
            "owner_manual": "Owner Manual"
        }.get(chunk["source"], chunk["source"])

        context_parts.append(
            f"[Context {i} — {source_label} | Model: {chunk['model']}]\n{chunk['text']}"
        )
    return "\n\n".join(context_parts)


def ask(question: str, top_k: int = 4) -> dict:
    """
    Full RAG pipeline:
      1. Retrieve top_k relevant chunks via semantic search
      2. Build a grounded prompt with injected context
      3. Call OpenAI LLM for a context-bound answer
      4. Return answer + source attribution

    RAG (Retrieval-Augmented Generation) grounds the LLM by supplying
    it with verified facts at inference time, preventing hallucination
    of vehicle specs, service intervals, or safety information.
    """
    # Step 1 — Retrieve
    chunks = search(question, top_k=top_k)

    if not chunks:
        return {
            "answer": "No relevant information found in the knowledge base.",
            "sources_used": []
        }

    # Step 2 — Build grounded context
    context = build_context(chunks)

    user_message = f"""Use ONLY the context below to answer the question.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    # Step 3 — Generate
    response = client.chat.completions.create(
        model="gpt-4o-mini",          # fast + cheap, ideal for RAG
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ],
        temperature=0.2,              # low temp = factual, less creative drift
        max_tokens=500,
    )

    answer = response.choices[0].message.content.strip()

    # Step 4 — Collect sources
    sources = list({
        f"{c['source']} → {c['model']}" for c in chunks
    })

    return {
        "answer": answer,
        "sources_used": sources
    }