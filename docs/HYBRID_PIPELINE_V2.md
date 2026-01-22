# 🔬 TruthLens: Hybrid Analysis Pipeline V2

> **Document Type:** Technical Architecture & Phased Implementation Plan  
> **Version:** 2.0 (Pre-trained Models + Multi-Input)  
> **Created:** January 2026  
> **Status:** Ready for Implementation

---

## 📋 Table of Contents

1. [Overview & Philosophy](#-overview--philosophy)
2. [Multi-Input Architecture](#-multi-input-architecture)
3. [Pipeline Layers](#-pipeline-layers)
4. [Pre-trained Models Stack](#-pre-trained-models-stack)
5. [Phased Implementation Plan](#-phased-implementation-plan)
6. [File Structure](#-file-structure)
7. [API Design](#-api-design)
8. [Success Criteria](#-success-criteria)

---

## 🎯 Overview & Philosophy

### What This Is

A **multi-layer hybrid misinformation detection pipeline** that:
- Uses **pre-trained ML models** (no fine-tuning required)
- Supports **multiple input types** (text, URLs, images)
- Combines NLP analysis, evidence gathering, stance detection, and LLM reasoning
- Provides explainable verdicts with evidence

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Incremental** | Build phase by phase, test each before moving on |
| **Extensible** | Easy to add new input types or analysis layers |
| **No Training** | Use pre-trained models from HuggingFace |
| **Honest Work** | Real ML pipeline, not just API wrappers |

### What Makes This "Hybrid"

```
┌─────────────────────────────────────────────────────────────────┐
│                     HYBRID = MULTIPLE TECHNIQUES                 │
├─────────────────────────────────────────────────────────────────┤
│  Traditional NLP (spaCy, VADER)                                 │
│        +                                                         │
│  Pre-trained Transformers (BERT, BART, RoBERTa)                 │
│        +                                                         │
│  External Knowledge (News APIs, Fact-checkers)                  │
│        +                                                         │
│  LLM Reasoning (Gemini Chain-of-Thought)                        │
│        =                                                         │
│  Comprehensive, Explainable Verdict                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Multi-Input Architecture

### Supported Input Types

```
┌─────────────────────────────────────────────────────────────────┐
│                       INPUT GATEWAY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│   │   📝 TEXT   │   │   🔗 URL    │   │   🖼️ IMAGE  │          │
│   │             │   │             │   │             │          │
│   │ Direct      │   │ Website     │   │ Screenshot  │          │
│   │ claim or    │   │ Article     │   │ Social post │          │
│   │ paragraph   │   │ Blog post   │   │ WhatsApp    │          │
│   │             │   │ News link   │   │ forward     │          │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘          │
│          │                 │                 │                  │
│          │                 ▼                 ▼                  │
│          │          ┌─────────────┐   ┌─────────────┐          │
│          │          │  SCRAPER    │   │    OCR      │          │
│          │          │  (trafilat- │   │  (Tesseract │          │
│          │          │   ura/BS4)  │   │   /EasyOCR) │          │
│          │          └──────┬──────┘   └──────┬──────┘          │
│          │                 │                 │                  │
│          └─────────────────┴─────────────────┘                  │
│                            │                                    │
│                            ▼                                    │
│                   ┌─────────────────┐                           │
│                   │  UNIFIED TEXT   │                           │
│                   │    CONTENT      │                           │
│                   └────────┬────────┘                           │
│                            │                                    │
│                            ▼                                    │
│                   ANALYSIS PIPELINE                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Input Processing Logic

```python
# Pseudocode for input routing
def process_input(input_data):
    if input_data.type == "TEXT":
        content = input_data.text
        source_url = None
        
    elif input_data.type == "URL":
        content = scrape_article(input_data.url)  # trafilatura
        source_url = input_data.url
        
    elif input_data.type == "IMAGE":
        content = extract_text_ocr(input_data.image)  # Tesseract/EasyOCR
        source_url = None
        
    # All paths lead to unified text content
    return analyze_content(content, source_url)
```

---

## 🏗️ Pipeline Layers

### Complete Architecture

```
                              USER INPUT
                    (Text / URL / Image)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT GATEWAY                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ Text Handler │ │ URL Scraper  │ │  OCR Engine  │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
╔═════════════════════════════════════════════════════════════════╗
║  LAYER 1: NLP PREPROCESSING                                      ║
║  ┌───────────────────────────────────────────────────────────┐  ║
║  │ • spaCy NER → Entities (Person, Org, Date, Location)     │  ║
║  │ • VADER → Sentiment Score (-1 to +1)                      │  ║
║  │ • ClaimBuster Model → Is this a verifiable claim? (0-1)  │  ║
║  │ • Language Detection → For multi-language support        │  ║
║  └───────────────────────────────────────────────────────────┘  ║
╚═════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔═════════════════════════════════════════════════════════════════╗
║  LAYER 2: EVIDENCE GATHERING                                     ║
║  ┌───────────────────────────────────────────────────────────┐  ║
║  │ • Google Fact Check API → Existing fact-checks           │  ║
║  │ • GNews API → Related news articles                       │  ║
║  │ • Source Domain Analysis → Trust score lookup            │  ║
║  │ • Metadata extraction → Publication date, author         │  ║
║  └───────────────────────────────────────────────────────────┘  ║
╚═════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔═════════════════════════════════════════════════════════════════╗
║  LAYER 3: STANCE DETECTION                                       ║
║  ┌───────────────────────────────────────────────────────────┐  ║
║  │ • BART-MNLI (Pre-trained) → Zero-shot classification     │  ║
║  │ • For each evidence article:                              │  ║
║  │   └─► SUPPORTS | REFUTES | NEUTRAL | UNRELATED           │  ║
║  │ • Confidence scores for each stance                       │  ║
║  └───────────────────────────────────────────────────────────┘  ║
╚═════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔═════════════════════════════════════════════════════════════════╗
║  LAYER 4: VERDICT AGGREGATION                                    ║
║  ┌───────────────────────────────────────────────────────────┐  ║
║  │ • Weighted scoring formula:                               │  ║
║  │   score = Σ(source_trust × stance × confidence) / Σ(trust)│  ║
║  │ • Map score to verdict:                                   │  ║
║  │   [-1.0 to -0.5] → LIKELY FALSE                          │  ║
║  │   [-0.5 to -0.2] → POSSIBLY FALSE                        │  ║
║  │   [-0.2 to +0.2] → UNVERIFIABLE                          │  ║
║  │   [+0.2 to +0.5] → POSSIBLY TRUE                         │  ║
║  │   [+0.5 to +1.0] → LIKELY TRUE                           │  ║
║  └───────────────────────────────────────────────────────────┘  ║
╚═════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔═════════════════════════════════════════════════════════════════╗
║  LAYER 5: LLM REASONING & EXPLANATION                            ║
║  ┌───────────────────────────────────────────────────────────┐  ║
║  │ • Gemini Chain-of-Thought prompting                       │  ║
║  │ • Input: Claim + Evidence + Stances + Verdict            │  ║
║  │ • Output: Human-readable explanation                      │  ║
║  │ • Key factors summary                                     │  ║
║  │ • Confidence justification                                │  ║
║  └───────────────────────────────────────────────────────────┘  ║
╚═════════════════════════════════════════════════════════════════╝
                              │
                              ▼
                    FINAL OUTPUT
            ┌─────────────────────────────────┐
            │ • Verdict (TRUE/FALSE/etc)      │
            │ • Confidence (0-100%)           │
            │ • Evidence sources              │
            │ • LLM explanation               │
            │ • Claim breakdown               │
            └─────────────────────────────────┘
```

---

## 🤖 Pre-trained Models Stack

### No Training Required - Just Use!

| Purpose | Model | Source | Why This One |
|---------|-------|--------|--------------|
| **Named Entities** | `en_core_web_lg` | spaCy | Industry standard, fast, accurate |
| **Sentiment** | VADER | NLTK | Works great for social media text |
| **Claim Detection** | `Nithiwat/bert-base_claimbuster` | HuggingFace | Trained on ClaimBuster dataset |
| **Stance Detection** | `facebook/bart-large-mnli` | HuggingFace | Zero-shot, no fine-tuning needed |
| **Fake News (backup)** | `hamzab/roberta-fake-news-classification` | HuggingFace | Pre-trained on fake news datasets |
| **OCR** | Tesseract / EasyOCR | Open Source | Battle-tested, works offline |
| **LLM Reasoning** | Gemini 2.5 Flash | Google | Already integrated in your project |

### Model Loading Code

```python
# models/loader.py

from transformers import pipeline
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class ModelLoader:
    """Singleton to load models once and reuse"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_models()
        return cls._instance
    
    def _load_models(self):
        # NLP
        self.nlp = spacy.load("en_core_web_lg")
        self.sentiment = SentimentIntensityAnalyzer()
        
        # Claim Detection
        self.claim_detector = pipeline(
            "text-classification",
            model="Nithiwat/bert-base_claimbuster"
        )
        
        # Stance Detection (Zero-shot)
        self.stance_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
```

---

## 📅 Phased Implementation Plan

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION PHASES                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PHASE 1          PHASE 2          PHASE 3          PHASE 4    │
│  ────────         ────────         ────────         ────────    │
│  Input            NLP              Stance +         Polish +    │
│  Gateway          Layer            Verdict          Testing     │
│                                                                  │
│  • Text input     • spaCy NER      • Stance model   • E2E tests │
│  • URL scraper    • Sentiment      • Weighted calc  • UI polish │
│  • OCR engine     • Claim detect   • LLM reasoning  • Report    │
│                                                                  │
│  [Week 1-2]       [Week 2-3]       [Week 3-4]       [Week 4-5]  │
│                                                                  │
│  TEST ──────────► TEST ──────────► TEST ──────────► DONE       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Input Gateway (Week 1-2)

**Goal:** Accept any input type, output unified text

#### Tasks

```
PHASE 1: INPUT GATEWAY
├── 1.1 Text Input Handler
│   ├── Accept raw text claims
│   ├── Basic text cleaning (trim, normalize whitespace)
│   └── ✅ TEST: Submit text, see it returned
│
├── 1.2 URL Scraper
│   ├── Install trafilatura: pip install trafilatura
│   ├── Scrape article content from URL
│   ├── Extract title, text, publish date
│   ├── Handle errors (404, paywall, etc)
│   └── ✅ TEST: Submit BBC URL, get article text
│
├── 1.3 OCR Engine
│   ├── Install: pip install easyocr (or pytesseract)
│   ├── Accept image upload (base64 or file)
│   ├── Extract text from image
│   ├── Handle multiple languages
│   └── ✅ TEST: Submit WhatsApp screenshot, get text
│
└── 1.4 API Integration
    ├── POST /api/v1/analyze endpoint update
    ├── Accept: { type: "text|url|image", content: "..." }
    └── ✅ TEST: All three input types work
```

#### End of Phase 1 Checkpoint

```python
# What should work after Phase 1
response = client.post("/api/v1/analyze", json={
    "type": "url",
    "content": "https://example.com/article"
})

assert response.json()["extracted_text"] is not None
assert len(response.json()["extracted_text"]) > 100
```

---

### Phase 2: NLP Analysis Layer (Week 2-3)

**Goal:** Extract meaningful features from text

#### Tasks

```
PHASE 2: NLP LAYER
├── 2.1 Entity Extraction
│   ├── Install: python -m spacy download en_core_web_lg
│   ├── Extract: PERSON, ORG, GPE, DATE entities
│   ├── Return structured entity list
│   └── ✅ TEST: "Biden met Modi" → [Biden:PERSON, Modi:PERSON]
│
├── 2.2 Sentiment Analysis
│   ├── Install: pip install vaderSentiment
│   ├── Get compound score (-1 to +1)
│   ├── Flag highly emotional content
│   └── ✅ TEST: Positive text → score > 0
│
├── 2.3 Claim Detection
│   ├── Load pre-trained ClaimBuster model
│   ├── Score: Is this a verifiable claim? (0-1)
│   ├── Threshold: > 0.5 = verifiable
│   └── ✅ TEST: "The sky is blue" → low score
│   └── ✅ TEST: "COVID kills 1M people" → high score
│
├── 2.4 Language Detection
│   ├── Use langdetect library
│   ├── Return ISO language code
│   └── ✅ TEST: Hindi text → "hi"
│
└── 2.5 Integration
    ├── NLP service orchestrator
    ├── Combine all outputs into single response
    └── ✅ TEST: Full NLP analysis on sample claim
```

#### End of Phase 2 Checkpoint

```python
# What should work after Phase 2
response = client.post("/api/v1/analyze", json={
    "type": "text",
    "content": "Donald Trump met with Kim Jong Un in 2018"
})

nlp_data = response.json()["nlp_analysis"]
assert "entities" in nlp_data
assert "sentiment" in nlp_data
assert "is_claim" in nlp_data
```

---

### Phase 3: Stance Detection + Verdict (Week 3-4)

**Goal:** Determine what evidence says, produce verdict

#### Tasks

```
PHASE 3: STANCE + VERDICT
├── 3.1 Evidence Retrieval (enhance existing)
│   ├── Fetch news from GNews API
│   ├── Fetch fact-checks from Google Fact Check
│   ├── Extract domain and calculate trust score
│   └── ✅ TEST: Claim → list of related articles
│
├── 3.2 Source Trust Scoring
│   ├── Create trusted_sources.json with scores
│   ├── Reuters=95, BBC=90, Unknown=50, InfoWars=10
│   ├── Lookup function for any domain
│   └── ✅ TEST: reuters.com → 95
│
├── 3.3 Stance Classification
│   ├── Load facebook/bart-large-mnli
│   ├── For each article: classify stance to claim
│   ├── Labels: supports, refutes, neutral
│   └── ✅ TEST: Pro-vaccine article + anti-vax claim → refutes
│
├── 3.4 Verdict Aggregation
│   ├── Implement weighted formula
│   ├── Map numerical score to verdict label
│   ├── Calculate overall confidence
│   └── ✅ TEST: Multiple refuting sources → LIKELY FALSE
│
└── 3.5 LLM Reasoning Integration
    ├── Chain-of-Thought prompt with evidence
    ├── Generate human-readable explanation
    ├── Summarize key factors
    └── ✅ TEST: Full claim → explanation makes sense
```

#### End of Phase 3 Checkpoint

```python
# What should work after Phase 3
response = client.post("/api/v1/analyze", json={
    "type": "text",
    "content": "5G towers cause coronavirus"
})

result = response.json()
assert result["verdict"] in ["LIKELY_TRUE", "LIKELY_FALSE", ...]
assert result["confidence"] > 0
assert len(result["evidence"]) > 0
assert result["explanation"] is not None
```

---

### Phase 4: Polish + Testing (Week 4-5)

**Goal:** Production-ready, tested, documented

#### Tasks

```
PHASE 4: POLISH
├── 4.1 End-to-End Testing
│   ├── Create test suite with 20+ claims
│   ├── Mix of true, false, unverifiable
│   ├── Test all input types
│   └── ✅ Measure accuracy, precision, recall
│
├── 4.2 Error Handling
│   ├── Graceful degradation if model fails
│   ├── Timeout handling for slow APIs
│   ├── Rate limiting protection
│   └── ✅ TEST: Bad URL → graceful error response
│
├── 4.3 Frontend Integration
│   ├── Update UI to show all layers
│   ├── Display entities, sentiment, stances
│   ├── Visual verdict with confidence bar
│   └── ✅ TEST: UI shows complete analysis
│
├── 4.4 Performance Optimization
│   ├── Cache model loading (singleton)
│   ├── Async evidence retrieval
│   ├── Response time < 15 seconds
│   └── ✅ TEST: Time analysis, ensure < threshold
│
├── 4.5 Documentation
│   ├── API documentation update
│   ├── Architecture diagram
│   ├── Academic report section
│   └── Demo preparation
│
└── 4.6 Evaluation Report
    ├── Test on labeled dataset
    ├── Compare: MVP vs Hybrid
    ├── Generate confusion matrix
    └── Calculate improvement metrics
```

#### End of Phase 4 Checkpoint

```
System is production-ready:
✅ All input types work
✅ All layers functional
✅ Error handling in place
✅ Tests passing
✅ Documentation complete
✅ Evaluation metrics calculated
```

---

## 📁 File Structure

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── analyze.py              # Main endpoint (update)
│   │   └── ...
│   │
│   ├── services/
│   │   ├── input/                  # NEW: Phase 1
│   │   │   ├── __init__.py
│   │   │   ├── text_handler.py     # Direct text processing
│   │   │   ├── url_scraper.py      # Article extraction
│   │   │   ├── ocr_engine.py       # Image text extraction
│   │   │   └── input_gateway.py    # Routes to appropriate handler
│   │   │
│   │   ├── nlp/                    # NEW: Phase 2
│   │   │   ├── __init__.py
│   │   │   ├── entity_extractor.py # spaCy NER
│   │   │   ├── sentiment.py        # VADER sentiment
│   │   │   ├── claim_detector.py   # ClaimBuster model
│   │   │   └── nlp_orchestrator.py # Combines all NLP
│   │   │
│   │   ├── evidence/               # ENHANCED: Phase 3
│   │   │   ├── __init__.py
│   │   │   ├── news_retriever.py   # GNews (existing, enhance)
│   │   │   ├── fact_checker.py     # Google Fact Check (existing)
│   │   │   ├── source_trust.py     # NEW: Domain trust lookup
│   │   │   └── stance_detector.py  # NEW: BART-MNLI stance
│   │   │
│   │   ├── verdict/                # NEW: Phase 3
│   │   │   ├── __init__.py
│   │   │   ├── aggregator.py       # Weighted verdict formula
│   │   │   └── llm_reasoner.py     # Gemini Chain-of-Thought
│   │   │
│   │   └── orchestrator.py         # NEW: Master pipeline
│   │
│   └── models/
│       └── loader.py               # NEW: Model singleton
│
├── data/
│   └── trusted_sources.json        # NEW: Domain trust scores
│
└── tests/
    ├── test_input_gateway.py       # Phase 1 tests
    ├── test_nlp_layer.py           # Phase 2 tests
    ├── test_stance_verdict.py      # Phase 3 tests
    └── test_e2e.py                 # Full pipeline tests
```

---

## 🔌 API Design

### Updated Analyze Endpoint

```python
# POST /api/v1/analyze

# Request
{
    "input_type": "text" | "url" | "image",
    "content": "string or base64",
    "options": {
        "deep_analysis": true,
        "include_evidence": true,
        "include_explanation": true
    }
}

# Response
{
    "id": "analysis-uuid",
    "input": {
        "type": "url",
        "original": "https://example.com/article",
        "extracted_text": "Article content...",
        "source_domain": "example.com"
    },
    
    "nlp_analysis": {
        "entities": [
            {"text": "Biden", "type": "PERSON"},
            {"text": "2024", "type": "DATE"}
        ],
        "sentiment": {
            "score": -0.3,
            "label": "slightly_negative"
        },
        "is_verifiable_claim": true,
        "claim_score": 0.87,
        "language": "en"
    },
    
    "evidence": [
        {
            "title": "Fact check: ...",
            "source": "Reuters",
            "url": "https://...",
            "trust_score": 95,
            "stance": "refutes",
            "stance_confidence": 0.89
        }
    ],
    
    "verdict": {
        "label": "LIKELY_FALSE",
        "score": -0.72,
        "confidence": 0.85,
        "supporting_sources": 1,
        "refuting_sources": 4
    },
    
    "explanation": {
        "summary": "This claim has been widely debunked...",
        "key_factors": [
            "Multiple credible sources refute this",
            "No supporting evidence from reliable outlets"
        ],
        "reasoning": "Based on the evidence gathered..."
    },
    
    "metadata": {
        "processing_time_ms": 3240,
        "models_used": ["spacy", "vader", "bart-mnli", "gemini"]
    }
}
```

---

## 🎯 Success Criteria

### Per Phase

| Phase | Success Metric |
|-------|----------------|
| **Phase 1** | All 3 input types extract text successfully |
| **Phase 2** | NLP analysis returns entities, sentiment, claim score |
| **Phase 3** | Stance detection + verdict calculation works |
| **Phase 4** | Full E2E test suite passes, accuracy > 70% |

### Final System

| Metric | Target |
|--------|--------|
| Input Types Supported | 3 (text, url, image) |
| Average Response Time | < 15 seconds |
| Verdict Accuracy (on test set) | > 70% |
| API Uptime | > 95% |
| Test Coverage | > 60% |

---

## 📚 Dependencies to Install

```bash
# NLP & ML
pip install spacy
python -m spacy download en_core_web_lg
pip install transformers torch
pip install vaderSentiment
pip install langdetect

# Input Processing
pip install trafilatura  # URL scraping
pip install easyocr      # OCR (or pytesseract)
pip install Pillow       # Image handling

# Already have
# fastapi, uvicorn, requests, etc.
```

---

## 🚀 Getting Started

After reading this plan, start with:

```bash
# Phase 1, Step 1
cd backend
pip install trafilatura easyocr

# Create the input gateway service
touch app/services/input/__init__.py
touch app/services/input/input_gateway.py
```

Then follow the phase tasks sequentially, testing each component before moving on.

---

> **Document Version:** 2.0  
> **Last Updated:** January 2026  
> **Philosophy:** Real ML pipeline, no training overhead, incremental delivery
