#!/usr/bin/env python3
"""
LlamaIndex Tigrinya Ingestion Pipeline
======================================

Loads PDFs from pdfs/ directory, applies Tigrinya preprocessing,
and stores embeddings in Qdrant vector database.

Flow:
1. Run scraper.py to download PDFs to pdfs/
2. Run pdf_processor.py (or this script handles extraction)
3. This script: load PDFs → preprocess → embed → store in Qdrant

Usage:
    python llama_ingest.py                    # Ingest all PDFs
    python llama_ingest.py --limit 5          # Ingest first 5 PDFs
"""

import json
import os
import argparse
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Tigrinya preprocessing (reuse existing)
from pdf_processor import extract_text_from_pdf, clean_text
from preprocessor import fix_character_duplication, split_into_sentences

# LlamaIndex
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

load_dotenv('.env_config')


def load_pdf_metadata(filepath: str = "pdf_metadata.json") -> List[dict]:
    """Load PDF metadata from scraper output."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        completed = [m for m in metadata if m.get('download_status') == 'completed']
        return completed
    except FileNotFoundError:
        print(f"❌ {filepath} not found. Run scraper.py first.")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {filepath}: {e}")
        return []


def load_pdfs_from_directory(pdf_dir: str = "pdfs") -> List[dict]:
    """Load PDF metadata by scanning pdfs/ directory if pdf_metadata.json not available."""
    pdf_path = Path(pdf_dir)
    if not pdf_path.exists():
        return []

    metadata = []
    for i, pdf_file in enumerate(sorted(pdf_path.glob("*.pdf")), 1):
        # Extract title from filename (e.g., "On Jan 23, 2026_Haddas Ertra.pdf" -> "Haddas Ertra")
        name = pdf_file.stem
        news_title = name.split('_', 1)[1] if '_' in name else name
        metadata.append({
            'index': i,
            'pdf_filepath': str(pdf_file),
            'pdf_filename': pdf_file.name,
            'news_title': news_title,
        })
    return metadata


def extract_and_preprocess(metadata: dict) -> List[dict]:
    """
    Extract text from PDF, apply Tigrinya preprocessing, return sentences with metadata.
    """
    pdf_path = metadata.get('pdf_filepath') or metadata.get('pdf_url')
    if not pdf_path or not os.path.exists(pdf_path):
        return []

    # Extract raw text with pdfplumber
    extracted_text, word_count = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        return []

    # Step 1: Fix OCR character duplication
    cleaned_text = fix_character_duplication(extracted_text)

    # Step 2: Split into valid sentences
    sentences = split_into_sentences(cleaned_text)

    # Build article metadata (scraper uses 'title'/'date', pdf_processor uses 'news_title'/'publication_date')
    news_title = metadata.get('news_title') or metadata.get('title', '') or \
        Path(metadata.get('pdf_filename', '')).stem
    pub_date = metadata.get('publication_date') or metadata.get('date', '')

    return [
        {
            'text': sentence,
            'metadata': {
                'article_index': metadata.get('index', 0),
                'news_title': news_title,
                'article_url': metadata.get('article_url', ''),
                'publication_date': pub_date,
                'pdf_filename': metadata.get('pdf_filename', ''),
                'pdf_url': metadata.get('pdf_url', ''),
                'sentence_index': i,
            }
        }
        for i, sentence in enumerate(sentences)
    ]


def create_documents(metadata_list: List[dict], limit: Optional[int] = None) -> List[Document]:
    """Create LlamaIndex Documents from PDF metadata."""
    documents = []
    metadata_list = metadata_list[:limit] if limit else metadata_list

    for meta in metadata_list:
        items = extract_and_preprocess(meta)
        for item in items:
            doc = Document(
                text=item['text'],
                metadata=item['metadata'],
            )
            documents.append(doc)

    return documents


def run_ingestion(
    pdf_dir: str = "pdfs",
    collection_name: str = "tigrinya_llamaindex",
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
    limit: Optional[int] = None,
):
    """Run the full LlamaIndex ingestion pipeline."""

    print("=" * 60)
    print("🚀 LlamaIndex Tigrinya Ingestion")
    print("=" * 60)

    # 1. Load PDF metadata
    metadata_list = load_pdf_metadata()
    if not metadata_list:
        metadata_list = load_pdfs_from_directory(pdf_dir)
    if not metadata_list:
        print("❌ No PDFs found. Run: python scraper.py")
        return

    print(f"\n📖 Found {len(metadata_list)} PDFs")

    # 2. Create documents (extract + preprocess)
    print("\n🔄 Extracting and preprocessing PDFs...")
    documents = create_documents(metadata_list, limit=limit)
    print(f"   Created {len(documents)} sentence documents")

    if not documents:
        print("❌ No documents to ingest")
        return

    # 3. Configure LlamaIndex
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not set")
        return

    embed_model = GoogleGenAIEmbedding(
        model_name="models/text-embedding-004",
        api_key=api_key,
    )
    Settings.embed_model = embed_model
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50

    # 4. Connect to Qdrant
    print("\n🔌 Connecting to Qdrant...")
    from qdrant_client import QdrantClient

    client = QdrantClient(host=qdrant_host, port=qdrant_port)

    # Create collection if needed (768 dims for text-embedding-004)
    from qdrant_client.models import Distance, VectorParams

    collections = client.get_collections()
    if collection_name not in [c.name for c in collections.collections]:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        print(f"   Created collection '{collection_name}'")

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        enable_hybrid=False,
    )

    # 5. Build index and store
    print("\n💾 Building index and storing in Qdrant...")
    index = VectorStoreIndex.from_documents(
        documents,
        vector_store=vector_store,
        show_progress=True,
    )

    # 6. Summary
    info = client.get_collection(collection_name)
    print("\n" + "=" * 60)
    print("✅ Ingestion complete!")
    print("=" * 60)
    print(f"   • Documents ingested: {len(documents)}")
    print(f"   • Qdrant collection: {collection_name}")
    print(f"   • Total points: {info.points_count}")


def main():
    parser = argparse.ArgumentParser(description="LlamaIndex Tigrinya PDF ingestion")
    parser.add_argument("--limit", type=int, help="Limit number of PDFs to process")
    parser.add_argument("--pdf-dir", default="pdfs", help="PDF directory")
    parser.add_argument("--collection", default="tigrinya_llamaindex", help="Qdrant collection name")
    parser.add_argument("--qdrant-host", default="localhost", help="Qdrant host")
    parser.add_argument("--qdrant-port", type=int, default=6333, help="Qdrant port")

    args = parser.parse_args()

    run_ingestion(
        pdf_dir=args.pdf_dir,
        collection_name=args.collection,
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
