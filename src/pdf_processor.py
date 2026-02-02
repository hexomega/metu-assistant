"""
PDF processor for downloading and extracting text from METU PDFs
"""

import requests
from pathlib import Path
from urllib.parse import urlparse, unquote
import fitz  # PyMuPDF

from src.config import RAW_DIR, PDF_URLS


def download_pdf(url: str, save_dir: Path = None) -> Path | None:
    """
    Download a PDF file from URL.
    Returns the path to saved file or None if failed.
    """
    if save_dir is None:
        save_dir = RAW_DIR
    
    try:
        print(f"Downloading: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Get filename from URL
        parsed = urlparse(url)
        filename = unquote(Path(parsed.path).name)
        
        # Ensure .pdf extension
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        # Clean filename
        filename = "".join(c if c.isalnum() or c in '._-' else '_' for c in filename)
        
        filepath = save_dir / filename
        filepath.write_bytes(response.content)
        
        print(f"  Saved: {filepath.name} ({len(response.content) / 1024:.1f} KB)")
        return filepath
        
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return None


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text content from a PDF file using PyMuPDF.
    """
    try:
        doc = fitz.open(pdf_path)
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
        
        doc.close()
        
        full_text = '\n\n'.join(text_parts)
        
        # Clean up the text
        # Remove excessive whitespace while preserving paragraph structure
        lines = []
        for line in full_text.splitlines():
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
            elif lines and lines[-1] != '':
                lines.append('')  # Preserve paragraph breaks
        
        return '\n'.join(lines)
        
    except Exception as e:
        print(f"  Error extracting text from {pdf_path}: {e}")
        return ""


def process_pdf(url: str) -> tuple[Path, str] | None:
    """
    Download PDF and extract text.
    Returns (pdf_path, extracted_text) or None if failed.
    """
    pdf_path = download_pdf(url)
    
    if pdf_path is None:
        return None
    
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print(f"  Warning: No text extracted from {pdf_path.name}")
        return pdf_path, ""
    
    # Save extracted text
    text_filename = pdf_path.stem + ".txt"
    text_path = RAW_DIR / text_filename
    text_path.write_text(text, encoding='utf-8')
    print(f"  Extracted text saved: {text_filename} ({len(text)} chars)")
    
    return pdf_path, text


def process_all_pdfs(pdf_urls: list[str] = None) -> dict:
    """
    Process all PDF URLs.
    Returns statistics dictionary.
    """
    if pdf_urls is None:
        pdf_urls = PDF_URLS
    
    stats = {
        'total': len(pdf_urls),
        'downloaded': 0,
        'extracted': 0,
        'failed': 0,
    }
    
    print(f"\n{'='*50}")
    print(f"Processing {len(pdf_urls)} PDF(s)")
    print('='*50)
    
    for url in pdf_urls:
        result = process_pdf(url)
        
        if result is None:
            stats['failed'] += 1
        else:
            stats['downloaded'] += 1
            pdf_path, text = result
            if text:
                stats['extracted'] += 1
    
    print(f"\n{'='*50}")
    print("PDF Processing Complete!")
    print(f"Downloaded: {stats['downloaded']}/{stats['total']}")
    print(f"Text extracted: {stats['extracted']}/{stats['total']}")
    print(f"Failed: {stats['failed']}/{stats['total']}")
    print('='*50)
    
    return stats


def process_local_pdfs(pdf_dir: Path = None) -> dict:
    """
    Process all PDF files in a directory (for manually added PDFs).
    """
    if pdf_dir is None:
        pdf_dir = RAW_DIR
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    stats = {
        'total': len(pdf_files),
        'extracted': 0,
        'failed': 0,
    }
    
    print(f"\n{'='*50}")
    print(f"Processing {len(pdf_files)} local PDF(s)")
    print('='*50)
    
    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")
        
        # Check if already processed
        text_path = RAW_DIR / (pdf_path.stem + ".txt")
        if text_path.exists():
            print(f"  Already processed, skipping...")
            stats['extracted'] += 1
            continue
        
        text = extract_text_from_pdf(pdf_path)
        
        if text:
            text_path.write_text(text, encoding='utf-8')
            print(f"  Extracted: {len(text)} characters")
            stats['extracted'] += 1
        else:
            stats['failed'] += 1
    
    print(f"\n{'='*50}")
    print("Local PDF Processing Complete!")
    print(f"Extracted: {stats['extracted']}/{stats['total']}")
    print(f"Failed: {stats['failed']}/{stats['total']}")
    print('='*50)
    
    return stats


if __name__ == "__main__":
    # Test with configured PDFs
    process_all_pdfs()