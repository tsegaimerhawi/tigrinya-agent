#!/usr/bin/env python3
"""
Store Preprocessed Sentences in Qdrant
======================================

Stores preprocessed Tigrinya sentences directly in Qdrant vector database.
This version works without the LLM-based POS tagging.

Usage:
    python store_sentences.py                    # Store all sentences
    python store_sentences.py --limit 5          # Store from first 5 articles
    python store_sentences.py --batch-size 50    # Process 50 sentences per batch
"""

import json
import os
import sys
import argparse
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env_config')

# Import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Import embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings


class SentenceStore:
    """Store Tigrinya sentences in Qdrant with embeddings"""
    
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        self.collection_name = "tigrinya_sentences"
        
        # Initialize Qdrant client
        print("🔌 Connecting to Qdrant...")
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
        # Initialize embeddings
        print("🧠 Initializing embedding model...")
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        
        # Ensure collection exists
        self._ensure_collection()
        
        # Stats
        self.stats = {
            'articles_processed': 0,
            'sentences_processed': 0,
            'sentences_stored': 0,
            'errors': 0
        }
    
    def _ensure_collection(self):
        """Ensure Qdrant collection exists"""
        collections = self.qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if self.collection_name not in collection_names:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )
            print(f"✅ Created collection '{self.collection_name}'")
        else:
            # Get current count
            info = self.qdrant_client.get_collection(self.collection_name)
            print(f"✅ Collection '{self.collection_name}' exists ({info.points_count} points)")
    
    def load_preprocessed_data(self, filepath: str = "preprocessed_data.json") -> Dict:
        """Load preprocessed data"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_sentence_id(self, article_index: int, sentence_index: int) -> int:
        """Generate unique ID for a sentence"""
        id_string = f"article_{article_index}_sentence_{sentence_index}"
        return int(hashlib.md5(id_string.encode()).hexdigest(), 16) % (2**63)
    
    def store_batch(self, sentences_data: List[Dict]) -> int:
        """Store a batch of sentences in Qdrant"""
        if not sentences_data:
            return 0
        
        try:
            # Generate embeddings for all texts in batch
            texts = [s['text'] for s in sentences_data]
            embeddings = self.embeddings.embed_documents(texts)
            
            # Create points
            points = []
            for i, (sentence_data, embedding) in enumerate(zip(sentences_data, embeddings)):
                point = PointStruct(
                    id=sentence_data['id'],
                    vector=embedding,
                    payload={
                        'text': sentence_data['text'],
                        'article_index': sentence_data['article_index'],
                        'sentence_index': sentence_data['sentence_index'],
                        'news_title': sentence_data['news_title'],
                        'article_url': sentence_data['article_url'],
                        'publication_date': sentence_data['publication_date'],
                        'word_count': len(sentence_data['text'].split()),
                        'stored_at': datetime.now().isoformat()
                    }
                )
                points.append(point)
            
            # Upsert to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            return len(points)
            
        except Exception as e:
            print(f"\n   ⚠️ Error storing batch: {e}")
            self.stats['errors'] += 1
            return 0
    
    def store_all_sentences(self, 
                           article_limit: Optional[int] = None,
                           batch_size: int = 20):
        """Store all preprocessed sentences in Qdrant"""
        
        print("\n" + "=" * 60)
        print("🚀 TIGRINYA SENTENCE STORAGE")
        print("=" * 60)
        
        # Load data
        print("\n📖 Loading preprocessed data...")
        data = self.load_preprocessed_data()
        articles = data.get('articles', [])
        
        if article_limit:
            articles = articles[:article_limit]
        
        total_sentences = sum(len(a.get('sentences', [])) for a in articles)
        print(f"   Articles to process: {len(articles)}")
        print(f"   Total sentences: {total_sentences}")
        print(f"   Batch size: {batch_size}")
        
        # Prepare all sentences
        print("\n📊 Preparing sentences...")
        all_sentences = []
        
        for article_idx, article in enumerate(articles):
            sentences = article.get('sentences', [])
            
            for sent_idx, sentence in enumerate(sentences):
                # Skip very short sentences
                if len(sentence) < 20:
                    continue
                
                all_sentences.append({
                    'id': self.generate_sentence_id(article.get('original_index', article_idx), sent_idx),
                    'text': sentence,
                    'article_index': article.get('original_index', article_idx),
                    'sentence_index': sent_idx,
                    'news_title': article.get('news_title', ''),
                    'article_url': article.get('article_url', ''),
                    'publication_date': article.get('publication_date', '')
                })
        
        print(f"   Valid sentences to store: {len(all_sentences)}")
        
        # Process in batches
        print("\n💾 Storing sentences in Qdrant...")
        
        for i in range(0, len(all_sentences), batch_size):
            batch = all_sentences[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(all_sentences) + batch_size - 1) // batch_size
            
            print(f"   Batch {batch_num}/{total_batches} ({len(batch)} sentences)... ", end='', flush=True)
            
            stored = self.store_batch(batch)
            self.stats['sentences_stored'] += stored
            self.stats['sentences_processed'] += len(batch)
            
            if stored > 0:
                print(f"✅ stored {stored}")
            else:
                print("❌ failed")
        
        self.stats['articles_processed'] = len(articles)
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print storage summary"""
        print("\n" + "=" * 60)
        print("📊 STORAGE SUMMARY")
        print("=" * 60)
        print(f"   • Articles processed: {self.stats['articles_processed']}")
        print(f"   • Sentences processed: {self.stats['sentences_processed']}")
        print(f"   • Sentences stored in Qdrant: {self.stats['sentences_stored']}")
        print(f"   • Errors: {self.stats['errors']}")
        
        # Get collection info
        try:
            info = self.qdrant_client.get_collection(self.collection_name)
            print(f"\n📦 Qdrant Collection '{self.collection_name}':")
            print(f"   • Total points: {info.points_count}")
            print(f"   • Vector size: {info.config.params.vectors.size}")
        except Exception as e:
            print(f"   ⚠️ Could not get collection info: {e}")
        
        print("\n✅ Storage completed!")
    
    def search_similar(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar sentences"""
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Search in Qdrant
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        
        return [
            {
                'text': r.payload.get('text', ''),
                'score': r.score,
                'news_title': r.payload.get('news_title', ''),
                'article_index': r.payload.get('article_index', 0)
            }
            for r in results
        ]


def main():
    parser = argparse.ArgumentParser(description='Store Tigrinya sentences in Qdrant')
    parser.add_argument('--limit', type=int, help='Limit number of articles to process')
    parser.add_argument('--batch-size', type=int, default=20, help='Batch size for storage (default: 20)')
    parser.add_argument('--search', type=str, help='Search for similar sentences (test mode)')
    parser.add_argument('--qdrant-host', default='localhost', help='Qdrant host')
    parser.add_argument('--qdrant-port', type=int, default=6333, help='Qdrant port')
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Error: GOOGLE_API_KEY not set")
        print("   Please set it in .env_config file")
        sys.exit(1)
    
    try:
        store = SentenceStore(
            qdrant_host=args.qdrant_host,
            qdrant_port=args.qdrant_port
        )
        
        if args.search:
            # Search mode
            print(f"\n🔍 Searching for: '{args.search}'")
            results = store.search_similar(args.search, limit=5)
            
            print(f"\n📋 Top {len(results)} results:")
            for i, r in enumerate(results, 1):
                print(f"\n{i}. Score: {r['score']:.4f}")
                print(f"   Article: {r['news_title']}")
                print(f"   Text: {r['text'][:100]}...")
        else:
            # Storage mode
            store.store_all_sentences(
                article_limit=args.limit,
                batch_size=args.batch_size
            )
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
