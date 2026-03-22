from typing import List, Dict, Any
import logging
import asyncio

from app.models.evidence import EvidenceCollection, EvidenceItem, Verdict, EvidenceType, Stance
from app.services.investigation.strategies.base import (
    InvestigationStrategy, InvestigationContext, InvestigationResult
)
from app.services.investigation.searchers.pubmed import PubMedSearcher
from app.services.investigation.stance_detector import StanceDetector

logger = logging.getLogger(__name__)

class ScientificStrategy(InvestigationStrategy):
    """
    Strategy for Scientific and Medical claims.
    Focuses on academic consensus, meta-analyses, and high-trust sources.
    """
    
    def __init__(self):
        self.pubmed_searcher = PubMedSearcher()
        self.stance_detector = StanceDetector()
        
    async def execute(self, ctx: InvestigationContext) -> InvestigationResult:
        evidence_collection = EvidenceCollection()
        
        # 1. Formulation: Hierarchical Search
        # We try to find high-quality evidence first
        queries = [
            f"{ctx.claim.text} meta-analysis",
            f"{ctx.claim.text} systematic review",
            f"{ctx.claim.text} scientific consensus",
            ctx.claim.text # Fallback
        ]
        
        raw_results = []
        for query in queries:
            results = await self.pubmed_searcher.search(query, max_results=3)
            if results:
                raw_results.extend(results)
                # If we found meta-analyses, stop searching deeper
                if query != ctx.claim.text: 
                    break
        
        # Deduplicate by URL
        unique_results = {r.url: r for r in raw_results}.values()
        
        # 2. Analysis & Stance Detection
        weighted_support = 0.0
        weighted_refute = 0.0
        total_weight = 0.0
        
        processed_items = []
        
        for result in unique_results:
            # Check for retraction
            is_retracted = "retracted" in result.title.lower() or "retracted" in result.snippet.lower()
            
            # Detect Stance (Async)
            stance_result = await self.stance_detector.detect_async(ctx.claim.text, result.snippet)
            label = stance_result["label"]
            confidence = stance_result["score"]
            
            # HEURISTIC: Retracted papers REFUTE the claim if the claim relies on them,
            # but usually a retracted paper means the findings are INVALID.
            # If the findings supported the claim, now they don't.
            # For simplicity: If paper matches claim keyword and is retracted -> Penalize.
            
            mapped_stance = Stance.NEUTRAL
            if label == "SUPPORTS": mapped_stance = Stance.SUPPORTS
            elif label == "REFUTES": mapped_stance = Stance.REFUTES
            
            # Override if retracted
            if is_retracted:
                mapped_stance = Stance.REFUTES
                confidence = 1.0
            
            # Weighting: Scientific sources are high trust
            weight = 1.0
            if "meta-analysis" in result.title.lower(): weight = 2.0
            if "systematic review" in result.title.lower(): weight = 1.5
            
            if mapped_stance == Stance.SUPPORTS:
                weighted_support += confidence * weight
            elif mapped_stance == Stance.REFUTES:
                weighted_refute += confidence * weight
                
            total_weight += weight
            
            # Convert to EvidenceItem
            item = EvidenceItem(
                text=result.snippet,
                source_url=result.url,
                source_domain=result.source_domain,
                source_type=EvidenceType.ACADEMIC_PAPER,
                stance=mapped_stance,
                stance_confidence=confidence,
                trust_score=95
            )
            processed_items.append(item)
            evidence_collection.add(item)
            
        # 3. Consensus Calculation
        if total_weight == 0:
            return InvestigationResult(
                verdict=Verdict.UNVERIFIED,
                confidence_score=0.0,
                evidence=evidence_collection,
                reason="No scientific literature found matching the claim."
            )
            
        # Normalize scores
        net_score = (weighted_support - weighted_refute) / total_weight
        
        # Decide Verdict
        # Range: -1 (Refute) to +1 (Support)
        verdict = Verdict.UNVERIFIED
        final_confidence = abs(net_score)
        
        reason = ""
        
        if final_confidence < 0.3:
            verdict = Verdict.UNVERIFIED
            reason = "Scientific literature is inconclusive or neutral."
        elif weighted_refute > weighted_support:
            verdict = Verdict.REFUTED
            reason = f"Scientific consensus refutes this claim (Confidence: {final_confidence:.2f})."
        else:
            verdict = Verdict.VERIFIED_TRUE  # Or SUPPORTED using V3 terminology
            reason = f"Scientific consensus supports this claim (Confidence: {final_confidence:.2f})."
            
        return InvestigationResult(
            verdict=verdict,
            confidence_score=final_confidence,
            evidence=evidence_collection,
            strategy_stats={
                "weighted_support": weighted_support,
                "weighted_refute": weighted_refute,
                "total_papers": len(processed_items)
            },
            reason=reason
        )
