# app/core/embedder.py

from sentence_transformers import SentenceTransformer
import numpy as np

# all-MiniLM-L6-v2 is lightweight (80MB), fast, and excellent for semantic similarity.
# It maps sentences to a 384-dimensional dense vector space.
MODEL_NAME = "all-MiniLM-L6-v2"

# Load once at module level — reused across all requests (no reload overhead)
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"[Embedder] Loading model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Converts a list of strings into a 2D numpy array of float32 embeddings.
    Shape: (len(texts), 384)
    """
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    return embeddings.astype("float32")


def embed_query(query: str) -> np.ndarray:
    """
    Embeds a single query string.
    Returns shape: (1, 384) — ready for FAISS search.
    """
    model = get_model()
    embedding = model.encode([query], convert_to_numpy=True)
    return embedding.astype("float32")