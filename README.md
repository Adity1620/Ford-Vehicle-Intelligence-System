# FVIS — Ford Vehicle Intelligence System

> An AI-powered automotive knowledge assistant built for the **Sorim.AI Technical Assessment**.  
> Answers questions about Ford vehicles using **Semantic Search**, **Retrieval-Augmented Generation (RAG)**, and **Rule-Based Recommendation Logic**.

---

## Table of Contents

- [Overview](#overview)
- [Live Demo](#live-demo)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [API Endpoints](#api-endpoints)
- [Design Decisions](#design-decisions)
- [Key Concepts Explained](#key-concepts-explained)
- [Hallucination Mitigation Strategy](#hallucination-mitigation-strategy)
- [Dataset](#dataset)
- [Tech Stack](#tech-stack)

---

## Overview

FVIS is a production-grade AI assistant that helps users query information about Ford vehicles across three core capabilities:

| Capability | Endpoint | Description |
|---|---|---|
| Semantic Search | `/search` | Search vehicle specs, service data, and owner manual using natural language |
| RAG Q&A | `/ask` | Ask questions and get grounded, cited answers powered by GPT-4o-mini |
| Vehicle Recommender | `/recommend` | Get top 2 vehicle suggestions based on your requirements and budget |

The system is built on a **3-layer knowledge base**:
- **Vehicle Specifications** — 36 Ford models with engine, fuel, seating, drivetrain, safety features
- **Service & Maintenance Data** — oil change intervals, tire rotation, brake inspection, warranty
- **Owner Manual** — dashboard warning lights, troubleshooting procedures, maintenance reminders

---

## Live Demo

Start both servers and open the frontend UI:

```
Backend  → http://localhost:8000
API Docs → http://localhost:8000/docs
Frontend → http://localhost:5173
```

---

![](/Ford Vehicle Intelligence System-architecture.png)

### Request Flow — `/ask` Endpoint (RAG Pipeline)

```
User Question
     │
     ▼
Embed question using all-MiniLM-L6-v2
     │
     ▼
L2-normalize vector → FAISS cosine search
     │
     ▼
Retrieve top-k relevant chunks (vehicle specs / service / manual)
     │
     ▼
Inject chunks into structured prompt template
     │
     ▼
GPT-4o-mini generates grounded, cited answer
     │
     ▼
Return answer + source attribution to user
```

---

## Project Structure

```
Ford-Vehicle-Intelligence-System/
│
├── app/                          # FastAPI backend
│   ├── main.py                   # App entry point, CORS, lifespan
│   ├── models.py                 # Pydantic request/response schemas
│   │
│   ├── core/
│   │   ├── data_loader.py        # Reads CSVs + manual, produces text chunks
│   │   ├── embedder.py           # Sentence-transformer embedding pipeline
│   │   ├── vector_store.py       # FAISS index build + cosine search
│   │   └── rag.py                # Prompt template + OpenAI RAG pipeline
│   │
│   └── routes/
│       ├── search.py             # /search endpoint
│       ├── ask.py                # /ask endpoint
│       └── recommend.py          # /recommend endpoint
│
├── frontend/                     # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx               # Main app — Search, Ask, Recommend panels
│   │   └── App.css               # Dark automotive theme
│   ├── index.html
│   ├── Dockerfile
│   └── .dockerignore
│
├── Data/
│   ├── ford_vehicles_dataset.csv      # 36 Ford vehicle specs
│   ├── ford_vehicles_service_data.csv # Service & maintenance schedules
│   └── ford_owner_manual.txt          # Dashboard warnings + troubleshooting
│
├── Dockerfile                    # Backend Docker image
├── .dockerignore                 # Backend build exclusions
├── docker-compose.yml            # Runs backend + frontend together
├── requirements.txt              # Python dependencies
└── README.md
```

---

## Setup Instructions

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend runtime |
| Node.js | 16+ | Frontend runtime |
| npm | 8+ | Frontend package manager |
| OpenAI API Key | — | Powers the `/ask` RAG endpoint |

---

### Option 1 — Local Development (Recommended)

#### 1. Clone the repository

```bash
git clone https://github.com/Adity1620/Ford-Vehicle-Intelligence-System.git
cd Ford-Vehicle-Intelligence-System
```

#### 2. Backend setup

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

> Get your API key from [platform.openai.com](https://platform.openai.com)

#### 4. Start the backend

```bash
uvicorn app.main:app --reload
```

The backend will:
- Load all 3 datasets
- Embed 85 chunks using `all-MiniLM-L6-v2`
- Build the FAISS index
- Start serving at `http://localhost:8000`

#### 5. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

#### 6. Open the app

| URL | Description |
|---|---|
| `http://localhost:5173` | React frontend UI |
| `http://localhost:8000/docs` | Interactive Swagger API docs |
| `http://localhost:8000` | Health check |

---

### Option 2 — Docker (Full Stack)

```bash
# Make sure .env file exists with your OpenAI key, then:
docker-compose up --build
```

This builds and starts both backend and frontend containers automatically.

| Service | URL |
|---|---|
| Backend | `http://localhost:8000` |
| Frontend | `http://localhost:5173` |

To stop:
```bash
docker-compose down
```

---

## API Endpoints

### `POST /search` — Semantic Search

Search the vehicle knowledge base using natural language.

**Request:**
```json
{
  "query": "Which Ford SUV has 7 seats?",
  "top_k": 3,
  "source_filter": "vehicle_specs"
}
```

**Response:**
```json
{
  "query": "Which Ford SUV has 7 seats?",
  "results": [
    {
      "model": "Ford Explorer",
      "source": "vehicle_specs",
      "score": 0.6324,
      "text": "Model: Ford Explorer. Body Style: SUV. Seating Capacity: 7 seats..."
    }
  ],
  "total_results": 3
}
```

`source_filter` options: `vehicle_specs` | `service_data` | `owner_manual`

---

### `POST /ask` — RAG Assistant

Ask a natural language question. The system retrieves relevant context and generates a grounded answer.

**Request:**
```json
{
  "question": "What does the engine oil pressure warning mean?",
  "top_k": 4
}
```

**Response:**
```json
{
  "question": "What does the engine oil pressure warning mean?",
  "answer": "The engine oil pressure warning indicates critically low oil pressure. Shut off the engine immediately to prevent permanent damage. For safety-critical issues, please consult a certified Ford technician immediately.",
  "sources_used": ["owner_manual → ALL"]
}
```

---

### `POST /recommend` — Vehicle Recommender

Get top 2 vehicle recommendations based on natural language requirements.

**Request:**
```json
{
  "requirement": "I need a 7 seater family SUV",
  "budget_lakhs": 55
}
```

**Response:**
```json
{
  "requirement": "I need a 7 seater family SUV",
  "recommendations": [
    {
      "model": "Ford Explorer",
      "body_style": "SUV",
      "fuel_type": "Petrol",
      "seating": 7,
      "price_lakhs": 50.0,
      "reason": "Matches body style: SUV | Meets seating requirement (7 seats ≥ 7)"
    }
  ]
}
```

---

## Design Decisions

### 1. Embedding Model — `all-MiniLM-L6-v2`

Chosen for its balance of **speed, size, and accuracy**:
- Maps sentences to a **384-dimensional** dense vector space
- Model size: ~80MB — runs fully on CPU, no GPU required
- Significantly faster than larger models (BERT, MPNet) with competitive accuracy on semantic similarity tasks
- Downloaded once at startup and cached — zero overhead on subsequent requests

### 2. FAISS with Cosine Similarity

We use `IndexFlatIP` (Inner Product index) on **L2-normalized vectors**, which is mathematically equivalent to cosine similarity:

```
cos(a, b) = (a · b) / (|a| · |b|)

When |a| = |b| = 1  →  cos(a, b) = a · b
```

**Why cosine over Euclidean distance?**  
Cosine similarity measures the **angle** between vectors — it is length-invariant, meaning only the direction (semantic meaning) matters, not the magnitude. This makes it ideal for comparing sentence embeddings where meaning should drive relevance, not vector length.

### 3. Chunking Strategy

Different data sources require different chunking:

| Source | Strategy | Reason |
|---|---|---|
| Vehicle CSV | One row → one chunk | Keeps all specs for a model together (entity coherence) |
| Service CSV | One row → one chunk | Maintenance data is per-model and self-contained |
| Owner Manual | Split by double newline | Each paragraph covers one topic (topic coherence) |

This ensures retrieved chunks are **semantically complete units** — no partial specs or split warning descriptions.

### 4. RAG — Why Not Just Use the LLM Directly?

Without RAG, an LLM would answer from **parametric memory** — knowledge baked in during training. This causes:
- Hallucinated specs (wrong horsepower, incorrect seating capacity)
- Outdated information
- Fabricated service intervals — a genuine safety risk

With RAG, the LLM only sees **verified, retrieved context** at inference time. It cannot answer beyond what's in the retrieved chunks, making every answer traceable to a source.

### 5. `/recommend` — No LLM Used

The recommendation engine is **fully deterministic rule-based logic**:
- Natural language → structured filters via keyword maps + regex
- Every vehicle is scored numerically against those filters
- Results are reproducible and auditable

Using an LLM here would introduce randomness and make the system unpredictable for a task that should have consistent, explainable outputs.

### 6. Regex-Based Seat Extraction

Instead of hardcoding every possible seat phrasing (`"7 seat"`, `"8 seater"`, `"seven seater"`...), we use a generalized regex that handles any number in any phrasing:

```python
# Handles: "7 seat", "seven seater", "seats for 8", "seating capacity of 6"
r'(\d+|two|three|...|ten)\s*[-\s]?\s*seat'
```

This makes the system **open-ended and robust** — any new seat count works automatically.

### 7. Temperature = 0.2 for RAG

Low temperature reduces creative drift in the LLM. In automotive advice, a creative answer is a dangerous answer — we want factual precision, not eloquence.

---

## Key Concepts Explained

### What is RAG (Retrieval-Augmented Generation)?

RAG is an AI architecture that combines two systems:

1. **Retrieval** — A vector search engine finds relevant documents from a knowledge base
2. **Generation** — An LLM reads those documents and generates a human-readable answer

The key insight: the LLM doesn't need to memorize facts if it can look them up at runtime. This separates *knowledge* (in the vector store) from *reasoning* (in the LLM).

### What are Embeddings?

An embedding is a fixed-length numerical vector that represents the **semantic meaning** of a piece of text. Texts with similar meaning produce vectors that point in similar directions in high-dimensional space.

Example:
- `"engine oil pressure warning"` and `"oil pressure light on dashboard"` → vectors close together
- `"engine oil pressure warning"` and `"tire rotation schedule"` → vectors far apart

### What is Cosine Similarity?

A metric that measures the angle between two vectors. A score of `1.0` means identical direction (identical meaning). A score of `0.0` means perpendicular (completely unrelated).

---

## Hallucination Mitigation Strategy

Hallucination in automotive AI is not just an accuracy problem — it is a **safety risk**. A fabricated brake inspection interval or a misidentified warning light can cause real-world harm.

FVIS uses a 4-layer mitigation approach:

| Layer | Mechanism |
|---|---|
| **System Prompt** | LLM is explicitly forbidden from using outside knowledge |
| **Context Injection** | Only verified, retrieved chunks are passed to the LLM |
| **Low Temperature** | Set to 0.2 — minimizes creative drift |
| **Honest Fallback** | If context is insufficient, system says so instead of guessing |

Additionally, all safety-critical answers (warning lights, overheating, brakes) automatically append a recommendation to consult a certified Ford technician.

---

## Dataset

All data is synthetic, generated specifically for this assessment.

| File | Records | Content |
|---|---|---|
| `ford_vehicles_dataset.csv` | 36 models | Engine specs, fuel type, seating, drivetrain, safety features, price |
| `ford_vehicles_service_data.csv` | 36 models | Oil change, tire rotation, brake inspection, warranty |
| `ford_owner_manual.txt` | ~20 sections | Warning lights, troubleshooting, maintenance reminders |

**Total chunks embedded: 85**

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | FastAPI (Python) |
| Embedding Model | `all-MiniLM-L6-v2` via `sentence-transformers` |
| Vector Database | FAISS (`IndexFlatIP`) |
| LLM | GPT-4o-mini via OpenAI API |
| Frontend | React + Vite |
| HTTP Client | Axios |
| Data Processing | Pandas |
| Containerization | Docker + Docker Compose |

