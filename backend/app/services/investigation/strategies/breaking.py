from typing import List, Dict, Set
import logging
import asyncio
from datetime import datetime, timedelta

from app.models.evidence import EvidenceCollection, EvidenceItem, Verdict, EvidenceType, Stance
from app.services.investigation.strategies.base import (
    InvestigationStrategy, InvestigationContext, InvestigationResult
)
from app.services.investigation.searchers import get_duckduckgo_searcher

logger = logging.getLogger(__name__)

class BreakingNewsStrategy(InvestigationStrategy):
    """
    Strategy for Breaking/Emerging Events.
    Focuses on recency, velocity (number of sources), and stability markers.
    """
    
    STABILITY_MARKERS_UNSTABLE = {
        "developing story", "unconfirmed", "reports say", "reportedly", 
        "sources claim", "just in", "breaking", "preliminary"
    }

    def __init__(self):
        self.searcher = get_duckduckgo_searcher()
        
    async def execute(self, ctx: InvestigationContext) -> InvestigationResult:
        evidence_collection = EvidenceCollection()
        
        # 1. Temporal Search (Last 24 Hours)
        # Use duckduckgo 'd' filter
        query = f"{ctx.claim.text} news"
        results = await self.searcher.search(query, max_results=10, time='d')
        
        unique_sources: Set[str] = set()
        unstable_keyword_count = 0
        
        for res in results:
            unique_sources.add(res.source_domain)
            
            # Check for unstable keywords
            text_lower = (res.title + " " + res.snippet).lower()
            if any(marker in text_lower for marker in self.STABILITY_MARKERS_UNSTABLE):
                unstable_keyword_count += 1
                
            evidence_collection.add(EvidenceItem(
                text=res.snippet,
                source_url=res.url,
                source_domain=res.source_domain,
                source_type=EvidenceType.NEWS_ARTICLE,
                stance=Stance.NEUTRAL,
                stance_confidence=0.0,
                trust_score=70 # Default for breaking news (could be higher if trusted domain)
            ))
            
        # 2. Velocity Check
        source_count = len(unique_sources)
        
        # 3. Verdict Logic
        
        if source_count == 0:
            return InvestigationResult(
                verdict=Verdict.UNVERIFIED,
                confidence_score=0.1,
                evidence=evidence_collection,
                reason="No recent reports found in the last 24 hours. Validating as older claim or completely unverified.",
                strategy_stats={"velocity": 0, "status": "SILENT"}
            )
            
        if source_count < 3:
             return InvestigationResult(
                verdict=Verdict.UNVERIFIED,
                confidence_score=0.3,
                evidence=evidence_collection,
                reason=f"Only {source_count} source(s) reporting. Waiting for more confirmation.",
                strategy_stats={"velocity": source_count, "status": "LOW_VELOCITY"}
            )

        # 4. Stability Check
        # If > 50% of results have "developing" markers, it's unstable
        unstable_ratio = unstable_keyword_count / len(results)
        
        is_developing = unstable_ratio > 0.3 # stricter threshold
        
        if is_developing:
            return InvestigationResult(
                verdict=Verdict.DEVELOPING,  # Need to ensure Verdict enum has this or map to UNVERIFIED
                confidence_score=0.6,        # We are confident it IS happening, but facts are flux
                evidence=evidence_collection,
                reason="Multiple sources reporting, but situation is described as 'developing' or 'unconfirmed'.",
                strategy_stats={"velocity": source_count, "unstable_ratio": unstable_ratio}
            )
            
        # If we get here, we have multiple sources and stability
        return InvestigationResult(
            verdict=Verdict.VERIFIED_TRUE, # Tentative verification
            confidence_score=0.8,
            evidence=evidence_collection,
            reason=f"Confirmed by {source_count} independent sources in the last 24 hours.",
            strategy_stats={"velocity": source_count, "status": "STABLE"}
        )
