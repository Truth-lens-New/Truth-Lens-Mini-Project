from typing import List, Dict
import logging
import asyncio
from urllib.parse import urlparse

from app.models.evidence import EvidenceCollection, EvidenceItem, Verdict, EvidenceType, Stance
from app.services.investigation.strategies.base import (
    InvestigationStrategy, InvestigationContext, InvestigationResult
)
from app.services.investigation.searchers import get_duckduckgo_searcher
from app.services.evidence.wikidata_verifier import get_wikidata_verifier

logger = logging.getLogger(__name__)

class PoliticalStrategy(InvestigationStrategy):
    """
    Strategy for Political Allegations.
    Focuses on Official Records, identifying polarization, and avoiding binary verdicts on subjective issues.
    """
    
    # Biased Source Map (Simplified for MVP)
    # Ideally this comes from a database
    BIAS_MAP = {
        "foxnews.com": "RIGHT",
        "breitbart.com": "RIGHT",
        "opindia.com": "RIGHT",
        "msnbc.com": "LEFT",
        "cnn.com": "LEFT",
        "themeta.news": "LEFT",
        "scroll.in": "LEFT",
        "reuters.com": "CENTER",
        "apnews.com": "CENTER",
        "bbc.com": "CENTER",
    }
    
    OFFICIAL_DOMAINS = [".gov", ".gov.in", ".nic.in", ".org.in", "loc.gov", "whitehouse.gov"]

    def __init__(self):
        self.searcher = get_duckduckgo_searcher()
        self.wikidata_verifier = get_wikidata_verifier()
        
    async def execute(self, ctx: InvestigationContext) -> InvestigationResult:
        evidence_collection = EvidenceCollection()
        
        # 0. Quick Factual Pre-Check (Wikidata)
        # Check if this political claim contains a factual error about history/data
        wiki_result = await self.wikidata_verifier.quick_fact_check(ctx.claim.text)
        if wiki_result and wiki_result.verified is not None:
             logger.info(f"Political claim verified via Wikidata: {wiki_result.verified}")
             
             verdict = Verdict.VERIFIED_TRUE if wiki_result.verified else Verdict.VERIFIED_FALSE
             
             # If proven false, return immediately
             evidence_collection.add(EvidenceItem(
                 text=f"Historical Fact Check: {wiki_result.reason} (Actual: {wiki_result.actual_value})",
                 source_url=f"https://www.wikidata.org/wiki/{wiki_result.entity_id}" if wiki_result.entity_id else "wikidata",
                 source_domain="wikidata.org",
                 source_type=EvidenceType.WIKIDATA,
                 stance=Stance.SUPPORTS if wiki_result.verified else Stance.REFUTES,
                 stance_confidence=1.0,
                 trust_score=100
             ))
             
             return InvestigationResult(
                 verdict=verdict,
                 confidence_score=1.0,
                 evidence=evidence_collection,
                 reason=wiki_result.reason,
                 strategy_stats={"method": "wikidata_fact_check"}
             )

        # 1. Official Record Search
        # Try to find primary source documents
        official_query = f"{ctx.claim.text} site:.gov OR site:.gov.in"
        official_results = await self.searcher.search(official_query, max_results=3)
        
        has_official_record = False
        
        for res in official_results:
            domain = res.source_domain
            if any(domain.endswith(tld) for tld in self.OFFICIAL_DOMAINS):
                item = EvidenceItem(
                    text=res.snippet,
                    source_url=res.url,
                    source_domain=domain,
                    source_type=EvidenceType.OFFICIAL_RECORD, # Need to ensure this exists or use suitable type
                    stance=Stance.NEUTRAL, # Will update with synthesizer if needed, assume Support/Refute logic later
                    stance_confidence=1.0,
                    trust_score=100
                )
                evidence_collection.add(item)
                has_official_record = True
        
        # 2. Spectrum Search (General News)
        news_query = f"{ctx.claim.text} news analysis"
        news_results = await self.searcher.search(news_query, max_results=10)
        
        left_sources = []
        right_sources = []
        center_sources = []
        
        for res in news_results:
            # Skip if already added as official
            if any(e.source_url == res.url for e in evidence_collection.items):
                continue
                
            bias = self.BIAS_MAP.get(res.source_domain, "UNKNOWN")
            
            item = EvidenceItem(
                text=res.snippet,
                source_url=res.url,
                source_domain=res.source_domain,
                source_type=EvidenceType.NEWS_ARTICLE,
                stance=Stance.NEUTRAL,
                stance_confidence=0.0,
                trust_score=80 if bias == "CENTER" else 60
            )
            evidence_collection.add(item)
            
            if bias == "LEFT": left_sources.append(item)
            elif bias == "RIGHT": right_sources.append(item)
            elif bias == "CENTER": center_sources.append(item)

        # 3. Verdict Logic
        
        # A. Official Record Overrides All
        if has_official_record:
            # In a real impl, we'd run stance detection on the official doc.
            # Here we act as a placeholder logic: presence of official doc suggests it's a matter of record.
            # We need to read the snippet to know if it confirms or denies.
            # For MVP: Return "Verifiable Data Found" -> Let human review or Synthesizer handle.
            # We'll mark as Unverified but with High Confidence in Evidence.
            # Actually, let's just return UNVERIFIED (let synthesizer decide) but with specific reason.
            return InvestigationResult(
                verdict=Verdict.UNVERIFIED, 
                confidence_score=0.9,
                evidence=evidence_collection,
                reason="Official government records found. See evidence details.",
                strategy_stats={"official_sources": len(official_results)}
            )

        # B. Polarization Check
        if left_sources and right_sources:
             # If both sides are talking about it, likely controversial.
             return InvestigationResult(
                verdict=Verdict.DISPUTED,
                confidence_score=0.7,
                evidence=evidence_collection,
                reason=f"Claim discussed by both Left ({len(left_sources)}) and Right ({len(right_sources)}) sources. Likely polarized.",
                strategy_stats={
                    "polarization": "HIGH",
                    "left_count": len(left_sources),
                    "right_count": len(right_sources)
                }
             )

        # C. Default
        return InvestigationResult(
            verdict=Verdict.UNVERIFIED,
            confidence_score=0.5,
            evidence=evidence_collection,
            reason="Standard political analysis completed.",
            strategy_stats={"polarization": "LOW"}
        )
