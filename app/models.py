# app/models.py

from pydantic import BaseModel, Field
from typing import Optional

# ── /search ──────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., example="Which Ford SUV has 7 seats?")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    source_filter: Optional[str] = Field(
        default=None,
        description="Filter by source: 'vehicle_specs' | 'service_data' | 'owner_manual'"
    )

class SearchResult(BaseModel):
    model: str
    source: str
    score: float
    text: str

class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_results: int


# ── /ask ─────────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., example="What does the engine warning light mean?")
    top_k: int = Field(default=4, ge=1, le=10)

class AskResponse(BaseModel):
    question: str
    answer: str
    sources_used: list[str]


# ── /recommend ───────────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    requirement: str = Field(..., example="I need a family SUV with 7 seats")
    budget_lakhs: Optional[float] = Field(
        default=None,
        description="Optional max budget in INR Lakhs"
    )

class VehicleRecommendation(BaseModel):
    model: str
    body_style: str
    fuel_type: str
    seating: int
    price_lakhs: float
    reason: str

class RecommendResponse(BaseModel):
    requirement: str
    recommendations: list[VehicleRecommendation]