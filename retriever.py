"""
Tigrinya Retriever
==================

Handles semantic search against the Qdrant vector database.
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load environment variables
load_dotenv('.env_config')

class TigrinyaRetriever:
    """Retriever for Tigrinya Qdrant Collection"""
    
    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "tigrinya_corpus"):
        self.collection_name = collection_name
        
        # Initialize Client
        self.client = QdrantClient(host=host, port=port)
        
        # Initialize Embeddings
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")
            
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key
        )
        
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search for the query.
        
        Args:
            query: The user's question or search term
            k: Number of results to return
            
        Returns:
            List of dictionaries containing the result payload and score
        """
        # Generate embedding for the query
        query_vector = self.embeddings.embed_query(query)
        
        # Search Qdrant
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=k
        ).points
        
        # Format results
        results = []
        for scored_point in search_result:
            results.append({
                'score': scored_point.score,
                'text': scored_point.payload.get('original_text', ''),
                'metadata': scored_point.payload,
                'id': scored_point.id
            })
            
        return results

if __name__ == "__main__":
    # Simple test
    try:
        retriever = TigrinyaRetriever()
        results = retriever.search("ኤርትራ", k=1)
        print(f"Test search found {len(results)} results")
        if results:
            print(f"Top result: {results[0]['text'][:50]}...")
    except Exception as e:
        print(f"Retriever initialization failed: {e}")
