"""
Data Ingestion Pipeline for METU Assistant

This script orchestrates:
1. Web scraping from METU OIDB website
2. PDF downloading and text extraction
3. Creating embeddings and vector store

Run this script before starting the chatbot for the first time,
or whenever you want to update the knowledge base.
"""

import argparse
from src.config import PDF_URLS, MAX_PAGES
from src.scraper import run_scraper
from src.pdf_processor import process_all_pdfs, process_local_pdfs
from src.embeddings import get_or_create_vector_store, get_collection_stats


def run_full_ingestion(
    max_pages: int = None,
    skip_scraping: bool = False,
    skip_pdfs: bool = False,
    force_rebuild: bool = False,
):
    """
    Run the full data ingestion pipeline.
    
    Args:
        max_pages: Maximum pages to scrape per base URL
        skip_scraping: If True, skip web scraping
        skip_pdfs: If True, skip PDF processing
        force_rebuild: If True, rebuild vector store from scratch
    """
    if max_pages is None:
        max_pages = MAX_PAGES
    
    print("\n" + "="*60)
    print("METU Assistant - Data Ingestion Pipeline")
    print("="*60)
    
    pdf_links_from_scraping = []
    
    # Step 1: Web Scraping
    if not skip_scraping:
        print("\n" + "-"*60)
        print("STEP 1: Web Scraping")
        print("-"*60)
        
        result = run_scraper(max_pages=max_pages)
        pdf_links_from_scraping = result.get('pdf_links', [])
        
        print(f"\nFound {len(pdf_links_from_scraping)} PDF links during scraping")
    else:
        print("\n[Skipping web scraping]")
    
    # Step 2: PDF Processing
    if not skip_pdfs:
        print("\n" + "-"*60)
        print("STEP 2: PDF Processing")
        print("-"*60)
        
        # Combine configured PDFs with discovered PDFs
        all_pdf_urls = list(set(PDF_URLS + pdf_links_from_scraping))
        
        print(f"\nProcessing {len(all_pdf_urls)} PDF(s)...")
        
        if all_pdf_urls:
            process_all_pdfs(all_pdf_urls)
        
        # Also process any manually added PDFs
        process_local_pdfs()
    else:
        print("\n[Skipping PDF processing]")
    
    # Step 3: Create/Update Vector Store
    print("\n" + "-"*60)
    print("STEP 3: Creating Vector Store")
    print("-"*60)
    
    try:
        vector_store = get_or_create_vector_store(force_recreate=force_rebuild)
        
        # Print stats
        stats = get_collection_stats()
        print(f"\nVector Store Statistics:")
        print(f"  - Total documents/chunks: {stats.get('total_documents', 'N/A')}")
        print(f"  - Collection name: {stats.get('collection_name', 'N/A')}")
        print(f"  - Storage location: {stats.get('persist_directory', 'N/A')}")
        
    except Exception as e:
        print(f"\nError creating vector store: {e}")
        print("Make sure Ollama is running: ollama serve")
        return False
    
    print("\n" + "="*60)
    print("Data Ingestion Complete!")
    print("="*60)
    print("\nYou can now run the chatbot with: uv run streamlit run app.py")
    
    return True


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="METU Assistant Data Ingestion Pipeline"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=MAX_PAGES,
        help=f"Maximum pages to scrape per base URL (default: {MAX_PAGES})"
    )
    
    parser.add_argument(
        "--skip-scraping",
        action="store_true",
        help="Skip web scraping step"
    )
    
    parser.add_argument(
        "--skip-pdfs",
        action="store_true",
        help="Skip PDF processing step"
    )
    
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Force rebuild of vector store from scratch"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick run: scrape only 5 pages (for testing)"
    )
    
    args = parser.parse_args()
    
    # Quick mode overrides
    if args.quick:
        args.max_pages = 5
        print("\n[Quick mode: Limited to 5 pages]")
    
    success = run_full_ingestion(
        max_pages=args.max_pages,
        skip_scraping=args.skip_scraping,
        skip_pdfs=args.skip_pdfs,
        force_rebuild=args.force_rebuild,
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())