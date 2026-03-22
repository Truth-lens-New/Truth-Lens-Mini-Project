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
    
    # Domain sets by region
    DOMAINS_INDIA = [".gov.in", ".nic.in", ".org.in"]
    DOMAINS_US = [".gov", "whitehouse.gov", "loc.gov", "senate.gov", "house.gov"]
    DOMAINS_UK = [".gov.uk", "parliament.uk"]
    
    # Default fallback
    DOMAINS_DEFAULT = [".gov", ".gov.in", ".gov.uk"]

    def __init__(self):
        self.searcher = get_duckduckgo_searcher()
        self.wikidata_verifier = get_wikidata_verifier()
        
    def _get_target_domains(self, claim_text: str) -> List[str]:
        """Detect region from claim text and return relevant official domains."""
        text = claim_text.lower()
        
        # Simple keyword heuristics
        if any(w in text for w in ["india", "modi", "bjp", "congress", "delhi", "mumbai"]):
            return self.DOMAINS_INDIA
        if any(w in text for w in ["us", "usa", "america", "biden", "trump", "white house", "senate", "congress"]):
            # Note: "congress" is tricky as it exists in both, but usually implies US in global context or check context
            # We can enable both if ambiguous, but let's prioritize US for "congress" if "india" is absent
            if "india" not in text and "bjp" not in text:
                return self.DOMAINS_US
            return self.DOMAINS_INDIA + self.DOMAINS_US
            
        if any(w in text for w in ["uk", "britain", "london", "parliament"]):
            return self.DOMAINS_UK
            
        return self.DOMAINS_DEFAULT
        
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
        target_domains = self._get_target_domains(ctx.claim.text)
        
        # Construct query: "claim site:d1 OR site:d2 ..."
        site_operators = " OR ".join([f"site:{d}" for d in target_domains])
        official_query = f"{ctx.claim.text} {site_operators}"
        
        logger.info(f"Searching official records with query: {official_query}")
        official_results = await self.searcher.search(official_query, max_results=3)
        
        has_official_record = False
        
        for res in official_results:
            domain = res.source_domain
            # Double check domain match (search engine might be fuzzy)
            if any(domain.endswith(tld) or tld in domain for tld in target_domains):
                item = EvidenceItem(
                    text=res.snippet,
                    source_url=res.url,
                    source_domain=domain,
                    source_type=EvidenceType.OFFICIAL_RECORD, 
                    stance=Stance.NEUTRAL, # We don't know yet without reading
                    stance_confidence=0.5, # Low confidence on stance without reading
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
        
        # A. Official Record Found
        if has_official_record:
            # We found records, but haven't analyzed them.
            # Return UNVERIFIED but with LOW confidence so Synthesizer can take over.
            # (Previously was 0.9, blocking synthesizer)
            return InvestigationResult(
                verdict=Verdict.UNVERIFIED, 
                confidence_score=0.4, # Allow synthesizer to override if it can read the text
                evidence=evidence_collection,
                reason="Official records found but require content analysis.",
                strategy_stats={"official_sources": len(official_results), "region_detected": str(target_domains)}
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
            confidence_score=0.3, # Low confidence default
            evidence=evidence_collection,
            reason="Standard political analysis completed. Insufficient conclusive evidence.",
            strategy_stats={"polarization": "LOW"}
        )
