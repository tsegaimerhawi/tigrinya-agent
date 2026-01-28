"""
Tigrinya RAG Agent
==================

An agent that answers questions using retrieved context from the Tigrinya corpus.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from retriever import TigrinyaRetriever

# Load environment
load_dotenv('.env_config')

class TigrinyaRAGAgent:
    """Agent for Question Answering over Tigrinya Documents"""
    
    def __init__(self):
        self.retriever = TigrinyaRetriever()
        
        # Initialize LLM
        # Using Gemini 2.5 Pro as requested for better Tigrinya support
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0.3,
            max_tokens=2048
        )
        
        # Define Prompt
        self.template = """You are a helpful assistant for Tigrinya news and history.
        Use the following pieces of retrieved context to answer the question. 
        If you don't know the answer, just say that you don't know. 
        
        The context is in Tigrinya. You can answer in English or Tigrinya, depending on the language of the question.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:"""
        
        self.prompt = ChatPromptTemplate.from_template(self.template)
        
        # Build Chain
        self.chain = (
            {"context": lambda x: self._format_docs(x["context"]), "question": lambda x: x["question"]}
            | self.prompt
            | self.llm
        )
        
    def _format_docs(self, docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into a single string"""
        return "\n\n".join([f"[Source: {d.get('metadata', {}).get('article_id', 'Unknown')}]\n{d.get('text', '')}" for d in docs])
        
    def answer(self, question: str, k: int = 5) -> str:
        """
        Answer a question using RAG
        
        Args:
            question: User question
            k: Number of documents to retrieve
            
        Returns:
            The generated answer
        """
        # 1. Retrieve
        print(f"🔍 Searching for: '{question}'...")
        docs = self.retriever.search(question, k=k)
        
        if not docs:
            return "I couldn't find any relevant documents to answer your question."
            
        print(f"📚 Found {len(docs)} relevant snippets.")
        
        # 2. Generate
        print("🤔 Thinking...")
        response = self.chain.invoke({"context": docs, "question": question})
        
        return response.content

if __name__ == "__main__":
    agent = TigrinyaRAGAgent()
    q = "ኤርትራ"
    print(f"\nQ: {q}")
    print(f"A: {agent.answer(q)}")
