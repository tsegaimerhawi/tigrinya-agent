#!/usr/bin/env python3
"""
Tigrinya Chat Interface
=======================

CLI for chatting with the Tigrinya RAG Agent.
"""

import sys
import argparse
from dotenv import load_dotenv
from agent_rag import TigrinyaRAGAgent

def main():
    parser = argparse.ArgumentParser(description='Chat with Tigrinya Corpus')
    parser.add_argument('query', nargs='?', help='Initial question to ask')
    args = parser.parse_args()
    
    # Load env
    load_dotenv('.env_config')
    
    try:
        print("🤖 Initializing RAG Agent...")
        agent = TigrinyaRAGAgent()
        print("✅ Ready! Type 'exit' or 'quit' to stop.\n")
        
        # If query provided via CLI
        if args.query:
            print(f"You: {args.query}")
            response = agent.answer(args.query)
            print(f"\nAgent: {response}\n")
            
        # Interactive loop
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye! 👋")
                    break
                
                if not user_input.strip():
                    continue
                    
                response = agent.answer(user_input)
                print(f"\nAgent: {response}\n")
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        print("Make sure Qdrant is running and .env_config has GOOGLE_API_KEY")

if __name__ == "__main__":
    main()
