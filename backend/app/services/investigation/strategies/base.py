from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from app.models.domain import TypedClaim, ClaimType
from app.models.evidence import EvidenceCollection, EvidenceItem, Verdict

class InvestigationDepth(Enum):
    QUICK = "quick"
    STANDARD = "standard" 
    DEEP = "deep"

@dataclass(frozen=True)
class InvestigationContext:
    """
    Immutable context passed to strategies.
    Ensures strategies are side-effect free regarding inputs.
    """
    claim: TypedClaim
    timestamp: datetime = field(default_factory=datetime.now)
    required_depth: InvestigationDepth = InvestigationDepth.DEEP
    allow_unverified_sources: bool = False
    
    # Optional: Pre-existing evidence (e.g. from Quick Check)
    known_evidence: Optional[EvidenceCollection] = None

@dataclass
class InvestigationResult:
    verdict: Verdict
    confidence_score: float
    evidence: EvidenceCollection
    reason: str = ""
    strategy_stats: Dict[str, Any] = field(default_factory=dict)
    
class InvestigationStrategy(ABC):
    """
    Abstract Base Class for all investigation strategies.
    Enforces the 'execute' contract.
    """
    
    @abstractmethod
    async def execute(self, ctx: InvestigationContext) -> InvestigationResult:
        """
        Execute the investigation strategy.
        Must return a standardized InvestigationResult.
        """
        pass
