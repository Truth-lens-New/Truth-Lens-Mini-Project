import sys
import os
from unittest.mock import MagicMock

# Mock unrelated heavy dependencies
sys.modules["timm"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["app.services.deepfake"] = MagicMock()

sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.input.url_scraper import URLScraper

def test_scraper():
    url = "https://www.historyextra.com/period/20th-century/did-nasa-fake-moon-landing-real-history-conspiracy/"
    print(f"Attempting to scrape: {url}")
    
    scraper = URLScraper()
    try:
        result = scraper.process(url)
        print("✅ Success!")
        print(f"Extracted length: {len(result.text)}")
        print(f"Preview: {result.text[:100]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_scraper()
