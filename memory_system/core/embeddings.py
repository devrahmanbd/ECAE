import logging
from sentence_transformers import SentenceTransformer
from functools import lru_cache
import os
import sys
from tqdm import tqdm

# Load model once at module level locally pointing to cached offline weights
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
local_model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "local_model")

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(local_model_path)
    return _model

@lru_cache(maxsize=1000)
def embed(text: str) -> list[float]:
    """Generate a vector embedding for the given text with caching."""
    model = _get_model()
    return model.encode(text).tolist()

# Phase 2 alias compatibility
def get_embedding(text: str) -> list[float]:
    return embed(text)
