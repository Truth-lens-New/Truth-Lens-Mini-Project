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
        
        # Fetch content
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError(f"Could not fetch URL: {url}")
        
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
