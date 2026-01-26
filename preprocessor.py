#!/usr/bin/env python3
"""
Tigrinya Text Preprocessor
==========================

Preprocesses raw_data.json to fix OCR character duplication issues
and split text into sentences.

In Tigrinya, characters never repeat 3+ times consecutively.
If a character repeats 2 times and multiple characters in the word
follow this pattern, it's an OCR error - we keep only one of each.
"""

import json
import re
from typing import List, Dict, Any


def detect_duplication_pattern(word: str) -> bool:
    """
    Detect if a word has the OCR duplication pattern.
    
    The pattern is when multiple characters are duplicated consecutively,
    e.g., "ንንኣኣሌሌክክሳሳንንደደርር" where every character appears twice.
    
    Returns True if the word has this pattern (likely OCR error).
    """
    if len(word) < 4:
        return False
    
    # Count consecutive character pairs
    pair_count = 0
    i = 0
    while i < len(word) - 1:
        if word[i] == word[i + 1]:
            pair_count += 1
            i += 2  # Skip the pair
        else:
            i += 1
    
    # If more than 2 consecutive pairs found, it's likely an OCR error
    # This helps distinguish between legitimate double characters and OCR errors
    total_chars = len(word)
    
    # Calculate ratio of paired characters
    paired_chars = pair_count * 2
    
    # If majority of the word consists of paired characters, it's an error
    # Threshold: if more than 50% of characters are in pairs
    return paired_chars >= total_chars * 0.5 and pair_count >= 2


def fix_character_duplication(text: str) -> str:
    """
    Fix OCR character duplication in Tigrinya text.
    
    Rules:
    1. In Tigrinya, a character never repeats 3+ times consecutively
    2. If a word has multiple consecutive character pairs (pattern like "ንንኣኣሌሌ"),
       it's an OCR error - remove duplicates
    3. Apply same logic to non-alphabet characters (punctuation, etc.)
    """
    if not text:
        return text
    
    # Split into words while preserving separators
    # This regex splits on whitespace but keeps the separators
    tokens = re.split(r'(\s+)', text)
    
    fixed_tokens = []
    for token in tokens:
        if not token or token.isspace():
            # Preserve whitespace
            fixed_tokens.append(token)
            continue
        
        # Check if this token has the duplication pattern
        if detect_duplication_pattern(token):
            # Remove consecutive duplicates
            fixed_word = remove_consecutive_duplicates(token)
            fixed_tokens.append(fixed_word)
        else:
            # Check for triple+ character repetitions (always an error)
            fixed_word = fix_triple_repetitions(token)
            fixed_tokens.append(fixed_word)
    
    return ''.join(fixed_tokens)


def remove_consecutive_duplicates(word: str) -> str:
    """
    Remove consecutive duplicate characters from a word.
    "ንንኣኣሌሌክክሳሳንንደደርር" -> "ንኣሌክሳንደር"
    """
    if not word:
        return word
    
    result = [word[0]]
    for i in range(1, len(word)):
        # Only add character if it's different from the previous one
        if word[i] != word[i - 1]:
            result.append(word[i])
    
    return ''.join(result)


def fix_triple_repetitions(text: str) -> str:
    """
    Fix any character that repeats 3+ times (always an error in Tigrinya).
    "ንንን" -> "ን" (or "ንን" depending on context)
    """
    if not text:
        return text
    
    # Replace any character repeated 3+ times with just one
    # This handles cases like "ንንን" -> "ን"
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        count = 1
        
        # Count consecutive repetitions
        while i + count < len(text) and text[i + count] == char:
            count += 1
        
        # If 3+ repetitions, it's definitely an error - keep only one
        # If 2 repetitions, could be legitimate or error (handled by detect_duplication_pattern)
        if count >= 3:
            result.append(char)
        else:
            result.append(char * count)
        
        i += count
    
    return ''.join(result)


def is_valid_sentence(sentence: str, min_words: int = 5) -> bool:
    """
    Check if a sentence is valid (not just a fragment).
    
    A valid sentence must:
    - Have more than min_words words (default: 5, so 4 or fewer words = invalid)
    - Not be just punctuation or numbers
    - Not be just abbreviations
    """
    if not sentence:
        return False
    
    # Check if it's just dots, dashes, or similar
    if re.match(r'^[\.\-\s።?!,:\'"]+$', sentence):
        return False
    
    # Count words by simple whitespace split (most reliable)
    words = sentence.split()
    
    # Must have more than min_words (so 4 or fewer = not a sentence)
    if len(words) < min_words:
        return False
    
    # Check if it has enough Ge'ez characters (real Tigrinya content)
    geez_chars = sum(1 for c in sentence if '\u1200' <= c <= '\u137F')
    if geez_chars < 10:  # Must have at least 10 Ge'ez characters
        return False
    
    return True


def split_into_sentences(text: str) -> List[str]:
    """
    Split Tigrinya text into sentences.
    
    Tigrinya uses various sentence-ending punctuation:
    - ። (Ethiopian full stop / Ethiopic full stop)
    - ? ! . (standard punctuation sometimes used)
    - :: (sometimes used as full stop)
    
    Filters out fragments with 4 or fewer words.
    """
    if not text:
        return []
    
    # Tigrinya sentence delimiters
    # ። is the traditional Ethiopic full stop (U+1362)
    # We also handle standard punctuation
    sentence_pattern = r'[።?!.።]+\s*'
    
    # Split by sentence delimiters but keep them
    parts = re.split(f'({sentence_pattern})', text)
    
    sentences = []
    current_sentence = ""
    
    for part in parts:
        if not part:
            continue
        
        current_sentence += part
        
        # Check if this part is a delimiter
        if re.match(sentence_pattern, part):
            # Clean up the sentence
            sentence = current_sentence.strip()
            # Only add if it's a valid sentence (more than 4 words)
            if is_valid_sentence(sentence, min_words=5):
                sentences.append(sentence)
            current_sentence = ""
    
    # Add any remaining text as final sentence (if valid)
    remaining = current_sentence.strip()
    if is_valid_sentence(remaining, min_words=5):
        sentences.append(remaining)
    
    # Additional splitting on newlines if sentences are too long
    final_sentences = []
    for sentence in sentences:
        # If sentence is very long, also split on newlines
        if len(sentence) > 500 and '\n' in sentence:
            sub_sentences = [s.strip() for s in sentence.split('\n') if s.strip()]
            final_sentences.extend(sub_sentences)
        else:
            final_sentences.append(sentence)
    
    return final_sentences


def preprocess_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess a single article from raw_data.json.
    
    Returns a new article dict with:
    - Original fields preserved
    - cleaned_text: the preprocessed text
    - sentences: list of sentences
    - original_article_index: link back to raw_data.json
    """
    extracted_text = article.get('extracted_text', '')
    
    # Step 1: Fix character duplication
    cleaned_text = fix_character_duplication(extracted_text)
    
    # Step 2: Split into sentences
    sentences = split_into_sentences(cleaned_text)
    
    # Create preprocessed article
    preprocessed = {
        'original_index': article.get('index', 0),
        'news_title': article.get('news_title', ''),
        'article_url': article.get('article_url', ''),
        'publication_date': article.get('publication_date', ''),
        'pdf_filename': article.get('pdf_filename', ''),
        'pdf_url': article.get('pdf_url', ''),
        'cleaned_text': cleaned_text,
        'sentences': sentences,
        'sentence_count': len(sentences),
        'original_char_count': len(extracted_text),
        'cleaned_char_count': len(cleaned_text),
        'reduction_ratio': round(1 - len(cleaned_text) / len(extracted_text), 4) if extracted_text else 0
    }
    
    return preprocessed


def preprocess_raw_data(input_file: str = 'raw_data.json', 
                        output_file: str = 'preprocessed_data.json') -> Dict[str, Any]:
    """
    Preprocess all articles in raw_data.json and save to preprocessed_data.json.
    
    Returns statistics about the preprocessing.
    """
    print(f"📖 Loading data from {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {input_file} not found")
        return {'error': f'{input_file} not found'}
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {input_file}: {e}")
        return {'error': str(e)}
    
    print(f"✅ Loaded {len(raw_data)} articles")
    
    # Preprocess each article
    preprocessed_articles = []
    total_original_chars = 0
    total_cleaned_chars = 0
    total_sentences = 0
    
    for i, article in enumerate(raw_data):
        print(f"🔄 Processing article {i + 1}/{len(raw_data)}...", end='\r')
        
        preprocessed = preprocess_article(article)
        preprocessed_articles.append(preprocessed)
        
        total_original_chars += preprocessed['original_char_count']
        total_cleaned_chars += preprocessed['cleaned_char_count']
        total_sentences += preprocessed['sentence_count']
    
    print(f"\n✅ Processed {len(preprocessed_articles)} articles")
    
    # Create output structure with metadata
    output_data = {
        'metadata': {
            'source_file': input_file,
            'total_articles': len(preprocessed_articles),
            'total_sentences': total_sentences,
            'total_original_chars': total_original_chars,
            'total_cleaned_chars': total_cleaned_chars,
            'overall_reduction_ratio': round(1 - total_cleaned_chars / total_original_chars, 4) if total_original_chars else 0,
            'preprocessing_notes': [
                'Fixed OCR character duplication issues',
                'Split text into sentences',
                'Characters never repeat 3+ times in Tigrinya'
            ]
        },
        'articles': preprocessed_articles
    }
    
    # Save to output file
    print(f"💾 Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    # Print statistics
    print("\n📊 Preprocessing Statistics:")
    print(f"   • Articles processed: {len(preprocessed_articles)}")
    print(f"   • Total sentences extracted: {total_sentences}")
    print(f"   • Original characters: {total_original_chars:,}")
    print(f"   • Cleaned characters: {total_cleaned_chars:,}")
    print(f"   • Character reduction: {output_data['metadata']['overall_reduction_ratio'] * 100:.1f}%")
    
    return output_data['metadata']


def demo_preprocessing():
    """Demonstrate preprocessing on sample text."""
    sample_texts = [
        "ንንኣኣሌሌክክሳሳንንደደርር",  # Should become: ንኣሌክሳንደር
        "ገገጽጽ 22",                    # Should become: ገጽ 22
        "ጂጂኦኦፖፖለለቲቲካካ",          # Should become: ጂኦፖለቲካ
        "ኤርትራ",                       # Should stay: ኤርትራ (no duplication)
        "ሓሓዳዳስስ",                     # Should become: ሓዳስ
    ]
    
    print("🔬 Preprocessing Demo:")
    print("-" * 50)
    
    for text in sample_texts:
        fixed = fix_character_duplication(text)
        has_pattern = detect_duplication_pattern(text)
        print(f"  Input:  '{text}'")
        print(f"  Output: '{fixed}'")
        print(f"  Pattern detected: {has_pattern}")
        print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        demo_preprocessing()
    else:
        print("=" * 60)
        print("🔧 Tigrinya Text Preprocessor")
        print("=" * 60)
        
        # Run preprocessing
        stats = preprocess_raw_data()
        
        if 'error' not in stats:
            print("\n✅ Preprocessing complete!")
            print("📁 Output saved to: preprocessed_data.json")
        else:
            print(f"\n❌ Preprocessing failed: {stats['error']}")
