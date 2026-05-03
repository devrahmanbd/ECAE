from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import time

# We're running in a restricted sandbox, wait for it or mock Qdrant locally.
# Actually, since qdrant/qdrant docker pull failed with rate limit, let's use the local memory qdrant client (in-memory mode) for the prototype if we can't get the docker one.
