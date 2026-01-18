"""
TruthLens Input Gateway

Routes different input types to appropriate handlers.
"""

from app.models.domain import InputType, ProcessedInput
from .text_handler import TextHandler
from .url_scraper import URLScraper
from .ocr_engine import OCREngine


class InputGateway:
    """
    Main entry point for all input types.
    Routes to appropriate handler based on input_type.
    """
    
    def __init__(self):
        self.text_handler = TextHandler()
        self.url_scraper = URLScraper()
        self.ocr_engine = OCREngine()
    
    def process(self, input_type: InputType, content: str) -> ProcessedInput:
        """
        Process any input type into unified ProcessedInput.
        
        Args:
            input_type: Type of input (text, url, image, social)
            content: The actual content
            
        Returns:
            ProcessedInput with extracted text and metadata
            
        Raises:
            ValueError: If input type is unknown or processing fails
        """
        if input_type == InputType.TEXT:
            return self.text_handler.process(content)
        
        elif input_type == InputType.URL:
            return self.url_scraper.process(content)
        
        elif input_type == InputType.IMAGE:
            return self.ocr_engine.process(content)
        
        elif input_type == InputType.SOCIAL:
            # For now, treat social as text
            # TODO: Add social-specific parsing (handle @mentions, hashtags)
            return self.text_handler.process(content)
        
        else:
            raise ValueError(f"Unknown input type: {input_type}")
