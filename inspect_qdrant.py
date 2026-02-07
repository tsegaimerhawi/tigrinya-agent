
from qdrant_client import QdrantClient
client = QdrantClient("localhost", port=6333)
print("Methods:")
print([m for m in dir(client) if not m.startswith('_')])
