import streamlit as st
import time
from agent_rag import TigrinyaRAGAgent
from dotenv import load_dotenv
import os

# Page configuration
st.set_page_config(
    page_title="Tigrinya AI Agent",
    page_icon="🇪🇷",
    layout="centered"
)

# Load environment
load_dotenv('.env_config')

# Custom CSS for aesthetics
st.markdown("""
<style>
    .stChatInput {
        border-radius: 20px;
    }
    .user-message {
        background-color: #e6f7ff;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .agent-message {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    h1 {
        text-align: center;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("Tigrinya AI Agent 🇪🇷")
st.caption("Ask questions about Eritrean news and history in Tigrinya or English.")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    try:
        with st.spinner("Connecting to Knowledge Base..."):
            st.session_state.agent = TigrinyaRAGAgent()
        st.success("Connected!", icon="✅")
        time.sleep(1) # Show success briefly
        st.rerun() # Refresh to remove spinner
    except Exception as e:
        st.error(f"Failed to connect to agent: {e}")
        st.stop()

# Sidebar options
with st.sidebar:
    st.header("Settings")
    k_retrieval = st.slider("Context Documents", min_value=1, max_value=10, value=3, help="Number of documents to retrieve for each query.")
    
    if st.button("Clear Conversation", type="primary"):
        st.session_state.messages = []
        st.rerun()
        
    st.divider()
    st.markdown("### About")
    st.markdown("This agent uses **RAG (Retrieval Augmented Generation)** to answer questions based on the *Haddas Ertra* newspaper corpus.")
    st.markdown(f"**Model:** Gemini 2.5 Flash")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask something... (e.g., ኤርትራ እንታይ እያ?)"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.agent.answer(prompt, k=k_retrieval)
                
                # Simulate typing effect
                for chunk in response.split():
                    full_response += chunk + " "
                    time.sleep(0.05)
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                
            except Exception as e:
                st.error(f"Error generating response: {e}")
                full_response = "Sorry, I encountered an error."
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
