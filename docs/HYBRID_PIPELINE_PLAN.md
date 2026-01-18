# 🔬 TruthLens: Hybrid Analysis Pipeline - Implementation Plan

> **Document Type:** Technical Architecture & Implementation Roadmap  
> **Version:** 2.0 (Academic Enhancement)  
> **Created:** January 2026  
> **Author:** Team TruthLens (Shivam, Harsh, Uday)

---

## 📋 Table of Contents

1. [Executive Summary](#-executive-summary)
2. [Current vs Proposed Architecture](#-current-vs-proposed-architecture)
3. [Hybrid Pipeline Architecture](#-hybrid-pipeline-architecture)
4. [Layer-by-Layer Deep Dive](#-layer-by-layer-deep-dive)
5. [Technology Stack](#-technology-stack)
6. [Implementation Phases](#-implementation-phases)
7. [Data & Training Requirements](#-data--training-requirements)
8. [Evaluation Framework](#-evaluation-framework)
9. [File Structure](#-file-structure)
10. [API Design](#-api-design)
11. [Timeline](#-timeline)

---

## 📌 Executive Summary

### What We're Building

A **5-layer hybrid misinformation detection system** that combines:
- Traditional NLP techniques (solid foundation)
- Pre-trained transformer models (state-of-the-art)
- External knowledge bases (fact verification)
- LLM reasoning (natural explanations)
- Explainability layer (academic rigor)

### Why Hybrid?

| Approach | Pros | Cons |
|----------|------|------|
| Pure API (Current MVP) | Fast, easy | No learning, black box |
| Pure ML | Interpretable | Limited accuracy |
| Pure Deep Learning | High accuracy | Needs lots of data |
| **Hybrid (Our Choice)** | Best of all worlds | Slightly complex |

---

## 🔄 Current vs Proposed Architecture

### ❌ Current MVP (Shortcut Version)

```
User Input
    │
    ▼
┌─────────────────────┐
│  Google Fact Check  │ ──► Returns existing fact-checks only
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│     GNews API       │ ──► Just finds related news
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│   Gemini Prompt     │ ──► Summarizes without verification
└─────────────────────┘
    │
    ▼
   Result

Problems:
❌ No real verification of new claims
❌ Relies entirely on external fact-checkers
❌ No trained models (nothing learned)
❌ No explainability
```

### ✅ Proposed Hybrid Pipeline

```
User Input (Claim/Article/URL)
    │
    ▼
╔═══════════════════════════════════════════════════════════════╗
║  LAYER 1: NLP PREPROCESSING & CLAIM EXTRACTION                ║
║  ┌─────────────────────────────────────────────────────────┐  ║
║  │ • spaCy NER (entities: people, orgs, dates)            │  ║
║  │ • Claim Detection (fine-tuned DistilBERT)              │  ║
║  │ • Sentiment Analysis (TextBlob/VADER)                  │  ║
║  │ • Linguistic Features (readability, subjectivity)      │  ║
║  └─────────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════╝
    │
    ▼
╔═══════════════════════════════════════════════════════════════╗
║  LAYER 2: KNOWLEDGE VERIFICATION                              ║
║  ┌─────────────────────────────────────────────────────────┐  ║
║  │ • Wikidata SPARQL queries (verify facts)               │  ║
║  │ • Google Knowledge Graph API                            │  ║
║  │ • Domain WHOIS lookup (site credibility)               │  ║
║  │ • Known fact-checker database                           │  ║
║  └─────────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════╝
    │
    ▼
╔═══════════════════════════════════════════════════════════════╗
║  LAYER 3: EVIDENCE RETRIEVAL & STANCE DETECTION               ║
║  ┌─────────────────────────────────────────────────────────┐  ║
║  │ • Semantic Search (Sentence-BERT embeddings)           │  ║
║  │ • Multi-source news retrieval (GNews, NewsAPI)         │  ║
║  │ • Stance Classification (fine-tuned RoBERTa)           │  ║
║  │   └─► SUPPORTS | REFUTES | DISCUSSES | UNRELATED       │  ║
║  └─────────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════╝
    │
    ▼
╔═══════════════════════════════════════════════════════════════╗
║  LAYER 4: VERDICT AGGREGATION & LLM REASONING                 ║
║  ┌─────────────────────────────────────────────────────────┐  ║
║  │ • Weighted voting (source credibility × stance)        │  ║
║  │ • Confidence scoring                                    │  ║
║  │ • Chain-of-Thought prompting (Gemini)                  │  ║
║  │ • Self-consistency checking                             │  ║
║  └─────────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════╝
    │
    ▼
╔═══════════════════════════════════════════════════════════════╗
║  LAYER 5: EXPLAINABILITY & OUTPUT                             ║
║  ┌─────────────────────────────────────────────────────────┐  ║
║  │ • LIME explanations (word importance)                  │  ║
║  │ • Decision path visualization                           │  ║
║  │ • Confidence breakdown                                  │  ║
║  │ • Human-readable report                                 │  ║
║  └─────────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════╝
    │
    ▼
   Final Verdict + Explanation + Evidence
```

---

## 🏗️ Hybrid Pipeline Architecture

### System Architecture Diagram

```
                              ┌──────────────────────────────────────┐
                              │           USER INTERFACE             │
                              │        (React + TypeScript)          │
                              └──────────────────┬───────────────────┘
                                                 │
                                                 ▼
                              ┌──────────────────────────────────────┐
                              │            API GATEWAY               │
                              │            (FastAPI)                 │
                              └──────────────────┬───────────────────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────────┐
                    │                            │                            │
                    ▼                            ▼                            ▼
        ┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
        │  NLP Processor    │      │  Knowledge Base   │      │  ML Models        │
        │  (spaCy + NLTK)   │      │  (Wikidata, etc)  │      │  (HuggingFace)    │
        └─────────┬─────────┘      └─────────┬─────────┘      └─────────┬─────────┘
                  │                          │                          │
                  └──────────────────────────┼──────────────────────────┘
                                             │
                                             ▼
                              ┌──────────────────────────────────────┐
                              │         ORCHESTRATOR SERVICE         │
                              │    (Combines all layer results)      │
                              └──────────────────┬───────────────────┘
                                                 │
                                                 ▼
                              ┌──────────────────────────────────────┐
                              │          LLM REASONING               │
                              │       (Gemini 2.5 Flash)             │
                              └──────────────────┬───────────────────┘
                                                 │
                                                 ▼
                              ┌──────────────────────────────────────┐
                              │           EXPLAINABILITY             │
                              │          (LIME + SHAP)               │
                              └──────────────────┬───────────────────┘
                                                 │
                                                 ▼
                              ┌──────────────────────────────────────┐
                              │             DATABASE                 │
                              │           (PostgreSQL)               │
                              └──────────────────────────────────────┘
```

---

## 🔍 Layer-by-Layer Deep Dive

### Layer 1: NLP Preprocessing & Claim Extraction

**Purpose:** Extract structured information from raw text input

```python
# Components
├── ClaimDetector
│   ├── Input: Raw text or URL
│   ├── Model: Fine-tuned DistilBERT
│   ├── Output: List of verifiable claims
│   └── Training: ClaimBuster dataset
│
├── EntityExtractor
│   ├── Input: Text
│   ├── Model: spaCy en_core_web_lg
│   ├── Output: Named entities (PERSON, ORG, DATE, GPE)
│   └── Purpose: Identify what/who the claim is about
│
├── SentimentAnalyzer
│   ├── Input: Text
│   ├── Model: VADER / TextBlob
│   ├── Output: Sentiment score (-1 to +1)
│   └── Purpose: Highly emotional = suspicious
│
└── LinguisticAnalyzer
    ├── Input: Text
    ├── Features:
    │   ├── Readability (Flesch-Kincaid)
    │   ├── Subjectivity score
    │   ├── Use of superlatives ("BEST", "WORST")
    │   └── Presence of sensational words
    └── Purpose: Detect clickbait patterns
```

**Sample Code Structure:**

```python
# backend/app/services/nlp/claim_detector.py

class ClaimDetector:
    def __init__(self):
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "./models/claim_detector"
        )
        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    
    def detect_claims(self, text: str) -> List[Claim]:
        """
        Identify verifiable claims in text.
        Returns list of claims with confidence scores.
        """
        sentences = self._split_sentences(text)
        claims = []
        
        for sentence in sentences:
            score = self._get_claim_score(sentence)
            if score > 0.7:  # Threshold
                claims.append(Claim(
                    text=sentence,
                    confidence=score,
                    entities=self._extract_entities(sentence)
                ))
        
        return claims
```

---

### Layer 2: Knowledge Verification

**Purpose:** Verify factual claims against structured knowledge bases

```python
# Components
├── WikidataVerifier
│   ├── Input: Entity + Claim
│   ├── Method: SPARQL queries
│   ├── Output: VERIFIED | CONTRADICTED | UNKNOWN
│   └── Example: "Narendra Modi is PM of India" → VERIFIED
│
├── DomainAnalyzer
│   ├── Input: URL
│   ├── Checks:
│   │   ├── WHOIS age (older = more trustworthy)
│   │   ├── SSL certificate
│   │   ├── Known fact-checker list
│   │   └── Traffic ranking (Alexa)
│   └── Output: Trust score (0-100)
│
└── KnowledgeGraphChecker
    ├── Input: Entity
    ├── API: Google Knowledge Graph
    ├── Output: Entity facts and relationships
    └── Purpose: Verify entity claims
```

**Wikidata Query Example:**

```sparql
# Verify: "Joe Biden is the President of USA"
SELECT ?person ?personLabel ?position ?positionLabel WHERE {
  ?person wdt:P31 wd:Q5.                    # Instance of human
  ?person wdt:P39 ?position.                # Position held
  ?position wdt:P31 wd:Q30461.              # Instance of head of state
  ?person rdfs:label "Joe Biden"@en.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

---

### Layer 3: Evidence Retrieval & Stance Detection

**Purpose:** Find related articles and determine their stance toward the claim

```python
# Components
├── SemanticSearcher
│   ├── Input: Claim text
│   ├── Model: Sentence-BERT (all-MiniLM-L6-v2)
│   ├── Method: Cosine similarity with news embeddings
│   └── Output: Top-K relevant articles
│
├── MultiSourceRetriever
│   ├── Sources:
│   │   ├── GNews API
│   │   ├── NewsAPI
│   │   ├── Google Fact Check API
│   │   └── Cached verified news
│   └── Output: List of articles with metadata
│
└── StanceClassifier
    ├── Input: (Claim, Article) pair
    ├── Model: Fine-tuned RoBERTa on FNC-1 dataset
    ├── Output:
    │   ├── AGREE (article supports claim)
    │   ├── DISAGREE (article refutes claim)
    │   ├── DISCUSS (article mentions but neutral)
    │   └── UNRELATED (no connection)
    └── Confidence: 0.0 to 1.0
```

**Stance Classification Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    STANCE CLASSIFIER                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input: [CLS] Claim [SEP] Article Headline + Body [SEP]    │
│                          │                                  │
│                          ▼                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              RoBERTa Encoder                          │ │
│  │                                                       │ │
│  │  Claim: "COVID vaccines are safe"                     │ │
│  │  Article: "WHO confirms vaccine safety after trials"  │ │
│  │                                                       │ │
│  │           ┌──────────────────────┐                    │ │
│  │           │  [CLS] embedding     │                    │ │
│  │           └──────────┬───────────┘                    │ │
│  │                      │                                │ │
│  │                      ▼                                │ │
│  │           ┌──────────────────────┐                    │ │
│  │           │  Classification Head │                    │ │
│  │           │  (Linear + Softmax)  │                    │ │
│  │           └──────────┬───────────┘                    │ │
│  │                      │                                │ │
│  │                      ▼                                │ │
│  │     ┌────────┬────────┬──────────┬───────────┐       │ │
│  │     │ AGREE  │DISAGREE│ DISCUSS  │ UNRELATED │       │ │
│  │     │  0.85  │  0.05  │   0.08   │    0.02   │       │ │
│  │     └────────┴────────┴──────────┴───────────┘       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Output: AGREE (confidence: 0.85)                          │
└─────────────────────────────────────────────────────────────┘
```

---

### Layer 4: Verdict Aggregation & LLM Reasoning

**Purpose:** Combine all evidence into a final verdict with reasoning

```python
# Verdict Calculation Formula

verdict_score = Σ (source_trust × stance_weight × confidence)
                ─────────────────────────────────────────────
                           Σ (source_trust)

# Where:
# stance_weight:
#   AGREE = +1.0
#   DISAGREE = -1.0
#   DISCUSS = 0.0
#   UNRELATED = 0.0 (excluded)

# Example:
sources = [
    {"trust": 90, "stance": "DISAGREE", "confidence": 0.95},  # Reuters
    {"trust": 85, "stance": "DISAGREE", "confidence": 0.88},  # BBC
    {"trust": 30, "stance": "AGREE", "confidence": 0.70},     # Unknown blog
]

# Calculation:
# (90 × -1.0 × 0.95) + (85 × -1.0 × 0.88) + (30 × 1.0 × 0.70)
# ─────────────────────────────────────────────────────────────
#                        (90 + 85 + 30)
# = (-85.5 - 74.8 + 21) / 205
# = -139.3 / 205
# = -0.68 → Likely FALSE
```

**LLM Chain-of-Thought Prompt:**

```python
REASONING_PROMPT = """
You are a fact-checking expert analyzing a claim.

CLAIM: {claim}

EVIDENCE GATHERED:
{evidence_list}

STANCE ANALYSIS:
- Supporting sources: {agree_count}
- Refuting sources: {disagree_count}
- Neutral sources: {discuss_count}

KNOWLEDGE BASE CHECK:
{knowledge_result}

Based on this evidence, analyze step-by-step:

1. What is the core factual assertion?
2. What do high-credibility sources say?
3. Is there consensus among sources?
4. Are there any red flags (emotional language, no citations)?
5. What is the most likely verdict?

Provide your reasoning, then conclude with:
VERDICT: [TRUE / FALSE / PARTIALLY TRUE / UNVERIFIABLE]
CONFIDENCE: [0-100%]
"""
```

---

### Layer 5: Explainability & Output

**Purpose:** Make the decision transparent and understandable

```python
# Components
├── LIMEExplainer
│   ├── Input: Model prediction
│   ├── Output: Word importance scores
│   └── Visualization: Highlighted text
│
├── DecisionPathVisualizer
│   ├── Shows: Which layer contributed what
│   ├── Format: Sankey diagram or tree
│   └── Purpose: Debug and explain
│
└── ReportGenerator
    ├── Components:
    │   ├── Executive summary
    │   ├── Evidence breakdown
    │   ├── Source credibility chart
    │   ├── Confidence explanation
    │   └── Recommendations
    └── Format: JSON + Human-readable
```

**LIME Explanation Example:**

```
Claim: "5G towers cause COVID-19"

Word Importance (LIME):
┌─────────────────────────────────────────────────────────────┐
│  "5G"      ████████████████░░░░  +0.82 (strong indicator)  │
│  "towers"  █████████░░░░░░░░░░░  +0.45                      │
│  "cause"   ██████████████░░░░░░  +0.71 (causal claim)      │
│  "COVID"   █████████████████░░░  +0.85 (health topic)      │
└─────────────────────────────────────────────────────────────┘

Model learned: Claims linking 5G + COVID + causation = high fake probability
```

---

## 🛠️ Technology Stack

### Backend (Python)

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | API server |
| NLP | spaCy, NLTK | Text processing |
| ML Models | HuggingFace Transformers | BERT, RoBERTa |
| Embeddings | Sentence-Transformers | Semantic search |
| LLM | Google Gemini API | Reasoning & explanation |
| Explainability | LIME, SHAP | Model interpretability |
| Database | PostgreSQL + SQLAlchemy | Data storage |
| Task Queue | Celery + Redis | Async processing |

### Models to Fine-tune

| Model | Base | Purpose | Dataset |
|-------|------|---------|---------|
| Claim Detector | DistilBERT | Identify verifiable claims | ClaimBuster |
| Stance Classifier | RoBERTa | Determine article stance | FNC-1 |
| Fake News Detector | BERT | Binary classification | LIAR + FakeNewsNet |

### Frontend (TypeScript)

| Component | Technology |
|-----------|------------|
| Framework | React 18 |
| Build | Vite |
| Styling | Tailwind CSS |
| Charts | Recharts / D3.js |
| State | React Context / Zustand |

---

## 📅 Implementation Phases

### Phase 1: Foundation (Week 1-2)

```
□ Set up model training pipeline
□ Download and preprocess datasets
  ├── LIAR dataset
  ├── FNC-1 dataset
  └── ClaimBuster dataset
□ Implement spaCy NLP layer
□ Create entity extraction service
□ Add sentiment analysis
```

### Phase 2: Model Training (Week 3-4)

```
□ Fine-tune DistilBERT for claim detection
□ Fine-tune RoBERTa for stance classification
□ Set up model evaluation pipeline
□ Calculate metrics (Precision, Recall, F1)
□ Create model serving infrastructure
```

### Phase 3: Knowledge Integration (Week 5)

```
□ Implement Wikidata SPARQL queries
□ Add domain trust scoring
□ Integrate Google Knowledge Graph
□ Create fact-checker database
```

### Phase 4: Pipeline Orchestration (Week 6)

```
□ Build orchestrator service
□ Implement verdict aggregation
□ Add Chain-of-Thought prompting
□ Create async processing with Celery
```

### Phase 5: Explainability (Week 7)

```
□ Integrate LIME explanations
□ Create decision visualization
□ Build report generator
□ Add confidence breakdown
```

### Phase 6: Testing & Documentation (Week 8)

```
□ End-to-end testing
□ Performance benchmarking
□ Write academic report
□ Create demo presentation
□ Prepare for viva
```

---

## 📊 Data & Training Requirements

### Datasets

| Dataset | Size | Use | Source |
|---------|------|-----|--------|
| LIAR | 12,836 statements | Fake news classification | [PolitiFact](https://www.cs.ucsb.edu/~william/data/liar_dataset.zip) |
| FNC-1 | 75,385 pairs | Stance detection | [Fake News Challenge](http://www.fakenewschallenge.org/) |
| ClaimBuster | 23,533 sentences | Claim detection | [ClaimBuster](https://idir.uta.edu/claimbuster/) |
| FEVER | 185,445 claims | Fact verification | [FEVER](https://fever.ai/) |

### Training Configuration

```python
# Claim Detector Training Config
claim_config = {
    "model": "distilbert-base-uncased",
    "max_length": 128,
    "batch_size": 32,
    "learning_rate": 2e-5,
    "epochs": 3,
    "warmup_steps": 500,
    "weight_decay": 0.01,
}

# Stance Classifier Training Config
stance_config = {
    "model": "roberta-base",
    "max_length": 256,
    "batch_size": 16,
    "learning_rate": 1e-5,
    "epochs": 5,
    "num_labels": 4,  # agree, disagree, discuss, unrelated
}
```

---

## 📈 Evaluation Framework

### Metrics to Report

```python
evaluation_metrics = {
    "claim_detection": {
        "precision": "% of detected claims that are actually claims",
        "recall": "% of actual claims that were detected",
        "f1_score": "harmonic mean of precision and recall",
    },
    "stance_classification": {
        "accuracy": "overall correct predictions",
        "macro_f1": "average F1 across all classes",
        "confusion_matrix": "breakdown by class",
    },
    "overall_system": {
        "verdict_accuracy": "% correct final verdicts",
        "explanation_quality": "human evaluation score",
        "processing_time": "average seconds per claim",
    }
}
```

### Baseline Comparisons

| System | What to Compare |
|--------|-----------------|
| Random Baseline | Random verdict assignment |
| Majority Class | Always predict most common verdict |
| API-Only (Current MVP) | Current implementation |
| Hybrid (Proposed) | Our new system |

---

## 📁 Proposed File Structure

```
TruthLens/
├── backend/
│   └── app/
│       ├── api/v1/
│       │   ├── analyze.py          # Main analysis endpoint
│       │   ├── auth.py
│       │   └── history.py
│       │
│       ├── services/
│       │   ├── nlp/                 # NEW: Layer 1
│       │   │   ├── __init__.py
│       │   │   ├── claim_detector.py
│       │   │   ├── entity_extractor.py
│       │   │   ├── sentiment_analyzer.py
│       │   │   └── linguistic_analyzer.py
│       │   │
│       │   ├── knowledge/           # NEW: Layer 2
│       │   │   ├── __init__.py
│       │   │   ├── wikidata_verifier.py
│       │   │   ├── domain_analyzer.py
│       │   │   └── knowledge_graph.py
│       │   │
│       │   ├── evidence/            # ENHANCED: Layer 3
│       │   │   ├── __init__.py
│       │   │   ├── semantic_search.py
│       │   │   ├── news_retriever.py
│       │   │   └── stance_classifier.py
│       │   │
│       │   ├── reasoning/           # NEW: Layer 4
│       │   │   ├── __init__.py
│       │   │   ├── verdict_aggregator.py
│       │   │   └── llm_reasoner.py
│       │   │
│       │   ├── explainability/      # NEW: Layer 5
│       │   │   ├── __init__.py
│       │   │   ├── lime_explainer.py
│       │   │   └── report_generator.py
│       │   │
│       │   └── orchestrator.py      # NEW: Pipeline coordinator
│       │
│       ├── models/                   # Database models (existing)
│       └── core/                     # Config (existing)
│
├── models/                           # NEW: Trained ML models
│   ├── claim_detector/
│   │   ├── config.json
│   │   └── pytorch_model.bin
│   ├── stance_classifier/
│   │   ├── config.json
│   │   └── pytorch_model.bin
│   └── embeddings/
│       └── sentence_bert/
│
├── training/                         # NEW: Model training
│   ├── notebooks/
│   │   ├── 01_data_exploration.ipynb
│   │   ├── 02_claim_detector_training.ipynb
│   │   ├── 03_stance_classifier_training.ipynb
│   │   └── 04_evaluation.ipynb
│   ├── scripts/
│   │   ├── train_claim_detector.py
│   │   └── train_stance_classifier.py
│   └── data/
│       ├── liar/
│       ├── fnc1/
│       └── claimbuster/
│
├── evaluation/                       # NEW: Academic rigor
│   ├── metrics.py
│   ├── baselines.py
│   ├── ablation_study.py
│   └── results/
│       ├── confusion_matrices/
│       └── performance_plots/
│
├── client/                           # Frontend (existing)
│   └── src/
│       └── components/
│           └── AnalysisResults.tsx   # Enhanced with explainability
│
├── docs/
│   ├── HYBRID_PIPELINE_PLAN.md      # This document
│   ├── API_DOCUMENTATION.md
│   └── FINAL_REPORT.pdf             # Academic paper
│
└── docker-compose.yml                # Add Redis for Celery
```

---

## 🔌 API Design

### New Endpoints

```python
# Analysis Pipeline
POST /api/v1/analyze
Request:
{
    "text": "COVID vaccines contain microchips",
    "url": null,  # Optional
    "options": {
        "deep_analysis": true,
        "include_explanation": true
    }
}

Response:
{
    "claim": "COVID vaccines contain microchips",
    "verdict": "FALSE",
    "confidence": 0.94,
    
    "layers": {
        "nlp": {
            "entities": [{"text": "COVID", "type": "DISEASE"}],
            "sentiment": -0.2,
            "is_claim": true,
            "claim_confidence": 0.92
        },
        "knowledge": {
            "wikidata_result": "NO_MATCH",
            "domain_trust": null
        },
        "evidence": {
            "sources": [
                {
                    "title": "Fact check: No microchips in vaccines",
                    "source": "Reuters",
                    "trust_score": 95,
                    "stance": "DISAGREE",
                    "stance_confidence": 0.89
                }
            ]
        },
        "reasoning": {
            "chain_of_thought": "...",
            "key_factors": [
                "Multiple high-credibility sources refute",
                "No scientific evidence supports claim"
            ]
        }
    },
    
    "explanation": {
        "summary": "This claim has been fact-checked...",
        "word_importance": {"5G": 0.82, "COVID": 0.85},
        "decision_path": "..."
    }
}
```

---

## ⏰ Timeline

```
Week 1-2: Foundation & Data Preparation
├── Day 1-3: Dataset download and preprocessing
├── Day 4-7: SpaCy NLP layer implementation
└── Day 8-14: Entity extraction and sentiment analysis

Week 3-4: Model Training
├── Day 15-18: Fine-tune claim detector
├── Day 19-23: Fine-tune stance classifier
└── Day 24-28: Evaluation and optimization

Week 5: Knowledge Integration
├── Day 29-31: Wikidata integration
├── Day 32-33: Domain trust scoring
└── Day 34-35: Knowledge graph API

Week 6: Pipeline Orchestration
├── Day 36-38: Orchestrator service
├── Day 39-40: Verdict aggregation
└── Day 41-42: LLM Chain-of-Thought

Week 7: Explainability
├── Day 43-45: LIME integration
├── Day 46-47: Report generator
└── Day 48-49: Frontend updates

Week 8: Testing & Documentation
├── Day 50-52: End-to-end testing
├── Day 53-54: Academic report writing
└── Day 55-56: Demo preparation
```

---

## 🎯 Success Criteria

| Metric | Target |
|--------|--------|
| Claim Detection F1 | > 0.85 |
| Stance Classification F1 | > 0.75 |
| Overall Verdict Accuracy | > 0.80 |
| Processing Time | < 10 seconds |
| Explanation Quality (Human Eval) | > 4/5 |

---

## 📚 References

1. Wang, W.Y. (2017). "Liar, Liar Pants on Fire": A New Benchmark Dataset for Fake News Detection
2. Pomerleau, D. & Rao, D. (2017). Fake News Challenge (FNC-1)
3. Thorne, J. et al. (2018). FEVER: a Large-scale Dataset for Fact Extraction and VERification
4. Hassan, N. et al. (2017). ClaimBuster: The First-ever End-to-end Fact-checking System

---

> **Document Version:** 1.0  
> **Last Updated:** January 2026  
> **Status:** Ready for Implementation

