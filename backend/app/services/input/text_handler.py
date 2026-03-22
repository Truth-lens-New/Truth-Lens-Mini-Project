"""
TruthLens Text Handler

Handles plain text input processing.
"""

import re
from app.models.domain import ProcessedInput, InputType


class TextHandler:
    """Handle plain text input."""
    
    def process(self, content: str) -> ProcessedInput:
        """
        Process plain text.
        
        Args:
            content: Raw text input
            
        Returns:
            ProcessedInput with cleaned text
        """
        if not content or not content.strip():
            raise ValueError("Text content cannot be empty")
        
        # Clean the text
        cleaned = self._clean_text(content)
        
        return ProcessedInput(
            text=cleaned,
            source_type=InputType.TEXT
        )
    
    def _clean_text(self, text: str) -> str:
        """Basic text cleaning."""
        # Normalize whitespace (multiple spaces/newlines → single space)
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
