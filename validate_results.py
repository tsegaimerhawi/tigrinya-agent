#!/usr/bin/env python3
"""
Validation script for PDF processing results.
Shows summary statistics and checks for English word removal.
Supports both raw_data.json and preprocessed_data.json.
"""

import json
import re
import sys


def validate_raw_data():
    """Validate the raw PDF processing results."""
    try:
        with open('raw_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: raw_data.json not found")
        return

    print("=" * 50)
    print("📄 RAW DATA VALIDATION")
    print("=" * 50)
    print(f'Processed {len(data)} PDFs')

    total_words = sum(item.get('word_count', 0) for item in data)
    print(f'Total words extracted: {total_words}')
    print(f'Average words per PDF: {total_words/len(data):.1f}')

    print('\nSample extracted text from first PDF:')
    sample_text = data[0]['extracted_text'][:300] if data else 'No data'
    print(repr(sample_text))

    print('\nChecking for English words...')
    english_words = []
    for item in data[:3]:
        text = item['extracted_text']
        found_english = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        if found_english:
            english_words.extend(found_english[:5])

    print(f'English words found: {english_words[:10]}')
    print(f'Total English words detected: {len(english_words)}')

    if not english_words:
        print('✅ SUCCESS: No English words detected in the sample!')
    else:
        print('⚠️  WARNING: English words still present in the text')

    print('\nPer-article breakdown:')
    for item in data:
        word_count = item.get('word_count', len(item.get('extracted_text', '').split()))
        status = "✓" if word_count > 0 else "✗"
        print(f"{status} {item['news_title']}: {word_count} words")


def validate_preprocessed_data():
    """Validate the preprocessed data."""
    try:
        with open('preprocessed_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: preprocessed_data.json not found")
        print("Run: python preprocessor.py")
        return

    print("=" * 50)
    print("🔧 PREPROCESSED DATA VALIDATION")
    print("=" * 50)

    metadata = data.get('metadata', {})
    articles = data.get('articles', [])

    print(f"Source file: {metadata.get('source_file', 'unknown')}")
    print(f"Total articles: {metadata.get('total_articles', len(articles))}")
    print(f"Total sentences: {metadata.get('total_sentences', 0)}")
    print(f"Character reduction: {metadata.get('overall_reduction_ratio', 0) * 100:.1f}%")

    print('\nSample cleaned text from first article:')
    if articles:
        sample_text = articles[0].get('cleaned_text', '')[:300]
        print(repr(sample_text))

    print('\nSample sentences from first article:')
    if articles and articles[0].get('sentences'):
        for i, sentence in enumerate(articles[0]['sentences'][:5]):
            print(f"  {i+1}. {sentence[:80]}{'...' if len(sentence) > 80 else ''}")

    print('\nChecking for character duplication issues...')
    duplication_found = False
    for article in articles[:3]:
        text = article.get('cleaned_text', '')
        # Check for triple+ character repetitions (should be none after preprocessing)
        for i in range(len(text) - 2):
            if text[i] == text[i+1] == text[i+2]:
                print(f"⚠️  Found triple char at position {i}: '{text[max(0,i-2):i+5]}'")
                duplication_found = True
                break

    if not duplication_found:
        print('✅ SUCCESS: No character duplication issues detected!')

    print('\nPer-article statistics:')
    for article in articles:
        title = article.get('news_title', 'Unknown')[:40]
        sentences = article.get('sentence_count', 0)
        reduction = article.get('reduction_ratio', 0) * 100
        print(f"  • {title}: {sentences} sentences, {reduction:.1f}% reduction")


def main():
    """Main validation function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--raw':
            validate_raw_data()
        elif sys.argv[1] == '--preprocessed':
            validate_preprocessed_data()
        elif sys.argv[1] == '--all':
            validate_raw_data()
            print("\n")
            validate_preprocessed_data()
        else:
            print("Usage: python validate_results.py [--raw|--preprocessed|--all]")
            print("  --raw          Validate raw_data.json")
            print("  --preprocessed Validate preprocessed_data.json (default)")
            print("  --all          Validate both files")
    else:
        # Default: validate preprocessed data
        validate_preprocessed_data()


if __name__ == "__main__":
    main()