
import sys
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv('.env_config')

def test_retriever():
    print("Testing Retriever...")
    from retriever import TigrinyaRetriever
    try:
        retriever = TigrinyaRetriever()
        results = retriever.search("ኤርትራ", k=1)
        print("✅ Retriever initialized successfully")
        print(f"   Found {len(results)} results")
        if results:
            print(f"   Top result score: {results[0]['score']}")
            print(f"   Top result text: {results[0]['text'][:50]}...")
        else:
            print("   ⚠️ No results found (Collection might be empty)")
        return True
    except Exception as e:
        print(f"❌ Retriever failed: {e}")
        return False

def test_agent():
    print("\nTesting RAG Agent...")
    from agent_rag import TigrinyaRAGAgent
    try:
        agent = TigrinyaRAGAgent()
        print("✅ Agent initialized successfully")
        
        query = "ኤርትራ እንታይ እያ?" # What is Eritrea?
        print(f"   Asking: {query}")
        
        answer = agent.answer(query, k=2)
        print(f"   Answer: {answer[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Agent failed: {e}")
        return False

if __name__ == "__main__":
    key = os.getenv('GOOGLE_API_KEY')
    if not key:
        print("❌ GOOGLE_API_KEY not found in environment")
        sys.exit(1)
    
    print(f"🔑 API Key loaded: {key[:5]}... ({len(key)} chars)")
        
    r_ok = test_retriever()
    a_ok = test_agent()
    
    if r_ok and a_ok:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
