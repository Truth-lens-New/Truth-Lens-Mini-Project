"""
TruthLens Claim Extractor V3

Extracts claims from processed text using spaCy.
Over-extraction strategy: Better to have false positives than miss claims.
"""

from typing import List
from app.models.domain import ProcessedInput, RawClaim
from app.services.models import get_model_manager


class ClaimExtractorV3:
    """
    Extract claims from processed text using spaCy NLP.
    
    Strategy: Over-extract (false positives OK, false negatives NOT OK)
    We'd rather analyze a non-claim than miss a real claim.
    """
    
    # Keywords that suggest a sentence contains a claim
    CLAIM_KEYWORDS = [
        'cause', 'proven', 'linked', 'study', 'research',
        'confirmed', 'announced', 'reported', 'according',
        'claim', 'found', 'show', 'reveal', 'discover',
        'evidence', 'scientist', 'expert', 'official'
    ]
    
    def __init__(self):
        self.models = get_model_manager()
    
    def extract(self, processed_input: ProcessedInput) -> List[RawClaim]:
        """
        Extract claims from processed input.
        
        Args:
            processed_input: Output from InputGateway
            
        Returns:
            List of RawClaim objects
        """
        # Parse with spaCy
        doc = self.models.nlp(processed_input.text)
        
        claims = []
        for idx, sent in enumerate(doc.sents):
            sent_text = sent.text.strip()
            
            # Skip empty sentences
            if not sent_text:
                continue
            
            # Check if this sentence is a potential claim
            is_assertion = self._is_assertion(sent)
            
            claim = RawClaim(
                text=sent_text,
                sentence_index=idx,
                char_start=sent.start_char,
                char_end=sent.end_char,
                is_assertion=is_assertion
            )
            
            # Over-extract: include if assertion OR might be claim
            if is_assertion or self._might_be_claim(sent):
                claims.append(claim)
        
        return claims
    
    def _is_assertion(self, sent) -> bool:
        """
        Check if sentence is an assertion (statement of fact).
        
        Returns True if the sentence:
        - Is not a question
        - Is not too short
        - Has subject-verb structure
        """
        text = sent.text.strip()
        
        # Not a question
        if text.endswith('?'):
            return False
        
        # Not too short (at least 3 words)
        if len(text.split()) < 3:
            return False
        
        # Has a subject and verb (basic sentence structure)
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass'] for token in sent)
        has_verb = any(token.pos_ == 'VERB' for token in sent)
        
        return has_subject and has_verb
    
    def _might_be_claim(self, sent) -> bool:
        """
        Check if sentence MIGHT be a claim (over-extraction).
        Used for borderline cases to avoid missing claims.
        """
        text = sent.text.lower()
        
        # Contains entity mentions (likely factual)
        has_entities = len(sent.ents) > 0
        
        # Contains numbers (likely factual)
        has_numbers = any(token.like_num for token in sent)
        
        # Contains claim keywords
        has_keywords = any(kw in text for kw in self.CLAIM_KEYWORDS)
        
        # Contains opinion keywords (should still extract, classifier will mark as opinion)
        opinion_keywords = ['best', 'worst', 'great', 'terrible', 'i think', 'i believe']
        has_opinion = any(kw in text for kw in opinion_keywords)
        
        return has_entities or has_numbers or has_keywords or has_opinion
    
    def extract_from_text(self, text: str) -> List[RawClaim]:
        """
        Convenience method to extract claims from raw text.
        
        Args:
            text: Raw text to extract claims from
            
        Returns:
            List of RawClaim objects
        """
        from app.models.domain import InputType
        
        processed = ProcessedInput(
            text=text,
            source_type=InputType.TEXT
        )
        return self.extract(processed)
