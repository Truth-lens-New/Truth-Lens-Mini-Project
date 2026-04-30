"""
TruthLens Claim Extractor V3

Extracts claims from processed text using spaCy.
Over-extraction strategy: Better to have false positives than miss claims.
"""

from typing import List
from enum import Enum

class InputType(str, Enum):
    """Types of input the system can process."""
    TEXT = "text"
    URL = "url"
    IMAGE = "image"
    SOCIAL = "social"

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
        # Lazy load CruxExtractor to prevent circular imports or init issues
        self._crux_extractor = None

    @property
    def crux_extractor(self):
        if self._crux_extractor is None:
            from app.services.extraction.crux_extractor import CruxExtractor
            self._crux_extractor = CruxExtractor()
        return self._crux_extractor
    
    def extract(self, processed_input: ProcessedInput) -> List[RawClaim]:
        """
        Extract claims from processed input.
        """
        # Parse with spaCy
        doc = self.models.nlp(processed_input.text)
        
        claims = []
        
        # Phase 4: Handle Visual Content (even if OCR text is generic)
        if processed_input.source_type == InputType.IMAGE:
             # Generate a primary visual claim
             claims.append(RawClaim(
                 text=processed_input.text,
                 sentence_index=0,
                 char_start=0,
                 char_end=len(processed_input.text),
                 is_assertion=True,
                 raw_data=processed_input.raw_data
             ))

        # Standard text extraction
        for idx, sent in enumerate(doc.sents):
            sent_text = sent.text.strip()
            
            # Skip empty sentences
            if not sent_text:
                continue

            # Attempt to split compound sentences
            sub_sentences = self._split_compound_sentence(sent)
            
            for sub_idx, sub_text in enumerate(sub_sentences):
                # Create a pseudo-doc for the sub-sentence to analyze it
                sub_doc = self.models.nlp(sub_text)
                sub_sent = list(sub_doc.sents)[0] if list(sub_doc.sents) else sent

                # Check if this sub-sentence is a potential claim
                is_assertion = self._is_assertion(sub_sent)
                might_be_claim = self._might_be_claim(sub_sent)
                
                if (is_assertion or might_be_claim) and sub_text not in [c.text for c in claims]:
                    claim = RawClaim(
                        text=sub_text,
                        sentence_index=(idx + 1) * 100 + sub_idx, # Unique index
                        char_start=sent.start_char,
                        char_end=sent.end_char,
                        is_assertion=is_assertion,
                        raw_data=processed_input.raw_data # Carry data to all potential claims
                    )
                    claims.append(claim)
        
        return claims

    def extract_crux(self, processed_input: ProcessedInput) -> List[RawClaim]:
        """
        Extract core 'Crux' claims using LLM Synthesis.
        Falls back to standard extraction if LLM fails or is disabled.
        """
        # 1. Try LLM Extraction
        try:
            if self.crux_extractor.enabled:
                claims = self.crux_extractor.extract(processed_input.text)
                if claims:
                    return claims
        except Exception as e:
            print(f"Crux extraction failed, falling back: {e}")
            
        # 2. Fallback to Standard Extraction (but maybe limit it?)
        return self.extract(processed_input)

    def _split_compound_sentence(self, sent) -> List[str]:
        """
        Split a spaCy sentence into potential sub-claims based on punctuation.
        Mainly targets comma splices in user input.
        """
        text = sent.text.strip()
        
        # If it's short, don't split
        if len(text.split()) < 6:
            return [text]
            
        # Split by comma if the parts look like independent clauses (len > 3 words)
        parts = [p.strip() for p in text.split(',')]
        valid_parts = []
        current_part = []
        
        for p in parts:
            current_part.append(p)
            combined = ", ".join(current_part)
            # If this chunk is long enough to be a sentence, verify if it stands alone
            if len(combined.split()) >= 3:
                valid_parts.append(combined)
                current_part = []
        
        # If we have leftover, append to last
        if current_part and valid_parts:
            valid_parts[-1] += ", " + ", ".join(current_part)
        elif current_part:
            valid_parts.append(", ".join(current_part))
            
        # Fallback: if splitting didn't create well-sized chunks, return original
        if len(valid_parts) <= 1:
            return [text]
            
        return valid_parts
    
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
        # Include AUX (auxiliary verbs like "is", "are", "was") as valid verbs
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass'] for token in sent)
        has_verb = any(token.pos_ in ['VERB', 'AUX'] for token in sent)
        
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
