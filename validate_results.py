#!/usr/bin/env python3
"""
Validation script for PDF processing results.
Shows summary statistics and checks for English word removal.
"""

import json
import re


def main():
    """Validate the PDF processing results."""

    # Load processed data
    try:
        with open('raw_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: raw_data.json not found")
        return

    print(f'Processed {len(data)} PDFs')

    total_words = sum(item['word_count'] for item in data)
    print(f'Total words extracted: {total_words}')
    print(f'Average words per PDF: {total_words/len(data):.1f}')

    print('\nSample extracted text from first PDF:')
    sample_text = data[0]['extracted_text'][:300] if data else 'No data'
    print(repr(sample_text))

    print('\nChecking for English words...')
    english_words = []
    for item in data[:3]:  # Check first 3 PDFs
        text = item['extracted_text']
        # Look for English word patterns (words 3+ characters)
        found_english = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        if found_english:
            english_words.extend(found_english[:5])  # First 5 from each

    print(f'English words found: {english_words[:10]}')  # Show first 10
    print(f'Total English words detected: {len(english_words)}')

    if not english_words:
        print('✅ SUCCESS: No English words detected in the sample!')
    else:
        print('⚠️  WARNING: English words still present in the text')

    # Show per-article breakdown
    print('\nPer-article breakdown:')
    for item in data:
        status = "✓" if item['word_count'] > 0 else "✗"
        print(f"{status} {item['news_title']}: {item['word_count']} words")


if __name__ == "__main__":
    main()