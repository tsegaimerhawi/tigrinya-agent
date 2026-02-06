#!/usr/bin/env python3
"""
Qdrant Connection Checker
=========================

Quick utility to check if Qdrant is running and accessible.
"""

import sys
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException


def check_qdrant(host: str = "localhost", port: int = 6333) -> bool:
    """Check if Qdrant is running and accessible."""
    try:
        client = QdrantClient(host=host, port=port)
        collections = client.get_collections()
        print(f"✅ Qdrant is running at {host}:{port}")
        print(f"   Found {len(collections.collections)} collection(s)")
        if collections.collections:
            for col in collections.collections:
                try:
                    info = client.get_collection(col.name)
                    print(f"   • {col.name}: {info.points_count} points")
                except Exception as e:
                    print(f"   • {col.name}: (error getting info: {e})")
        else:
            print("   No collections found yet")
        return True
    except (ConnectionError, ResponseHandlingException, Exception) as e:
        print(f"❌ Qdrant is NOT running at {host}:{port}")
        print(f"   Error: {e}")
        print("\n💡 To start Qdrant:")
        print("   docker run -p 6333:6333 qdrant/qdrant")
        print("\n💡 To check if Qdrant is running:")
        print("   curl http://localhost:6333/collections")
        return False


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 6333
    
    success = check_qdrant(host, port)
    sys.exit(0 if success else 1)
