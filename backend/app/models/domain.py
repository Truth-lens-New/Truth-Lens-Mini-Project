"""
TruthLens V3 Domain Models

Data models for the claim analysis pipeline.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


class InputType(str, Enum):
    """Types of input the system can process."""
    TEXT = "text"
    URL = "url"
    IMAGE = "image"
    SOCIAL = "social"


class ClaimType(str, Enum):
    """
    Classification types for claims.
    
    Checkable types: Can be verified with evidence
    Non-checkable types: Cannot be fact-checked (opinions, predictions, etc.)
    """
    # Checkable claim types
    SCIENTIFIC_MEDICAL = "scientific_medical"
    POLITICAL_ALLEGATION = "political_allegation"
    FACTUAL_STATEMENT = "factual_statement"
    BREAKING_EVENT = "breaking_event"
    QUOTE_ATTRIBUTION = "quote_attribution"
    
    # Non-checkable claim types
    OPINION = "opinion"              # Subjective value judgments
    PREDICTION = "prediction"        # Future events that haven't occurred
    QUESTION = "question"            # Interrogative statements
    COMMAND = "command"              # Imperative statements
    HYPOTHETICAL = "hypothetical"    # "What if" scenarios
    UNKNOWN = "unknown"              # Catch-all for unclassifiable


@dataclass
class ProcessedInput:
    """
    Output of Input Gateway.
    Unified format for all input types.
    """
    text: str
    source_type: InputType
    source_url: Optional[str] = None
    source_domain: Optional[str] = None
    extracted_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.text:
            raise ValueError("ProcessedInput text cannot be empty")


@dataclass
class RawClaim:
    """
    Output of Claim Extraction.
    A potential claim extracted from text.
    """
    text: str
    sentence_index: int
    char_start: int
    char_end: int
    is_assertion: bool = True


@dataclass
class TypedClaim:
    """
    Output of Claim Typing.
    A claim with its type and metadata.
    """
    text: str
    claim_type: ClaimType
    type_confidence: float
    is_checkable: bool
    evidence_strategy: str
    status: str
    sentence_index: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "original_text": self.text,
            "claim_type": self.claim_type.value,
            "type_confidence": round(self.type_confidence, 3),
            "is_checkable": self.is_checkable,
            "evidence_strategy": self.evidence_strategy,
            "status": self.status
        }


# Evidence strategies per claim type (reference data)
EVIDENCE_STRATEGIES = {
    # Checkable types - have verification strategies
    ClaimType.SCIENTIFIC_MEDICAL: "Scientific consensus check (PubMed, WHO)",
    ClaimType.POLITICAL_ALLEGATION: "Multi-source verification, official records",
    ClaimType.FACTUAL_STATEMENT: "Wikidata verification, authoritative sources",
    ClaimType.BREAKING_EVENT: "Multi-source news check, timeline analysis",
    ClaimType.QUOTE_ATTRIBUTION: "Quote source verification",
    
    # Non-checkable types - explain why
    ClaimType.OPINION: "Not fact-checkable (subjective value judgment)",
    ClaimType.PREDICTION: "Not fact-checkable (future event hasn't occurred)",
    ClaimType.QUESTION: "Not fact-checkable (interrogative, not assertion)",
    ClaimType.COMMAND: "Not fact-checkable (imperative, not assertion)",
    ClaimType.HYPOTHETICAL: "Not fact-checkable (hypothetical scenario)",
    ClaimType.UNKNOWN: "Classification unclear - manual review suggested"
}

# Which claim types are fact-checkable
CHECKABLE_TYPES = {
    ClaimType.SCIENTIFIC_MEDICAL,
    ClaimType.POLITICAL_ALLEGATION,
    ClaimType.FACTUAL_STATEMENT,
    ClaimType.BREAKING_EVENT,
    ClaimType.QUOTE_ATTRIBUTION
}
