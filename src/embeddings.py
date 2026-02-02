"""
Embeddings and vector store management for METU Assistant
Using FAISS for vector storage.
"""

from pathlib import Path
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from src.config import (
    RAW_DIR,
    VECTORDB_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

# FAISS index filename
FAISS_INDEX_NAME = "metu_faiss_index"


def get_embedding_function():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True},
    )


def load_documents(data_dir: Path = None) -> list:
    """Load all text documents from the data directory."""
    if data_dir is None:
        data_dir = RAW_DIR
    
    print(f"Loading documents from: {data_dir}")
    
    # Load all .txt files
    loader = DirectoryLoader(
        str(data_dir),
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'},
        show_progress=True,
    )
    
    documents = loader.load()
    print(f"Loaded {len(documents)} document(s)")
    
    return documents


def chunk_documents(documents: list) -> list:
    """Split documents into chunks for embedding."""
    print(f"Chunking {len(documents)} document(s)...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunk(s)")
    
    return chunks


def create_vector_store(chunks: list, persist_directory: Path = None) -> FAISS:
    """Create a new vector store from document chunks."""
    if persist_directory is None:
        persist_directory = VECTORDB_DIR
    
    print(f"Creating vector store with {len(chunks)} chunks...")
    print(f"This may take a few minutes depending on the amount of data...")
    
    embeddings = get_embedding_function()
    
    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )
    
    # Save to disk
    vector_store.save_local(str(persist_directory), FAISS_INDEX_NAME)
    print(f"Vector store saved at: {persist_directory}")
    
    return vector_store


def load_vector_store(persist_directory: Path = None) -> FAISS:
    """Load an existing vector store."""
    if persist_directory is None:
        persist_directory = VECTORDB_DIR
    
    embeddings = get_embedding_function()
    
    vector_store = FAISS.load_local(
        str(persist_directory),
        embeddings,
        FAISS_INDEX_NAME,
        allow_dangerous_deserialization=True,  # Required for loading pickled data
    )
    
    return vector_store


def get_or_create_vector_store(force_recreate: bool = False) -> FAISS:
    """
    Get existing vector store or create a new one.
    Set force_recreate=True to rebuild from scratch.
    """
    faiss_index_path = VECTORDB_DIR / f"{FAISS_INDEX_NAME}.faiss"
    faiss_exists = faiss_index_path.exists()
    
    if faiss_exists and not force_recreate:
        print("Loading existing vector store...")
        return load_vector_store()
    
    print("Creating new vector store...")
    
    # Load and process documents
    documents = load_documents()
    
    if not documents:
        raise ValueError(
            f"No documents found in {RAW_DIR}. "
            "Please run the scraper and PDF processor first."
        )
    
    chunks = chunk_documents(documents)
    
    # Create vector store
    vector_store = create_vector_store(chunks)
    
    return vector_store


def add_documents_to_store(
    new_documents: list,
    vector_store: FAISS = None
) -> FAISS:
    """Add new documents to an existing vector store."""
    if vector_store is None:
        vector_store = load_vector_store()
    
    chunks = chunk_documents(new_documents)
    
    print(f"Adding {len(chunks)} new chunks to vector store...")
    vector_store.add_documents(chunks)
    
    # Save updated store
    vector_store.save_local(str(VECTORDB_DIR), FAISS_INDEX_NAME)
    
    return vector_store


def search_similar(
    query: str,
    k: int = 5,
    vector_store: FAISS = None
) -> list:
    """Search for similar documents."""
    if vector_store is None:
        vector_store = load_vector_store()
    
    results = vector_store.similarity_search(query, k=k)
    
    return results


def get_collection_stats() -> dict:
    """Get statistics about the vector store."""
    try:
        faiss_index_path = VECTORDB_DIR / f"{FAISS_INDEX_NAME}.faiss"
        
        if not faiss_index_path.exists():
            return {
                'error': 'Vector store not found',
                'message': 'Vector store may not exist yet.',
            }
        
        vector_store = load_vector_store()
        
        return {
            'total_documents': vector_store.index.ntotal,
            'index_name': FAISS_INDEX_NAME,
            'persist_directory': str(VECTORDB_DIR),
        }
    except Exception as e:
        return {
            'error': str(e),
            'message': 'Vector store may not exist yet.',
        }


if __name__ == "__main__":
    # Test the embedding pipeline
    print("\n" + "="*50)
    print("Testing Embedding Pipeline")
    print("="*50)
    
    # Check stats
    stats = get_collection_stats()
    print(f"\nVector Store Stats: {stats}")
    
    # Test search if store exists
    if 'total_documents' in stats and stats['total_documents'] > 0:
        print("\nTesting search...")
        results = search_similar("kayıt işlemleri", k=3)
        for i, doc in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            print(doc.page_content[:200] + "...")