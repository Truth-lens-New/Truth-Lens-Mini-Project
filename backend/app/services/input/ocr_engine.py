"""
TruthLens OCR Engine

Extracts text from images using EasyOCR.
"""

import base64
import tempfile
import os
from app.models.domain import ProcessedInput, InputType


class OCREngine:
    """Extract text from images using EasyOCR."""
    
    def __init__(self):
        # Lazy load EasyOCR (heavy import)
        self._reader = None
    
    @property
    def reader(self):
        """Lazy load EasyOCR reader."""
        if self._reader is None:
            import easyocr
            # Use English, GPU=False for CPU (set True if GPU available)
            self._reader = easyocr.Reader(['en'], gpu=False)
        return self._reader
    
    def process(self, image_data: str) -> ProcessedInput:
        """
        Extract text from image.
        
        Args:
            image_data: Base64 encoded image string
            
        Returns:
            ProcessedInput with OCR text
            
        Raises:
            ValueError: If image processing fails
        """
        if not image_data:
            raise ValueError("Image data cannot be empty")
        
        # Handle data URL format (e.g., "data:image/png;base64,...")
        if image_data.startswith('data:image'):
            # Remove data URL prefix
            try:
                image_data = image_data.split(',')[1]
            except IndexError:
                raise ValueError("Invalid image data URL format")
        
        # Decode base64 to bytes
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise ValueError(f"Failed to decode base64 image: {e}")
        
        # Write to temp file and process
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(image_bytes)
            temp_path = f.name
        
        try:
            # Run OCR
            results = self.reader.readtext(temp_path)
            
            # Extract text from results (format: [(bbox, text, confidence), ...])
            texts = [result[1] for result in results]
            combined_text = ' '.join(texts)
            
            if not combined_text.strip():
                raise ValueError("No text found in image")
            
            return ProcessedInput(
                text=combined_text,
                source_type=InputType.IMAGE
            )
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
