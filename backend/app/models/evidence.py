"""
TruthLens Evidence Data Models

Models for evidence gathering and verdict determination.
Phase 2A: Core evidence types and structures.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


class EvidenceType(str, Enum):
    """Types of evidence sources."""
    GOOGLE_FACT_CHECK = "google_fact_check"
    WIKIDATA = "wikidata"
    WIKIPEDIA = "wikipedia"
    NEWS_ARTICLE = "news_article"
    ACADEMIC_PAPER = "academic_paper"
    ARCHIVE = "archive"
    SOCIAL_MEDIA = "social_media"
    KNOWN_MISINFO = "known_misinfo"
    WEB_SEARCH = "web_search"
    FACT_CHECK = "fact_check"


class Stance(str, Enum):
    """Stance of evidence relative to claim."""
    SUPPORTS = "supports"
    REFUTES = "refutes"
    NEUTRAL = "neutral"


class Verdict(str, Enum):
    """Final verdict on a claim."""
    VERIFIED_TRUE = "verified_true"
    VERIFIED_FALSE = "verified_false"
    DISPUTED = "disputed"
    UNVERIFIED = "unverified"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_CHECKABLE = "not_checkable"


# Source type weights for evidence synthesis
SOURCE_WEIGHTS = {
    EvidenceType.ACADEMIC_PAPER: 1.5,
    EvidenceType.FACT_CHECK: 1.4,
    EvidenceType.GOOGLE_FACT_CHECK: 1.4,
    EvidenceType.KNOWN_MISINFO: 2.0,  # Our verified database
    EvidenceType.WIKIDATA: 1.2,
    EvidenceType.WIKIPEDIA: 1.0,
    EvidenceType.NEWS_ARTICLE: 0.8,
    EvidenceType.WEB_SEARCH: 0.7,
    EvidenceType.ARCHIVE: 0.7,
    EvidenceType.SOCIAL_MEDIA: 0.3,
}


@dataclass
class EvidenceItem:
    """
    Single piece of evidence from any source.
    """
    text: str
    source_url: str
    source_domain: str
    source_type: EvidenceType
    stance: Stance = Stance.NEUTRAL
    stance_confidence: float = 0.5
    trust_score: int = 50
    retrieved_at: datetime = field(default_factory=datetime.now)
    
    @property
    def weighted_score(self) -> float:
        """
        Calculate weighted score for synthesis.
        Formula: stance_confidence × source_type_weight × (trust_score / 100)
        """
        type_weight = SOURCE_WEIGHTS.get(self.source_type, 0.5)
        trust_factor = self.trust_score / 100
        return self.stance_confidence * type_weight * trust_factor
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "source_url": self.source_url,
            "source_domain": self.source_domain,
            "source_type": self.source_type.value,
            "stance": self.stance.value,
            "stance_confidence": round(self.stance_confidence, 3),
            "trust_score": self.trust_score
        }


@dataclass
class EvidenceCollection:
    """
    Collection of evidence items from investigation.
    """
    items: List[EvidenceItem] = field(default_factory=list)
    investigation_time_ms: int = 0
    sources_checked: int = 0
    stopped_early: bool = False
    stop_reason: Optional[str] = None
    
    def add(self, item: EvidenceItem):
        """Add evidence item to collection."""
        self.items.append(item)
        self.sources_checked += 1
    
    @property
    def support_score(self) -> float:
        """Total weighted score of supporting evidence."""
        return sum(
            e.weighted_score 
            for e in self.items 
            if e.stance == Stance.SUPPORTS
        )
    
    @property
    def refute_score(self) -> float:
        """Total weighted score of refuting evidence."""
        return sum(
            e.weighted_score 
            for e in self.items 
            if e.stance == Stance.REFUTES
        )
    
    @property
    def total_score(self) -> float:
        """Total of all weighted scores."""
        return self.support_score + self.refute_score
    
    def get_by_type(self, evidence_type: EvidenceType) -> List[EvidenceItem]:
        """Get all evidence of a specific type."""
        return [e for e in self.items if e.source_type == evidence_type]
    
    def get_by_stance(self, stance: Stance) -> List[EvidenceItem]:
        """Get all evidence with a specific stance."""
        return [e for e in self.items if e.stance == stance]


@dataclass
class VerifiedClaim:
    """
    Final output: claim with verdict and evidence trail.
    """
    original_text: str
    claim_type: str
    verdict: Verdict
    confidence: float
    evidence_summary: str
    evidence_items: List[EvidenceItem]
    investigation_time_ms: int
    sources_checked: int
    verified_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "original_text": self.original_text,
            "claim_type": self.claim_type,
            "verdict": self.verdict.value,
            "confidence": round(self.confidence, 3),
            "evidence_summary": self.evidence_summary,
            "evidence_count": len(self.evidence_items),
            "sources_checked": self.sources_checked,
            "investigation_time_ms": self.investigation_time_ms,
            "verified_at": self.verified_at.isoformat(),
            "evidence": [
                e.to_dict() 
                for e in self.evidence_items[:5]  # Top 5 evidence
            ]
        }
