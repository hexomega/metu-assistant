"""
Web scraper for METU OIDB website
"""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path

from src.config import (
    RAW_DIR,
    BASE_URLS,
    MAX_PAGES,
    SCRAPE_DELAY,
)


def is_valid_url(url: str, base_domain: str) -> bool:
    """Check if URL belongs to the target domain and is a valid page."""
    parsed = urlparse(url)
    
    # Must be same domain
    if base_domain not in parsed.netloc:
        return False
    
    # Skip unwanted file types
    skip_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.ico', '.svg']
    if any(url.lower().endswith(ext) for ext in skip_extensions):
        return False
    
    # Skip external links and anchors
    if url.startswith('#') or 'mailto:' in url or 'tel:' in url:
        return False
    
    return True


def extract_text_from_html(soup: BeautifulSoup) -> str:
    """Extract clean text from HTML, focusing on main content."""
    # Remove script and style elements
    for element in soup(['script', 'style', 'nav', 'footer', 'header']):
        element.decompose()
    
    # Try to find main content area
    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
    
    if main_content:
        text = main_content.get_text(separator='\n', strip=True)
    else:
        text = soup.get_text(separator='\n', strip=True)
    
    # Clean up multiple newlines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines)


def extract_links(soup: BeautifulSoup, current_url: str, base_domain: str) -> list[str]:
    """Extract all valid links from a page."""
    links = []
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        full_url = urljoin(current_url, href)
        
        if is_valid_url(full_url, base_domain):
            # Remove fragments
            full_url = full_url.split('#')[0]
            links.append(full_url)
    
    return list(set(links))  # Remove duplicates


def extract_pdf_links(soup: BeautifulSoup, current_url: str) -> list[str]:
    """Extract all PDF links from a page."""
    pdf_links = []
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        if href.lower().endswith('.pdf'):
            full_url = urljoin(current_url, href)
            pdf_links.append(full_url)
    
    return list(set(pdf_links))


def scrape_page(url: str) -> tuple[str, list[str], list[str]] | None:
    """
    Scrape a single page.
    Returns: (text_content, page_links, pdf_links) or None if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Handle encoding
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
          
        # Get base domain for link filtering
        base_domain = urlparse(url).netloc
        
        # Extract links BEFORE text (text extraction destroys nav/footer)
        page_links = extract_links(soup, url, base_domain)
        pdf_links = extract_pdf_links(soup, url)
        
        # Extract content (this removes nav/footer/header)
        text = extract_text_from_html(soup)
        
        return text, page_links, pdf_links
        
    except Exception as e:
        print(f"  Error scraping {url}: {e}")
        return None


def save_scraped_content(url: str, content: str) -> Path:
    """Save scraped content to a text file."""
    # Create a safe filename from URL
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').replace('/', '_') or 'index'
    filename = f"{parsed.netloc}_{path_parts}.txt"
    
    # Clean filename
    filename = "".join(c if c.isalnum() or c in '._-' else '_' for c in filename)
    
    filepath = RAW_DIR / filename
    filepath.write_text(content, encoding='utf-8')
    
    return filepath


def run_scraper(base_urls: list[str] = None, max_pages: int = None) -> dict:
    """
    Main scraping function.
    Returns dict with statistics and found PDF links.
    """
    if base_urls is None:
        base_urls = BASE_URLS
    if max_pages is None:
        max_pages = MAX_PAGES
    
    all_pdf_links = []
    stats = {
        'pages_scraped': 0,
        'pages_failed': 0,
        'pdfs_found': 0,
    }
    
    for base_url in base_urls:
        print(f"\n{'='*50}")
        print(f"Scraping: {base_url}")
        print('='*50)
        
        visited = set()
        to_visit = [base_url]
        
        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            
            if url in visited:
                continue
            
            visited.add(url)
            print(f"\n[{len(visited)}/{max_pages}] Scraping: {url}")
            
            result = scrape_page(url)
            
            if result is None:
                stats['pages_failed'] += 1
                continue
            
            text, page_links, pdf_links = result
            
            # Save content if not empty
            if text and len(text) > 100:  # Skip near-empty pages
                filepath = save_scraped_content(url, text)
                print(f"  Saved: {filepath.name}")
                stats['pages_scraped'] += 1
            
            # Collect PDF links
            if pdf_links:
                print(f"  Found {len(pdf_links)} PDF(s)")
                all_pdf_links.extend(pdf_links)
                stats['pdfs_found'] += len(pdf_links)
            
            # Add new links to queue (only under base_url path)
            base_path = urlparse(base_url).path.rstrip('/')
            for link in page_links:
                if link not in visited and link not in to_visit:
                    link_path = urlparse(link).path
                    if base_path and link_path.startswith(base_path):
                        to_visit.append(link)
                    elif not base_path:
                        to_visit.append(link)
            
            # Be polite - wait between requests
            time.sleep(SCRAPE_DELAY)
    
    # Remove duplicate PDF links
    all_pdf_links = list(set(all_pdf_links))
    
    print(f"\n{'='*50}")
    print("Scraping Complete!")
    print(f"Pages scraped: {stats['pages_scraped']}")
    print(f"Pages failed: {stats['pages_failed']}")
    print(f"Unique PDFs found: {len(all_pdf_links)}")
    print('='*50)
    
    return {
        'stats': stats,
        'pdf_links': all_pdf_links,
    }


if __name__ == "__main__":
    # Test run with limited pages
    result = run_scraper(max_pages=5)
    print("\nPDF links found:")
    for pdf in result['pdf_links']:
        print(f"  - {pdf}")