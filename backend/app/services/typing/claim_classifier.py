"""
TruthLens Claim Classifier (V3)

Classifies claims into types using zero-shot classification.
This is THE FORK - routes claims to different evidence strategies.
"""

from typing import List
from app.models.domain import (
    RawClaim, TypedClaim, ClaimType, 
    EVIDENCE_STRATEGIES, CHECKABLE_TYPES
)
from app.services.models import get_model_manager


class ClaimClassifier:
    """
    Classify claims into types using BART-large-mnli zero-shot classification.
    This is THE FORK in the pipeline - determines which evidence strategy to use.
    """
    
    # Labels for zero-shot classification
    LABELS = [
        "scientific or medical claim",
        "political allegation or accusation",
        "factual statement or assertion",
        "common misconception or conspiracy theory",
        "breaking news or recent event",
        "opinion or value judgment",
        "quote attribution"
    ]
    
    # Map zero-shot labels to our ClaimType enum
    LABEL_TO_TYPE = {
        "scientific or medical claim": ClaimType.SCIENTIFIC_MEDICAL,
        "political allegation or accusation": ClaimType.POLITICAL_ALLEGATION,
        "factual statement or assertion": ClaimType.FACTUAL_STATEMENT,
        "common misconception or conspiracy theory": ClaimType.FACTUAL_STATEMENT, # Map conspiracy to factual so we check it
        "breaking news or recent event": ClaimType.BREAKING_EVENT,
        "opinion or value judgment": ClaimType.OPINION,
        "quote attribution": ClaimType.QUOTE_ATTRIBUTION
    }
    
    def __init__(self):
        self.models = get_model_manager()
    
    def classify(self, claims: List[RawClaim]) -> List[TypedClaim]:
        """
        Classify list of raw claims into typed claims.
        
        Args:
            claims: List of RawClaim from extraction
            
        Returns:
            List of TypedClaim with type and confidence
        """
        typed_claims = []
        
        for claim in claims:
            # Classify all extracted claims (even borderline ones)
            typed_claim = self._classify_single(claim)
            typed_claims.append(typed_claim)
        
        return typed_claims
    
    # Opinion keywords - if present, likely an opinion
    OPINION_KEYWORDS = [
        'best', 'worst', 'great', 'terrible', 'amazing', 'awful',
        'love', 'hate', 'nice', 'bad', 'good', 'beautiful', 'ugly',
        'favorite', 'favourite', 'perfect', 'horrible', 'wonderful',
        'i think', 'i believe', 'i feel', 'in my opinion', 'personally',
        'should', 'ought to', 'must be', 'prettier', 'nicer', 'better'
    ]
    
    # Prediction keywords - future events
    PREDICTION_KEYWORDS = [
        'will be', 'will have', 'will become', 'going to be',
        'by 2025', 'by 2026', 'by 2027', 'by 2030', 'by 2040', 'by 2050',
        'in the future', 'next year', 'next decade', 'soon will',
        'is predicted', 'is expected to', 'forecast', 'projected to'
    ]
    
    # Question patterns - interrogative statements
    QUESTION_PATTERNS = ['?', 'is it true', 'did you know', 'have you heard']
    
    # Command patterns - imperatives
    COMMAND_KEYWORDS = [
        'do this', 'you must', 'you should', 'please do', 'click here',
        'subscribe', 'share this', 'vote for', 'sign up', 'buy now'
    ]
    
    # Hypothetical patterns
    HYPOTHETICAL_KEYWORDS = [
        'what if', 'if only', 'imagine if', 'suppose that',
        'hypothetically', 'in theory', 'theoretically'
    ]

    # Scientific/Medical Keywords (Strong Domain)
    SCIENTIFIC_KEYWORDS = [
        'vaccine', 'virus', 'covid', 'pandemic', 'disease', 'cure', 
        'treatment', 'doctor', 'scientist', 'autism', 'cancer', 'health', 
        'medicine', 'drug', 'study', 'research', 'medical', 'clinical',
        'mutation', 'variant', 'infection', 'immune'
    ]

    # Political Keywords (Strong Domain)
    POLITICAL_KEYWORDS = [
        'election', 'vote', 'ballot', 'congress', 'senate', 'parliament', 
        'president', 'prime minister', 'politics', 'democrat', 'republican', 
        'legislation', 'law', 'government', 'policy', 'campaign', 'candidate',
        'biden', 'trump', 'modi', 'putin', 'white house', 'fraud', 'rigged',
        'stolen', 'corruption', 'bribe', 'scandal'
    ]
    
    def _create_checkable_boost(self, claim: RawClaim, claim_type: ClaimType) -> TypedClaim:
        """Create TypedClaim with High Confidence for keyword matches."""
        # Checkable Types need a strategy
        strategy = EVIDENCE_STRATEGIES.get(claim_type, "General fact-check")
        
        return TypedClaim(
            text=claim.text,
            claim_type=claim_type,
            type_confidence=0.95,  # Boost confidence for strong keywords
            is_checkable=True,
            evidence_strategy=strategy,
            status="Pending evidence analysis",
            sentence_index=claim.sentence_index
        )

    def _classify_single(self, claim: RawClaim) -> TypedClaim:
        """Classify a single claim."""
        
        text_lower = claim.text.lower()
        
        # === QUICK CHECKS (before expensive zero-shot) ===
        # Check for non-checkable types using keywords
        
        # 1. Questions (contains ?)
        if any(p in text_lower for p in self.QUESTION_PATTERNS):
            return self._create_non_checkable(claim, ClaimType.QUESTION)
        
        # 2. Commands/Imperatives
        if any(kw in text_lower for kw in self.COMMAND_KEYWORDS):
            return self._create_non_checkable(claim, ClaimType.COMMAND)
        
        # 3. Hypotheticals
        if any(kw in text_lower for kw in self.HYPOTHETICAL_KEYWORDS):
            return self._create_non_checkable(claim, ClaimType.HYPOTHETICAL)
        
        # 4. Predictions (future events)
        if any(kw in text_lower for kw in self.PREDICTION_KEYWORDS):
            return self._create_non_checkable(claim, ClaimType.PREDICTION)
        
        # 5. Opinions (subjective judgments)
        if self._is_likely_opinion(text_lower):
            return self._create_non_checkable(claim, ClaimType.OPINION)

        # === HYBRID BOOSTING (Keywords override Zero-Shot) ===
        # 6. Scientific/Medical (Strong Keywords)
        if any(kw in text_lower for kw in self.SCIENTIFIC_KEYWORDS):
            return self._create_checkable_boost(claim, ClaimType.SCIENTIFIC_MEDICAL)

        # 7. Political (Strong Keywords)
        if any(kw in text_lower for kw in self.POLITICAL_KEYWORDS):
            return self._create_checkable_boost(claim, ClaimType.POLITICAL_ALLEGATION)

        # 8. Scam/Hoax (Strong Keywords) behavior
        # "Fake", "Scam" are claims about authenticity, definitely checkable.
        SCAM_KEYWORDS = ['fake', 'scam', 'hoax', 'fraud', 'clickbait', 'viral']
        if any(kw in text_lower for kw in SCAM_KEYWORDS):
             return self._create_checkable_boost(claim, ClaimType.FACTUAL_STATEMENT)
        
        # Run zero-shot classification
        result = self.models.zero_shot(
            claim.text,
            self.LABELS,
            multi_label=False
        )
        
        # Get top label and score
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        
        # Map to our type enum
        claim_type = self.LABEL_TO_TYPE.get(top_label, ClaimType.UNKNOWN)
        
        # Determine if checkable
        is_checkable = claim_type in CHECKABLE_TYPES
        
        # Get evidence strategy
        strategy = EVIDENCE_STRATEGIES.get(claim_type, "General fact-check")
        
        # Generate status
        if is_checkable:
            status = "Pending evidence analysis"
        else:
            status = "Not fact-checkable (opinion/value judgment)"
        
        return TypedClaim(
            text=claim.text,
            claim_type=claim_type,
            type_confidence=top_score,
            is_checkable=is_checkable,
            evidence_strategy=strategy,
            status=status,
            sentence_index=claim.sentence_index
        )
    
    def _create_non_checkable(self, claim: RawClaim, claim_type: ClaimType) -> TypedClaim:
        """Create TypedClaim for non-checkable statement types."""
        return TypedClaim(
            text=claim.text,
            claim_type=claim_type,
            type_confidence=0.85,  # High confidence for keyword match
            is_checkable=False,
            evidence_strategy=EVIDENCE_STRATEGIES.get(claim_type, "Not fact-checkable"),
            status=EVIDENCE_STRATEGIES.get(claim_type, "Not fact-checkable"),
            sentence_index=claim.sentence_index
        )
    
    def _is_likely_opinion(self, text: str) -> bool:
        """Check if text contains opinion keywords."""
        return any(kw in text for kw in self.OPINION_KEYWORDS)
    
    def classify_text(self, text: str) -> TypedClaim:
        """
        Convenience method to classify a single text string directly.
        
        Args:
            text: The claim text to classify
            
        Returns:
            TypedClaim with type and confidence
        """
        raw_claim = RawClaim(
            text=text,
            sentence_index=0,
            char_start=0,
            char_end=len(text),
            is_assertion=True
        )
        return self._classify_single(raw_claim)
