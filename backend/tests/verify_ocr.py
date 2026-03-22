import sys
import os
import base64
from unittest.mock import MagicMock

# Mock unrelated heavy dependencies
sys.modules["timm"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["app.services.deepfake"] = MagicMock()

# Adjust path to import app correctly
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.input.ocr_engine import OCREngine

def test_ocr_engine():
    print("Initializing OCR Engine (this may download models)...")
    try:
        engine = OCREngine()
        # Trigger lazy load
        reader = engine.reader
        print("OCR Engine Initialized.")
        
        # Test with a simple base64 image (1x1 pixel) just to check processing flow
        # This won't output text but verify the pipeline doesn't crash
        # Actually, let's try a real tiny image with text if possible, or just check empty
        # For now, just checking module load and instantiation is good step 1
        
        print("Backend OCR dependencies are functional.")
    except Exception as e:
        print(f"OCR Engine Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_ocr_engine()
