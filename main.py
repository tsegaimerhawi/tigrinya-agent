"""
Tigrinya POS Tagging Pipeline
=============================

Main orchestration script that connects the POS Tagger and Critic agents.
"""

import os
import json
from dotenv import load_dotenv

# Import our agents
from agent_tagger import run_pos_tagger
from agent_critic import TigrinyaGrammarianCritic, save_critique_results
from agent_refiner import TigrinyaDataEngineer, save_refined_article


def load_tigrinya_data(filepath: str = 'preprocessed_data.json') -> str:
    """Load Tigrinya text data for processing from preprocessed data"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Get the first article's cleaned text as sample
            articles = data.get('articles', [])
            if articles and len(articles) > 0:
                return articles[0].get('cleaned_text', '')[:1000]  # First 1000 chars
            return ""
    except FileNotFoundError:
        print(f"❌ Error: Data file '{filepath}' not found")
        print("   Please run preprocessor.py first to generate preprocessed_data.json")
        return ""
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{filepath}': {e}")
        return ""


def load_tigrinya_sentences(filepath: str = 'preprocessed_data.json', article_index: int = 0, max_sentences: int = 5) -> list:
    """Load Tigrinya sentences for processing from preprocessed data"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            articles = data.get('articles', [])
            if articles and len(articles) > article_index:
                sentences = articles[article_index].get('sentences', [])
                return sentences[:max_sentences]
            return []
    except FileNotFoundError:
        print(f"❌ Error: Data file '{filepath}' not found")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{filepath}': {e}")
        return []


def save_pipeline_results(tagger_result: dict, critic_result: dict, filepath: str = 'pipeline_results.json'):
    """Save the complete pipeline results"""
    results = {
        'tagger_output': tagger_result,
        'critic_feedback': critic_result,
        'pipeline_status': 'completed'
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def run_tigrinya_pipeline():
    """Main pipeline: POS Tagger → Critic → Results"""

    print("🚀 Starting Tigrinya POS Tagging Pipeline")
    print("=" * 50)

    # Step 1: Load environment
    load_dotenv()
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        print("Please create a .env file with your Google API key")
        return

    # Step 2: Load Tigrinya data
    print("\n📖 Loading Tigrinya text data...")
    sample_text = load_tigrinya_data()
    if not sample_text:
        print("❌ No text data available")
        return

    print(f"✅ Loaded {len(sample_text)} characters of Tigrinya text")

    # Step 3: Run POS Tagger
    print("\n🏷️  Running POS Tagger Agent...")
    tagger_result = run_pos_tagger(sample_text)

    pos_tags = tagger_result.get('pos_tags', [])
    if not pos_tags:
        print("❌ POS Tagger failed to generate tags")
        return

    print(f"✅ Generated {len(pos_tags)} POS tags")

    # Step 4: Run Critic Agent
    print("\n🔍 Running Critic Agent (Senior Tigrinya Grammarian)...")
    critic = TigrinyaGrammarianCritic()
    critic_result = critic.run_critique(pos_tags)

    # Step 5: Run Refiner Agent
    print("\n🔧 Running Refiner Agent (Data Engineer)...")
    engineer = TigrinyaDataEngineer()
    refined_article = engineer.refine_article_data(
        original_text=sample_text,
        tagged_tokens=pos_tags,
        critic_metadata={
            'critic_status': critic_result['status'],
            'critic_feedback': critic_result['feedback'],
            'original_metadata': {}  # Could be expanded with more metadata
        }
    )

    # Step 6: Display Final Results
    print("\n" + "=" * 50)
    print("📊 COMPLETE PIPELINE RESULTS")
    print("=" * 50)

    status = critic_result['status']
    if status == 'PASSED':
        print("🎉 SUCCESS: All POS tags passed grammatical review!")
        print("✅ The Tigrinya text has been accurately tagged")
    else:
        print("⚠️  FEEDBACK: Issues found requiring attention")
        print(f"📝 {len(critic_result['feedback'])} grammatical concerns identified")

        print("\n🔧 Detailed Feedback:")
        for i, fb in enumerate(critic_result['feedback'][:10], 1):  # Show first 10
            print(f"   {i}. {fb}")

        if len(critic_result['feedback']) > 10:
            print(f"   ... and {len(critic_result['feedback']) - 10} more issues")

    # Step 6: Display Refiner Results
    print(f"\n🏗️  Refiner Results:")
    print(f"   • Article ID: {refined_article['article_id']}")
    print(f"   • Topic Summary: {refined_article['metadata']['topic_summary']}")
    print(f"   • Dates Found: {len(refined_article['metadata']['dates_found'])}")

    if refined_article['metadata']['dates_found']:
        print(f"   • Sample Date: {refined_article['metadata']['dates_found'][0]['normalized']}")

    # Step 7: Summary Statistics
    print(f"\n📈 Complete Summary:")
    print(f"   • Total words tagged: {len(pos_tags)}")
    print(f"   • Grammatical status: {status}")
    print(f"   • Ge'ez script only: {refined_article['metadata']['geez_script_only']}")

    if pos_tags:
        tag_counts = {}
        for tag_entry in pos_tags:
            tag = tag_entry['tag']
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        print(f"   • Tag distribution: {tag_counts}")

    # Step 8: Save Results
    # Save comprehensive pipeline results
    complete_results = {
        'tagger_output': tagger_result,
        'critic_feedback': critic_result,
        'refined_article': refined_article,
        'pipeline_status': 'completed',
        'completed_at': refined_article['refined_at']
    }

    with open('complete_pipeline_results.json', 'w', encoding='utf-8') as f:
        json.dump(complete_results, f, ensure_ascii=False, indent=2)

    # Save refined article separately
    save_refined_article(refined_article)

    print("\n💾 Results saved:")
    print("   • Complete pipeline: 'complete_pipeline_results.json'")
    print("   • Refined articles: 'refined_articles.json'")

    print("\n🎯 Complete pipeline finished successfully!")


if __name__ == "__main__":
    run_tigrinya_pipeline()