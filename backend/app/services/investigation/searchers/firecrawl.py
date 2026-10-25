"""Firecrawl-backed web search for evidence collection.

The client targets a self-hosted Firecrawl base URL and asks the search endpoint
for page markdown. Results use the same ``SearchResult`` shape as DuckDuckGo so
investigation strategies can use either provider transparently.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.services.investigation.searchers.duckduckgo import (
    DuckDuckGoSearcher,
    SearchResult,
)


logger = logging.getLogger(__name__)


class FirecrawlSearcher:
    """Search Firecrawl and fall back to DuckDuckGo when it is unavailable."""

    _TIME_FILTERS = {"d": "qdr:d", "w": "qdr:w", "m": "qdr:m", "y": "qdr:y"}

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        fallback: Optional[DuckDuckGoSearcher] = None,
    ):
        self.base_url = (base_url if base_url is not None else settings.firecrawl_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.firecrawl_api_key
        self.fallback = fallback or DuckDuckGoSearcher()

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url)

    @property
    def search_url(self) -> str:
        """Build a v2 endpoint without duplicating a user-supplied /v2 suffix."""
        base = self.base_url.rstrip("/")
        return f"{base}/search" if base.endswith("/v2") else f"{base}/v2/search"

    async def search(
        self,
        query: str,
        max_results: int = 5,
        time: Optional[str] = None,
    ) -> List[SearchResult]:
        """Return Firecrawl results with scraped markdown, or a safe fallback."""
        if not query:
            return []
        if not self.is_configured:
            return await self.fallback.search(query, max_results=max_results, time=time)

        limit = max(1, min(max_results, settings.firecrawl_max_results))
        payload: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "safe": True,
            # Markdown gives the stance detector page content, not just a snippet.
            "scrapeOptions": {"formats": ["markdown"]},
            "timeout": int(settings.firecrawl_timeout_seconds * 1000),
        }
        if time in self._TIME_FILTERS:
            payload["tbs"] = self._TIME_FILTERS[time]

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            timeout = httpx.Timeout(settings.firecrawl_timeout_seconds, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                response = await client.post(self.search_url, json=payload, headers=headers)
                response.raise_for_status()
                results = self._parse_results(response.json())
            if results:
                return results
            logger.warning("Firecrawl returned no results; using DuckDuckGo fallback.")
        except (httpx.HTTPError, ValueError) as exc:
            # Do not expose server configuration or response details to callers.
            logger.warning("Firecrawl search failed; using DuckDuckGo fallback: %s", exc)

        return await self.fallback.search(query, max_results=max_results, time=time)

    @staticmethod
    def _parse_results(payload: Any) -> List[SearchResult]:
        """Handle Firecrawl v2 and older self-hosted response shapes."""
        if not isinstance(payload, dict):
            return []
        data = payload.get("data", payload)
        if isinstance(data, dict):
            raw_results = data.get("web", data.get("results", []))
        elif isinstance(data, list):
            raw_results = data
        else:
            raw_results = []

        parsed: List[SearchResult] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            url = item.get("url") or item.get("sourceURL") or ""
            if not url:
                continue
            metadata = item.get("metadata") or {}
            domain = urlparse(url).netloc.lower().removeprefix("www.")
            highlights = item.get("highlights") or []
            highlights_text = " ".join(map(str, highlights)) if isinstance(highlights, list) else str(highlights)
            markdown = item.get("markdown") or item.get("content") or ""
            # Prefer description and highlights; limit markdown context to prevent pipeline bloat
            snippet = "\n".join(
                part for part in (item.get("description", ""), highlights_text, markdown[:500]) if part
            )
            parsed.append(SearchResult(
                title=item.get("title") or metadata.get("title") or url,
                url=url,
                snippet=snippet[:800],
                source="Firecrawl",
                source_domain=domain or "unknown",
            ))
        return parsed


_searcher_instance: Optional[FirecrawlSearcher] = None


def get_firecrawl_searcher() -> FirecrawlSearcher:
    """Get the shared Firecrawl searcher instance."""
    global _searcher_instance
    if _searcher_instance is None:
        _searcher_instance = FirecrawlSearcher()
    return _searcher_instance
