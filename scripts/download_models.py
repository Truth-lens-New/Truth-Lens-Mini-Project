
"""
Download/Cache ML Models.

Run this script to pre-download all required models
so that the API doesn't time out on the first request.
"""

import os
import subprocess
import sys

def install_spacy():
    print("📦 Checking spaCy model...")
    try:
        import spacy
        spacy.load("en_core_web_sm")
        print("   ✅ spaCy model found.")
    except OSError:
        print("   ⬇️ Downloading spaCy model...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])

def download_transformers():
    print("📦 Checking Transformer models...")
    try:
        from transformers import pipeline
        
        # 2. BART (Unified Intelligence: Claim Typing + Stance)
        print("   ⬇️ Downloading/Loading BART-large-mnli...")
        pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        print("   ✅ BART loaded.")
        
    except Exception as e:
        print(f"   ❌ Error downloading transformers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("="*40)
    print("TRUTHLENS MODEL DOWNLOADER")
    print("="*40)
    
    install_spacy()
    download_transformers()
    
    print("\n✅ All models cached successfully!")
