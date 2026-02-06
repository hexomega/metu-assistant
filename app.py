"""
METU Assistant - Streamlit Chat Interface
A RAG-powered chatbot for METU students.
"""

import streamlit as st
from src.rag_chain import METUAssistant, test_connection
from src.embeddings import get_collection_stats

# Page configuration
st.set_page_config(
    page_title="METU Student Assistant",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS for better chat appearance
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
    }
    .main-header {
        text-align: center;
        padding: 1rem 0;
    }
    .status-box {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .status-ok {
        background-color: #d4edda;
        color: #155724;
    }
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "assistant" not in st.session_state:
        st.session_state.assistant = None
    
    if "ollama_status" not in st.session_state:
        st.session_state.ollama_status = None


def check_system_status():
    """Check if Groq API and vector store are available."""
    # Check Groq connection
    groq_ok, groq_msg = test_connection()
    
    # Check vector store
    stats = get_collection_stats()
    vectordb_ok = "total_documents" in stats and stats["total_documents"] > 0
    
    return {
        "groq_ok": groq_ok,
        "groq_msg": groq_msg,
        "vectordb_ok": vectordb_ok,
        "vectordb_stats": stats,
    }


def render_sidebar():
    """Render the sidebar with status and options."""
    with st.sidebar:
        st.header("🎓 METU Student Assistant")
        st.markdown("---")
        
        # System Status
        st.subheader("Sistem Durumu / System Status")
        
        status = check_system_status()
        
        # Ollama status
        if status["groq_ok"]:
            st.success("✓ LLM API: Çalışıyor / Running")
        else:
            st.error("✗ Groq: Bağlantı hatası / Connection error")
            st.caption(f"Error: {status['groq_msg']}")
        
        # Vector DB status
        if status["vectordb_ok"]:
            doc_count = status["vectordb_stats"].get("total_documents", 0)
            st.success(f"✓ Veri Kaynağı: {doc_count} döküman")
        else:
            st.error("✗ Bilgi Tabanı: Bulunamadı")
            st.caption("Run: `uv run python ingest.py`")
        
        st.markdown("---")
        
        if st.button("🗑️ Sohbeti Temizle / Clear Chat"):
            st.session_state.messages = []
            if st.session_state.assistant:
                st.session_state.assistant.clear_history()
            st.rerun()
        
        st.markdown("---")
        
        # Info
        st.subheader("Hakkında / About")
        st.markdown("""
        Bu asistan ODTÜ öğrencilerine yardımcı olmak için tasarlanmıştır.
        
        This assistant is designed to help METU students.\n
        (c) Efe Misirli - efemisirli@gmail.com\n
        **Veri Kaynakları / Data Sources:**
        - Öğreni İşleri DB Web Sitesi ve İlgili Yönetmelikler
        - Uluslararasi Işbirliği Ofisi Web Sitesi
        - Kafeterya Web Sitesi
        """)
        
        return status


def render_chat():
    """Render the main chat interface."""
    st.markdown("<h1 class='main-header'>🎓 METU Student Assistant</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: gray;'>"
        "ODTÜ öğrencileri için yapay zeka destekli asistan<br>"
        "AI-powered assistant for METU students"
        "</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; color: gray; font-size: 0.9rem;'>"
        "<b>Örnek Sorular / Example Questions:</b><br>"
        "• Kayıt işlemleri nasıl yapılır?<br>"
        "• Dersler ne zaman başlayacak?<br>"
        "• Dersten çekilme tarihleri nedir?<br>"
        "• How can I get my transcript?<br>"
        "• What are the tuition payment deadlines?"
        "</p>",
        unsafe_allow_html=True
    )
    st.warning("⚠️ Bu asistan hata yapabilir, bilgileri resmi kaynaklardan teyit ediniz. / This assistant may make mistakes, please verify information from official sources.")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Render sidebar and get options
    status = render_sidebar()
    
    # Render chat interface
    render_chat()
    
    # Check if system is ready
    system_ready = status["groq_ok"]
    
    if not system_ready:
        st.warning(
            "⚠️ Sistem hazır değil. Lütfen yan paneldeki durumu kontrol edin.\n\n"
            "System not ready. Please check the status in the sidebar."
        )
        return
    
    # Initialize assistant if needed
    if (st.session_state.assistant is None):
        with st.spinner("Asistan başlatılıyor... / Initializing assistant..."):
            try:
                st.session_state.assistant = METUAssistant(use_rag=True)
            except Exception as e:
                st.error(f"Error initializing assistant: {e}")
                return
    
    # Chat input
    if prompt := st.chat_input("Hocam nasıl yardımcı olabilirim? / How can I help you hocam? "):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Düşünüyorum... / Thinking..."):
                try:
                    response = st.session_state.assistant.chat(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Bir hata oluştu / An error occurred: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    main()