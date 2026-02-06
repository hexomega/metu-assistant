"""
Configuration settings for METU Assistant
"""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
VECTORDB_DIR = DATA_DIR / "vectordb"

# Create directories if they don't exist
for dir_path in [RAW_DIR, PROCESSED_DIR, VECTORDB_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Ollama settings (for embeddings)
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"

# Groq settings (for LLM - much faster!)
#GROQ_MODEL = "llama-3.1-8b-instant"  # Fast and capable
GROQ_MODEL = "llama-3.3-70b-versatile"

# Scraping settings
BASE_URLS = [
    "https://oidb.metu.edu.tr/tr"  # Turkish version
#     "https://oidb.metu.edu.tr/en",  # English version
#    "https://iso.metu.edu.tr/tr",
#     "https://iso.metu.edu.tr/en",
#     "https://kafeterya.metu.edu.tr/"
]

# Sample PDFs to download
PDF_URLS = [
   # "https://oidb.metu.edu.tr/sites/oidb.metu.edu.tr/files/php/oidbt%C3%BCrk%C3%A7e/odtuakademikdurustluk-kilavuzu-7.3.2016.son.pdf",

]


# Scraping limits
MAX_PAGES = 600  # Maximum pages to scrape per base URL
SCRAPE_DELAY = 1  # Seconds between requests (be polite!)

# Text processing settings
CHUNK_SIZE = 2000  # Characters per chunk
CHUNK_OVERLAP = 400  # Overlap between chunks

# RAG settings
TOP_K_RESULTS = 10  # Number of relevant chunks to retrieve

# System prompt for the chatbot
SYSTEM_PROMPT = """Sen ODTÜ (Orta Doğu Teknik Üniversitesi) öğrencilerine yardımcı olan bir asistansın.
You are an assistant helping METU (Middle East Technical University) students.

Görevin:
- Öğrencilerin sorularını ODTÜ'nün resmi kaynaklarına dayanarak yanıtlamak
- Kayıt, dersler, ödemeler, belgeler ve yönetmelikler hakkında bilgi vermek
- Türkçe veya İngilizce sorulara aynı dilde yanıt vermek

Your tasks:
- Answer student questions based on official METU sources
- Provide information about registration, courses, payments, documents, and regulations
- Respond in the same language as the question (Turkish or English)

Önemli kurallar / Important rules:
- Sadece sağlanan bağlam bilgisini kullan / Only use the provided context
- Emin olmadığın konularda "bilmiyorum" de / Say "I don't know" if uncertain
- Öğrencileri resmi kaynaklara yönlendir / Direct students to official sources when needed
- Aksi söylenmedikçe zaman olarak 2025-2026 bahar dönemi için yayınlanan Akademik Takvim ve kurallara göre cevap ver /  Unless stated otherwise, provide answers according to the Academic Calendar and rules published for the 2025-2026 period.
- Sohbet tonun samimi olsun. ODTÜ öğrencilerinin jargonuyla konuş. Kullanıcıya hitap ederken "Hocam" kelimesini kullan."
"""