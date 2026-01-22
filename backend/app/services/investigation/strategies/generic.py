from typing import List
import logging
import asyncio

from app.models.evidence import EvidenceCollection, EvidenceItem, Verdict, EvidenceType, Stance
from app.services.investigation.strategies.base import (
    InvestigationStrategy, InvestigationContext, InvestigationResult
)
from app.services.investigation.searchers import get_duckduckgo_searcher, get_wikipedia_searcher

logger = logging.getLogger(__name__)

class GenericStrategy(InvestigationStrategy):
    """
    Fallback strategy for claim types without a specialized strategy
    (e.g. Factual statements not adhering to official records, or Quotes).
    Performs standard broad web search + Wikipedia.
    """
    
    def __init__(self):
        self.ddg_searcher = get_duckduckgo_searcher()
        self.wiki_searcher = get_wikipedia_searcher()
        
    async def execute(self, ctx: InvestigationContext) -> InvestigationResult:
        evidence_collection = EvidenceCollection()
        
        # Parallel Execution: DDG + Wiki
        tasks = []
        
        tasks.append(self._search_ddg(ctx.claim.text, evidence_collection))
        tasks.append(self._search_wiki(ctx.claim.text, evidence_collection))
        
        await asyncio.gather(*tasks)
        
        return InvestigationResult(
            verdict=Verdict.UNVERIFIED, # Generic search rarely gives definitive verdict without synthesis
            confidence_score=0.5,
            evidence=evidence_collection,
            reason="Standard web search completed.",
            strategy_stats={"sources_found": len(evidence_collection.items)}
        )

    async def _search_ddg(self, query: str, evidence: EvidenceCollection):
        results = await self.ddg_searcher.search(query, max_results=5)
        for res in results:
            evidence.add(EvidenceItem(
                text=res.snippet,
                source_url=res.url,
                source_domain=res.source_domain,
                source_type=EvidenceType.WEB_SEARCH,
                stance=Stance.NEUTRAL,
                stance_confidence=0.0,
                trust_score=50
            ))

    async def _search_wiki(self, query: str, evidence: EvidenceCollection):
        results = await self.wiki_searcher.get_extract_for_claim(query, max_articles=1)
        for res in results:
            evidence.add(EvidenceItem(
                text=res.extract,
                source_url=res.url,
                source_domain="wikipedia.org",
                source_type=EvidenceType.WIKIPEDIA,
                stance=Stance.NEUTRAL,
                stance_confidence=0.0,
                trust_score=85
            ))
