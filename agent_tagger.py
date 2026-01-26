#!/usr/bin/env python3
"""
Tigrinya POS Tagger Agent using LangGraph and LangChain.
Performs part-of-speech tagging on Tigrinya text extracted from newspapers.
"""

import json
import os
import re
from typing import TypedDict, List, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env_config')
print(f"GOOGLE_API_KEY loaded: {'Yes' if os.getenv('GOOGLE_API_KEY') else 'No'}")


class AgentState(TypedDict):
    """State for the POS tagging agent."""
    raw_text: str
    pos_tags: List[Dict[str, str]]


def load_sample_text() -> str:
    """Load a sample paragraph from preprocessed_data.json for testing."""
    try:
        with open('preprocessed_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Get the first article's cleaned text
        articles = data.get('articles', [])
        if articles and len(articles) > 0:
            full_text = articles[0].get('cleaned_text', '')
            if not full_text:
                print("No cleaned text found in preprocessed_data.json")
                return ""

            # Extract first 800 characters as a sample paragraph
            sample_text = full_text[:800].strip()

            # Make sure we end at a word boundary
            if len(sample_text) < len(full_text):
                last_space = sample_text.rfind(' ')
                if last_space > 0:
                    sample_text = sample_text[:last_space]

            print(f"Sample text length: {len(sample_text)} characters")
            return sample_text

    except FileNotFoundError:
        print("❌ Error: preprocessed_data.json not found. Please run preprocessor.py first.")
        return ""
    except Exception as e:
        print(f"Error loading sample text: {e}")
        return ""


def load_sentences(article_index: int = 0, max_sentences: int = 5) -> list:
    """Load sentences from preprocessed_data.json for sentence-by-sentence processing."""
    try:
        with open('preprocessed_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        articles = data.get('articles', [])
        if articles and len(articles) > article_index:
            sentences = articles[article_index].get('sentences', [])
            return sentences[:max_sentences]
        return []

    except FileNotFoundError:
        print("❌ Error: preprocessed_data.json not found. Please run preprocessor.py first.")
        return []
    except Exception as e:
        print(f"Error loading sentences: {e}")
        return []


def validate_geez_text(text: str) -> bool:
    """Validate that text contains only Ge'ez script characters."""
    if not text:
        return False

    # Count Ge'ez characters vs total characters
    geez_chars = sum(1 for c in text if '\u1200' <= c <= '\u137F')
    total_chars = len(text.replace(' ', '').replace('\n', ''))

    if total_chars == 0:
        return False

    # Allow up to 5% non-Ge'ez characters (for punctuation, numbers)
    geez_ratio = geez_chars / total_chars
    return geez_ratio >= 0.95


def tagger_node(state: AgentState) -> Dict[str, Any]:
    """POS tagging node that processes Tigrinya text."""

    # Initialize LLM with Gemini 2.5 Flash
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,  # Low temperature for consistent tagging
        max_tokens=1000
    )

    # Create the prompt
    system_prompt = """You are a professional Tigrinya linguist and expert in Eritrean geopolitics. Your task is to analyze Tigrinya text and assign part-of-speech tags to each word.

TAGGING RULES:
- Noun: People, places, things, ideas (ኣስመራ, ኤርትራ, ሓዳስ)
- Verb: Actions, states (ምጽኣል, ኣለዋ, ምሓር)
- Adjective: Descriptions (እታው, ሓድሽ, ገዚፍ)
- Particle: Small function words (ን, ኣብ, እንተ, እውን)

SPECIAL ATTENTION:
- Pay special attention to geopolitical entities (countries, cities, regions)
- ኤርትራ (Eritrea), ኣስመራ (Asmara), ትግራይ (Tigray), ኣፍርቃ (Africa), etc.

IMPORTANT:
- Do not hallucinate or add non-Ge'ez characters
- Focus only on the Tigrinya words provided
- Be accurate in your linguistic analysis"""

    user_prompt = f"""Analyze this Tigrinya text and assign POS tags to each word. Return the results as a simple list where each line contains a word and its tag separated by a colon:

{state['raw_text']}

Example format:
ኤርትራ:Noun
ሓዳስ:Noun
ኣለዋ:Verb"""

    # Create and run the chain
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt)
    ])

    chain = prompt | llm

    try:
        response = chain.invoke({})

        # Extract response text
        response_text = response.content.strip()

        # Parse the colon-separated format
        pos_tags = []
        for line in response_text.split('\n'):
            line = line.strip()
            if ':' in line:
                word, tag = line.split(':', 1)
                word = word.strip()
                tag = tag.strip()

                # Validate tag
                if tag in ['Noun', 'Verb', 'Adjective', 'Particle'] and word:
                    pos_tags.append({"word": word, "tag": tag})

        # Validate no non-Ge'ez characters in the response
        if pos_tags and not validate_geez_text(' '.join(tag['word'] for tag in pos_tags)):
            print("⚠️  WARNING: LLM response contains non-Ge'ez characters")
            # Filter out invalid entries
            pos_tags = [tag for tag in pos_tags if validate_geez_text(tag.get('word', ''))]

        return {"pos_tags": pos_tags}

    except Exception as e:
        print(f"Error in POS tagging: {e}")
        return {"pos_tags": []}


def create_tagger_graph():
    """Create the LangGraph for POS tagging."""

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add the tagger node
    workflow.add_node("tagger", tagger_node)

    # Set entry point
    workflow.set_entry_point("tagger")

    # Add edge to END
    workflow.add_edge("tagger", END)

    # Compile the graph
    return workflow.compile()


def run_pos_tagger(text: str = None):
    """Run the POS tagger on sample Tigrinya text."""

    # Load sample text
    if text is None:
        sample_text = load_sample_text()
    else:
        sample_text = text

    if not sample_text:
        print("❌ No text available for POS tagging")
        return None

    print(f"Loaded sample text ({len(sample_text)} characters)")
    print(f"Sample: {sample_text[:100]}...")

    # Validate input text
    if not validate_geez_text(sample_text):
        print("⚠️  WARNING: Input text contains non-Ge'ez characters")
    else:
        print("✅ Input text validation passed")

    # Create initial state
    initial_state = AgentState(
        raw_text=sample_text,
        pos_tags=[]
    )

    # Create and run the graph
    graph = create_tagger_graph()

    print("\n🔄 Running POS tagging...")
    result = graph.invoke(initial_state)

    # Display results
    pos_tags = result.get('pos_tags', [])

    print(f"\n📊 POS Tagging Results:")
    print(f"Total tagged words: {len(pos_tags)}")

    if pos_tags:
        print("\nSample tags:")
        for i, tag_entry in enumerate(pos_tags[:10]):
            print(f"  {tag_entry['word']} -> {tag_entry['tag']}")

        # Count tags
        tag_counts = {}
        for tag_entry in pos_tags:
            tag = tag_entry['tag']
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        print("\nTag distribution:")
        for tag, count in tag_counts.items():
            print(f"  {tag}: {count}")

    else:
        print("❌ No POS tags generated")

    return result


if __name__ == "__main__":
    # Check for Google API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        print("Please create a .env file with your Google API key:")
        print("GOOGLE_API_KEY=your_google_api_key_here")
        exit(1)

    run_pos_tagger()