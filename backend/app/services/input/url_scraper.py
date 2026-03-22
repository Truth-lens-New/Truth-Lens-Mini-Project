"""
TruthLens URL Scraper

Extracts main content from URLs using trafilatura.
"""

import trafilatura
from urllib.parse import urlparse
from app.models.domain import ProcessedInput, InputType


class URLScraper:
    """Extract content from URLs using trafilatura."""
    
    def process(self, url: str) -> ProcessedInput:
        """
        Fetch and extract main content from URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            ProcessedInput with extracted text
            
        Raises:
            ValueError: If URL is invalid or content extraction fails
        """
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")
        
        # Custom headers to avoid 403 blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            import requests
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            downloaded = response.text
        except Exception as e:
            # Fallback to trafilatura fetch if requests fails (though unlikely to help if blocked)
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                 raise ValueError(f"Could not fetch URL: {url} (Error: {str(e)})")
        
        # Extract main text content
        text = trafilatura.extract(downloaded)
        if not text:
            raise ValueError(f"Could not extract content from URL: {url}")
        
        return ProcessedInput(
            text=text,
            source_type=InputType.URL,
            source_url=url,
            source_domain=parsed.netloc
        )
