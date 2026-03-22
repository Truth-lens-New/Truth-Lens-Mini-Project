from typing import Dict, Type
from app.models.domain import ClaimType
from app.services.investigation.strategies.base import InvestigationStrategy

from app.services.investigation.strategies.scientific import ScientificStrategy
from app.services.investigation.strategies.political import PoliticalStrategy
from app.services.investigation.strategies.breaking import BreakingNewsStrategy
from app.services.investigation.strategies.generic import GenericStrategy

class StrategyFactory:
    """
    Factory to select the appropriate investigation strategy based on ClaimType.
    """
    
    _strategies: Dict[ClaimType, Type[InvestigationStrategy]] = {}
    
    @classmethod
    def register(cls, claim_type: ClaimType, strategy_class: Type[InvestigationStrategy]):
        """Register a strategy class for a claim type."""
        cls._strategies[claim_type] = strategy_class
        
    @classmethod
    def get_strategy(cls, claim_type: ClaimType) -> Type[InvestigationStrategy]:
        """
        Get the strategy class for the given claim type.
        Returns a default/generic strategy if no specific one is found.
        """
        # Return specific strategy if registered
        if claim_type in cls._strategies:
            return cls._strategies[claim_type]
            
        return GenericStrategy

# Static registration (will be populated as modules are imported)
StrategyFactory.register(ClaimType.SCIENTIFIC_MEDICAL, ScientificStrategy)
StrategyFactory.register(ClaimType.POLITICAL_ALLEGATION, PoliticalStrategy)
StrategyFactory.register(ClaimType.BREAKING_EVENT, BreakingNewsStrategy)
