"""
TruthLens URL Scraper

Downloads pages safely (SSRF-guarded) and extracts main content with
trafilatura.
"""

from typing import Optional

import requests
import trafilatura
from urllib.parse import urlparse

from app.models.domain import ProcessedInput, InputType
from app.services.input.url_guard import UnsafeURLError, validate_http_url, validate_redirect_target

# Fetch hard limits
MAX_REDIRECTS = 5
CONNECT_TIMEOUT = 10.0
READ_TIMEOUT = 20.0
MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB of HTML is plenty for extraction

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
}


def _fetch_with_guard(url: str) -> str:
    """
    Fetch HTML enforcing SSRF validation on the first URL and on every hop.

    Redirects are followed manually so no intermediate request can reach an
    internal host without validation. Also enforces response size limits.
    """
    # Raises UnsafeURLError (ValueError) for non-public destinations.
    current_url = validate_http_url(url)

    with requests.Session() as session:
        for hop in range(MAX_REDIRECTS + 1):
            response = session.get(
                current_url,
                headers=_HEADERS,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                allow_redirects=False,
                stream=True,
            )

            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                current_url = validate_redirect_target(current_url, location)
                response.close()
                continue

            response.raise_for_status()

            # Read the body with a hard cap on bytes.
            downloaded = bytearray()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                downloaded.extend(chunk)
                if len(downloaded) > MAX_RESPONSE_BYTES:
                    response.close()
                    raise ValueError(
                        f"Response too large from {url} (limit {MAX_RESPONSE_BYTES} bytes)"
                    )
            response.close()
            return bytes(downloaded).decode(
                response.encoding or "utf-8", errors="replace"
            )

        raise ValueError(f"Too many redirects while fetching {url}")


class URLScraper:
    """Extract content from URLs using trafilatura (with SSRF protection)."""

    def process(self, url: str) -> ProcessedInput:
        """
        Fetch and extract main content from URL.

        Args:
            url: The URL to scrape

        Returns:
            ProcessedInput with extracted text

        Raises:
            ValueError: If URL is invalid, unsafe, or content extraction fails
        """
        try:
            downloaded = _fetch_with_guard(url)
        except UnsafeURLError:
            # Surface the (already descriptive) safety error directly.
            raise
        except Exception as exc:
            raise ValueError(f"Could not fetch URL: {url} (Error: {exc})")

        # Extract main text content
        text = trafilatura.extract(downloaded)
        if not text:
            raise ValueError(f"Could not extract content from URL: {url}")

        parsed = urlparse(url)
        return ProcessedInput(
            text=text,
            source_type=InputType.URL,
            source_url=parsed.geturl(),
            source_domain=parsed.netloc,
        )
