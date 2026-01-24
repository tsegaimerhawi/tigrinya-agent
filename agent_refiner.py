"""
Agent Refiner - Data Engineer for NLP
=====================================

Specializes in structuring and refining NLP data for storage and analysis.
Handles date normalization, topic summarization, and data structuring.
"""

import json
import re
from typing import Dict, List, Any, Optional
from typing_extensions import TypedDict
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment for potential LLM use
load_dotenv()

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.prompts import ChatPromptTemplate
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class RefinedArticle(TypedDict):
    """Structured output from the Refiner Agent"""
    article_id: str
    original_text: str
    tagged_tokens: List[Dict[str, str]]
    metadata: Dict[str, Any]
    refined_at: str


class TigrinyaDataEngineer:
    """Data Engineer specializing in Tigrinya NLP data refinement"""

    def __init__(self):
        # Tigrinya month names and their numeric equivalents
        self.tigrinya_months = {
            'መስከረም': 1, 'ሚያዝያ': 2, 'ግንቦት': 3, 'ሰኔ': 4, 'ሐምሌ': 5, 'ነሐሴ': 6,
            'መስክሬም': 1, 'ሜስከረም': 1, 'መስከረም': 1,  # Alternative spellings
            'ጥሪ': 2, 'ጥቅምት': 3, 'ህዳር': 4, 'ታህሳስ': 5, 'ጥር': 6, 'የካቲት': 7,
            'መጋቢት': 8, 'ሚያዝያ': 2, 'ግንቦት': 3, 'ሰኔ': 4, 'ሓምለ': 5,
            'ነሓሰ': 6, 'መስክሪም': 1, 'ትሪ': 2, 'ህዳር': 4, 'ታህሳስ': 5
        }

        # Ethiopian calendar months (for reference)
        self.ethiopian_months = {
            'መስከረም': 1, 'ጥቅምት': 2, 'ህዳር': 3, 'ታህሳስ': 4,
            'ጥር': 5, 'የካቲት': 6, 'መጋቢት': 7, 'ሚያዝያ': 8,
            'ግንቦት': 9, 'ሰኔ': 10, 'ሓምለ': 11, 'ነሓሰ': 12
        }

        # Initialize LLM for summarization if available
        if LLM_AVAILABLE and os.getenv('GOOGLE_API_KEY'):
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.1,
                max_tokens=100
            )
        else:
            self.llm = None

    def extract_dates_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract and normalize dates from Tigrinya text"""
        dates = []

        # Pattern 1: DD/MM/YYYY or DD-MM-YYYY
        gregorian_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        for match in re.finditer(gregorian_pattern, text):
            day, month, year = map(int, match.groups())
            try:
                # Validate date
                datetime(year, month, day)
                dates.append({
                    'original': match.group(0),
                    'normalized': f"{year:04d}-{month:02d}-{day:02d}",
                    'type': 'gregorian'
                })
            except ValueError:
                continue

        # Pattern 2: Tigrinya month names with day and year
        # e.g., "መስከረም 15 ቀን 2015 ዓመት"
        tigrinya_date_pattern = r'(\w+)\s+(\d{1,2})\s*(?:ቀን)?\s*(\d{4})\s*(?:ዓመት)?'
        for match in re.finditer(tigrinya_date_pattern, text):
            month_name, day, year = match.groups()
            day = int(day)
            year = int(year)

            # Try Ethiopian calendar first, then fallback to Gregorian month names
            month_num = self.ethiopian_months.get(month_name.strip())
            if month_num:
                # Convert Ethiopian date to Gregorian (approximate)
                # Ethiopian calendar is about 7-8 years behind Gregorian
                gregorian_year = year + 8  # Rough approximation
                try:
                    datetime(gregorian_year, month_num, day)
                    dates.append({
                        'original': match.group(0),
                        'normalized': f"{gregorian_year:04d}-{month_num:02d}-{day:02d}",
                        'type': 'ethiopian_tigrinya'
                    })
                except ValueError:
                    continue

        # Pattern 3: Year only (e.g., "2015 ዓመት")
        year_only_pattern = r'(\d{4})\s*ዓመት'
        for match in re.finditer(year_only_pattern, text):
            year = match.group(1)
            dates.append({
                'original': match.group(0),
                'normalized': year,
                'type': 'year_only'
            })

        return dates

    def generate_topic_summary(self, text: str, tagged_tokens: List[Dict[str, str]]) -> str:
        """Generate a 3-5 word topic summary"""

        if self.llm:
            # Use LLM for intelligent summarization
            prompt = ChatPromptTemplate.from_template("""
            Analyze this Tigrinya newspaper article and provide a concise 3-5 word summary of the main topic.
            Focus on the core subject matter.

            Article text: {text}

            Provide only the summary, nothing else. Example: "Diplomatic Seminar in Qatar"
            """)

            try:
                chain = prompt | self.llm
                response = chain.invoke({"text": text[:500]})  # Limit text length
                summary = response.content.strip()

                # Validate length (3-5 words)
                word_count = len(summary.split())
                if 3 <= word_count <= 5:
                    return summary
            except Exception as e:
                print(f"LLM summarization failed: {e}")

        # Fallback: Extract key nouns and create summary
        nouns = [token['word'] for token in tagged_tokens
                if token.get('tag', '').lower() == 'noun']

        # Priority nouns (geopolitical, organizational)
        priority_nouns = []
        for noun in nouns[:10]:  # Check first 10 nouns
            if any(entity in noun for entity in ['ኤርትራ', 'ኣስመራ', 'ኣድዋ', 'ኣፍሪቃ', 'ኣመሪካ']):
                priority_nouns.append(noun)

        if priority_nouns:
            # Use first priority noun + context
            main_subject = priority_nouns[0]
            if len(nouns) > 1:
                return f"{main_subject} ሓድሽ ኣቀራርያ"  # Default: "Subject News"
            else:
                return f"{main_subject} ዜና"  # Default: "Subject News"

        # Generic fallback
        return "ኤርትራ ዜና መራገጭታ"  # "Eritrea News Update"

    def create_article_id(self, metadata: Dict[str, Any]) -> str:
        """Generate a unique article identifier"""
        # Use URL or title hash, fallback to timestamp
        if 'url' in metadata:
            import hashlib
            url_hash = hashlib.md5(metadata['url'].encode()).hexdigest()[:8]
            return f"article_{url_hash}"
        elif 'title' in metadata:
            import hashlib
            title_hash = hashlib.md5(metadata['title'].encode()).hexdigest()[:8]
            return f"article_{title_hash}"
        else:
            import time
            timestamp = str(int(time.time()))
            return f"article_{timestamp}"

    def refine_article_data(self,
                          original_text: str,
                          tagged_tokens: List[Dict[str, str]],
                          critic_metadata: Dict[str, Any]) -> RefinedArticle:
        """
        Main refinement function

        Args:
            original_text: The cleaned Tigrinya text
            tagged_tokens: POS-tagged tokens from the critic
            critic_metadata: Metadata from the critic agent

        Returns:
            Structured article data ready for storage
        """

        print("🔧 Data Engineer refining article data...")
        print("📅 Converting dates...")
        dates = self.extract_dates_from_text(original_text)

        print("📝 Generating topic summary...")
        topic_summary = self.generate_topic_summary(original_text, tagged_tokens)

        print("🆔 Creating article ID...")
        article_id = self.create_article_id(critic_metadata)

        # Build comprehensive metadata
        metadata = {
            **critic_metadata,  # Include all critic metadata
            'dates_found': dates,
            'topic_summary': topic_summary,
            'word_count': len(tagged_tokens),
            'geez_script_only': all('\u1200' <= token['word'][0] <= '\u137f'
                                  for token in tagged_tokens if token['word']),
            'refined_timestamp': datetime.now().isoformat()
        }

        # Create final structured output
        refined_article: RefinedArticle = {
            'article_id': article_id,
            'original_text': original_text,
            'tagged_tokens': tagged_tokens,
            'metadata': metadata,
            'refined_at': datetime.now().isoformat()
        }

        print(f"✅ Article refined: {article_id}")
        print(f"📊 {len(dates)} dates normalized, topic: '{topic_summary}'")

        return refined_article


def load_critic_results(filepath: str = 'pipeline_results.json') -> Optional[Dict]:
    """Load results from the critic agent"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Critic results file '{filepath}' not found")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{filepath}': {e}")
        return None


def save_refined_article(refined_article: RefinedArticle, filepath: str = 'refined_articles.json'):
    """Save refined article to JSON file"""
    # Load existing articles if file exists
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            articles = json.load(f)
            if not isinstance(articles, list):
                articles = [articles]
    except (FileNotFoundError, json.JSONDecodeError):
        articles = []

    # Add new article
    articles.append(refined_article)

    # Save back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Example usage
    sample_text = "መስከረም 15 ቀን 2015 ዓመት ኤርትራ ኣብ ኣድዋ ዓቢ ስብሃት ኣለዋ ብሓዳስ ኤርትራ ኣኼባ።"
    sample_tags = [
        {'word': 'መስከረም', 'tag': 'Noun'},
        {'word': 'ኤርትራ', 'tag': 'Noun'},
        {'word': 'ኣብ', 'tag': 'Preposition'},
        {'word': 'ኣድዋ', 'tag': 'Noun'}
    ]
    sample_metadata = {
        'url': 'https://example.com/article1',
        'title': 'ኤርትራ ስብሃት',
        'date': '2024-01-15'
    }

    engineer = TigrinyaDataEngineer()
    result = engineer.refine_article_data(sample_text, sample_tags, sample_metadata)

    print("\n📋 Refined Article Structure:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Save example
    save_refined_article(result)
    print("\n💾 Saved to 'refined_articles.json'")