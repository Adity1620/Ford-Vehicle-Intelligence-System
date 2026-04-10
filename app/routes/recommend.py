# app/routes/recommend.py

import re
from fastapi import APIRouter
from app.models import RecommendRequest, RecommendResponse, VehicleRecommendation
from app.core.data_loader import load_vehicle_chunks

router = APIRouter()

# ── Keyword maps — user intent → vehicle attributes ───────────────────────────

BODY_STYLE_KEYWORDS = {
    "suv":          "SUV",
    "pickup":       "Pickup Truck",
    "truck":        "Pickup Truck",
    "van":          "Van",
    "mpv":          "MPV",
    "sedan":        "Sedan",
    "sports":       "Sports Car",
    "commercial":   "Commercial Chassis",
}

FUEL_KEYWORDS = {
    "electric":  "Electric",
    "ev":        "Electric",
    "hybrid":    "Hybrid",
    "diesel":    "Diesel",
    "petrol":    "Petrol",
    "gas":       "Petrol",
}

# Seat-specific keywords removed — handled generically by regex in _parse_filters
FEATURE_KEYWORDS = {
    "family":        {"min_seating": 5, "body_style_pref": ["SUV", "MPV"]},
    "spacious":      {"min_seating": 7},
    "tow":           {"drivetrain_pref": ["4WD", "AWD"], "body_style_pref": ["Pickup Truck", "SUV"]},
    "towing":        {"drivetrain_pref": ["4WD", "AWD"], "body_style_pref": ["Pickup Truck", "SUV"]},
    "off-road":      {"drivetrain_pref": ["4WD", "AWD"]},
    "off road":      {"drivetrain_pref": ["4WD", "AWD"]},
    "cargo":         {"body_style_pref": ["Van", "Pickup Truck", "Commercial Chassis"]},
    "city":          {"fuel_pref": ["Electric", "Hybrid", "Petrol"]},
    "best mileage":  {"sort_by_mileage": True},
    "fuel efficient":{"fuel_pref": ["Electric", "Hybrid"], "sort_by_mileage": True},
    "eco":           {"fuel_pref": ["Electric", "Hybrid"], "sort_by_mileage": True},
    "efficient":     {"sort_by_mileage": True},
    "good mileage":  {"sort_by_mileage": True},
    "performance":   {"body_style_pref": ["Sports Car"]},
    "sport":         {"body_style_pref": ["Sports Car"]},
}

# Word-to-number mapping for written seat numbers
WORD_TO_NUM = {
    "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}


def _extract_seat_count(text: str) -> int | None:
    """
    Generalized regex extractor for seat count from natural language.

    Handles patterns like:
      "7 seat", "7 seater", "7-seater", "seven seater",
      "seats for 7", "seating for 6", "capacity of 8",
      "need 5 seats", "a 3 seat car"
    Returns an int if found, else None.
    """
    num_pattern = r'(\d+|two|three|four|five|six|seven|eight|nine|ten)'

    patterns = [
        # "7 seat", "7 seater", "7-seat", "seven seater"
        rf'{num_pattern}\s*[-\s]?\s*seat',
        # "seats for 7", "seating for 6", "seating capacity of 8"
        rf'seat(?:ing|s)?\s+(?:for|of|capacity)?\s*{num_pattern}',
        # "capacity of 7", "capacity for 7"
        rf'capacity\s+(?:of|for)\s*{num_pattern}',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            raw = match.group(1) if match.lastindex == 1 else match.group(match.lastindex)
            if raw.isdigit():
                return int(raw)
            return WORD_TO_NUM.get(raw)

    return None


def _score_vehicle(vehicle: dict, filters: dict) -> tuple[int, list[str]]:
    """
    Scores a vehicle against parsed filters.
    Returns (score, list_of_matching_reasons).
    Higher score = better match.
    """
    score = 0
    reasons = []

    # Body style match
    if "body_style" in filters:
        if vehicle["body_style"] == filters["body_style"]:
            score += 10
            reasons.append(f"Matches body style: {filters['body_style']}")

    # Fuel type match
    if "fuel_type" in filters:
        if vehicle["fuel_type"] == filters["fuel_type"]:
            score += 8
            reasons.append(f"Matches fuel type: {filters['fuel_type']}")

    # Seating requirement
    if "min_seating" in filters:
        if vehicle["seating"] >= filters["min_seating"]:
            score += 12
            reasons.append(f"Meets seating requirement ({vehicle['seating']} seats ≥ {filters['min_seating']})")

    # Drivetrain preference
    if "drivetrain_pref" in filters:
        if vehicle["drivetrain"] in filters["drivetrain_pref"]:
            score += 6
            reasons.append(f"Suitable drivetrain for use case: {vehicle['drivetrain']}")

    # Body style preference (from feature keywords)
    if "body_style_pref" in filters:
        if vehicle["body_style"] in filters["body_style_pref"]:
            score += 5
            reasons.append(f"Body style suits requirement: {vehicle['body_style']}")

    # Fuel preference (from feature keywords)
    if "fuel_pref" in filters:
        if vehicle["fuel_type"] in filters["fuel_pref"]:
            score += 5
            reasons.append(f"Fuel type suits requirement: {vehicle['fuel_type']}")

    # Mileage scoring — higher mileage = higher score
    # EVs get a normalized score based on km/charge
    if filters.get("sort_by_mileage"):
        mileage = vehicle.get("mileage", 0)
        mileage_unit = vehicle.get("mileage_unit", "km/l")
        # Normalize EV range: km/charge is typically 300-500, divide by 30 to compare fairly
        normalized = float(mileage) / 30 if mileage_unit == "km/charge" else float(mileage)
        score += normalized
        reasons.append(f"Mileage: {mileage} {mileage_unit}")

    return score, reasons


def _parse_filters(requirement: str, budget: float | None) -> dict:
    """
    Parses a natural language requirement string into a structured filter dict.

    Examples:
      "family SUV with 7 seats"  → { body_style: SUV, min_seating: 7 }
      "I need a 8 seater mpv"    → { body_style: MPV, min_seating: 8 }
      "affordable hybrid"        → { fuel_type: Hybrid, sort_by_mileage: True }
      "seating for 6 people"     → { min_seating: 6 }
    """
    req_lower = requirement.lower()
    filters = {}

    # 1. Detect explicit body style
    for keyword, style in BODY_STYLE_KEYWORDS.items():
        if keyword in req_lower:
            filters["body_style"] = style
            break

    # 2. Detect explicit fuel type
    for keyword, fuel in FUEL_KEYWORDS.items():
        if keyword in req_lower:
            filters["fuel_type"] = fuel
            break

    # 3. Generalized seat count extraction via regex — handles any number, any phrasing
    seat_count = _extract_seat_count(req_lower)
    if seat_count:
        filters["min_seating"] = seat_count

    # 4. Detect feature-based implicit filters
    for keyword, attrs in FEATURE_KEYWORDS.items():
        if keyword in req_lower:
            for k, v in attrs.items():
                # Don't overwrite explicit body_style with a preference list
                if k == "body_style_pref" and "body_style" in filters:
                    continue
                # Don't overwrite regex-extracted seat count with keyword default
                if k == "min_seating" and "min_seating" in filters:
                    continue
                filters[k] = v

    if budget:
        filters["max_budget"] = budget

    return filters


def recommend(requirement: str, budget: float | None = None) -> list[VehicleRecommendation]:
    """
    Recommendation pipeline:
    1. Parse user requirement into structured filters
    2. Score every vehicle against those filters
    3. Apply hard budget filter
    4. Return top 2 scored vehicles with reasoning
    """
    vehicles = load_vehicle_chunks()
    filters = _parse_filters(requirement, budget)

    scored = []
    for v in vehicles:
        # Hard budget filter
        if "max_budget" in filters and v["price"] > filters["max_budget"]:
            continue

        score, reasons = _score_vehicle(v, filters)

        if score > 0:
            scored.append((score, reasons, v))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Deduplicate by model name, take top 2
    seen = set()
    results = []
    for score, reasons, v in scored:
        if v["model"] not in seen:
            seen.add(v["model"])
            reason_text = " | ".join(reasons) if reasons else "General match based on your requirement."
            results.append(
                VehicleRecommendation(
                    model=v["model"],
                    body_style=v["body_style"],
                    fuel_type=v["fuel_type"],
                    seating=v["seating"],
                    price_lakhs=v["price"],
                    reason=reason_text
                )
            )
        if len(results) == 2:
            break

    # Fallback if nothing matched
    if not results:
        results.append(
            VehicleRecommendation(
                model="No Match Found",
                body_style="N/A",
                fuel_type="N/A",
                seating=0,
                price_lakhs=0.0,
                reason="No vehicles matched your requirement. Try being more specific (e.g. 'SUV', 'electric', '7 seats')."
            )
        )

    return results


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/recommend", response_model=RecommendResponse, tags=["Vehicle Recommendation"])
def recommend_vehicle(request: RecommendRequest):
    """
    Attribute-based vehicle recommendation engine.

    ## How it works
    No LLM is used here — this is **deterministic rule-based matching**:
    1. Natural language is parsed into structured filters (body style, fuel, seating, drivetrain)
    2. Seat count is extracted generically via **regex** — handles any number in any phrasing
    3. Every vehicle is scored against filters; budget acts as a hard cutoff
    4. Top 2 highest-scoring vehicles are returned with full reasoning

    ## Why not use LLM here?
    Recommendations require **consistent, reproducible logic**.
    Rule-based scoring ensures the system always picks the objectively
    best match — not a probabilistic guess.

    ## Example queries
    - "I need a family SUV with 7 seats"
    - "I want a pickup truck for towing"
    - "Suggest an electric vehicle"
    - "Affordable hybrid under 30 lakhs"
    - "I need a 8 seater mpv"
    - "Seating for 6 people"
    """
    recs = recommend(
        requirement=request.requirement,
        budget=request.budget_lakhs
    )
    return RecommendResponse(
        requirement=request.requirement,
        recommendations=recs
    )