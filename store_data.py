"""
Data Storage Script - Qdrant Vector Database
===========================================

Stores Tigrinya corpus articles in Qdrant vector database with embeddings.
"""

import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import Qdrant client
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Import LangChain for embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load environment variables
load_dotenv(dotenv_path='.env_config')


def initialize_qdrant_collection(client: QdrantClient, collection_name: str = "tigrinya_corpus"):
    """Initialize Qdrant collection if it doesn't exist"""

    # Check if collection exists
    collections = client.get_collections()
    collection_names = [col.name for col in collections.collections]

    if collection_name in collection_names:
        print(f"✅ Collection '{collection_name}' already exists")
        return

    # Create collection with vector parameters
    # Using 768 dimensions for Google text embeddings
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )

    print(f"✅ Created collection '{collection_name}' with 768-dimensional vectors")


def load_refined_articles(filepath: str = "refined_articles.json") -> List[Dict]:
    """Load refined articles from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            articles = json.load(f)

        if not isinstance(articles, list):
            articles = [articles]

        print(f"✅ Loaded {len(articles)} articles from {filepath}")
        return articles

    except FileNotFoundError:
        print(f"❌ Error: File '{filepath}' not found")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{filepath}': {e}")
        return []


def create_embedding_model():
    """Create Google Generative AI embedding model"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    # Initialize Google Generative AI embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",  # Google's latest embedding model
        google_api_key=api_key
    )

    return embeddings


def generate_embeddings_batch(embeddings_model, texts: List[str], batch_size: int = 10) -> List[List[float]]:
    """Generate embeddings for a batch of texts"""
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        print(f"🔄 Generating embeddings for batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")

        try:
            batch_embeddings = embeddings_model.embed_documents(batch_texts)
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"❌ Error generating embeddings for batch starting at index {i}: {e}")
            # Add None placeholders for failed embeddings
            all_embeddings.extend([None] * len(batch_texts))

    return all_embeddings


def store_articles_in_qdrant(client: QdrantClient,
                            articles: List[Dict],
                            embeddings_model,
                            collection_name: str = "tigrinya_corpus"):
    """Store articles with embeddings in Qdrant"""

    # Prepare data for batch insertion
    texts = []
    payloads = []
    ids = []

    for article in articles:
        # Extract text for embedding
        text = article.get('original_text', '')
        if not text:
            print(f"⚠️  Skipping article {article.get('article_id', 'unknown')} - no text")
            continue

        texts.append(text)
        payloads.append(article)  # Store full article data as payload

        # Use article_id as numeric ID (extract number from string)
        article_id = article.get('article_id', '')
        if article_id.startswith('article_'):
            try:
                numeric_id = int(article_id.split('_')[1])
                ids.append(numeric_id)
            except (ValueError, IndexError):
                # Fallback to hash-based ID
                import hashlib
                id_hash = int(hashlib.md5(article_id.encode()).hexdigest(), 16) % (2**63)
                ids.append(id_hash)
        else:
            # Fallback for other ID formats
            import hashlib
            id_hash = int(hashlib.md5(article_id.encode()).hexdigest(), 16) % (2**63)
            ids.append(id_hash)

    if not texts:
        print("❌ No valid articles to store")
        return

    print(f"📊 Preparing to store {len(texts)} articles...")

    # Generate embeddings
    embeddings = generate_embeddings_batch(embeddings_model, texts)

    # Prepare points for Qdrant
    points = []
    successful_count = 0

    for i, (embedding, payload, article_id) in enumerate(zip(embeddings, payloads, ids)):
        if embedding is None:
            print(f"⚠️  Skipping article {payload.get('article_id', 'unknown')} - embedding failed")
            continue

        points.append(PointStruct(
            id=article_id,
            vector=embedding,
            payload=payload
        ))

        successful_count += 1

        # Batch upload every 50 articles or at the end
        if len(points) >= 50 or i == len(embeddings) - 1:
            try:
                client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                print(f"✅ Uploaded batch of {len(points)} articles")
                points = []  # Reset batch
            except Exception as e:
                print(f"❌ Error uploading batch: {e}")
                continue

    print(f"🎉 Successfully stored {successful_count} articles in Qdrant collection '{collection_name}'")


def verify_qdrant_setup(client: QdrantClient, collection_name: str = "tigrinya_corpus"):
    """Verify Qdrant connection and collection setup"""
    try:
        # Test connection
        collections = client.get_collections()
        print(f"✅ Connected to Qdrant. Found {len(collections.collections)} collections.")

        # Check our collection
        collection_info = client.get_collection(collection_name)
        print(f"✅ Collection '{collection_name}' info:")
        print(f"   • Vectors: {collection_info.config.params.vectors.size}")
        print(f"   • Distance: {collection_info.config.params.vectors.distance}")
        print(f"   • Points: {collection_info.points_count}")

        return True

    except Exception as e:
        print(f"❌ Qdrant setup verification failed: {e}")
        return False


def main():
    """Main function to store Tigrinya corpus in Qdrant"""

    print("🚀 Starting Tigrinya Corpus Storage in Qdrant")
    print("=" * 50)

    # Configuration
    QDRANT_URL = "localhost"
    QDRANT_PORT = 6333
    COLLECTION_NAME = "tigrinya_corpus"

    try:
        # Connect to Qdrant
        print("🔌 Connecting to Qdrant...")
        client = QdrantClient(host=QDRANT_URL, port=QDRANT_PORT)

        # Initialize collection
        initialize_qdrant_collection(client, COLLECTION_NAME)

        # Verify setup
        if not verify_qdrant_setup(client, COLLECTION_NAME):
            return

        # Load refined articles
        print("\n📖 Loading refined articles...")
        articles = load_refined_articles()

        if not articles:
            print("❌ No articles to store")
            return

        # Create embedding model
        print("\n🧠 Initializing Google Generative AI embeddings...")
        embeddings_model = create_embedding_model()

        # Store articles
        print("\n💾 Storing articles in Qdrant...")
        store_articles_in_qdrant(client, articles, embeddings_model, COLLECTION_NAME)

        # Final verification
        print("\n🔍 Final verification...")
        verify_qdrant_setup(client, COLLECTION_NAME)

        print("\n🎯 Tigrinya corpus storage completed successfully!")
        print(f"📊 Articles stored in collection: {COLLECTION_NAME}")

    except Exception as e:
        print(f"❌ Error during storage process: {e}")
        print("💡 Make sure Qdrant is running on localhost:6333")


if __name__ == "__main__":
    main()