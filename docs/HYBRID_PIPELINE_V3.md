# 🔬 TruthLens: Multi-Stage Claim Analysis Pipeline V3

> **Document Type:** Technical Architecture & Evidence Framework  
> **Version:** 3.0 (Type-Aware Evidence System)  
> **Created:** January 2026  
> **Status:** Architecture Finalized

---

## 📋 Table of Contents

1. [Core Philosophy](#-core-philosophy)
2. [System Overview](#-system-overview)
3. [ML Model Stack](#-ml-model-stack-balanced-approach) ⭐ NEW
4. [Stage 0: Unified Input Processing](#-stage-0-unified-input-processing)
5. [Stage 1: Claim Extraction](#-stage-1-claim-extraction)
6. [Stage 2: Claim Normalization](#-stage-2-claim-normalization)
7. [Stage 3: Claim Typing](#-stage-3-claim-typing-the-fork)
8. [Deep Investigation Engine](#-deep-investigation-engine-the-evidence-backbone)
9. [Stage 4: Evidence Strategy Engine](#-stage-4-evidence-strategy-engine)
10. [Stage 5: Time-Aware Analysis](#-stage-5-time-aware-analysis)
11. [Stage 6: Output Design](#-stage-6-output-design)
12. [Implementation Phases](#-implementation-phases)
13. [Technical Specifications](#-technical-specifications)

---

## 🎯 Core Philosophy

### What This System IS

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRUTHLENS PRINCIPLES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Transparent      — Shows what was analyzed and how          │
│  ✅ Type-Aware       — Different claims need different logic    │
│  ✅ Evidence-Based   — Cites sources, not opinions              │
│  ✅ Time-Conscious   — Truth evolves, evidence has timestamps   │
│  ✅ Non-Binary       — Not just TRUE/FALSE                      │
│  ✅ Honest           — "Insufficient evidence" is valid output  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### What This System IS NOT

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRUTHLENS ANTI-PATTERNS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ❌ An opinion machine   — "The model thinks..."                │
│  ❌ A binary classifier  — TRUE/FALSE on everything             │
│  ❌ An authority         — "This is definitely true"            │
│  ❌ Type-blind           — All claims handled the same way     │
│  ❌ Time-ignorant        — Treating 2020 claim same as today's │
│  ❌ An LLM wrapper ⭐    — LLM decides truth, we just call it  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

> **⚠️ CRITICAL ARCHITECTURE DECISION**
> 
> LLM (Gemini) is used **ONLY** for:
> - Generating human-readable explanations (Stage 6)
> - Summarizing evidence in natural language
> 
> LLM is **NEVER** used for:
> - Determining verdicts
> - As evidence source
> - In investigation levels 1-4
> 
> **Verdict = Evidence Synthesis Algorithm (no LLM)**
> **Explanation = LLM (after verdict is determined)**

### The Fundamental Insight

**Different claims require different verification logic.**

If the system treats these as the same type of problem:

| Claim | Type | Evidence Required |
|-------|------|-------------------|
| "COVID vaccines cause autism" | Scientific/Medical | Peer-reviewed research, systematic reviews |
| "BJP rigged elections with ECI" | Political Allegation | Court rulings, official investigations |
| "New virus leaked yesterday" | Breaking Event | Real-time sources, confirmation pending |

**...the system is wrong by design.**

---

## 🏗️ System Overview

### The Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRUTHLENS CLAIM ANALYSIS PIPELINE             │
└─────────────────────────────────────────────────────────────────┘

 USER INPUT (Any Format)
      │
      ▼
╔═════════════════════════════════════════════════════════════════╗
║  STAGE 0: UNIFIED INPUT PROCESSING                               ║
║  • Image → OCR                                                   ║
║  • Video → Speech-to-text + Frame OCR                           ║
║  • Link → Content extraction                                     ║
║  • Social post → Text + Engagement metadata                     ║
║  OUTPUT: Text + Metadata (mechanical, no intelligence)          ║
╚═════════════════════════════════════════════════════════════════╝
      │
      ▼
╔═════════════════════════════════════════════════════════════════╗
║  STAGE 1: CLAIM EXTRACTION                                      ║
║  • Split into sentences                                         ║
║  • Filter assertive statements                                  ║
║  • Discard: Questions, opinions, emotions, rhetoric             ║
║  OUTPUT: List of raw claims (over-extract, not under-extract)   ║
╚═════════════════════════════════════════════════════════════════╝
      │
      ▼
╔═════════════════════════════════════════════════════════════════╗
║  STAGE 2: CLAIM NORMALIZATION                                    ║
║  • Different phrasings → Canonical representation               ║
║  • Enable: Deduplication, trend tracking, evidence aggregation  ║
║  OUTPUT: Normalized claims in standard format                    ║
╚═════════════════════════════════════════════════════════════════╝
      │
      ▼
╔═════════════════════════════════════════════════════════════════╗
║  STAGE 3: CLAIM TYPING ⭐ THE FORK                               ║
║  • Scientific/Medical                                            ║
║  • Factual/Historical                                            ║
║  • Political Allegation                                          ║
║  • Breaking/Emerging Event                                       ║
║  • Opinion/Value Judgment                                        ║
║  OUTPUT: Typed claims with classification confidence            ║
╚═════════════════════════════════════════════════════════════════╝
      │
      ├─────────────────┬────────────────┬─────────────────┐
      │                 │                │                 │
      ▼                 ▼                ▼                 ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ SCIENTIFIC  │ │  POLITICAL  │ │   FACTUAL   │ │  BREAKING   │
│ EVIDENCE    │ │  EVIDENCE   │ │  EVIDENCE   │ │   NEWS      │
│ STRATEGY    │ │  STRATEGY   │ │  STRATEGY   │ │  STRATEGY   │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │               │
       └───────────────┴───────────────┴───────────────┘
                              │
                              ▼
╔═════════════════════════════════════════════════════════════════╗
║  STAGE 5: TIME-AWARE ANALYSIS                                    ║
║  • Claim versioning                                              ║
║  • Evidence timestamps                                           ║
║  • Confidence over time                                          ║
║  OUTPUT: Time-contextualized assessment                          ║
╚═════════════════════════════════════════════════════════════════╝
      │
      ▼
╔═════════════════════════════════════════════════════════════════╗
║  STAGE 6: OUTPUT GENERATION                                      ║
║  • What claim was analyzed                                       ║
║  • How it was interpreted                                        ║
║  • What evidence types were used                                 ║
║  • What is known vs alleged vs unknown                          ║
║  • Confidence with justification                                 ║
║  • Date-sensitive context                                        ║
║  OUTPUT: Transparent, non-binary assessment                      ║
╚═════════════════════════════════════════════════════════════════╝
```

---

## 🤖 ML Model Stack (Balanced Approach)

> **Philosophy:** Use models where they genuinely improve results.
> Don't add models just to impress — add them because they solve real problems.

### What's Model vs API vs Rules

```
┌─────────────────────────────────────────────────────────────────┐
│               TECHNOLOGY BREAKDOWN BY STAGE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Stage 0: Input Processing                                       │
│  ├── EasyOCR ─────────────────────────── LOCAL MODEL (neural)   │
│  ├── trafilatura ─────────────────────── LIBRARY (no ML)        │
│  └── whisper (optional) ──────────────── LOCAL MODEL (audio)    │
│                                                                  │
│  Stage 1: Claim Extraction                                       │
│  ├── spaCy (en_core_web_sm) ──────────── LOCAL MODEL (NLP)      │
│  └── Assertion classifier ────────────── LOCAL MODEL (BERT)     │
│                                                                  │
│  Stage 2: Claim Normalization                                    │
│  └── sentence-transformers ───────────── LOCAL MODEL (embeddings)│
│                                                                  │
│  Stage 3: Claim Typing (THE FORK) ⭐                             │
│  └── BART-large-mnli ─────────────────── LOCAL MODEL (zero-shot)│
│                                                                  │
│  Deep Investigation Engine                                       │
│  ├── DuckDuckGo, Wikipedia, etc. ─────── EXTERNAL APIs          │
│  └── Stance detection ────────────────── LOCAL MODEL (NLI)      │
│                                                                  │
│  Stage 4: Evidence Strategy                                      │
│  └── Rule-based logic ────────────────── RULES (no ML)          │
│                                                                  │
│  Stage 5: Time-Aware Analysis                                    │
│  └── Rule-based logic ────────────────── RULES (no ML)          │
│                                                                  │
│  Stage 6: Output Generation                                      │
│  └── Gemini API ──────────────────────── EXTERNAL API (LLM)     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The 4 Core Local Models (Pre-trained, No Fine-tuning)

| Model | HuggingFace ID | Purpose | Why Needed |
|-------|----------------|---------|------------|
| **spaCy NLP** | `en_core_web_sm` | Sentence splitting, NER, POS tagging | Foundational NLP - can't extract claims without sentence boundaries |
| **BART Zero-Shot** | `facebook/bart-large-mnli` | Claim type classification | THE FORK - routes claims to different strategies. Critical. |
| **Sentence Transformers** | `all-MiniLM-L6-v2` | Claim embeddings | Deduplication, semantic search, finding similar claims |
| **Stance Detector** | `roberta-large-mnli` | Does evidence SUPPORT/REFUTE/NEUTRAL? | Without this, we can't synthesize evidence properly |

### Why Each Model is Justified

#### 1. spaCy (Claim Extraction)
```
WITHOUT: "COVID vaccines cause autism and also the weather is nice today"
         → Treated as ONE claim

WITH:    → Sentence 1: "COVID vaccines cause autism" → CHECKABLE
         → Sentence 2: "the weather is nice today" → OPINION, SKIP
```
**Verdict:** Essential. Can't do anything without sentence splitting.

---

#### 2. BART-large-mnli (Claim Typing)
```
WITHOUT: All claims go through same verification path
         → Scientific claim checked like political allegation
         → Wrong evidence strategy, wrong output

WITH:    Claim: "COVID vaccines cause autism"
         → Zero-shot classification with labels:
           ["scientific claim", "political allegation", "factual statement", ...]
         → Result: "scientific claim" (92% confidence)
         → Routes to SCIENTIFIC evidence strategy
```
**Verdict:** Critical. This IS the fork in the pipeline.

---

#### 3. Sentence Transformers (Normalization)
```
WITHOUT: 
         "Vaccines cause autism" → Search evidence
         "COVID shots lead to autism" → Search evidence AGAIN
         "Vaccination causes autism spectrum disorder" → Search evidence AGAIN
         → 3x API calls for same claim

WITH:    
         All three → embedding similarity > 0.9
         → Treat as SAME canonical claim
         → Search evidence ONCE, apply to all
```
**Verdict:** Important for efficiency and trend detection. Not critical for MVP but valuable.

---

#### 4. Stance Detection (Evidence Synthesis)
```
Evidence found:
  - Article A: "Study finds no link between vaccines and autism"
  - Article B: "Parents claim vaccine caused their child's autism"
  - Article C: "Scientific consensus rejects vaccine-autism link"

WITHOUT: Count = 3 articles. But what do they say? No idea.

WITH:    Stance detection on each:
  - Article A: REFUTES claim (confidence: 0.91)
  - Article B: SUPPORTS claim (confidence: 0.67)
  - Article C: REFUTES claim (confidence: 0.94)
  → Synthesis: 2 REFUTE (high confidence) vs 1 SUPPORT (low confidence)
  → Verdict: Strong evidence against claim
```
**Verdict:** Essential. Without stance detection, evidence is useless.

---

### What We're NOT Using (and Why)

| Model | Why Considered | Why Rejected |
|-------|----------------|--------------|
| Fine-tuned claim detector | Higher accuracy | Requires training data, time, compute |
| Multiple sentiment models | Rich emotion analysis | Overkill - VADER alone is enough if needed |
| Named Entity Linking (NEL) | Link entities to Wikidata | spaCy NER is sufficient for our use case |
| Fact verification model | End-to-end fact check | We have evidence pipeline - don't need black box |
| Multiple LLMs | Ensemble reasoning | Gemini alone is sufficient for explanation |

### Model Loading Strategy

```python
# services/models/model_manager.py

from transformers import pipeline
from sentence_transformers import SentenceTransformer
import spacy

class ModelManager:
    """
    Singleton pattern - load models ONCE, reuse everywhere
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_models()
        return cls._instance
    
    def _load_models(self):
        print("Loading models (one-time)...")
        
        # 1. spaCy for NLP
        self.nlp = spacy.load("en_core_web_sm")
        
        # 2. Zero-shot classifier for claim typing
        self.zero_shot = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1  # CPU (use 0 for GPU)
        )
        
        # 3. Sentence transformer for embeddings
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        
        # 4. NLI model for stance detection
        self.stance_detector = pipeline(
            "text-classification",
            model="roberta-large-mnli",
            device=-1
        )
        
        print("Models loaded!")
    
    def classify_claim_type(self, claim: str) -> dict:
        """Classify claim into types using zero-shot"""
        labels = [
            "scientific or medical claim",
            "political allegation",
            "factual statement about dates or numbers",
            "breaking news event",
            "opinion or value judgment",
            "quote attribution"
        ]
        result = self.zero_shot(claim, labels)
        return {
            "type": result["labels"][0],
            "confidence": result["scores"][0]
        }
    
    def get_embedding(self, text: str):
        """Get semantic embedding for similarity"""
        return self.embedder.encode(text)
    
    def detect_stance(self, premise: str, hypothesis: str) -> dict:
        """Does premise SUPPORT/REFUTE/NEUTRAL hypothesis?"""
        input_text = f"{premise} </s></s> {hypothesis}"
        result = self.stance_detector(input_text)
        return {
            "stance": result[0]["label"],  # entailment/contradiction/neutral
            "confidence": result[0]["score"]
        }

# Usage (anywhere in codebase)
models = ModelManager()  # Singleton - loads once
```

### Performance Considerations

| Model | Size | Load Time | Inference Time | Memory |
|-------|------|-----------|----------------|--------|
| spaCy (sm) | 12 MB | ~2 sec | ~10 ms | ~50 MB |
| BART-mnli | 1.6 GB | ~15 sec | ~200 ms | ~2 GB |
| MiniLM-L6 | 80 MB | ~3 sec | ~20 ms | ~200 MB |
| RoBERTa-mnli | 1.4 GB | ~12 sec | ~150 ms | ~1.8 GB |

**Total first-load time:** ~30 seconds (one-time, on server start)
**Total memory:** ~4 GB (manageable on most machines)

---

## 📥 Stage 0: Unified Input Processing

### Purpose

Reduce ALL input types to: **Text + Metadata**

This stage is purely mechanical. No intelligence yet.

### Input Types Supported

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT TYPE HANDLERS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📝 RAW TEXT                                                     │
│     └─→ Pass through (minimal cleaning)                         │
│                                                                  │
│  🔗 NEWS ARTICLE LINK                                            │
│     └─→ trafilatura extraction                                   │
│     └─→ Metadata: source domain, publish date, author           │
│                                                                  │
│  📱 SOCIAL MEDIA POST (Tweet, Instagram, Facebook)              │
│     └─→ Text extraction                                          │
│     └─→ Metadata: platform, engagement, account age             │
│                                                                  │
│  📰 BLOG / MEDIUM POST                                           │
│     └─→ Content extraction                                       │
│     └─→ Metadata: author, publication date                      │
│                                                                  │
│  🖼️ IMAGE / SCREENSHOT                                           │
│     └─→ OCR (EasyOCR / Tesseract)                               │
│     └─→ Metadata: image source if detectable                    │
│                                                                  │
│  🎥 VIDEO / REEL                                                 │
│     └─→ Speech-to-text (Whisper)                                │
│     └─→ Frame extraction + OCR                                  │
│     └─→ Metadata: duration, source platform                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Output Structure

```python
class ProcessedInput:
    text: str                    # Extracted text content
    input_type: InputType        # ENUM: TEXT, URL, IMAGE, VIDEO, SOCIAL
    source_url: Optional[str]    # Original source if available
    source_domain: Optional[str] # Domain for trust assessment
    publish_date: Optional[date] # When content was published
    extraction_confidence: float # How confident are we in extraction
    metadata: dict               # Platform-specific metadata
```

---

## 📋 Stage 1: Claim Extraction

### Purpose

From extracted text, identify **assertive statements** that can be analyzed.

### Process

```
INPUT TEXT
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: SENTENCE SEGMENTATION                                   │
│  Split text into individual sentences using spaCy               │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: STATEMENT CLASSIFICATION                                │
│  For each sentence, classify as:                                │
│  • ASSERTION (keep) — "X happened", "X causes Y"                │
│  • QUESTION (discard) — "Did X happen?"                         │
│  • OPINION (flag) — "X is good/bad"                             │
│  • RHETORIC (discard) — "Can you believe this?"                 │
│  • EMOTION (discard) — "I'm so angry about X"                   │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: CLAIM CANDIDATE FILTERING                               │
│  Keep assertions that:                                           │
│  • Make verifiable claims                                        │
│  • Reference entities, events, or facts                         │
│  • Are not purely subjective                                    │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
OUTPUT: List of Claim Candidates
```

### Guiding Principle

> **Over-extract, not under-extract.**
> False positives are acceptable here. False negatives are costly.

### Example

**Input:**
```
"BJP is stealing votes. Rahul Gandhi has proven it. Can you believe the 
audacity? BJP loses elections intentionally to fool the opposition. They 
are colluding with ECI. This makes me so angry!"
```

**Output Claims:**
```python
[
    Claim("BJP is stealing votes"),
    Claim("Rahul Gandhi has proven it"),
    Claim("BJP loses elections intentionally to fool the opposition"),
    Claim("They are colluding with ECI")
]

# Discarded:
# - "Can you believe the audacity?" → Rhetorical question
# - "This makes me so angry!" → Emotion
```

---

## 🔄 Stage 2: Claim Normalization

### Purpose

Convert different phrasings of the same claim into a **canonical representation**.

### Why This Matters

```
These are the SAME claim:
├── "Vaccines cause autism"
├── "COVID shots lead to autism"
├── "Autism caused by vaccination"
├── "Getting vaccinated gives children autism"
└── "There's a link between vaccines and autism"

Canonical form:
    COVID-19 vaccines → cause → autism
    
Structure:
    SUBJECT → RELATION → OBJECT
```

### Normalization Process

```
RAW CLAIM
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: ENTITY EXTRACTION                                       │
│  • Identify key entities (spaCy NER)                            │
│  • PERSON, ORG, GPE, EVENT, DATE                                │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: RELATION EXTRACTION                                     │
│  • Identify relationship type                                    │
│  • CAUSES, IS_A, LOCATED_IN, SAID, DID, etc.                    │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: CANONICAL FORM                                          │
│  • Standardize entity names                                      │
│  • Standardize relation type                                     │
│  • Remove stylistic variations                                   │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
NORMALIZED CLAIM TRIPLE: (Subject, Relation, Object)
```

### Benefits

```
NORMALIZATION ENABLES:

├── DEDUPLICATION
│   └── Same claim from 100 sources = 1 canonical claim
│
├── TREND TRACKING
│   └── "This claim appeared 500 times this week"
│
├── EVIDENCE AGGREGATION
│   └── All evidence for same claim pooled together
│
└── HISTORICAL MATCHING
    └── "This claim was debunked in 2020"
```

---

## 🎯 Stage 3: Claim Typing (THE FORK)

### Purpose

This is where the pipeline branches. Different claim types require **fundamentally different evidence strategies**.

### Core Claim Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAIM TYPE TAXONOMY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. SCIENTIFIC / MEDICAL                                         │
│     • Causal claims about health, medicine, biology             │
│     • Empirical claims that can be tested                       │
│     • Example: "Vaccines cause autism"                          │
│                                                                  │
│  2. FACTUAL / HISTORICAL                                         │
│     • Claims about established facts                            │
│     • Verifiable against records                                │
│     • Example: "India won the 2011 World Cup"                   │
│                                                                  │
│  3. POLITICAL ALLEGATION                                         │
│     • Claims about political actors                             │
│     • Often contested, requires legal/official sources          │
│     • Example: "BJP rigged elections"                           │
│                                                                  │
│  4. BREAKING / EMERGING EVENT                                    │
│     • Recent claims, evidence still developing                  │
│     • Requires real-time source verification                    │
│     • Example: "New virus leaked yesterday"                     │
│                                                                  │
│  5. QUOTE / STATEMENT                                            │
│     • Claims that someone said something                        │
│     • Requires source tracing                                   │
│     • Example: "Gandhi said XYZ"                                │
│                                                                  │
│  6. STATISTICAL / NUMERICAL                                      │
│     • Claims with numbers, percentages, data                    │
│     • Requires data source verification                         │
│     • Example: "Crime increased by 50%"                         │
│                                                                  │
│  7. OPINION / VALUE JUDGMENT (usually excluded)                  │
│     • Subjective claims                                          │
│     • Not fact-checkable                                         │
│     • Example: "This policy is bad for India"                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Typing Signals

```python
def classify_claim_type(claim: NormalizedClaim) -> ClaimType:
    """
    Use multiple signals to determine claim type
    """
    
    signals = {
        "has_medical_entities": check_medical_entities(claim),
        "has_causal_relation": check_causal_language(claim),
        "has_political_entities": check_political_entities(claim),
        "has_temporal_recency": check_recent_timeframe(claim),
        "has_quote_markers": check_attribution_language(claim),
        "has_statistics": check_numerical_claims(claim),
        "is_subjective": check_opinion_markers(claim),
    }
    
    # Decision logic based on signals
    if signals["is_subjective"]:
        return ClaimType.OPINION
    elif signals["has_medical_entities"] and signals["has_causal_relation"]:
        return ClaimType.SCIENTIFIC_MEDICAL
    elif signals["has_temporal_recency"]:
        return ClaimType.BREAKING_EVENT
    elif signals["has_political_entities"]:
        return ClaimType.POLITICAL_ALLEGATION
    elif signals["has_quote_markers"]:
        return ClaimType.QUOTE_STATEMENT
    elif signals["has_statistics"]:
        return ClaimType.STATISTICAL
    else:
        return ClaimType.FACTUAL_HISTORICAL
```

---

## 🔍 Deep Investigation Engine (The Evidence Backbone)

### Why This Matters

> **A fact-checking system that can't find evidence is useless.**
> 
> Surface-level searches (just news APIs) fail for 80% of claims.
> Deep investigation finds evidence where shallow searches fail.

### Zero-Cost Constraint

This system is designed for **student projects with ₹0 budget:**

| Tool | Free Tier | Limits | Use For |
|------|-----------|--------|---------|
| **DuckDuckGo Instant API** | Unlimited | No API key needed | General web search |
| **Google Custom Search** | 100 queries/day | Free tier | Structured web search |
| **SerpAPI** | 100 queries/month | Free account | Rich search results |
| **Wikimedia APIs** | Unlimited | No key needed | Wikipedia, Wikidata |
| **Archive.org Wayback** | Unlimited | Public API | Historical verification |
| **PubMed API** | Unlimited | Free | Scientific papers |
| **Semantic Scholar** | 100 requests/5min | Free | Academic research |
| **Reddit API** | 60 requests/min | Free | Discussion search |
| **Google Fact Check API** | Unlimited | API key | Existing fact-checks |

> ⚠️ **LLM (Gemini) is NOT listed here intentionally.**
> LLM is used ONLY in Stage 6 for explanation generation, NEVER for evidence or verdict.

### Investigation Depth Levels

> **CRITICAL DESIGN DECISION:**
> LLM is NOT used anywhere in investigation.
> All evidence comes from verifiable, external sources.
> This is what makes TruthLens a real pipeline, not an LLM wrapper.

```
┌─────────────────────────────────────────────────────────────────┐
│              INVESTIGATION DEPTH LEVELS                          │
│              (NO LLM - All Real Sources)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LEVEL 1: QUICK CHECK (~5 seconds)                              │
│  ├── Check OUR known misinformation database (local JSON)       │
│  ├── Query Google Fact Check API (existing fact-checks)         │
│  ├── Query Wikidata for simple factual claims                   │
│  └── STOP IF: Exact match found in database/fact-check          │
│                                                                  │
│  LEVEL 2: STANDARD SEARCH (~15 seconds)                         │
│  ├── DuckDuckGo search (web results)                            │
│  ├── Wikipedia API (encyclopedia lookup)                        │
│  ├── GNews API (news articles)                                  │
│  └── STOP IF: 3+ independent sources agree                      │
│                                                                  │
│  LEVEL 3: DEEP INVESTIGATION (~45 seconds)                      │
│  ├── PubMed search (for scientific/medical claims)              │
│  ├── Follow leads → verify at original source                  │
│  ├── Archive.org (verify historical claims)                     │
│  ├── Reddit search (find debunking threads)                     │
│  └── Cross-reference multiple sources                           │
│                                                                  │
│  LEVEL 4: FORENSIC (optional, ~90 seconds)                      │
│  ├── Reverse image search (TinEye API for image claims)         │
│  ├── Deep archive verification                                  │
│  ├── Source origin tracing                                      │
│  └── For high-stakes claims only                                │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  === VERDICT DETERMINED BY EVIDENCE SYNTHESIS ALGORITHM ===     │
│  === NO LLM INVOLVED IN VERDICT DETERMINATION ===               │
│                                                                  │
│  THEN (Stage 6):                                                 │
│  └── LLM receives: claim + evidence + verdict                  │
│  └── LLM produces: human-readable explanation only              │
│  └── LLM does NOT decide the verdict                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Smart Orchestration: When to Stop

```python
class InvestigationOrchestrator:
    """
    Smart controller that decides investigation depth dynamically
    """
    
    MAX_TIME_SECONDS = 45  # Hard limit for user experience
    
    def investigate(self, claim: TypedClaim) -> Evidence:
        start_time = time.now()
        evidence = EvidenceCollection()
        
        # LEVEL 1: Quick Check (always run)
        evidence += self.quick_check(claim)
        if self.should_stop(evidence, start_time):
            return evidence.with_depth("QUICK")
        
        # LEVEL 2: Standard Search
        evidence += self.standard_search(claim)
        if self.should_stop(evidence, start_time):
            return evidence.with_depth("STANDARD")
        
        # LEVEL 3: Deep Investigation (conditional)
        if self.needs_deep_investigation(claim, evidence):
            evidence += self.deep_investigate(claim, evidence.leads)
        
        return evidence.with_depth("DEEP")
    
    def should_stop(self, evidence: Evidence, start: datetime) -> bool:
        """Smart stopping conditions"""
        
        # Time limit exceeded
        if (time.now() - start).seconds > self.MAX_TIME_SECONDS:
            return True
        
        # Strong existing fact-check found
        if evidence.has_authoritative_factcheck():
            return True
        
        # Multiple independent sources agree strongly
        if evidence.source_agreement_score > 0.85:
            return True
        
        # Known misinformation pattern matched
        if evidence.matches_known_misinfo():
            return True
        
        return False
    
    def needs_deep_investigation(self, claim: TypedClaim, evidence: Evidence) -> bool:
        """Decide if deeper digging is warranted"""
        
        # Don't go deep for opinions
        if claim.type == ClaimType.OPINION:
            return False
        
        # Go deep if contradictory evidence
        if evidence.has_contradictions():
            return True
        
        # Go deep for scientific claims without academic sources
        if claim.type == ClaimType.SCIENTIFIC and not evidence.has_academic():
            return True
        
        # Go deep if insufficient evidence
        if evidence.confidence < 0.5:
            return True
        
        return False
```

### Investigation Layers (What Gets Searched)

```
┌─────────────────────────────────────────────────────────────────┐
│                    INVESTIGATION LAYERS                          │
└─────────────────────────────────────────────────────────────────┘

CLAIM: "WHO banned aspartame as carcinogen"
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER A: KNOWN INFORMATION (NO LLM)                             │
│                                                                  │
│  1. Known Misinformation Database (local)                       │
│     └── Check if this exact claim was debunked before          │
│     └── FREE: JSON/SQLite file we maintain                      │
│     └── Contains: Common myths, viral hoaxes, debunked claims   │
│                                                                  │
│  2. Existing Fact-Checks                                         │
│     └── Google Fact Check API                                   │
│     └── FREE: Unlimited queries                                 │
│     └── Returns: Fact-checks from verified organizations        │
│                                                                  │
│  3. Wikidata Quick Facts                                         │
│     └── Query structured knowledge base                         │
│     └── FREE: Unlimited SPARQL queries                          │
│     └── For: Simple factual claims (dates, locations, etc.)     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER B: WEB SEARCH                                             │
│                                                                  │
│  1. General Web Search                                           │
│     ├── DuckDuckGo Instant Answers API (FREE, no key)           │
│     ├── Google Custom Search (100/day free)                     │
│     └── Search: "[claim keywords] fact check"                   │
│                                                                  │
│  2. News Search                                                  │
│     ├── GNews API (existing)                                    │
│     └── Search: Recent articles about the topic                 │
│                                                                  │
│  3. Official Sources Search                                      │
│     └── Search specific domains: who.int, cdc.gov, etc.        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER C: STRUCTURED KNOWLEDGE                                   │
│                                                                  │
│  1. Wikipedia                                                    │
│     └── Wikipedia API (FREE, unlimited)                         │
│     └── Get: Article content, references                        │
│                                                                  │
│  2. Wikidata                                                     │
│     └── SPARQL queries (FREE, unlimited)                        │
│     └── Get: Structured facts about entities                    │
│                                                                  │
│  3. Domain-Specific Sources                                      │
│     ├── PubMed API (FREE) → Medical/scientific claims           │
│     ├── Semantic Scholar (FREE) → Academic papers               │
│     └── Government portals → Official announcements             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER D: VERIFICATION & TRACING                                 │
│                                                                  │
│  1. Source Verification                                          │
│     └── If claim says "WHO announced X", go to WHO.int         │
│     └── Check if announcement actually exists                   │
│                                                                  │
│  2. Origin Tracing                                               │
│     ├── Archive.org Wayback Machine (FREE)                      │
│     ├── When did this claim first appear?                       │
│     └── Who shared it first?                                    │
│                                                                  │
│  3. Quote Verification                                           │
│     └── If claim attributes quote to person                     │
│     └── Search for primary source of quote                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER E: SOCIAL & DISCUSSION (Optional)                         │
│                                                                  │
│  1. Reddit Search                                                │
│     └── Reddit API (FREE)                                       │
│     └── Find: Discussions, debunking threads                   │
│                                                                  │
│  2. Pattern Analysis                                             │
│     └── Is this claim spreading virally?                        │
│     └── What's the sentiment around it?                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
    EVIDENCE SYNTHESIS
```

### Implementation: Zero-Cost Search Functions

```python
# services/investigation/searchers.py

import requests
from typing import List, Dict

class FreeSearchers:
    """
    All search functions use FREE tier APIs only
    """
    
    # ========================================
    # DUCKDUCKGO (No API key, unlimited)
    # ========================================
    def duckduckgo_search(self, query: str) -> List[Dict]:
        """
        DuckDuckGo Instant Answer API - completely free
        """
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        results = []
        # Abstract (direct answer)
        if data.get("AbstractText"):
            results.append({
                "type": "direct_answer",
                "text": data["AbstractText"],
                "source": data.get("AbstractSource"),
                "url": data.get("AbstractURL")
            })
        
        # Related topics
        for topic in data.get("RelatedTopics", [])[:5]:
            if "Text" in topic:
                results.append({
                    "type": "related",
                    "text": topic["Text"],
                    "url": topic.get("FirstURL")
                })
        
        return results
    
    # ========================================
    # WIKIPEDIA (No API key, unlimited)
    # ========================================
    def wikipedia_search(self, query: str) -> Dict:
        """
        Wikipedia API - completely free, unlimited
        """
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        try:
            response = requests.get(f"{url}{query.replace(' ', '_')}")
            if response.status_code == 200:
                data = response.json()
                return {
                    "title": data.get("title"),
                    "extract": data.get("extract"),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
                    "type": "encyclopedia"
                }
        except:
            pass
        return None
    
    # ========================================
    # PUBMED (No API key, unlimited)
    # ========================================
    def pubmed_search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        PubMed API - free for scientific claims
        """
        # Search for article IDs
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json"
        }
        response = requests.get(search_url, params=params)
        ids = response.json().get("esearchresult", {}).get("idlist", [])
        
        if not ids:
            return []
        
        # Fetch article summaries
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json"
        }
        response = requests.get(fetch_url, params=params)
        results = response.json().get("result", {})
        
        articles = []
        for id in ids:
            if id in results:
                article = results[id]
                articles.append({
                    "title": article.get("title"),
                    "authors": article.get("authors", []),
                    "source": article.get("source"),
                    "pubdate": article.get("pubdate"),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{id}/",
                    "type": "scientific_paper"
                })
        
        return articles
    
    # ========================================
    # ARCHIVE.ORG (No API key, unlimited)
    # ========================================
    def wayback_check(self, url: str) -> Dict:
        """
        Check if URL exists in Wayback Machine - verify historical existence
        """
        api_url = f"https://archive.org/wayback/available?url={url}"
        response = requests.get(api_url)
        data = response.json()
        
        if data.get("archived_snapshots", {}).get("closest"):
            snapshot = data["archived_snapshots"]["closest"]
            return {
                "available": True,
                "archived_url": snapshot["url"],
                "timestamp": snapshot["timestamp"],
                "status": snapshot["status"]
            }
        return {"available": False}
    
    # ========================================
    # WIKIDATA (No API key, unlimited)
    # ========================================
    def wikidata_query(self, sparql_query: str) -> List[Dict]:
        """
        Query Wikidata for structured facts
        """
        url = "https://query.wikidata.org/sparql"
        headers = {"Accept": "application/json"}
        params = {"query": sparql_query}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("results", {}).get("bindings", [])
        return []
    
    # ========================================
    # REDDIT (Free tier: 60 requests/min)
    # ========================================
    def reddit_search(self, query: str, subreddit: str = None) -> List[Dict]:
        """
        Search Reddit for discussions - uses public JSON endpoints
        """
        if subreddit:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
        else:
            url = "https://www.reddit.com/search.json"
        
        params = {
            "q": query,
            "limit": 10,
            "sort": "relevance"
        }
        headers = {"User-Agent": "TruthLens/1.0"}
        
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            posts = response.json().get("data", {}).get("children", [])
            return [{
                "title": post["data"]["title"],
                "subreddit": post["data"]["subreddit"],
                "score": post["data"]["score"],
                "url": f"https://reddit.com{post['data']['permalink']}",
                "type": "discussion"
            } for post in posts[:5]]
        return []
```

### Lead Following: The Key to Deep Investigation

```python
# services/investigation/lead_follower.py

class LeadFollower:
    """
    When search finds a lead, follow it to the source
    """
    
    def follow_leads(self, evidence: Evidence) -> List[FollowedLead]:
        """
        Identify and follow promising leads from initial search
        """
        leads_to_follow = []
        
        for item in evidence.items:
            # Lead: Official source mentioned
            if self.mentions_official_source(item):
                leads_to_follow.append(
                    OfficialSourceLead(
                        mentioned_org=self.extract_org(item),
                        claim_context=item.text
                    )
                )
            
            # Lead: Document/study cited
            if self.cites_document(item):
                leads_to_follow.append(
                    DocumentLead(
                        document_name=self.extract_doc_name(item),
                        claimed_content=item.text
                    )
                )
            
            # Lead: Person quoted
            if self.has_quote_attribution(item):
                leads_to_follow.append(
                    QuoteLead(
                        attributed_to=self.extract_person(item),
                        quote=self.extract_quote(item)
                    )
                )
        
        # Follow each lead (within time budget)
        followed = []
        for lead in leads_to_follow[:3]:  # Limit to 3 leads for time
            result = self.follow(lead)
            followed.append(result)
        
        return followed
    
    def follow(self, lead: Lead) -> FollowedLead:
        """Execute the lead-following strategy"""
        
        if isinstance(lead, OfficialSourceLead):
            # Go to the official website and search
            return self.check_official_source(lead)
        
        elif isinstance(lead, DocumentLead):
            # Try to find the actual document
            return self.find_document(lead)
        
        elif isinstance(lead, QuoteLead):
            # Verify the quote attribution
            return self.verify_quote(lead)
    
    def check_official_source(self, lead: OfficialSourceLead) -> FollowedLead:
        """
        Actually go to official source and verify
        """
        org_urls = {
            "WHO": "who.int",
            "CDC": "cdc.gov",
            "ICMR": "icmr.gov.in",
            "FDA": "fda.gov",
            # Add more...
        }
        
        if lead.mentioned_org in org_urls:
            domain = org_urls[lead.mentioned_org]
            # Search within that domain using Google Custom Search
            results = self.search_within_domain(domain, lead.claim_context)
            return FollowedLead(
                original=lead,
                found=len(results) > 0,
                evidence=results,
                note=f"Searched {domain} for related announcements"
            )
        
        return FollowedLead(original=lead, found=False, note="Could not access official source")
```

### Time-Bounded Investigation

```python
# services/investigation/orchestrator.py

import asyncio
from datetime import datetime, timedelta

class TimeAwareOrchestrator:
    """
    Ensures investigation completes within acceptable time
    """
    
    def __init__(self, max_seconds: int = 45):
        self.max_seconds = max_seconds
        self.start_time = None
    
    def time_remaining(self) -> float:
        """Seconds left in budget"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return max(0, self.max_seconds - elapsed)
    
    def has_time(self, required_seconds: float = 5) -> bool:
        """Check if we have enough time for another operation"""
        return self.time_remaining() > required_seconds
    
    async def investigate_with_timeout(self, claim: TypedClaim) -> Evidence:
        """
        Run investigation with hard timeout
        """
        self.start_time = datetime.now()
        evidence = EvidenceCollection()
        
        try:
            # Run investigation with timeout
            result = await asyncio.wait_for(
                self._investigate(claim, evidence),
                timeout=self.max_seconds
            )
            return result
        except asyncio.TimeoutError:
            # Return whatever we have so far
            evidence.add_note("Investigation time limit reached")
            return evidence
    
    async def _investigate(self, claim: TypedClaim, evidence: Evidence) -> Evidence:
        """
        Progressive investigation with time checks
        """
        # Level 1: Quick checks (parallel, ~3 seconds) - NO LLM
        quick_results = await asyncio.gather(
            self.check_known_misinfo(claim),      # Our local database
            self.check_factcheck_api(claim),       # Google Fact Check API
            self.wikidata_quick_check(claim),      # Wikidata for simple facts
            return_exceptions=True
        )
        evidence.add_all(quick_results)
        
        # Early exit if sufficient
        if evidence.is_sufficient() or not self.has_time(10):
            return evidence
        
        # Level 2: Web search (parallel, ~8 seconds)
        search_results = await asyncio.gather(
            self.duckduckgo_search(claim),
            self.wikipedia_search(claim),
            self.news_search(claim),
            return_exceptions=True
        )
        evidence.add_all(search_results)
        
        # Early exit if sufficient
        if evidence.is_sufficient() or not self.has_time(15):
            return evidence
        
        # Level 3: Deep investigation (sequential, uses remaining time)
        if self.has_time(15):
            leads = evidence.extract_leads()
            for lead in leads[:2]:  # Max 2 leads
                if not self.has_time(5):
                    break
                result = await self.follow_lead(lead)
                evidence.add(result)
        
        return evidence
```

### Evidence Synthesis

```python
# services/investigation/synthesizer.py

class EvidenceSynthesizer:
    """
    Combine all evidence into coherent assessment
    """
    
    def synthesize(self, evidence: EvidenceCollection) -> Synthesis:
        """
        Weight and combine evidence from all sources
        """
        
        # Group by source type
        factchecks = evidence.filter(type="factcheck")
        official = evidence.filter(type="official_source")
        academic = evidence.filter(type="scientific_paper")
        news = evidence.filter(type="news")
        discussions = evidence.filter(type="discussion")
        
        # Calculate weighted consensus
        weighted_score = 0
        total_weight = 0
        
        # Authoritative sources get highest weight
        for item in factchecks:
            weight = 1.0  # Fact-checks are definitive
            weighted_score += weight * item.stance_score
            total_weight += weight
        
        for item in official:
            weight = 0.9  # Official sources very reliable
            weighted_score += weight * item.stance_score
            total_weight += weight
        
        for item in academic:
            weight = 0.85  # Academic papers reliable
            weighted_score += weight * item.stance_score
            total_weight += weight
        
        for item in news:
            weight = item.source_trust * 0.7  # News weighted by trust
            weighted_score += weight * item.stance_score
            total_weight += weight
        
        for item in discussions:
            weight = 0.2  # Discussions are informative but not authoritative
            # Don't add to score, just note sentiment
        
        # Final consensus
        if total_weight > 0:
            consensus_score = weighted_score / total_weight
        else:
            consensus_score = 0  # No evidence
        
        return Synthesis(
            consensus_score=consensus_score,  # -1 to +1
            evidence_strength=self.calculate_strength(evidence),
            source_diversity=self.calculate_diversity(evidence),
            key_sources=self.extract_key_sources(evidence),
            contradictions=self.find_contradictions(evidence),
            gaps=self.identify_gaps(evidence)
        )
```

### Investigation Output

```python
# What the investigation engine returns

class InvestigationResult:
    # Investigation metadata
    depth_reached: str  # "QUICK", "STANDARD", "DEEP"
    time_taken_seconds: float
    sources_checked: int
    leads_followed: int
    
    # Evidence found
    evidence_items: List[EvidenceItem]
    synthesis: Synthesis
    
    # For transparency
    search_queries_used: List[str]
    sources_consulted: List[str]
    limitations: List[str]  # "Could not access X", "No results for Y"
    
    # Ready for next stage
    def to_evidence_for_strategy(self) -> Evidence:
        """Format evidence for claim-type-specific strategy"""
        return Evidence(
            items=self.evidence_items,
            synthesis=self.synthesis,
            metadata=self.get_metadata()
        )
```

---

## ⚖️ Stage 4: Evidence Strategy Engine

### The Critical Insight

> **Each claim type has its own rules for what constitutes valid evidence.**
>
> The Deep Investigation Engine (above) gathers evidence.
> The Evidence Strategy Engine interprets it according to claim type.

### Evidence Strategy by Claim Type

---

#### 4.1 SCIENTIFIC / MEDICAL Claims

**Example:** "COVID vaccines cause autism"

```
┌─────────────────────────────────────────────────────────────────┐
│  SCIENTIFIC CLAIM EVIDENCE STRATEGY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EVIDENCE SOURCES (Priority Order):                             │
│  1. Peer-reviewed research papers                               │
│  2. Systematic reviews and meta-analyses                        │
│  3. Public health institutions (WHO, CDC, ICMR)                 │
│  4. Scientific consensus statements                             │
│  5. Longitudinal studies                                        │
│                                                                  │
│  EVIDENCE RULES:                                                 │
│  • Single study ≠ proof                                         │
│  • Consensus of studies matters                                 │
│  • Retracted papers are negative evidence                       │
│  • Source credibility weighted by impact factor                 │
│                                                                  │
│  OUTPUT STYLE:                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Status: Contradicted by strong scientific consensus     │    │
│  │ Evidence strength: Very high                            │    │
│  │ Credible support: None                                  │    │
│  │ Pattern: Long-running, repeatedly debunked              │    │
│  │ Confidence: Very high                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

#### 4.2 POLITICAL ALLEGATION Claims

**Example:** "BJP government is doing vote theft with ECI collusion"

```
┌─────────────────────────────────────────────────────────────────┐
│  POLITICAL ALLEGATION EVIDENCE STRATEGY                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EVIDENCE SOURCES (Priority Order):                             │
│  1. Court rulings and legal findings                            │
│  2. Official investigations (CBI, EC, etc.)                     │
│  3. Independent election observers                              │
│  4. Constitutional authority findings                           │
│  5. Documented evidence (not just allegations)                  │
│                                                                  │
│  EVIDENCE RULES:                                                 │
│  • Allegations by political actors ≠ evidence                   │
│  • High social volume ≠ truth                                   │
│  • Emotional certainty ≠ factual certainty                      │
│  • Polarized discourse requires caution                         │
│                                                                  │
│  SOCIAL SIGNAL ANALYSIS (informative but not conclusive):       │
│  • Repetition patterns                                          │
│  • Ideological clustering                                       │
│  • Emotional intensity                                          │
│  • Contradictory narratives from different sides                │
│                                                                  │
│  OUTPUT STYLE:                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Status: Unverified political allegation                 │    │
│  │ Source of claim: Political statements                   │    │
│  │ Independent verification: Not established               │    │
│  │ Legal status: Disputed / under review                   │    │
│  │ Evidence strength: Insufficient to confirm              │    │
│  │ Confidence: Low                                         │    │
│  │                                                         │    │
│  │ NOTE: This is not debunked. It is not verified.        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

#### 4.3 FACTUAL / HISTORICAL Claims

**Example:** "India won the 2011 World Cup"

```
┌─────────────────────────────────────────────────────────────────┐
│  FACTUAL CLAIM EVIDENCE STRATEGY                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EVIDENCE SOURCES:                                               │
│  1. Wikidata / Wikipedia (structured knowledge)                 │
│  2. Official records                                            │
│  3. Established reference sources                               │
│  4. Multiple independent confirmations                          │
│                                                                  │
│  VERIFICATION METHOD:                                            │
│  • Query structured knowledge bases                             │
│  • Compare claimed value vs actual value                        │
│  • DETERMINISTIC verification possible                          │
│                                                                  │
│  OUTPUT STYLE:                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Status: Verified as TRUE                                │    │
│  │ Source: Wikidata, ICC Records                           │    │
│  │ Confidence: Very high                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

#### 4.4 BREAKING / EMERGING EVENT Claims

**Example:** "New virus leaked from lab yesterday"

```
┌─────────────────────────────────────────────────────────────────┐
│  BREAKING EVENT EVIDENCE STRATEGY                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EVIDENCE SOURCES:                                               │
│  1. Wire services (Reuters, AP, AFP)                            │
│  2. Multiple independent news sources                           │
│  3. Official statements (if available)                          │
│  4. On-ground reports                                           │
│                                                                  │
│  EVIDENCE RULES:                                                 │
│  • Recency of evidence matters critically                       │
│  • Single source = unconfirmed                                  │
│  • Breaking news often contains errors                          │
│  • Must mark as "developing"                                    │
│                                                                  │
│  OUTPUT STYLE:                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Status: DEVELOPING / UNCONFIRMED                        │    │
│  │ First reported: [timestamp]                             │    │
│  │ Confirmed by: [list sources or "single source only"]   │    │
│  │ Last updated: [timestamp]                               │    │
│  │ Confidence: Low (breaking story)                        │    │
│  │                                                         │    │
│  │ NOTE: This assessment may change as facts emerge.      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

#### 4.5 QUOTE / STATEMENT Claims

**Example:** "Gandhi said 'Be the change you wish to see'"

```
┌─────────────────────────────────────────────────────────────────┐
│  QUOTE VERIFICATION STRATEGY                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EVIDENCE SOURCES:                                               │
│  1. Primary source documents                                    │
│  2. Verified transcripts                                        │
│  3. Academic citations with sources                             │
│  4. Wikiquote (with source checking)                            │
│                                                                  │
│  VERIFICATION METHOD:                                            │
│  • Trace to original source                                     │
│  • Check for alterations or paraphrasing                        │
│  • Verify speaker attribution                                   │
│                                                                  │
│  OUTPUT STYLE:                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Status: MISATTRIBUTED / ALTERED / VERIFIED              │    │
│  │ Actual source: [if found]                               │    │
│  │ Original quote: [if different]                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

#### 4.6 STATISTICAL / NUMERICAL Claims

**Example:** "Crime in Delhi increased by 50% this year"

```
┌─────────────────────────────────────────────────────────────────┐
│  STATISTICAL CLAIM STRATEGY                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EVIDENCE SOURCES:                                               │
│  1. Official statistics (government data)                       │
│  2. Published datasets                                          │
│  3. Research reports with methodology                           │
│                                                                  │
│  VERIFICATION CHECKS:                                            │
│  • Is the statistic accurate?                                   │
│  • Is it taken out of context?                                  │
│  • Is the comparison valid?                                     │
│  • Is the timeframe correctly stated?                           │
│                                                                  │
│  OUTPUT STYLE:                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Status: ACCURATE / MISLEADING / LACKS CONTEXT           │    │
│  │ Actual figure: [from official source]                   │    │
│  │ Context: [what's missing from the claim]                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

#### 4.7 OPINION / VALUE JUDGMENT

**Example:** "This policy is destroying India's economy"

```
┌─────────────────────────────────────────────────────────────────┐
│  OPINION HANDLING STRATEGY                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ACTION: Flag and exclude from fact-checking                    │
│                                                                  │
│  OUTPUT STYLE:                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Status: NOT FACT-CHECKABLE (Opinion/Value Judgment)     │    │
│  │ Reason: This is a subjective assessment, not a          │    │
│  │         verifiable factual claim.                        │    │
│  │                                                         │    │
│  │ Different perspectives exist on this topic.             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⏰ Stage 5: Time-Aware Analysis

### Core Principle

> **Truth is not static. Claims exist on timelines.**

### Temporal States of Claims

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAIM TEMPORAL STATES                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STABILIZED                                                      │
│  └── Strong consensus reached, unlikely to change               │
│  └── Example: "Vaccines cause autism" (debunked for decades)    │
│                                                                  │
│  UNDER INVESTIGATION                                             │
│  └── Evidence being gathered, outcome uncertain                 │
│  └── Example: Court cases in progress                           │
│                                                                  │
│  DEVELOPING                                                      │
│  └── Breaking story, facts still emerging                       │
│  └── Example: "New variant detected yesterday"                  │
│                                                                  │
│  HISTORICALLY CONTESTED                                          │
│  └── Long-term disagreement, no resolution expected             │
│  └── Example: Political allegations during elections            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Time Metadata

```python
class TemporalContext:
    claim_first_seen: datetime        # When was this claim first detected
    evidence_timestamps: List[datetime] # When was each piece of evidence from
    last_updated: datetime            # When did we last check
    stability_score: float            # How stable is the evidence (0-1)
    temporal_state: TemporalState     # STABILIZED, DEVELOPING, etc.
    
    # For trending detection
    mention_velocity: float           # Rate of new mentions
    geographic_spread: List[str]      # Where is it spreading
```

---

## 📤 Stage 6: Output Design

### Core Principle

> **The system never says:**
> - "True"
> - "False"  
> - "People say"
> - "The model thinks"
>
> **It always shows:**
> - What claim was analyzed
> - How it was interpreted
> - What evidence types were used
> - What is known vs alleged vs unknown
> - Confidence with justification
> - Date-sensitive context

### Output Structure

```python
class ClaimAssessment:
    # What was analyzed
    original_input: str
    normalized_claim: NormalizedClaim
    claim_type: ClaimType
    
    # Evidence used
    evidence_strategy: str                 # Which strategy was applied
    evidence_sources: List[EvidenceSource] # What sources were consulted
    evidence_summary: str                  # Human-readable summary
    
    # Assessment
    status: AssessmentStatus  # See below
    confidence: float
    confidence_justification: str
    
    # Time context
    temporal_context: TemporalContext
    assessment_date: datetime
    may_change: bool  # Flag if developing situation
    
    # Transparency
    decision_path: str  # How we reached this conclusion
    limitations: List[str]  # What we couldn't verify
```

### Assessment Status Values

```
┌─────────────────────────────────────────────────────────────────┐
│                    ASSESSMENT STATUS OPTIONS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FOR FACTUAL CLAIMS:                                             │
│  • VERIFIED_TRUE — Confirmed by reliable sources                │
│  • VERIFIED_FALSE — Contradicted by reliable sources            │
│  • MOSTLY_TRUE — True with minor inaccuracies                   │
│  • MOSTLY_FALSE — False with minor accuracies                   │
│  • MISLEADING — Technically true but deceptive context          │
│  • LACKS_CONTEXT — Missing important details                    │
│                                                                  │
│  FOR UNCERTAIN CLAIMS:                                           │
│  • UNVERIFIED — Insufficient evidence to determine              │
│  • DISPUTED — Credible sources disagree                         │
│  • UNDER_INVESTIGATION — Official inquiry ongoing               │
│  • DEVELOPING — Breaking story, evidence emerging               │
│                                                                  │
│  FOR SPECIAL CASES:                                              │
│  • NOT_CHECKABLE — Opinion, prediction, or subjective           │
│  • SATIRE_PARODY — Intentionally fictional                      │
│  • OUTDATED — Was true/false but circumstances changed          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Example Output: Scientific Claim

```json
{
  "claim": "COVID-19 vaccines cause autism",
  "claim_type": "SCIENTIFIC_MEDICAL",
  
  "assessment": {
    "status": "VERIFIED_FALSE",
    "status_explanation": "Contradicted by strong scientific consensus",
    "confidence": 0.97,
    "confidence_justification": "Decades of research, multiple systematic reviews, no credible supporting evidence"
  },
  
  "evidence": {
    "strategy_used": "Scientific/Medical claim verification",
    "sources_consulted": [
      {"type": "systematic_review", "source": "Cochrane Library", "finding": "No link found"},
      {"type": "public_health", "source": "WHO", "finding": "No evidence of link"},
      {"type": "longitudinal_study", "count": 12, "finding": "No association"}
    ],
    "supporting_evidence": "None from credible sources",
    "contradicting_evidence": "Strong, consistent, global"
  },
  
  "context": {
    "pattern": "Long-running misinformation, repeatedly debunked since 1998",
    "origin": "Retracted 1998 Wakefield study",
    "temporal_state": "STABILIZED",
    "note": "This claim persists despite overwhelming contrary evidence"
  },
  
  "transparency": {
    "decision_path": "Claim classified as medical/causal → Applied scientific evidence standards → Found strong consensus against claim → Marked as verified false",
    "limitations": []
  }
}
```

### Example Output: Political Allegation

```json
{
  "claim": "BJP government is doing vote theft with ECI collusion",
  "claim_type": "POLITICAL_ALLEGATION",
  
  "assessment": {
    "status": "UNVERIFIED",
    "status_explanation": "Political allegation without independent verification",
    "confidence": 0.30,
    "confidence_justification": "No court rulings, no official investigation findings, high partisan polarization"
  },
  
  "evidence": {
    "strategy_used": "Political allegation verification",
    "sources_consulted": [
      {"type": "court_rulings", "finding": "No ruling confirming the allegation"},
      {"type": "official_investigation", "finding": "No public findings available"},
      {"type": "election_observers", "finding": "No reports of systematic fraud"}
    ],
    "claim_source": "Political statements from opposition parties",
    "independent_verification": "Not established"
  },
  
  "social_context": {
    "mention_volume": "High",
    "ideological_clustering": "Strong",
    "emotional_intensity": "Very high",
    "contradictory_narratives": true,
    "note": "These signals indicate polarized discourse, not factual validity"
  },
  
  "transparency": {
    "decision_path": "Claim classified as political allegation → Applied political evidence standards → Found no authoritative confirmation → Marked as unverified",
    "limitations": [
      "Cannot access sealed court proceedings",
      "Official investigations may not be public"
    ],
    "important_note": "This is NOT marked as false. It is marked as unverified. The system does not have evidence to confirm or deny this allegation."
  }
}
```

---

## 📅 Implementation Phases

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION ROADMAP                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PHASE 1: Input & Extraction (Week 1-2)                         │
│  ├── Stage 0: Unified input processing                          │
│  └── Stage 1: Claim extraction                                   │
│                                                                  │
│  PHASE 2: Normalization & Typing (Week 2-3)                     │
│  ├── Stage 2: Claim normalization                               │
│  └── Stage 3: Claim type classification                         │
│                                                                  │
│  PHASE 3: Evidence Strategies (Week 3-5)                        │
│  ├── Stage 4a: Factual claim verification (Wikidata)            │
│  ├── Stage 4b: Scientific claim strategy                        │
│  ├── Stage 4c: Political claim strategy                         │
│  └── Stage 4d: Breaking news strategy                           │
│                                                                  │
│  PHASE 4: Output & Polish (Week 5-6)                            │
│  ├── Stage 5: Time-aware context                                │
│  ├── Stage 6: Output generation                                 │
│  └── Testing & documentation                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Specifications

### Dependencies

```bash
# NLP & Extraction
spacy
transformers
easyocr
trafilatura
langdetect

# Knowledge Bases
SPARQLWrapper  # For Wikidata queries
wikipedia-api

# ML Models (pre-trained)
sentence-transformers  # For semantic similarity
# Use: facebook/bart-large-mnli for claim classification
# Use: spacy en_core_web_lg for NER

# APIs
google-api-python-client  # Fact Check API
gnews  # News retrieval
```

### File Structure

```
backend/app/services/
├── input/
│   ├── gateway.py              # Routes input to handlers
│   ├── text_handler.py
│   ├── url_scraper.py
│   ├── ocr_engine.py
│   └── video_processor.py
│
├── extraction/
│   ├── claim_extractor.py      # Stage 1
│   ├── sentence_classifier.py  # Assertion vs Question vs Opinion
│   └── entity_extractor.py
│
├── normalization/
│   ├── normalizer.py           # Stage 2
│   ├── canonical_form.py
│   └── deduplicator.py
│
├── typing/
│   ├── claim_classifier.py     # Stage 3
│   └── type_signals.py
│
├── evidence/
│   ├── strategy_router.py      # Routes to correct strategy
│   ├── scientific_strategy.py
│   ├── political_strategy.py
│   ├── factual_strategy.py
│   ├── breaking_strategy.py
│   └── sources/
│       ├── wikidata.py
│       ├── news_apis.py
│       └── fact_checkers.py
│
├── temporal/
│   ├── time_context.py         # Stage 5
│   └── claim_history.py
│
├── output/
│   ├── assessment_generator.py # Stage 6
│   └── explanation_builder.py
│
└── orchestrator.py             # Master pipeline
```

---

## 🎯 Summary

This is a **serious system** that:

1. **Classifies claims early** — Different types get different treatment
2. **Applies appropriate evidence standards** — Scientific claims need scientific evidence, political claims need legal/official evidence
3. **Is honest about uncertainty** — "Unverified" is a valid, respectable output
4. **Shows its work** — Transparent about what was checked and how
5. **Respects time** — Acknowledges that evidence evolves
6. **Avoids false confidence** — Never claims authority it doesn't have

> **Anything simpler will either lie confidently or collapse under scrutiny.**

---

> **Document Version:** 3.0  
> **Created:** January 2026  
> **Status:** Architecture Finalized, Ready for Implementation
