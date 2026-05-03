from sentence_transformers import SentenceTransformer

# Load model once at module level
model = SentenceTransformer("all-MiniLM-L6-v2")

def embed(text: str):
    """Generate a vector embedding for the given text."""
    return model.encode(text).tolist()
