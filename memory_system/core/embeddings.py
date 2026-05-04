from sentence_transformers import SentenceTransformer
from functools import lru_cache

# Load model once at module level
model = SentenceTransformer("all-MiniLM-L6-v2")

@lru_cache(maxsize=1000)
def embed(text: str) -> list[float]:
    """Generate a vector embedding for the given text with caching."""
    return model.encode(text).tolist()

# Phase 2 alias compatibility
def get_embedding(text: str) -> list[float]:
    return embed(text)
