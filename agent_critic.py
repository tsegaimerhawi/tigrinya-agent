"""
Agent Critic - Senior Tigrinya Grammarian
=========================================

A skeptical Tigrinya linguist who rigorously validates POS tagging results.
"""

import json
import re
from typing import List, Dict, Tuple, Union
from typing_extensions import TypedDict


class CriticState(TypedDict):
    """State for the Tigrinya Grammarian Critic Agent"""
    pos_tags: List[Dict[str, str]]
    feedback: List[str]
    status: str  # 'PASSED' or 'FEEDBACK'


class TigrinyaGrammarianCritic:
    """Senior Tigrinya Grammarian with a skeptical personality"""

    def __init__(self):
        # Tigrinya linguistic patterns and rules
        self.prefixes = {
            'ካ': 'ablative preposition',
            'ኣዝ': 'instrumental preposition',
            'ን': 'accusative preposition',
            'ብ': 'instrumental preposition',
            'መ': 'infinitive prefix',
            'የ': 'possessive/attributive',
            'እ': 'subject prefix',
            'ይ': 'object/3rd person prefix',
            'ት': '2nd person feminine prefix',
            'ን': '1st person plural prefix'
        }

        # Common Tigrinya proper nouns and entities (especially geopolitical)
        self.proper_nouns = {
            'ኤርትራ', 'ኣስመራ', 'ኣድዋ', 'ኣፍሪቃ', 'ኣመሪካ', 'እንግሊዝ',
            'ኣይቲ', 'ኣሌክስ', 'ኣብ ዓለም', 'ሓዳስ ኤርትራ', 'ሻቤት',
            'መበል', 'ዓመት', 'ዓርቢ', 'ጥሪ', 'ናቕፋ', 'ገጻት'
        }

        # Word patterns that indicate potential issues
        self.suspicious_patterns = [
            (r'^ኣ', 'Possible noun with definite article - check if base form is tagged'),
            (r'^ብ', 'Instrumental preposition prefix - ensure base word is properly tagged'),
            (r'^ካ', 'Ablative preposition - verify preposition-noun separation'),
            (r'^መ', 'Infinitive marker - should be part of verb morphology'),
        ]

    def analyze_prefixes(self, word: str, tag: str) -> List[str]:
        """Check for missing prefix analysis"""
        issues = []

        # Check for common prefixes that might be incorrectly separated
        for prefix_char, prefix_name in self.prefixes.items():
            if word.startswith(prefix_char) and len(word) > len(prefix_char):
                base_word = word[len(prefix_char):]
                if base_word and base_word in self.proper_nouns:
                    issues.append(f"Word '{word}' appears to have {prefix_name} prefix '{prefix_char}' + proper noun '{base_word}' - consider separate tagging")

        # Check for compound words with prepositions
        if 'ካ' in word and word != 'ካ':
            issues.append(f"Word '{word}' contains ablative preposition 'ካ' - may need morphological analysis")

        return issues

    def check_proper_nouns(self, word: str, tag: str) -> List[str]:
        """Verify proper noun tagging"""
        issues = []

        if word in self.proper_nouns and tag.lower() != 'noun':
            issues.append(f"Proper noun '{word}' should be tagged as 'Noun', not '{tag}'")

        # Check for geopolitical entities that should be proper nouns
        geopolitical_indicators = ['ኤርትራ', 'ሓዳስ', 'ሻቤት', 'ኣስመራ']
        for indicator in geopolitical_indicators:
            if indicator in word and tag.lower() != 'noun':
                issues.append(f"Geopolitical entity '{word}' containing '{indicator}' should likely be 'Noun'")

        return issues

    def validate_morphology(self, word: str, tag: str) -> List[str]:
        """Check morphological consistency"""
        issues = []

        # Check for suspicious patterns
        for pattern, description in self.suspicious_patterns:
            if re.search(pattern, word):
                issues.append(f"Word '{word}' ({tag}): {description}")

        # Check for numbers in words (should be separate tokens)
        if any(char.isdigit() for char in word):
            issues.append(f"Word '{word}' contains numbers - consider tokenizing separately")

        # Check for very short words that might be prefixes
        if len(word) <= 2 and tag.lower() == 'noun':
            issues.append(f"Very short word '{word}' tagged as '{tag}' - might be a particle or prefix")

        return issues

    def critique_tags(self, pos_tags: List[Dict[str, str]]) -> Tuple[str, List[str]]:
        """
        Main critique function

        Returns:
            Tuple of (status, feedback_list)
            status: 'PASSED' or 'FEEDBACK'
            feedback_list: List of specific issues found
        """
        feedback = []

        print("🔍 Senior Tigrinya Grammarian reviewing POS tags...")
        print("⚖️  Applying skeptical analysis...\n")

        for tag_entry in pos_tags:
            word = tag_entry['word']
            tag = tag_entry['tag']

            # Analyze prefixes
            prefix_issues = self.analyze_prefixes(word, tag)
            feedback.extend(prefix_issues)

            # Check proper nouns
            noun_issues = self.check_proper_nouns(word, tag)
            feedback.extend(noun_issues)

            # Validate morphology
            morph_issues = self.validate_morphology(word, tag)
            feedback.extend(morph_issues)

        if feedback:
            print(f"❌ Found {len(feedback)} issues requiring attention:")
            for issue in feedback[:5]:  # Show first 5 issues
                print(f"   • {issue}")
            if len(feedback) > 5:
                print(f"   • ... and {len(feedback) - 5} more issues")
            return 'FEEDBACK', feedback
        else:
            print("✅ All tags appear grammatically sound")
            return 'PASSED', []

    def run_critique(self, pos_tags: List[Dict[str, str]]) -> CriticState:
        """Run the complete critique process"""
        status, feedback = self.critique_tags(pos_tags)

        state: CriticState = {
            'pos_tags': pos_tags,
            'feedback': feedback,
            'status': status
        }

        return state


def load_pos_tags_from_file(filepath: str = 'pos_tags.json') -> List[Dict[str, str]]:
    """Load POS tags from a JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('pos_tags', [])
    except FileNotFoundError:
        print(f"❌ Error: POS tags file '{filepath}' not found")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{filepath}': {e}")
        return []


def save_critique_results(state: CriticState, filepath: str = 'critique_results.json'):
    """Save critique results to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Example usage with sample data
    sample_tags = [
        {'word': 'መበል', 'tag': 'Particle'},
        {'word': 'ኤርትራ', 'tag': 'Noun'},
        {'word': 'ዓመት', 'tag': 'Noun'},
        {'word': 'ካኤርትራ', 'tag': 'Noun'},  # Should this be separate?
        {'word': 'ብሓዳስ', 'tag': 'Noun'},   # Should this be separate?
    ]

    critic = TigrinyaGrammarianCritic()
    result = critic.run_critique(sample_tags)

    print(f"\n📋 Final Status: {result['status']}")
    if result['feedback']:
        print("\n🔧 Feedback for Tagger:")
        for fb in result['feedback']:
            print(f"   • {fb}")

    # Save results
    save_critique_results(result)
    print("\n💾 Results saved to 'critique_results.json'")