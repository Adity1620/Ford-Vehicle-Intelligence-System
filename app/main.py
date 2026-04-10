from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.vector_store import get_index
from app.routes import search, ask, recommend

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Startup] Building FAISS index...")
    get_index()
    print("[Startup] Ready.")
    yield

app = FastAPI(
    title="Ford Vehicle Intelligence System",
    description="An AI-powered automotive knowledge assistant for Ford vehicles.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS must be added BEFORE routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # open for local dev
    allow_credentials=False,    # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(ask.router)
app.include_router(recommend.router)

@app.get("/", tags=["Health"])
def root():
    return {"status": "online", "system": "Ford Vehicle Intelligence System",
            "endpoints": ["/search", "/ask", "/recommend", "/docs"]}