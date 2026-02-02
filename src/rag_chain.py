"""
RAG (Retrieval-Augmented Generation) chain for METU Assistant
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import streamlit as st

# Load environment variables
load_dotenv()

from src.config import (
    GROQ_MODEL,
    SYSTEM_PROMPT,
    TOP_K_RESULTS,
)
from src.embeddings import get_or_create_vector_store


def get_llm():
    """Create and return the LLM instance."""
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY"),
        temperature=0.3,
    )


def get_retriever(k: int = None):
    """Create and return the retriever."""
    if k is None:
        k = TOP_K_RESULTS
    
    vector_store = get_or_create_vector_store()
    
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


def format_docs(docs) -> str:
    """Format retrieved documents into a single string."""
    if not docs:
        return "İlgili bilgi bulunamadı. / No relevant information found."
    
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get('source', 'Unknown')
        content = doc.page_content.strip()
        formatted.append(f"[Kaynak/Source {i}: {source}]\n{content}")
    
    return "\n\n---\n\n".join(formatted)


def create_rag_chain():
    """Create the RAG chain with retrieval and generation."""
    
    llm = get_llm()
    retriever = get_retriever()
    
    # Prompt template with context and chat history
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT + """

Aşağıdaki bağlam bilgisini kullanarak soruyu yanıtla:
Use the following context to answer the question:

{context}
"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])
    
    # Create the chain
    chain = (
        {
            "context": lambda x: format_docs(retriever.invoke(x["question"])),
            "chat_history": lambda x: x.get("chat_history", []),
            "question": lambda x: x["question"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain


def create_simple_chain():
    """Create a simple chain without retrieval (for testing)."""
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    return chain


class METUAssistant:
    """
    High-level assistant class managing conversation and retrieval.
    """
    
    def __init__(self, use_rag: bool = True):
        """
        Initialize the assistant.
        
        Args:
            use_rag: If True, use RAG with vector store. 
                     If False, use simple LLM without retrieval.
        """
        self.use_rag = use_rag
        self.chat_history = []
        
        if use_rag:
            self.chain = create_rag_chain()
        else:
            self.chain = create_simple_chain()
    
    def chat(self, user_message: str) -> str:
        """
        Send a message and get a response.
        
        Args:
            user_message: The user's question or message.
            
        Returns:
            The assistant's response.
        """
        # Invoke the chain
        response = self.chain.invoke({
            "question": user_message,
            "chat_history": self.chat_history,
        })
        
        # Update chat history
        self.chat_history.append(HumanMessage(content=user_message))
        self.chat_history.append(AIMessage(content=response))
        
        # Keep history manageable (last 10 exchanges)
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-20:]
        
        return response
    
    def clear_history(self):
        """Clear the conversation history."""
        self.chat_history = []
    
    def get_relevant_docs(self, query: str, k: int = None) -> list:
        """
        Get relevant documents for a query (useful for debugging).
        """
        if k is None:
            k = TOP_K_RESULTS
        
        retriever = get_retriever(k)
        return retriever.invoke(query)


def test_connection():
    """Test if Ollama is running and model is available."""
    try:
        llm = get_llm()
        response = llm.invoke("Say 'OK' if you can hear me.")
        return True, response.content
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing RAG Chain")
    print("="*50)
    
    # Test Ollama connection
    print("\n1. Testing Ollama connection...")
    success, message = test_connection()
    if success:
        print(f"   ✓ Ollama is working: {message}")
    else:
        print(f"   ✗ Ollama error: {message}")
        print("   Make sure Ollama is running: ollama serve")
        exit(1)
    
    # Test RAG chain
    print("\n2. Testing RAG chain...")
    try:
        assistant = METUAssistant(use_rag=True)
        response = assistant.chat("ODTÜ'de kayıt işlemleri nasıl yapılır?")
        print(f"   Response: {response[:500]}...")
    except Exception as e:
        print(f"   Error: {e}")
        print("   Vector store may not exist. Run ingest.py first.")