# 🚀 TruthLens V3: Phased Implementation Strategy

> **Purpose:** Break the 6-stage architecture into incremental phases  
> **Principle:** Each phase delivers working value. No "big bang" at the end.  
> **Created:** January 2026

---

## 📊 The Spine (Never Compromise)

These are **non-negotiable** — every phase must preserve:

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Claim Typing happens EARLY (before evidence gathering)      │
│  2. Different claim types → Different evidence strategies       │
│  3. Output is NEVER binary TRUE/FALSE for uncertain claims      │
│  4. System shows its work (transparency)                        │
│  5. Time context acknowledged                                   │
│  6. LLM is ONLY for explanation, NEVER for verdict ⭐           │
└─────────────────────────────────────────────────────────────────┘
```

> ⚠️ **CRITICAL: Why #6 Matters**
> 
> If LLM decides the verdict → Project is just an "LLM wrapper"
> If evidence decides the verdict, LLM explains → Real ML pipeline
> 
> **TruthLens = Evidence-driven pipeline + LLM-powered explanation**

---

## 🎯 Phase Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION PHASES                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PHASE 1: The Skeleton                                           │
│  ════════════════════                                            │
│  • Input → Text extraction (all formats)                        │
│  • Basic claim extraction                                        │
│  • Claim type detection (the fork)                              │
│  • Simple output structure                                       │
│  ✓ DELIVERS: Working pipeline, types claims, honest output      │
│                                                                  │
│  PHASE 2A: Basic Evidence                                        │
│  ═══════════════════════                                         │
│  • Factual claims → Wikidata verification                       │
│  • Google Fact Check API (existing fact-checks)                 │
│  • Source trust scoring database                                │
│  ✓ DELIVERS: Simple factual claims get verified                 │
│                                                                  │
│  PHASE 2B: Deep Investigation Engine ⭐ NEW                      │
│  ═══════════════════════════════════════                         │
│  • Multi-layer search (DuckDuckGo, Wikipedia, PubMed)           │
│  • Smart orchestration (when to stop)                           │
│  • Lead following (trace to original sources)                   │
│  • Evidence synthesis                                            │
│  ✓ DELIVERS: Real internet digging, not just API calls          │
│                                                                  │
│  PHASE 3: Type-Specific Strategies                               │
│  ══════════════════════════════                                  │
│  • Scientific claims → Consensus detection + PubMed             │
│  • Political claims → Proper uncertainty handling               │
│  • Breaking news → Time-sensitivity markers                     │
│  ✓ DELIVERS: Each type handled appropriately                    │
│                                                                  │
│  PHASE 4: Intelligence Layer                                     │
│  ═══════════════════════════                                     │
│  • Claim normalization (deduplication)                          │
│  • LLM reasoning integration                                    │
│  • Rich explanations                                            │
│  ✓ DELIVERS: Smart, explained outputs                           │
│                                                                  │
│  PHASE 5: Polish & Scale                                         │
│  ═══════════════════════                                         │
│  • Time-aware tracking                                          │
│  • Performance optimization                                      │
│  • Full testing                                                  │
│  ✓ DELIVERS: Production-ready system                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**MVP = Phase 1 + Phase 2A + Phase 2B** (Working pipeline with real investigation)

---

## 🔨 PHASE 1: The Skeleton (Week 1-2)

### Goal
A working end-to-end pipeline that accepts any input, extracts claims, types them, and produces honest output.

### What Gets Built

```
INPUT → EXTRACT TEXT → EXTRACT CLAIMS → TYPE CLAIMS → OUTPUT
  │          │              │               │            │
  │          │              │               │            │
  ▼          ▼              ▼               ▼            ▼
Any       Unified       List of         Claim        Honest
format    text          assertions      categories   assessment
```

### Deliverables

#### 1.1 Unified Input Processing
```python
# services/input/gateway.py
def process_input(input_data) -> ProcessedInput:
    """
    Text → pass through
    URL → trafilatura extraction  
    Image → EasyOCR
    """
```

**Files to create:**
- `services/input/gateway.py`
- `services/input/text_handler.py`
- `services/input/url_scraper.py`
- `services/input/ocr_engine.py`

#### 1.2 Claim Extraction (Basic)
```python
# services/extraction/claim_extractor.py
def extract_claims(text: str) -> List[RawClaim]:
    """
    Split into sentences
    Filter: keep assertions, discard questions/rhetoric
    Over-extract (false positives OK)
    """
```

**Files to create:**
- `services/extraction/claim_extractor.py`
- `services/extraction/sentence_classifier.py`

#### 1.3 Claim Typing (THE FORK) ⭐
```python
# services/typing/claim_classifier.py
from transformers import pipeline

# Load zero-shot classifier (BART-large-mnli)
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def classify_claim(claim: RawClaim) -> TypedClaim:
    """
    Uses BART-large-mnli for zero-shot classification
    
    Labels:
    - scientific or medical claim
    - political allegation  
    - factual statement about dates or numbers
    - breaking news event
    - opinion or value judgment
    - quote attribution
    """
    labels = [
        "scientific or medical claim",
        "political allegation",
        "factual statement",
        "breaking news event",
        "opinion or value judgment"
    ]
    result = classifier(claim.text, labels)
    return TypedClaim(
        text=claim.text,
        type=result["labels"][0],
        confidence=result["scores"][0]
    )
```

**Model used:** `facebook/bart-large-mnli` (1.6 GB, zero-shot classification)

**Files to create:**
- `services/typing/claim_classifier.py`
- `services/typing/type_signals.py`

#### 1.4 Basic Output Structure
```python
# services/output/assessment.py
class Assessment:
    claim: str
    claim_type: ClaimType
    status: str  # "Pending analysis", "Opinion - not checkable", etc.
    evidence_strategy: str  # What WOULD be used
    confidence: float
    note: str
```

### Phase 1 Success Criteria

```
✅ Submit text → Get claims extracted
✅ Submit URL → Get article scraped → Get claims  
✅ Submit image → Get OCR text → Get claims
✅ Each claim is TYPED correctly (>70% accuracy)
✅ Opinions flagged as "not fact-checkable"
✅ Output is honest: "Analysis pending" not fake verdict
```

### Phase 1 Testing

```python
# Test cases
test_inputs = [
    ("COVID vaccines cause autism", "SCIENTIFIC_MEDICAL"),
    ("Modi won 2024 election", "FACTUAL"),
    ("BJP is destroying India", "OPINION"),
    ("New variant detected today", "BREAKING_EVENT"),
    ("Congress did election fraud", "POLITICAL_ALLEGATION"),
]

for text, expected_type in test_inputs:
    result = pipeline.analyze(text)
    assert result.claim_type == expected_type
```

---

## 🔨 PHASE 2: Evidence Foundations (Week 2-3)

### Goal
Factual claims get real verification. Other types get appropriate "pending" status.

### What Gets Built

```
TYPED CLAIM
    │
    ├── FACTUAL → Wikidata query → TRUE/FALSE
    │
    ├── SCIENTIFIC → "Requires scientific evidence" (placeholder)
    │
    ├── POLITICAL → "Requires official sources" (placeholder)
    │
    └── BREAKING → News API search → DEVELOPING
```

### Deliverables

#### 2.1 Wikidata Verification (for FACTUAL claims)
```python
# services/evidence/wikidata.py
def verify_factual_claim(claim: TypedClaim) -> VerificationResult:
    """
    Extract: entity + property + claimed value
    Query Wikidata via SPARQL
    Compare claimed vs actual
    Return: VERIFIED_TRUE, VERIFIED_FALSE, NOT_FOUND
    """
```

**Example:**
```
Claim: "Delhi is the capital of India"
→ Entity: India (Q668)
→ Property: capital (P36) 
→ Query: SELECT ?capital WHERE { wd:Q668 wdt:P36 ?capital }
→ Result: New Delhi (Q987)
→ Verdict: VERIFIED_TRUE
```

#### 2.2 Source Trust Scoring
```python
# services/evidence/source_trust.py
TRUST_SCORES = {
    "reuters.com": 95,
    "bbc.com": 90,
    "thehindu.com": 85,
    "opindia.com": 40,
    "unknown": 50,
}

def get_trust_score(domain: str) -> int:
    return TRUST_SCORES.get(domain, 50)
```

#### 2.3 News Evidence (Enhanced Existing)
```python
# services/evidence/news_retriever.py
def gather_news_evidence(claim: TypedClaim) -> List[NewsEvidence]:
    """
    GNews API + Google Fact Check API
    Tag each with source trust score
    """
```

### Phase 2A Success Criteria

```
✅ "India's capital is Mumbai" → VERIFIED_FALSE (Wikidata)
✅ "Modi born in 1950" → VERIFIED_TRUE (Wikidata)
✅ Sources tagged with trust scores
✅ Scientific/Political claims still marked "pending full strategy"
```

---

## 🔨 PHASE 2B: Deep Investigation Engine (Week 2-3)

### Goal
The system actually digs the internet — not just calls one API. Multi-layer search with smart stopping.

### Zero-Cost Tools (All Free)

| Tool | Use For | Limit |
|------|---------|-------|
| **DuckDuckGo API** | General web search | Unlimited, no key |
| **Wikipedia API** | Encyclopedia facts | Unlimited, no key |
| **PubMed API** | Scientific papers | Unlimited, free |
| **Archive.org API** | Historical verification | Unlimited, free |
| **Reddit JSON API** | Discussions, debunking | 60 req/min |
| **Wikidata SPARQL** | Structured facts | Unlimited, free |

### What Gets Built

```
CLAIM
  │
  ├─── LEVEL 1: Quick Check (~5s) - NO LLM
  │    ├── Known misinfo database (our JSON)
  │    ├── Google Fact Check API
  │    └── Wikidata quick facts
  │
  ├─── LEVEL 2: Standard Search (~15s)
  │    ├── DuckDuckGo search
  │    ├── Wikipedia lookup
  │    └── GNews search
  │
  ├─── LEVEL 3: Deep Investigation (~45s)
  │    ├── PubMed for scientific claims
  │    ├── Follow leads to original sources
  │    └── Archive.org for verification
  │
  └─── VERDICT: Evidence Synthesis Algorithm
       └── NO LLM decides verdict
       └── Then LLM explains (Stage 6 only)
```

### Deliverables

#### 2B.1 Free Searchers
```python
# services/investigation/searchers.py
class FreeSearchers:
    def duckduckgo_search(self, query: str) -> List[Dict]:
        """DuckDuckGo Instant API - no key needed"""
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json"}
        return requests.get(url, params=params).json()
    
    def wikipedia_search(self, query: str) -> Dict:
        """Wikipedia REST API - unlimited, free"""
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        return requests.get(url).json()
    
    def pubmed_search(self, query: str) -> List[Dict]:
        """PubMed API - for scientific claims"""
        # E-utilities API, completely free
```

**Files to create:**
- `services/investigation/searchers.py`
- `services/investigation/duckduckgo.py`
- `services/investigation/wikipedia.py`
- `services/investigation/pubmed.py`

#### 2B.2 Smart Orchestrator
```python
# services/investigation/orchestrator.py
class InvestigationOrchestrator:
    MAX_TIME = 45  # seconds
    
    def investigate(self, claim) -> Evidence:
        # Level 1: Quick (always run)
        evidence = self.quick_check(claim)
        if self.should_stop(evidence): return evidence
        
        # Level 2: Standard (parallel search)
        evidence += await self.standard_search(claim)
        if self.should_stop(evidence): return evidence
        
        # Level 3: Deep (follow leads)
        evidence += self.deep_investigate(claim, evidence.leads)
        return evidence
    
    def should_stop(self, evidence) -> bool:
        """Smart stopping conditions"""
        return (
            evidence.has_authoritative_factcheck() or
            evidence.source_agreement > 0.85 or
            evidence.time_exceeded()
        )
```

**Files to create:**
- `services/investigation/orchestrator.py`
- `services/investigation/lead_follower.py`

#### 2B.3 Evidence Synthesizer + Stance Detection
```python
# services/investigation/synthesizer.py
from transformers import pipeline

# Stance detector using NLI (does evidence SUPPORT or REFUTE claim?)
stance_detector = pipeline("text-classification", model="roberta-large-mnli")

class EvidenceSynthesizer:
    def detect_stance(self, evidence_text: str, claim: str) -> dict:
        """
        Does this evidence SUPPORT, REFUTE, or is NEUTRAL to the claim?
        Uses roberta-large-mnli (Natural Language Inference)
        """
        # NLI format: premise </s></s> hypothesis
        input_text = f"{evidence_text} </s></s> {claim}"
        result = stance_detector(input_text)
        
        # Map NLI labels to stance
        label_map = {
            "ENTAILMENT": "SUPPORTS",
            "CONTRADICTION": "REFUTES", 
            "NEUTRAL": "NEUTRAL"
        }
        return {
            "stance": label_map.get(result[0]["label"], "NEUTRAL"),
            "confidence": result[0]["score"]
        }
    
    def synthesize(self, evidence_items: list, claim: str) -> Synthesis:
        """
        1. Detect stance for each evidence item
        2. Weight by source type
        3. Calculate consensus
        """
        stances = []
        for item in evidence_items:
            stance = self.detect_stance(item.text, claim)
            stances.append({
                "source": item.source,
                "stance": stance["stance"],
                "confidence": stance["confidence"],
                "source_weight": self.get_source_weight(item.type)
            })
        
        # Weighted vote
        support_score = sum(s["confidence"] * s["source_weight"] 
                          for s in stances if s["stance"] == "SUPPORTS")
        refute_score = sum(s["confidence"] * s["source_weight"] 
                          for s in stances if s["stance"] == "REFUTES")
        
        return Synthesis(
            verdict="REFUTED" if refute_score > support_score else "SUPPORTED",
            confidence=abs(refute_score - support_score) / (refute_score + support_score + 0.01),
            stance_breakdown=stances
        )
```

**Model used:** `roberta-large-mnli` (1.4 GB, stance detection via NLI)

**Files to create:**
- `services/investigation/synthesizer.py`
- `services/investigation/stance_detector.py`

### Phase 2B Success Criteria

```
✅ DuckDuckGo search returns results for any claim
✅ Wikipedia lookup works for entity-based claims
✅ PubMed returns papers for scientific claims
✅ Investigation stops early when confident (smart stopping)
✅ Time limit respected (max 45 seconds)
✅ Evidence from multiple sources synthesized into single score
```

---

## 🔨 PHASE 3: Type-Specific Strategies (Week 3-4)

### Goal
Each claim type gets its appropriate evidence strategy.

### Deliverables

#### 3.1 Scientific/Medical Strategy
```python
# services/evidence/scientific_strategy.py
def analyze_scientific_claim(claim: TypedClaim) -> ScientificAssessment:
    """
    Check for known debunked claims (database lookup)
    Check scientific consensus indicators
    Flag if claim matches misinformation patterns
    """
    
    # Known debunked claims database
    KNOWN_MISINFORMATION = {
        "vaccines cause autism": {
            "status": "VERIFIED_FALSE",
            "consensus": "Strong scientific consensus against",
            "pattern": "Long-running debunked claim since 1998"
        },
        "5g causes covid": {
            "status": "VERIFIED_FALSE", 
            "consensus": "No scientific support",
            "pattern": "Conspiracy theory"
        }
    }
```

#### 3.2 Political Allegation Strategy
```python
# services/evidence/political_strategy.py
def analyze_political_claim(claim: TypedClaim) -> PoliticalAssessment:
    """
    DO NOT give TRUE/FALSE verdict
    Instead:
    - Check for official investigation findings
    - Check court rulings
    - Note polarization signals
    - Output: UNVERIFIED / UNDER_INVESTIGATION / DISPUTED
    """
```

#### 3.3 Breaking News Strategy
```python
# services/evidence/breaking_strategy.py
def analyze_breaking_claim(claim: TypedClaim) -> BreakingAssessment:
    """
    Check multiple news sources
    Count independent confirmations
    Output: DEVELOPING / CONFIRMED / SINGLE_SOURCE
    Always include timestamp
    """
```

### Phase 3 Success Criteria

```
✅ "Vaccines cause autism" → Uses scientific strategy → VERIFIED_FALSE
✅ "Party X rigged elections" → Uses political strategy → UNVERIFIED
✅ "Breaking: earthquake today" → Uses breaking strategy → DEVELOPING
✅ Each output shows which strategy was used
```

---

## 🔨 PHASE 4: Intelligence Layer (Week 4-5)

### Goal
Smart processing: normalization, LLM reasoning, rich explanations.

### Deliverables

#### 4.1 Claim Normalization (Using Sentence Transformers)
```python
# services/normalization/normalizer.py
from sentence_transformers import SentenceTransformer
import numpy as np

# Load sentence transformer for embeddings
embedder = SentenceTransformer("all-MiniLM-L6-v2")

class ClaimNormalizer:
    def __init__(self):
        self.known_claims = []  # Store (embedding, canonical_form)
        self.similarity_threshold = 0.85
    
    def get_embedding(self, text: str):
        """Convert claim to semantic embedding"""
        return embedder.encode(text)
    
    def find_similar(self, claim: str) -> tuple:
        """Find existing similar claim"""
        claim_embedding = self.get_embedding(claim)
        
        for stored_emb, canonical in self.known_claims:
            # Cosine similarity
            similarity = np.dot(claim_embedding, stored_emb) / (
                np.linalg.norm(claim_embedding) * np.linalg.norm(stored_emb)
            )
            if similarity > self.similarity_threshold:
                return (canonical, similarity)
        
        return None
    
    def normalize(self, claim: str) -> NormalizedClaim:
        """
        "Vaccines cause autism" 
        "COVID shots lead to autism"
        "Vaccination causes autism"
        → All map to same canonical form using semantic similarity
        """
        existing = self.find_similar(claim)
        
        if existing:
            canonical, similarity = existing
            return NormalizedClaim(
                original=claim,
                canonical=canonical,
                is_duplicate=True,
                similarity=similarity
            )
        
        # New claim - store it
        embedding = self.get_embedding(claim)
        self.known_claims.append((embedding, claim))
        
        return NormalizedClaim(
            original=claim,
            canonical=claim,
            is_duplicate=False
        )
```

**Model used:** `all-MiniLM-L6-v2` (80 MB, semantic embeddings)

#### 4.2 LLM Reasoning Integration
```python
# services/reasoning/llm_reasoner.py
def generate_reasoning(claim: TypedClaim, evidence: Evidence) -> Reasoning:
    """
    Use Gemini to:
    - Explain the assessment
    - Summarize key factors
    - Provide context
    
    NOT to decide the verdict (that's done by evidence)
    """
```

#### 4.3 Rich Explanations
```python
# services/output/explanation_builder.py
def build_explanation(assessment: Assessment) -> Explanation:
    """
    - What claim was analyzed
    - How it was interpreted
    - What evidence was used
    - Why this conclusion
    - What's uncertain
    """
```

### Phase 4 Success Criteria

```
✅ Similar phrasings map to same canonical claim
✅ LLM provides natural language explanation
✅ Output includes decision path
✅ Limitations are acknowledged
```

---

## 🔨 PHASE 5: Polish & Scale (Week 5-6)

### Goal
Production-ready, tested, optimized.

### Deliverables

#### 5.1 Time-Aware Tracking
```python
# services/temporal/time_context.py
class TimeContext:
    first_seen: datetime
    last_checked: datetime
    evidence_freshness: timedelta
    stability: str  # STABILIZED, DEVELOPING, CONTESTED
```

#### 5.2 Performance Optimization
- Model caching (singleton pattern)
- Async evidence gathering
- Response time < 15 seconds

#### 5.3 Full Testing Suite
- Unit tests per stage
- Integration tests end-to-end
- Accuracy measurement on test dataset

#### 5.4 Documentation & Report
- API documentation
- Architecture diagrams
- Academic report sections

### Phase 5 Success Criteria

```
✅ All tests passing
✅ Response time < 15 seconds
✅ Accuracy > 70% on test set
✅ Documentation complete
```

---

## 📋 Phase Task Checklist

### Phase 1: The Skeleton
```
[ ] Input Gateway
    [ ] Text handler
    [ ] URL scraper (trafilatura)
    [ ] OCR engine (EasyOCR) ← LOCAL MODEL
[ ] Claim Extraction
    [ ] Sentence splitter (spaCy en_core_web_sm) ← LOCAL MODEL
    [ ] Assertion classifier
[ ] Claim Typing ⭐ CORE ML
    [ ] Zero-shot classifier (facebook/bart-large-mnli) ← LOCAL MODEL
    [ ] Type signal detection
[ ] Basic Output
    [ ] Assessment structure
    [ ] Honest "pending" responses
[ ] Model Manager (singleton pattern)
    [ ] Load all models once at startup
[ ] Integration test: end-to-end flow works
```

### Phase 2A: Basic Evidence
```
[ ] Wikidata Integration
    [ ] Entity linking
    [ ] SPARQL query builder
    [ ] Result comparator
[ ] Source Trust
    [ ] Trust score database
    [ ] Domain lookup
[ ] Fact Check API
    [ ] Google Fact Check integration
    [ ] Response parsing
[ ] Integration test: factual claims verified via Wikidata
```

### Phase 2B: Deep Investigation Engine ⭐
```
[ ] Free Searchers
    [ ] DuckDuckGo API integration
    [ ] Wikipedia API integration
    [ ] PubMed API integration
    [ ] Archive.org API integration
    [ ] Reddit JSON API integration
[ ] Investigation Orchestrator
    [ ] Level 1: Quick check (misinfo DB + Fact Check + Wikidata) - NO LLM
    [ ] Level 2: Standard search (parallel)
    [ ] Level 3: Deep investigation (lead following)
    [ ] Smart stopping conditions
    [ ] Time budget management (45s max)
[ ] Lead Follower
    [ ] Official source verification
    [ ] Document/study lookup
    [ ] Quote attribution check
[ ] Evidence Synthesizer + Stance Detection ⭐ CORE ML
    [ ] Stance detector (roberta-large-mnli) ← LOCAL MODEL
    [ ] Source type weighting
    [ ] Consensus calculation
    [ ] Contradiction detection
[ ] Integration test: multi-source search returns combined evidence
```

### Phase 3: Type-Specific Strategies
```
[ ] Scientific Strategy
    [ ] Known misinformation database
    [ ] Consensus detection
[ ] Political Strategy
    [ ] Uncertainty output
    [ ] Polarization signals
[ ] Breaking Strategy
    [ ] Multi-source checking
    [ ] Freshness tracking
[ ] Integration test: each type uses correct strategy
```

### Phase 4: Intelligence Layer
```
[ ] Normalization ⭐ CORE ML
    [ ] Semantic embeddings (all-MiniLM-L6-v2) ← LOCAL MODEL
    [ ] Cosine similarity for deduplication
    [ ] Canonical form storage
[ ] LLM Reasoning
    [ ] Explanation prompts
    [ ] Context generation
[ ] Rich Output
    [ ] Decision path
    [ ] Limitations section
[ ] Integration test: explanations are clear
```

### Phase 5: Polish & Scale
```
[ ] Time Tracking
    [ ] Temporal context
    [ ] Freshness indicators
[ ] Performance
    [ ] Model caching
    [ ] Async operations
[ ] Testing
    [ ] Full test suite
    [ ] Accuracy measurement
[ ] Documentation
    [ ] API docs
    [ ] Report sections
```

---

## 🎯 What Each Phase Delivers

| Phase | User Can Do | System Shows |
|-------|-------------|--------------|
| **1** | Submit any input, get typed claims | "This is a [TYPE] claim, analysis strategy: [X]" |
| **2A** | Get factual claims verified | "Verified against Wikidata: TRUE/FALSE" |
| **2B** | Get deep internet search | "Searched 5 sources, found 3 supporting, 1 contradicting" |
| **3** | Get appropriate handling per type | "Scientific consensus: X" / "Political: Unverified" |
| **4** | Get explained assessments | "Here's why, here's the evidence, here's what's uncertain" |
| **5** | Production-ready usage | Fast, reliable, documented |

---

## ⏱️ Timeline Summary

```
Week 1-2: Phase 1 (Skeleton)
    └── Working pipeline, claim typing

Week 2-3: Phase 2A (Basic Evidence) + Phase 2B (Deep Investigation)
    └── Wikidata + Multi-source internet search working

Week 3-4: Phase 3 (Strategies)
    └── All claim types handled with proper evidence

Week 4-5: Phase 4 (Intelligence)
    └── Smart, explained outputs

Week 5-6: Phase 5 (Polish)
    └── Production-ready
```

---

## 🚨 Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Wikidata queries are complex | Start with simple entity-property queries, expand gradually |
| Claim typing accuracy is low | Use LLM to assist classification initially |
| Scientific consensus hard to detect | Use known misinformation database as starting point |
| Political claims are sensitive | Default to "UNVERIFIED", never claim certainty |
| Time runs out | Phase 1-2 = MVP, Phase 3+ = enhancements |

---

## 🎬 Getting Started: Phase 1, Step 1

```bash
# Create the service structure
mkdir -p backend/app/services/input
mkdir -p backend/app/services/extraction  
mkdir -p backend/app/services/typing
mkdir -p backend/app/services/output

# First file to create
touch backend/app/services/input/gateway.py
```

Then implement the input gateway that routes to appropriate handlers.

---

> **Remember:** Phase 1-2 is your MVP. If time is tight, that's a complete, honest system.  
> Phases 3-5 add sophistication but aren't required for a working demo.
