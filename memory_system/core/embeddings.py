from sentence_transformers import SentenceTransformer
from functools import lru_cache
import os

# Load model once at module level locally pointing to cached offline weights
local_model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "local_model")
model = SentenceTransformer(local_model_path)

@lru_cache(maxsize=1000)
def embed(text: str) -> list[float]:
    """Generate a vector embedding for the given text with caching."""
    return model.encode(text).tolist()

# Phase 2 alias compatibility
def get_embedding(text: str) -> list[float]:
    return embed(text)
