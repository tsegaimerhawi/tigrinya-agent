#!/usr/bin/env python3
"""
Full Tigrinya NLP Pipeline
==========================

Runs the complete pipeline:
1. Load preprocessed data (sentences)
2. Run POS Tagger on each sentence
3. Run Critic for validation
4. Run Refiner for structuring
5. Store in Qdrant vector database

Usage:
    python run_pipeline.py                    # Process all articles
    python run_pipeline.py --article 0        # Process specific article
    python run_pipeline.py --limit 5          # Process first 5 articles
    python run_pipeline.py --sentences 10     # Process 10 sentences per article
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

# Import agents
from agent_tagger import run_pos_tagger, validate_geez_text
from agent_critic import TigrinyaGrammarianCritic
from agent_refiner import TigrinyaDataEngineer

# Import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Import embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings


class TigrinyaPipeline:
    """Complete Tigrinya NLP Pipeline with Qdrant storage"""
    
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        self.collection_name = "tigrinya_corpus"
        
        # Initialize Qdrant client
        print("🔌 Connecting to Qdrant...")
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
        # Initialize agents
        print("🤖 Initializing agents...")
        self.critic = TigrinyaGrammarianCritic()
        self.refiner = TigrinyaDataEngineer()
        
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
            print(f"✅ Collection '{self.collection_name}' exists")
    
    def load_preprocessed_data(self, filepath: str = "preprocessed_data.json") -> Dict:
        """Load preprocessed data"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def process_sentence(self, sentence: str, article_metadata: Dict) -> Optional[Dict]:
        """Process a single sentence through the full pipeline"""
        
        # Skip if too short or invalid
        if len(sentence) < 20 or not validate_geez_text(sentence):
            return None
        
        try:
            # Step 1: POS Tagging
            tagger_result = run_pos_tagger(sentence)
            pos_tags = tagger_result.get('pos_tags', []) if tagger_result else []
            
            if not pos_tags:
                return None
            
            # Step 2: Critic validation
            critic_result = self.critic.run_critique(pos_tags)
            
            # Step 3: Refiner structuring
            refined = self.refiner.refine_article_data(
                original_text=sentence,
                tagged_tokens=pos_tags,
                critic_metadata={
                    'critic_status': critic_result['status'],
                    'critic_feedback': critic_result['feedback'],
                    'article_metadata': article_metadata
                }
            )
            
            return refined
            
        except Exception as e:
            print(f"   ⚠️ Error processing sentence: {e}")
            self.stats['errors'] += 1
            return None
    
    def generate_sentence_id(self, article_index: int, sentence_index: int) -> int:
        """Generate unique ID for a sentence"""
        id_string = f"article_{article_index}_sentence_{sentence_index}"
        return int(hashlib.md5(id_string.encode()).hexdigest(), 16) % (2**63)
    
    def store_in_qdrant(self, refined_data: Dict, article_index: int, sentence_index: int):
        """Store refined sentence data in Qdrant"""
        try:
            # Generate embedding
            text = refined_data.get('original_text', '')
            embedding = self.embeddings.embed_documents([text])[0]
            
            # Create point
            point_id = self.generate_sentence_id(article_index, sentence_index)
            
            # Prepare payload (remove large nested objects if needed)
            payload = {
                'article_id': refined_data.get('article_id', ''),
                'article_index': article_index,
                'sentence_index': sentence_index,
                'original_text': text,
                'tagged_tokens': refined_data.get('tagged_tokens', []),
                'topic_summary': refined_data.get('metadata', {}).get('topic_summary', ''),
                'word_count': refined_data.get('metadata', {}).get('word_count', 0),
                'critic_status': refined_data.get('metadata', {}).get('critic_status', ''),
                'refined_at': refined_data.get('refined_at', ''),
                'stored_at': datetime.now().isoformat()
            }
            
            # Upsert to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(id=point_id, vector=embedding, payload=payload)]
            )
            
            self.stats['sentences_stored'] += 1
            return True
            
        except Exception as e:
            print(f"   ⚠️ Error storing in Qdrant: {e}")
            self.stats['errors'] += 1
            return False
    
    def run_pipeline(self, 
                     article_limit: Optional[int] = None,
                     article_index: Optional[int] = None,
                     sentences_per_article: int = 50):
        """Run the full pipeline on preprocessed data"""
        
        print("\n" + "=" * 60)
        print("🚀 TIGRINYA NLP PIPELINE")
        print("=" * 60)
        
        # Load data
        print("\n📖 Loading preprocessed data...")
        data = self.load_preprocessed_data()
        articles = data.get('articles', [])
        
        print(f"   Found {len(articles)} articles")
        print(f"   Total sentences: {data.get('metadata', {}).get('total_sentences', 0)}")
        
        # Determine which articles to process
        if article_index is not None:
            articles_to_process = [(article_index, articles[article_index])]
        elif article_limit:
            articles_to_process = list(enumerate(articles[:article_limit]))
        else:
            articles_to_process = list(enumerate(articles))
        
        print(f"\n📊 Processing {len(articles_to_process)} article(s), {sentences_per_article} sentences each")
        
        # Process each article
        for idx, article in articles_to_process:
            print(f"\n{'─' * 50}")
            print(f"📰 Article {idx + 1}/{len(articles)}: {article.get('news_title', 'Unknown')[:50]}")
            
            sentences = article.get('sentences', [])[:sentences_per_article]
            print(f"   Processing {len(sentences)} sentences...")
            
            article_metadata = {
                'news_title': article.get('news_title', ''),
                'article_url': article.get('article_url', ''),
                'publication_date': article.get('publication_date', ''),
                'original_index': article.get('original_index', idx)
            }
            
            for sent_idx, sentence in enumerate(sentences):
                print(f"   [{sent_idx + 1}/{len(sentences)}] ", end='', flush=True)
                
                # Process sentence
                refined = self.process_sentence(sentence, article_metadata)
                
                if refined:
                    # Store in Qdrant
                    stored = self.store_in_qdrant(refined, idx, sent_idx)
                    if stored:
                        print("✅")
                    else:
                        print("❌ (storage failed)")
                else:
                    print("⏭️ (skipped)")
                
                self.stats['sentences_processed'] += 1
            
            self.stats['articles_processed'] += 1
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print pipeline summary"""
        print("\n" + "=" * 60)
        print("📊 PIPELINE SUMMARY")
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
        
        print("\n✅ Pipeline completed!")


def main():
    parser = argparse.ArgumentParser(description='Run Tigrinya NLP Pipeline')
    parser.add_argument('--article', type=int, help='Process specific article index')
    parser.add_argument('--limit', type=int, help='Limit number of articles to process')
    parser.add_argument('--sentences', type=int, default=20, help='Sentences per article (default: 20)')
    parser.add_argument('--qdrant-host', default='localhost', help='Qdrant host')
    parser.add_argument('--qdrant-port', type=int, default=6333, help='Qdrant port')
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Error: GOOGLE_API_KEY not set")
        print("   Please set it in .env_config file")
        sys.exit(1)
    
    try:
        pipeline = TigrinyaPipeline(
            qdrant_host=args.qdrant_host,
            qdrant_port=args.qdrant_port
        )
        
        pipeline.run_pipeline(
            article_limit=args.limit,
            article_index=args.article,
            sentences_per_article=args.sentences
        )
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
