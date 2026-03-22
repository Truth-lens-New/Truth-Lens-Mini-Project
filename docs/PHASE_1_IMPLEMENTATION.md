# 🏗️ TruthLens Phase 1: Complete Implementation Blueprint

> **Document Type:** Architectural Deep-Dive & Implementation Guide  
> **Phase:** 1 - The Skeleton  
> **Duration:** Week 1-2  
> **Status:** Ready for Implementation  
> **Created:** January 2026

---

## 📋 Table of Contents

1. [Phase 1 Overview](#-phase-1-overview)
2. [Architecture Diagram](#-architecture-diagram)
3. [Directory Structure](#-directory-structure)
4. [Dependencies & Setup](#-dependencies--setup)
5. [Data Models](#-data-models)
6. [Component 1: Input Gateway](#-component-1-input-gateway)
7. [Component 2: Claim Extraction](#-component-2-claim-extraction)
8. [Component 3: Claim Typing](#-component-3-claim-typing)
9. [Component 4: Model Manager](#-component-4-model-manager)
10. [Component 5: Output Structure](#-component-5-output-structure)
11. [API Endpoints](#-api-endpoints)
12. [Testing Strategy](#-testing-strategy)
13. [Success Criteria](#-success-criteria)
14. [Task Breakdown](#-task-breakdown)

---

## 🎯 Phase 1 Overview

### What Phase 1 Delivers

```
USER INPUT (any format) → TYPED CLAIMS with honest status

Example:
Input:  "COVID vaccines cause autism. The weather is nice today."
Output: [
  {
    "claim": "COVID vaccines cause autism",
    "type": "SCIENTIFIC_MEDICAL",
    "status": "Pending evidence analysis",
    "confidence": 0.89
  },
  {
    "claim": "The weather is nice today", 
    "type": "OPINION",
    "status": "Not fact-checkable (opinion/observation)",
    "confidence": 0.92
  }
]
```

### What Phase 1 Does NOT Do

- ❌ Evidence gathering (Phase 2)
- ❌ Verdict determination (Phase 2+)
- ❌ Claim normalization (Phase 4)
- ❌ LLM explanations (Phase 4)

### Core Principle

> **Phase 1 = Honest skeleton.** 
> We extract claims, type them, and tell users "here's what we found, analysis pending."
> No fake verdicts. No pretending we know things we don't.

---

## 🏛️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1 ARCHITECTURE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                              USER REQUEST
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API LAYER (FastAPI)                                │
│                                                                              │
│  POST /api/v3/analyze                                                        │
│  ├── Request: { input_type, content, options }                               │
│  └── Response: { claims: [...], metadata: {...} }                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COMPONENT 1: INPUT GATEWAY                              │
│                                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │    TEXT     │   │     URL     │   │    IMAGE    │   │   SOCIAL    │      │
│  │   Handler   │   │   Scraper   │   │     OCR     │   │   Parser    │      │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘      │
│         │                  │                  │                  │           │
│         └──────────────────┴──────────────────┴──────────────────┘           │
│                                   │                                          │
│                                   ▼                                          │
│                          ProcessedInput                                      │
│                    { text, source_type, metadata }                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPONENT 2: CLAIM EXTRACTION                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      spaCy (en_core_web_sm)                          │    │
│  │                                                                      │    │
│  │  1. Sentence tokenization                                            │    │
│  │  2. Filter: Keep assertions, discard questions/opinions              │    │
│  │  3. Over-extract (false positives OK, false negatives NOT OK)        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                   │                                          │
│                                   ▼                                          │
│                         List[RawClaim]                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPONENT 3: CLAIM TYPING (THE FORK)                      │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │              facebook/bart-large-mnli (Zero-Shot)                    │    │
│  │                                                                      │    │
│  │  Labels:                                                             │    │
│  │  - "scientific or medical claim"                                     │    │
│  │  - "political allegation"                                            │    │
│  │  - "factual statement about dates or numbers"                        │    │
│  │  - "breaking news event"                                             │    │
│  │  - "opinion or value judgment"                                       │    │
│  │  - "quote attribution"                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                   │                                          │
│                                   ▼                                          │
│                         List[TypedClaim]                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPONENT 5: OUTPUT STRUCTURE                             │
│                                                                              │
│  {                                                                           │
│    "claims": [                                                               │
│      {                                                                       │
│        "original_text": "...",                                               │
│        "claim_type": "SCIENTIFIC_MEDICAL",                                   │
│        "type_confidence": 0.89,                                              │
│        "status": "Pending evidence analysis",                                │
│        "evidence_strategy": "Will use: Scientific consensus check",          │
│        "is_checkable": true                                                  │
│      }                                                                       │
│    ],                                                                        │
│    "metadata": { "input_type": "text", "processing_time_ms": 450 }           │
│  }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app entry point
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v3/
│   │       ├── __init__.py
│   │       ├── router.py                # API routes
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── analyze.py           # POST /analyze endpoint
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                    # Settings, environment vars
│   │   └── exceptions.py                # Custom exceptions
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py                  # Pydantic request models
│   │   ├── responses.py                 # Pydantic response models
│   │   └── domain.py                    # Domain models (RawClaim, TypedClaim)
│   │
│   └── services/
│       ├── __init__.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   └── model_manager.py         # Singleton model loader
│       │
│       ├── input/
│       │   ├── __init__.py
│       │   ├── gateway.py               # Main input router
│       │   ├── text_handler.py          # Plain text processing
│       │   ├── url_scraper.py           # URL content extraction
│       │   └── ocr_engine.py            # Image OCR
│       │
│       ├── extraction/
│       │   ├── __init__.py
│       │   └── claim_extractor.py       # Claim extraction logic
│       │
│       ├── typing/
│       │   ├── __init__.py
│       │   └── claim_classifier.py      # Zero-shot classification
│       │
│       └── output/
│           ├── __init__.py
│           └── assessment_builder.py    # Build response
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   ├── test_input_gateway.py
│   ├── test_claim_extractor.py
│   ├── test_claim_classifier.py
│   └── test_api_endpoints.py
│
├── requirements.txt
└── README.md
```

**Total files to create:** 25 files

---

## 📦 Dependencies & Setup

### requirements.txt

```txt
# FastAPI & Server
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6

# ML Models
transformers==4.36.0
torch==2.1.0
spacy==3.7.2
sentence-transformers==2.2.2

# NLP
nltk==3.8.1

# Web Scraping
trafilatura==1.6.0
requests==2.31.0

# OCR
easyocr==1.7.1

# Data Validation
pydantic==2.5.0

# Testing
pytest==7.4.0
pytest-asyncio==0.21.0
httpx==0.25.0

# Utilities
python-dotenv==1.0.0
```

### Setup Commands

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. First run will download HuggingFace models (~1.6GB for BART)
# Models are cached in ~/.cache/huggingface/
```

### Environment Variables (.env)

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Model Settings
DEVICE=-1  # -1 for CPU, 0 for GPU
MODEL_CACHE_DIR=./models_cache

# Timeouts
REQUEST_TIMEOUT=60
```

---

## 📊 Data Models

### File: `app/models/domain.py`

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class InputType(str, Enum):
    TEXT = "text"
    URL = "url"
    IMAGE = "image"
    SOCIAL = "social"


class ClaimType(str, Enum):
    SCIENTIFIC_MEDICAL = "scientific_medical"
    POLITICAL_ALLEGATION = "political_allegation"
    FACTUAL_STATEMENT = "factual_statement"
    BREAKING_EVENT = "breaking_event"
    OPINION = "opinion"
    QUOTE_ATTRIBUTION = "quote_attribution"
    UNKNOWN = "unknown"


@dataclass
class ProcessedInput:
    """Output of Input Gateway"""
    text: str
    source_type: InputType
    source_url: Optional[str] = None
    source_domain: Optional[str] = None
    extracted_at: datetime = None
    
    def __post_init__(self):
        if self.extracted_at is None:
            self.extracted_at = datetime.now()


@dataclass
class RawClaim:
    """Output of Claim Extraction"""
    text: str
    sentence_index: int
    char_start: int
    char_end: int
    is_assertion: bool


@dataclass
class TypedClaim:
    """Output of Claim Typing"""
    text: str
    claim_type: ClaimType
    type_confidence: float
    is_checkable: bool
    evidence_strategy: str
    status: str
    
    # Original extraction info
    sentence_index: int = 0
    
    def to_dict(self) -> dict:
        return {
            "original_text": self.text,
            "claim_type": self.claim_type.value,
            "type_confidence": round(self.type_confidence, 3),
            "is_checkable": self.is_checkable,
            "evidence_strategy": self.evidence_strategy,
            "status": self.status
        }
```

### File: `app/models/requests.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from .domain import InputType


class AnalyzeRequest(BaseModel):
    """Request body for /analyze endpoint"""
    
    input_type: InputType = Field(
        default=InputType.TEXT,
        description="Type of input: text, url, image, social"
    )
    
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="The content to analyze (text, URL, or base64 image)"
    )
    
    options: Optional[dict] = Field(
        default=None,
        description="Optional processing options"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_type": "text",
                "content": "COVID vaccines cause autism. The weather is nice.",
                "options": None
            }
        }
```

### File: `app/models/responses.py`

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ClaimResponse(BaseModel):
    """Single claim in response"""
    original_text: str
    claim_type: str
    type_confidence: float
    is_checkable: bool
    evidence_strategy: str
    status: str


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis"""
    input_type: str
    processing_time_ms: int
    claims_found: int
    checkable_claims: int
    analyzed_at: datetime


class AnalyzeResponse(BaseModel):
    """Response from /analyze endpoint"""
    success: bool
    claims: List[ClaimResponse]
    metadata: AnalysisMetadata
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "claims": [
                    {
                        "original_text": "COVID vaccines cause autism",
                        "claim_type": "scientific_medical",
                        "type_confidence": 0.89,
                        "is_checkable": True,
                        "evidence_strategy": "Scientific consensus check",
                        "status": "Pending evidence analysis"
                    }
                ],
                "metadata": {
                    "input_type": "text",
                    "processing_time_ms": 450,
                    "claims_found": 2,
                    "checkable_claims": 1,
                    "analyzed_at": "2026-01-18T12:00:00"
                }
            }
        }
```

---

## 🔌 Component 1: Input Gateway

### Purpose
Convert ANY input type into unified `ProcessedInput` format.

### File: `app/services/input/gateway.py`

```python
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
        """
        if input_type == InputType.TEXT:
            return self.text_handler.process(content)
        
        elif input_type == InputType.URL:
            return self.url_scraper.process(content)
        
        elif input_type == InputType.IMAGE:
            return self.ocr_engine.process(content)
        
        elif input_type == InputType.SOCIAL:
            # For now, treat social as text
            # TODO: Add social-specific parsing in Phase 2
            return self.text_handler.process(content)
        
        else:
            raise ValueError(f"Unknown input type: {input_type}")
```

### File: `app/services/input/text_handler.py`

```python
import re
from app.models.domain import ProcessedInput, InputType


class TextHandler:
    """Handle plain text input."""
    
    def process(self, content: str) -> ProcessedInput:
        """
        Process plain text.
        - Clean whitespace
        - Basic normalization
        """
        # Clean the text
        cleaned = self._clean_text(content)
        
        return ProcessedInput(
            text=cleaned,
            source_type=InputType.TEXT
        )
    
    def _clean_text(self, text: str) -> str:
        """Basic text cleaning."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
```

### File: `app/services/input/url_scraper.py`

```python
import trafilatura
from urllib.parse import urlparse
from app.models.domain import ProcessedInput, InputType


class URLScraper:
    """Extract content from URLs using trafilatura."""
    
    def process(self, url: str) -> ProcessedInput:
        """
        Fetch and extract main content from URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            ProcessedInput with extracted text
        """
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")
        
        # Fetch and extract
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError(f"Could not fetch URL: {url}")
        
        text = trafilatura.extract(downloaded)
        if not text:
            raise ValueError(f"Could not extract content from URL: {url}")
        
        return ProcessedInput(
            text=text,
            source_type=InputType.URL,
            source_url=url,
            source_domain=parsed.netloc
        )
```

### File: `app/services/input/ocr_engine.py`

```python
import base64
import tempfile
import os
import easyocr
from app.models.domain import ProcessedInput, InputType


class OCREngine:
    """Extract text from images using EasyOCR."""
    
    def __init__(self):
        # Initialize EasyOCR (loads model)
        # Use English, can add more languages
        self._reader = None  # Lazy load
    
    @property
    def reader(self):
        if self._reader is None:
            self._reader = easyocr.Reader(['en'], gpu=False)
        return self._reader
    
    def process(self, image_data: str) -> ProcessedInput:
        """
        Extract text from image.
        
        Args:
            image_data: Base64 encoded image OR file path
            
        Returns:
            ProcessedInput with OCR text
        """
        # Handle base64 input
        if image_data.startswith('data:image'):
            # Remove data URL prefix
            image_data = image_data.split(',')[1]
        
        # Decode base64 to temp file
        image_bytes = base64.b64decode(image_data)
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(image_bytes)
            temp_path = f.name
        
        try:
            # Run OCR
            results = self.reader.readtext(temp_path)
            
            # Extract text from results
            texts = [result[1] for result in results]
            combined_text = ' '.join(texts)
            
            return ProcessedInput(
                text=combined_text,
                source_type=InputType.IMAGE
            )
        finally:
            # Cleanup temp file
            os.unlink(temp_path)
```

---

## 🔍 Component 2: Claim Extraction

### Purpose
Extract individual claims from text using spaCy NLP.

### File: `app/services/extraction/claim_extractor.py`

```python
from typing import List
from app.models.domain import ProcessedInput, RawClaim
from app.services.models.model_manager import ModelManager


class ClaimExtractor:
    """
    Extract claims from processed text.
    Over-extraction strategy: Better to have false positives than miss claims.
    """
    
    # Sentence patterns that are NOT claims
    NON_CLAIM_PATTERNS = [
        # Questions
        lambda s: s.text.strip().endswith('?'),
        # Very short
        lambda s: len(s.text.split()) < 4,
        # Imperatives/commands (start with verb)
        lambda s: s[0].pos_ == 'VERB' and s[0].dep_ == 'ROOT',
        # Pure greetings
        lambda s: s.text.lower().strip() in ['hello', 'hi', 'hey', 'thanks'],
    ]
    
    def __init__(self):
        self.models = ModelManager()
    
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
            # Check if this sentence is a potential claim
            is_assertion = self._is_assertion(sent)
            
            claim = RawClaim(
                text=sent.text.strip(),
                sentence_index=idx,
                char_start=sent.start_char,
                char_end=sent.end_char,
                is_assertion=is_assertion
            )
            
            # Over-extract: include even if not sure
            if is_assertion or self._might_be_claim(sent):
                claims.append(claim)
        
        return claims
    
    def _is_assertion(self, sent) -> bool:
        """Check if sentence is an assertion (statement of fact)."""
        # Not a question
        if sent.text.strip().endswith('?'):
            return False
        
        # Not too short
        if len(sent.text.split()) < 4:
            return False
        
        # Has a subject and verb (basic sentence structure)
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass'] for token in sent)
        has_verb = any(token.pos_ == 'VERB' for token in sent)
        
        return has_subject and has_verb
    
    def _might_be_claim(self, sent) -> bool:
        """
        Check if sentence MIGHT be a claim (over-extraction).
        Used for borderline cases.
        """
        # Contains entity mentions (likely factual)
        has_entities = len(sent.ents) > 0
        
        # Contains numbers (likely factual)
        has_numbers = any(token.like_num for token in sent)
        
        # Contains claim keywords
        claim_keywords = ['cause', 'proven', 'linked', 'study', 'research', 
                         'confirmed', 'announced', 'reported', 'according']
        has_keywords = any(kw in sent.text.lower() for kw in claim_keywords)
        
        return has_entities or has_numbers or has_keywords
```

---

## 🏷️ Component 3: Claim Typing

### Purpose
Classify each claim into types using BART zero-shot classification.

### File: `app/services/typing/claim_classifier.py`

```python
from typing import List
from app.models.domain import RawClaim, TypedClaim, ClaimType
from app.services.models.model_manager import ModelManager


class ClaimClassifier:
    """
    Classify claims into types using zero-shot classification.
    This is THE FORK - routes claims to different evidence strategies.
    """
    
    # Labels for zero-shot classification
    LABELS = [
        "scientific or medical claim",
        "political allegation or accusation",
        "factual statement about dates, numbers, or events",
        "breaking news or recent event",
        "opinion or value judgment",
        "quote attribution"
    ]
    
    # Map labels to ClaimType enum
    LABEL_TO_TYPE = {
        "scientific or medical claim": ClaimType.SCIENTIFIC_MEDICAL,
        "political allegation or accusation": ClaimType.POLITICAL_ALLEGATION,
        "factual statement about dates, numbers, or events": ClaimType.FACTUAL_STATEMENT,
        "breaking news or recent event": ClaimType.BREAKING_EVENT,
        "opinion or value judgment": ClaimType.OPINION,
        "quote attribution": ClaimType.QUOTE_ATTRIBUTION
    }
    
    # Evidence strategies per claim type
    STRATEGIES = {
        ClaimType.SCIENTIFIC_MEDICAL: "Scientific consensus check (PubMed, WHO)",
        ClaimType.POLITICAL_ALLEGATION: "Multi-source verification, official records",
        ClaimType.FACTUAL_STATEMENT: "Wikidata verification, authoritative sources",
        ClaimType.BREAKING_EVENT: "Multi-source news check, timeline analysis",
        ClaimType.OPINION: "Not fact-checkable (opinion/value judgment)",
        ClaimType.QUOTE_ATTRIBUTION: "Quote source verification",
        ClaimType.UNKNOWN: "General fact-check"
    }
    
    # Which types are fact-checkable
    CHECKABLE_TYPES = {
        ClaimType.SCIENTIFIC_MEDICAL,
        ClaimType.POLITICAL_ALLEGATION,
        ClaimType.FACTUAL_STATEMENT,
        ClaimType.BREAKING_EVENT,
        ClaimType.QUOTE_ATTRIBUTION
    }
    
    def __init__(self):
        self.models = ModelManager()
    
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
            if not claim.is_assertion:
                # Skip non-assertions
                continue
            
            typed_claim = self._classify_single(claim)
            typed_claims.append(typed_claim)
        
        return typed_claims
    
    def _classify_single(self, claim: RawClaim) -> TypedClaim:
        """Classify a single claim."""
        
        # Run zero-shot classification
        result = self.models.zero_shot(
            claim.text,
            self.LABELS,
            multi_label=False
        )
        
        # Get top label
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        
        # Map to our type enum
        claim_type = self.LABEL_TO_TYPE.get(top_label, ClaimType.UNKNOWN)
        
        # Determine if checkable
        is_checkable = claim_type in self.CHECKABLE_TYPES
        
        # Get evidence strategy
        strategy = self.STRATEGIES.get(claim_type, "General fact-check")
        
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
```

---

## 🧠 Component 4: Model Manager

### Purpose
Singleton pattern to load ML models ONCE and reuse everywhere.

### File: `app/services/models/model_manager.py`

```python
import spacy
from transformers import pipeline


class ModelManager:
    """
    Singleton model manager.
    Loads all ML models once at startup, reuses everywhere.
    
    Models loaded:
    1. spaCy (en_core_web_sm) - NLP processing
    2. BART-large-mnli - Zero-shot classification
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
        
        print("🔄 Loading ML models (one-time)...")
        
        # 1. spaCy for NLP
        print("  Loading spaCy...")
        self.nlp = spacy.load("en_core_web_sm")
        
        # 2. Zero-shot classifier for claim typing
        print("  Loading BART-large-mnli...")
        self.zero_shot = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1  # CPU (-1), GPU (0)
        )
        
        print("✅ Models loaded!")
        ModelManager._initialized = True
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if models are loaded."""
        return cls._initialized
    
    @classmethod
    def reset(cls):
        """Reset singleton (for testing)."""
        cls._instance = None
        cls._initialized = False


# Pre-initialize on import (optional)
def get_model_manager() -> ModelManager:
    """Get the singleton model manager instance."""
    return ModelManager()
```

---

## 🌐 API Endpoints

### File: `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v3.router import router as v3_router
from app.services.models.model_manager import ModelManager

# Initialize models at startup
print("Starting TruthLens API...")
model_manager = ModelManager()

app = FastAPI(
    title="TruthLens API",
    description="Claim Analysis Pipeline V3",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(v3_router, prefix="/api/v3")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "models_loaded": ModelManager.is_initialized()
    }
```

### File: `app/api/v3/router.py`

```python
from fastapi import APIRouter
from .endpoints import analyze

router = APIRouter(tags=["v3"])
router.include_router(analyze.router)
```

### File: `app/api/v3/endpoints/analyze.py`

```python
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.models.requests import AnalyzeRequest
from app.models.responses import AnalyzeResponse, ClaimResponse, AnalysisMetadata
from app.services.input.gateway import InputGateway
from app.services.extraction.claim_extractor import ClaimExtractor
from app.services.typing.claim_classifier import ClaimClassifier


router = APIRouter()

# Initialize services
input_gateway = InputGateway()
claim_extractor = ClaimExtractor()
claim_classifier = ClaimClassifier()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_content(request: AnalyzeRequest):
    """
    Analyze content for claims.
    
    Phase 1: Extract and type claims.
    Returns typed claims with pending status.
    """
    start_time = time.time()
    
    try:
        # Step 1: Process input
        processed = input_gateway.process(
            request.input_type,
            request.content
        )
        
        # Step 2: Extract claims
        raw_claims = claim_extractor.extract(processed)
        
        # Step 3: Type claims
        typed_claims = claim_classifier.classify(raw_claims)
        
        # Step 4: Build response
        processing_time = int((time.time() - start_time) * 1000)
        
        claims_response = [
            ClaimResponse(
                original_text=c.text,
                claim_type=c.claim_type.value,
                type_confidence=c.type_confidence,
                is_checkable=c.is_checkable,
                evidence_strategy=c.evidence_strategy,
                status=c.status
            )
            for c in typed_claims
        ]
        
        metadata = AnalysisMetadata(
            input_type=request.input_type.value,
            processing_time_ms=processing_time,
            claims_found=len(typed_claims),
            checkable_claims=sum(1 for c in typed_claims if c.is_checkable),
            analyzed_at=datetime.now()
        )
        
        return AnalyzeResponse(
            success=True,
            claims=claims_response,
            metadata=metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
```

---

## 🧪 Testing Strategy

### Test Files Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_input_gateway.py      # Input processing tests
├── test_claim_extractor.py    # Claim extraction tests
├── test_claim_classifier.py   # Claim typing tests
└── test_api_endpoints.py      # API integration tests
```

### File: `tests/conftest.py`

```python
import pytest
from app.services.models.model_manager import ModelManager

@pytest.fixture(scope="session", autouse=True)
def load_models():
    """Load models once for all tests."""
    ModelManager()
    yield
    ModelManager.reset()

@pytest.fixture
def sample_texts():
    """Sample texts for testing."""
    return {
        "scientific": "COVID vaccines cause autism according to new studies.",
        "political": "The BJP rigged the 2024 elections with help from ECI.",
        "factual": "India has a population of 1.4 billion people.",
        "opinion": "Pizza is the best food in the world.",
        "question": "Is climate change real?",
        "mixed": "COVID vaccines are dangerous. What do you think? I love summer."
    }
```

### File: `tests/test_claim_classifier.py`

```python
import pytest
from app.services.typing.claim_classifier import ClaimClassifier
from app.models.domain import RawClaim, ClaimType

class TestClaimClassifier:
    @pytest.fixture
    def classifier(self):
        return ClaimClassifier()
    
    def test_scientific_claim(self, classifier):
        claim = RawClaim(
            text="COVID vaccines cause autism according to research",
            sentence_index=0, char_start=0, char_end=50, is_assertion=True
        )
        result = classifier.classify([claim])
        
        assert len(result) == 1
        assert result[0].claim_type == ClaimType.SCIENTIFIC_MEDICAL
        assert result[0].is_checkable == True
    
    def test_opinion_not_checkable(self, classifier):
        claim = RawClaim(
            text="Pizza is the best food ever",
            sentence_index=0, char_start=0, char_end=30, is_assertion=True
        )
        result = classifier.classify([claim])
        
        assert len(result) == 1
        assert result[0].claim_type == ClaimType.OPINION
        assert result[0].is_checkable == False
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_claim_classifier.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## ✅ Success Criteria

### Phase 1 Complete When:

```
✅ Submit text → Get claims extracted
✅ Submit URL → Get article scraped → Get claims
✅ Submit image → OCR → Get claims
✅ Each claim has a TYPE (scientific, political, factual, etc.)
✅ Each claim has STATUS "Pending analysis" (honest, not fake verdict)
✅ Each claim shows EVIDENCE STRATEGY (what WOULD be used)
✅ Response time < 5 seconds for text input
✅ All tests passing
```

### Manual Verification Checklist

```
1. Start the server:
   $ uvicorn app.main:app --reload

2. Test text input:
   POST /api/v3/analyze
   {
     "input_type": "text",
     "content": "COVID vaccines cause autism. The weather is nice."
   }
   
   Expected: 2 claims, one SCIENTIFIC (checkable), one OPINION (not checkable)

3. Test URL input:
   POST /api/v3/analyze
   {
     "input_type": "url",
     "content": "https://example.com/news-article"
   }
   
   Expected: Claims extracted from article

4. Check /health endpoint returns models_loaded: true
```

---

## 📋 Task Breakdown (Day by Day)

### Day 1: Setup & Data Models
```
[ ] Create directory structure (25 files)
[ ] Write requirements.txt
[ ] Create app/models/domain.py
[ ] Create app/models/requests.py
[ ] Create app/models/responses.py
```

### Day 2: Model Manager & Input Gateway
```
[ ] Create app/services/models/model_manager.py
[ ] Test model loading works
[ ] Create app/services/input/text_handler.py
[ ] Create app/services/input/url_scraper.py
[ ] Create app/services/input/ocr_engine.py
[ ] Create app/services/input/gateway.py
```

### Day 3: Claim Extraction
```
[ ] Create app/services/extraction/claim_extractor.py
[ ] Write tests for claim extraction
[ ] Test with sample texts
```

### Day 4: Claim Typing
```
[ ] Create app/services/typing/claim_classifier.py
[ ] Write tests for claim classification
[ ] Verify zero-shot classification works
```

### Day 5: API & Integration
```
[ ] Create app/main.py
[ ] Create app/api/v3/router.py
[ ] Create app/api/v3/endpoints/analyze.py
[ ] Write integration tests
[ ] End-to-end testing
```

### Day 6-7: Polish & Documentation
```
[ ] Fix any bugs found
[ ] Improve error handling
[ ] Add logging
[ ] Update README
[ ] Code review
```

---

## 🎯 Quick Reference

### Key Files

| Purpose | File |
|---------|------|
| Entry point | `app/main.py` |
| API endpoint | `app/api/v3/endpoints/analyze.py` |
| Model loading | `app/services/models/model_manager.py` |
| Input processing | `app/services/input/gateway.py` |
| Claim extraction | `app/services/extraction/claim_extractor.py` |
| Claim typing | `app/services/typing/claim_classifier.py` |

### Key Models

| Model | HuggingFace ID | Purpose |
|-------|----------------|---------|
| spaCy | `en_core_web_sm` | Sentence splitting, NER |
| BART | `facebook/bart-large-mnli` | Zero-shot claim typing |

### Run Commands

```bash
# Install
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run server
uvicorn app.main:app --reload --port 8000

# Test
pytest tests/ -v
```

---

**End of Phase 1 Implementation Blueprint**
