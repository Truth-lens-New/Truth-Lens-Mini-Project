"""
TruthLens Model Manager

Singleton pattern to load ML models ONCE and reuse everywhere.
"""

import spacy
from transformers import pipeline


class ModelManager:
    """
    Singleton model manager.
    Loads all ML models once at startup, reuses everywhere.
    
    Models loaded:
    1. spaCy (en_core_web_sm) - NLP processing
    2. BART-large-mnli - Zero-shot classification for claim typing
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if ModelManager._initialized:
            return
        
        self._load_models()
        ModelManager._initialized = True
    
    def _load_models(self):
        """Load all ML models."""
        print("🔄 Loading ML models (one-time startup)...")
        
        # 1. spaCy for NLP
        print("  📚 Loading spaCy en_core_web_sm...")
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("  ⚠️ spaCy model not found, downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # 2. Unified Intelligence Model (BART-Large-MNLI)
        # Used for BOTH Claim Typing and Stance Detection
        print("  🧠 Loading Unified Intelligence Model (BART-Large-MNLI)...")
        import torch
        self.unified_model = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device="cpu", # Use "cuda" if available, but "cpu" is safer for this dev env
            torch_dtype=torch.float32
        )
        
        # Alias for backward compatibility if needed, but better to access unified_model
        self.zero_shot = self.unified_model
        
        print("✅ Intelligence Engine Loaded.")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if models are loaded."""
        return cls._initialized
    
    @classmethod
    def reset(cls):
        """Reset singleton (for testing)."""
        cls._instance = None
        cls._initialized = False


def get_model_manager() -> ModelManager:
    """Get the singleton model manager instance."""
    return ModelManager()
