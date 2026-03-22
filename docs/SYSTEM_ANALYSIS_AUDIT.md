# 🔬 TruthLens System Analysis & Technical Audit

> **Document Type:** Deep Reverse-Engineering & AI Safety Audit  
> **Auditor Role:** Senior Research-Systems Engineer  
> **Date:** February 2026  
> **Status:** Complete Analysis

---

## Table of Contents

1. [System Understanding](#section-1--system-understanding)
2. [Claim Forensics Capability](#section-2--claim-forensics-capability)
3. [Deep Research Depth](#section-3--deep-research-depth)
4. [Evidence Model](#section-4--evidence-model)
5. [Conflict & Contradiction Handling](#section-5--conflict--contradiction-handling)
6. [Mis/Dis/Mal Information Logic](#section-6--misdismal-information-logic)
7. [Output Quality & Verdict Engine](#section-7--output-quality--verdict-engine)
8. [Failure Modes](#section-8--failure-modes)
9. [Security, Abuse & Adversarial Inputs](#section-9--security-abuse--adversarial-inputs)
10. [Scalability & Engineering](#section-10--scalability--engineering)
11. [Realistic Limitations](#section-11--realistic-limitations)
12. [Prioritized Roadmap](#section-12--prioritized-roadmap)
13. [Final Verdict & Readiness Score](#final-verdict)

---

## SECTION 1 – SYSTEM UNDERSTANDING

### Overall Goal

TruthLens is a **multi-modal misinformation detection platform** designed to analyze text-based content (posts, articles, WhatsApp forwards, tweets) and detect deepfakes in images/videos. The system aims to:

1. Extract verifiable claims from user input
2. Route claims to type-specific investigation strategies
3. Gather evidence from multiple free-tier sources
4. Synthesize verdicts using ML-based stance detection
5. Generate human-readable explanations via LLM

### End-to-End Data Flow

```
USER INPUT (Text/URL/Image/Video)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  INPUT GATEWAY (Stage 0)                                     │
│  • URL Scraper (trafilatura)                                │
│  • OCR Engine (EasyOCR)                                     │
│  • Text Handler (pass-through)                              │
│  OUTPUT: Unified text + metadata                            │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  CLAIM EXTRACTION (Stage 1)                                  │
│  • spaCy sentence splitting (en_core_web_sm)                │
│  • Gemini-based "Crux" distillation (optional)              │
│  • Candidate sentence filtering                              │
│  OUTPUT: List of RawClaim objects                           │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  CLAIM TYPING (Stage 3 - "THE FORK")                        │
│  • BART-large-mnli zero-shot classification                 │
│  • Categories: Scientific, Political, Breaking, Factual,   │
│    Quote, Opinion, Prediction, etc.                         │
│  OUTPUT: TypedClaim with is_checkable flag                  │
└─────────────────────────────────────────────────────────────┘
         │
         ├───────────────────────────────────────────────┐
         │                                               │
    [CHECKABLE]                                    [NON-CHECKABLE]
         │                                               │
         ▼                                               ▼
┌─────────────────────────────────────────────┐  ┌────────────────────┐
│  INVESTIGATION ORCHESTRATOR                  │  │ Return immediately │
│  • Strategy Factory selects strategy         │  │ verdict: NOT_CHECKABLE│
│  • Quick Checks: Google Fact Check API,      │  └────────────────────┘
│    Known Misinfo DB                          │
│  • Type-Specific Strategy Execution          │
│    - Scientific: PubMed, meta-analyses       │
│    - Political: .gov domains, polarization   │
│    - Breaking: Velocity, stability markers   │
│    - Generic: DuckDuckGo, Wikipedia          │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  EVIDENCE SYNTHESIZER                                        │
│  • RoBERTa-large-mnli stance detection (SUPPORTS/REFUTES)   │
│  • Weighted voting (source trust × type weight × stance)    │
│  • Veto power for authoritative sources                     │
│  OUTPUT: Verdict + Confidence + Evidence Collection         │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  EXPLANATION SERVICE (Stage 6)                               │
│  • Gemini 1.5 Flash / Groq Llama 3.3 70B                    │
│  • Type-specific prompt templates                           │
│  • LLM receives verdict + evidence (NOT deciding verdict)   │
│  OUTPUT: Human-readable explanation                         │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  VERIFIED CLAIM OUTPUT                                       │
│  • verdict: VERIFIED_TRUE / VERIFIED_FALSE / DISPUTED /     │
│    UNVERIFIED / INSUFFICIENT_EVIDENCE / NOT_CHECKABLE       │
│  • confidence: 0.0 - 1.0                                    │
│  • evidence_items: List of sources with stance              │
│  • strategy_stats: Type-specific metadata                   │
└─────────────────────────────────────────────────────────────┘
```

### Major Components & Agents

| Component | Location | Purpose |
|-----------|----------|---------|
| **Input Gateway** | `services/input/gateway.py` | Unifies all input types to text |
| **Crux Extractor** | `services/extraction/crux_extractor.py` | LLM-based core claim distillation |
| **Claim Extractor** | `services/claim_extractor.py` | spaCy + Gemini claim extraction |
| **Investigation Orchestrator** | `services/investigation/orchestrator.py` | Coordinates investigation pipeline |
| **Strategy Factory** | `services/investigation/strategies/factory.py` | Routes claims to type-specific strategies |
| **Scientific Strategy** | `strategies/scientific.py` | PubMed search, meta-analysis detection |
| **Political Strategy** | `strategies/political.py` | Official records, polarization analysis |
| **Breaking Strategy** | `strategies/breaking.py` | Velocity tracking, stability markers |
| **Generic Strategy** | `strategies/generic.py` | DDG + Wikipedia fallback |
| **Stance Detector** | `services/investigation/stance_detector.py` | BART-MNLI stance classification |
| **Evidence Synthesizer** | `services/investigation/synthesizer.py` | Weighted verdict synthesis |
| **Verdict Engine** | `services/investigation/verdict_engine.py` | Main entry point, verdict determination |
| **Explanation Service** | `services/investigation/explanation.py` | LLM-powered narrative generation |
| **Wikidata Verifier** | `services/evidence/wikidata_verifier.py` | SPARQL-based fact verification |
| **Deepfake Detector** | `services/deepfake.py` | EfficientNet-B0 + Grad-CAM |

### Where LLMs Are Used

| Stage | LLM Used | Purpose | Critical? |
|-------|----------|---------|-----------|
| Claim Extraction | Gemini 2.5 Flash | Distill text into core claims | Optional (fallback exists) |
| Claim Refinement | Gemini 2.5 Flash | Refine candidates into verifiable claims | Optional |
| **Explanation** | Gemini 1.5 Flash / Groq Llama 3.3 | Generate human-readable summaries | Required for UX |

> **CRITICAL DESIGN DECISION**: LLM is **NEVER** used for verdict determination. Verdict is fully algorithmic based on evidence synthesis.

### Where Retrieval Is Used

| Source | API | Purpose |
|--------|-----|---------|
| Google Fact Check | API | Existing fact-checks |
| DuckDuckGo | Web scraping | General web search |
| Wikipedia | REST API | Encyclopedia lookup |
| PubMed | E-utilities API | Scientific literature |
| Wikidata | SPARQL | Structured facts |
| Archive.org | Wayback API | Historical verification |

### What Is Automated vs Assumed

**Automated:**
- Input normalization (URL scraping, OCR)
- Claim extraction and typing
- Multi-source evidence retrieval
- Stance classification
- Verdict synthesis
- Explanation generation

**Assumed:**
- User input is in English
- Claims are verifiable with publicly available sources
- External APIs are available and responding
- Single-pass retrieval is sufficient
- Source trust scores are static and accurate

---

## SECTION 2 – CLAIM FORENSICS CAPABILITY

### Atomic Claim Extraction

| Capability | Status | Implementation |
|------------|--------|----------------|
| Sentence splitting | ✅ **Implemented** | spaCy `en_core_web_sm` |
| Assertion filtering | ✅ **Implemented** | Questions/emotions filtered |
| Crux distillation | ✅ **Implemented** | Gemini extracts top 7 core claims |

**What is implemented:**
- `CruxExtractor` uses Gemini to identify "the central pillars that, if proven false, would debunk the entire narrative"
- Basic sentence segmentation via spaCy
- Filtering of questions, rhetorical statements, emotions

### Multiple Claims Per Input

| Capability | Status | Notes |
|------------|--------|-------|
| Multi-claim extraction | ✅ **Implemented** | Returns `List[RawClaim]` |
| Per-claim investigation | ✅ **Implemented** | Each claim processed independently |
| Parallel execution | ⚠️ **Partial** | Strategies use `asyncio.gather` but claims processed sequentially |

### Entity Grounding

| Capability | Status | Notes |
|------------|--------|-------|
| Named Entity Recognition | ⚠️ **Partial** | spaCy NER available but not systematically used |
| Entity linking to Wikidata | ⚠️ **Partial** | Only for specific patterns (capital, PM) |
| Entity disambiguation | ❌ **Missing** | No handling of "Modi" → which Modi? |

**What is partially implemented:**
- `WikidataVerifier` extracts entities via regex patterns like "X is the capital of Y"
- Political strategy detects India/US/UK keywords for domain selection
- No systematic entity extraction-linking-disambiguation pipeline

### Time and Event Grounding

| Capability | Status | Notes |
|------------|--------|-------|
| Temporal markers | ⚠️ **Partial** | Breaking strategy checks 24h window |
| Event dating | ❌ **Missing** | No extraction of "when" from claims |
| Timeline construction | ❌ **Missing** | No temporal evidence ordering |

**What is partially implemented:**
- `BreakingNewsStrategy` uses DuckDuckGo's `time='d'` filter for last 24 hours
- `TemporalState` enum exists but is never populated
- No claim-level timestamp extraction

### Handling Vague or Implied Claims

| Capability | Status | Notes |
|------------|--------|-------|
| Implicit claim detection | ❌ **Missing** | No inference of unstated claims |
| Vague claim handling | ❌ **Missing** | No disambiguation prompt |
| Claim specificity scoring | ❌ **Missing** | All claims treated equally |

### Summary

| Aspect | Score |
|--------|-------|
| Atomic extraction | 7/10 |
| Multi-claim support | 6/10 |
| Entity grounding | 3/10 |
| Temporal grounding | 2/10 |
| Vague/implied handling | 1/10 |

---

## SECTION 3 – DEEP RESEARCH DEPTH

### Retrieval Pattern: Single-Pass vs Iterative

**Current State: SINGLE-PASS**

The system performs one round of searching per claim. There is no:
- Re-searching when new entities are discovered
- Follow-up queries based on initial results
- Iterative deepening based on evidence gaps

The documentation describes a "Lead Following" pattern (`LeadFollower` class in V3 docs) but it is **NOT IMPLEMENTED** in the actual codebase.

### Does It Re-Search on New Discoveries?

**NO.** 

When search results mention new entities or events, the system does not:
- Parse results for new search terms
- Follow links to original sources
- Verify claims made within evidence articles

### Primary/Official Source Preference

| Strategy | Implementation |
|----------|----------------|
| Political | ✅ Searches `.gov`, `.gov.in`, `.gov.uk` domains |
| Scientific | ✅ PubMed prioritized over web search |
| Breaking | ⚠️ No official source preference |
| Generic | ❌ No source prioritization |

### Original Reporting vs Copied Articles

**NOT IMPLEMENTED**

The system does not:
- Detect syndicated/copied content
- Trace claims to original reporting
- Penalize duplicate sources

### Publication Time Tracking

| Capability | Status |
|------------|--------|
| Extract publish dates | ❌ Not implemented |
| Filter by recency | ⚠️ Breaking strategy only (24h) |
| Track evidence age | ❌ `retrieved_at` exists but not used in synthesis |
| Detect outdated info | ❌ Not implemented |

### Research Depth Rating

| Criterion | Score | Justification |
|-----------|-------|---------------|
| Source diversity | 5/10 | Multiple sources but limited depth |
| Retrieval intelligence | 3/10 | Single-pass, no lead following |
| Official source priority | 4/10 | Only in political strategy |
| Temporal awareness | 2/10 | Only 24h filter in breaking |
| Original reporting | 0/10 | Not implemented |

**OVERALL RESEARCH DEPTH: 3/10**

The system collects evidence but does not deeply investigate. It's a breadth-first, single-pass retrieval with no adaptive re-search.

---

## SECTION 4 – EVIDENCE MODEL

### Are Claims Explicitly Stored?

**YES**, in `TypedClaim` dataclass:
```python
@dataclass
class TypedClaim:
    text: str
    claim_type: ClaimType
    type_confidence: float
    is_checkable: bool
    evidence_strategy: str
    status: str
```

However, there is **no persistent storage**. Claims exist only for the duration of the request.

### Are Sources Attached Per Claim?

**YES**, via `EvidenceItem`:
```python
@dataclass
class EvidenceItem:
    text: str
    source_url: str
    source_domain: str
    source_type: EvidenceType
    stance: Stance
    stance_confidence: float
    trust_score: int
```

### Support vs Contradiction Separation

**YES**, clearly modeled:
- `Stance.SUPPORTS` vs `Stance.REFUTES` vs `Stance.NEUTRAL`
- `EvidenceCollection.support_score` vs `refute_score` properties
- Weighted scoring separates supporting and contradicting evidence

### Evidence Graph or Relationship Structure

**NOT PRESENT**

The current model is **flat**:
- `EvidenceCollection` is a list ohne relationships
- No linking between evidence items
- No source-to-source relationships
- No claim-to-sub-claim hierarchy

**Required Structure for Real Forensics:**

```
Claim
├── SubClaim 1
│   ├── Evidence A (supports)
│   │   └── Derived from: Evidence B
│   └── Evidence B (refutes)
│       └── Contradicts: Evidence A
├── SubClaim 2
│   └── Evidence C (neutral)
│       └── Mentions: Entity X
└── Entity Graph
    ├── Entity X → Wikidata Q12345
    └── Entity Y → Disambiguation needed
```

---

## SECTION 5 – CONFLICT & CONTRADICTION HANDLING

### Contradictory Articles

**PARTIALLY HANDLED**

The synthesizer detects contradictions via:
1. Stance detection on each evidence item
2. Comparison of `support_score` vs `refute_score`
3. `DISPUTED` verdict when scores are close

```python
# synthesizer.py
if refute_score > support_score * 1.5:
    return Verdict.VERIFIED_FALSE, confidence
if support_score > refute_score * 1.5:
    return Verdict.VERIFIED_TRUE, confidence
return Verdict.DISPUTED, 0.5  # Mixed evidence
```

**Limitations:**
- No root cause analysis for contradictions
- No preference for more recent sources
- No detection of source bias causing contradiction

### Partial Confirmations

**NOT EXPLICITLY HANDLED**

Evidence is binary (supports/refutes/neutral). There is no:
- "Partially true" classification
- Percentage-based confirmation
- Aspect-level verification

### Outdated Information

**NOT HANDLED**

The system does not:
- Detect when evidence is outdated relative to claim date
- Prefer recent sources over older ones
- Mark evidence as "superseded"

### Retractions and Corrections

**PARTIALLY HANDLED** (Scientific Strategy Only)

```python
# scientific.py
is_retracted = "retracted" in result.title.lower()
if is_retracted:
    mapped_stance = Stance.REFUTES
    confidence = 1.0
```

This only works for PubMed results with "retracted" in the title. No general retraction/correction detection.

### Conflict Resolution Logic

**ALGORITHMIC ONLY**

The system uses weighted voting, not intelligent conflict resolution:
1. Each evidence item gets a weight
2. Weights are summed by stance
3. Verdict goes to higher weighted total

**Missing:**
- Temporal precedence (newer > older)
- Source authority hierarchy
- Logical consistency checking
- Human-in-the-loop for disputed cases

---

## SECTION 6 – MIS/DIS/MAL INFORMATION LOGIC

### Definitions

| Type | Definition | Intent Required? |
|------|------------|------------------|
| **Misinformation** | False information spread without intent to deceive | NO |
| **Disinformation** | False information deliberately spread to deceive | YES |
| **Malinformation** | True information shared to cause harm | YES (malicious) |

### What Can Be Reliably Inferred

| Type | Detectability | Notes |
|------|---------------|-------|
| **Misinformation** | ⚠️ **Partial** | Can detect false claims, cannot confirm "unintentional" |
| **Disinformation** | ❌ **Cannot** | Requires intent inference (not possible) |
| **Malinformation** | ❌ **Cannot** | Requires harm assessment + intent |

### What Cannot Be Inferred

1. **Author Intent** - The system has no access to creator's motivation
2. **Malicious Purpose** - Cannot distinguish error from deception
3. **Harm Potential** - No harm modeling or impact assessment
4. **Coordinated Campaigns** - No network analysis capabilities
5. **Source Authenticity** - Cannot verify if source is who they claim

### What The System Should NOT Claim

> [!CAUTION]
> The system MUST NOT output verdicts like:
> - "This is DISINFORMATION" (implies intent)
> - "This was deliberately spread to deceive" (requires intent proof)
> - "This is propaganda" (subjective + intent-based)
> - "The author is lying" (defamatory + unprovable)

### Recommended Output Language

**Current (Acceptable):**
- "VERIFIED_FALSE" - factually incorrect
- "DISPUTED" - evidence conflicts
- "UNVERIFIED" - cannot confirm

**Should Add:**
- "LACKS_CONTEXT" - technically true but misleading
- "OUTDATED" - was true, now false
- "MISATTRIBUTED" - quote/source wrong

---

## SECTION 7 – OUTPUT QUALITY & VERDICT ENGINE

### Verdict Types Supported

| Verdict | Meaning | When Used |
|---------|---------|-----------|
| `VERIFIED_TRUE` | Evidence supports claim | Support score > refute × 1.5 |
| `VERIFIED_FALSE` | Evidence refutes claim | Refute score > support × 1.5 |
| `DISPUTED` | Mixed evidence | Scores are close |
| `UNVERIFIED` | Insufficient decisive evidence | Low confidence |
| `INSUFFICIENT_EVIDENCE` | No evidence found | Empty results |
| `NOT_CHECKABLE` | Not a factual claim | Opinion, prediction, etc. |

### Explanation Depth

**Type-Specific Prompts:**

| Claim Type | Prompt Focus | Word Limit |
|------------|--------------|------------|
| Scientific | Consensus score, journal citations | 80 words |
| Political | Official records, polarization level | 100 words |
| Breaking | Velocity, stability markers | 80 words |
| Generic | Source synthesis | 100 words |

**Quality Issues:**
- Explanations can be generic despite type-specific prompts
- No direct source quotes included
- Evidence snippets truncated to 200 chars

### Traceability to Sources

| Aspect | Implementation |
|--------|----------------|
| Source URLs | ✅ Stored in `EvidenceItem.source_url` |
| Source domains | ✅ Stored and displayed |
| Evidence snippets | ✅ First 200 chars included |
| Full article text | ❌ Not stored |
| Exact passage matching | ❌ Not implemented |

### Transparency of Uncertainty

**PARTIALLY IMPLEMENTED**

- Confidence score (0-1) is included
- `DISPUTED` verdict acknowledges conflicting evidence
- Strategy stats show metadata (velocity, polarization)

**Missing:**
- Confidence intervals
- Per-evidence confidence breakdown
- "We don't know" explicit messaging
- Uncertainty sources explanation

### Where Output Looks Confident But Is Not

> [!WARNING]
> **High-Risk Scenarios:**
> 1. **Single authoritative source** → 95% confidence even if only one fact-check exists
> 2. **Keyword debunk detection** → May incorrectly flag discussing articles
> 3. **Political claims with no .gov results** → Falls back to generic search with lower reliability
> 4. **Scientific claims without PubMed hits** → Returns UNVERIFIED but no explanation why

---

## SECTION 8 – FAILURE MODES

### 1. Hallucinated Verification

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM inventing evidence | HIGH | LLM only used for explanation, not verdict |
| Stance misclassification | MEDIUM | Heuristic guardrails for debunk keywords |
| False confidence | MEDIUM | Veto power for authoritative sources |

### 2. Shallow Retrieval

| Risk | Severity | Example |
|------|----------|---------|
| Missing relevant sources | HIGH | PubMed may not index recent papers |
| Single-pass limitation | HIGH | Novel claims get shallow coverage |
| Query formulation failure | MEDIUM | Poor keywords → empty results |

### 3. Entity Mismatch

| Risk | Severity | Example |
|------|----------|---------|
| Wrong person | HIGH | "Gandhi said X" → which Gandhi? |
| Geographic confusion | MEDIUM | "Georgia" → US state vs country |
| Temporal entity | MEDIUM | "The President" → of which era? |

### 4. Wrong Event Linking

| Risk | Severity | Example |
|------|----------|---------|
| Unrelated articles matched | HIGH | "COVID vaccine" claim → influenza study cited |
| Similar event confusion | MEDIUM | 2020 election vs 2024 election |
| Retroactive sourcing | LOW | Old article cited for recent claim |

### 5. Outdated Confirmation

| Risk | Severity | Example |
|------|----------|---------|
| Citing old "true" | HIGH | "Pluto is a planet" verified by 1990s sources |
| Ignoring retractions | MEDIUM | Scientific strategy catches this |
| Stale fact-checks | MEDIUM | Fact-check from 2019 for 2026 event |

### 6. Narrative Bias

| Risk | Severity | Mitigation |
|------|----------|------------|
| Political lean in sources | MEDIUM | Bias map in political strategy |
| Cultural blind spots | HIGH | India-centric bias map |
| Popularity ≠ Truth | MEDIUM | No social proof correction |

### 7. Prompt Leakage

| Risk | Severity | Notes |
|------|----------|-------|
| System prompt exposure | LOW | Gemini may leak instructions |
| Jailbreak vulnerability | MEDIUM | No adversarial prompt filtering |

### 8. Source Overtrust

| Risk | Severity | Example |
|------|----------|---------|
| .gov = always right | HIGH | Government can publish errors |
| Wikipedia = authoritative | MEDIUM | Recently edited pages |
| Fact-check = final | MEDIUM | Fact-checkers disagree |

---

## SECTION 9 – SECURITY, ABUSE & ADVERSARIAL INPUTS

### Deliberately Misleading Wording

**VULNERABLE**

| Attack | System Response |
|--------|-----------------|
| "Studies show vaccines cause autism" | May find supporting anti-vax articles |
| "Many people say..." | Weak qualifying language not filtered |
| Gish gallop (many false claims) | Each processed independently, no pattern detection |

### Mixed True and False Claims

**PARTIALLY HANDLED**

The system extracts multiple claims and processes each independently. However:
- No cross-claim consistency checking
- True claims can provide cover for false ones
- No "claim sandwich" detection

### Sarcastic or Rhetorical Claims

**NOT HANDLED**

```
"Oh sure, the Earth is totally flat."
```

This would likely be classified as a factual claim and investigated, ignoring sarcasm markers.

### Politically Sensitive Framing

**PARTIALLY HANDLED**

The political strategy includes:
- Bias map (LEFT/RIGHT/CENTER)
- Polarization detection
- Official record prioritization

**Gaps:**
- No neutrality scoring of output
- No both-sides requirement
- India-US-UK bias only

### Emotionally Manipulative Text

**NOT HANDLED**

The system does not detect or adjust for:
- Emotional language ("shocking!", "unbelievable!")
- Fear-mongering patterns
- Outrage bait
- Victim narratives

---

## SECTION 10 – SCALABILITY & ENGINEERING

### Modularity of Components

**WELL DESIGNED** ✅

| Aspect | Rating | Notes |
|--------|--------|-------|
| Strategy Pattern | ✅ Excellent | Easy to add new strategies |
| Singleton Services | ✅ Good | Controlled instantiation |
| Data Models | ✅ Good | Clean dataclasses |
| API Structure | ✅ Good | v1/v3 versioning |

### Ability to Replace Models/Tools

| Component | Replaceable? | Notes |
|-----------|--------------|-------|
| Stance Detector | ✅ Easy | `StanceDetector` class abstraction |
| LLM Provider | ✅ Easy | Gemini + Groq fallback exists |
| Searchers | ✅ Easy | Each searcher is independent class |
| Deepfake Model | ⚠️ Medium | Tied to EfficientNet architecture |

### Cost Drivers

| Resource | Current | At Scale |
|----------|---------|----------|
| Gemini API | ~$0.01/request | PRIMARY COST |
| Groq API | Free tier | Limited fallback |
| DuckDuckGo | Free (scraping) | May get blocked |
| PubMed | Free | Rate limited |
| Compute (ML models) | ~4GB RAM | Scales linearly with concurrency |

### Latency Risks

| Stage | Latency | Risk |
|-------|---------|------|
| Input Processing | <500ms | Low |
| Claim Extraction | 1-3s (if LLM) | Medium |
| Investigation | 3-15s | **HIGH** |
| Stance Detection | 100-200ms/item | Medium |
| LLM Explanation | 1-3s | Medium |

**TOTAL: 5-20 seconds per claim**

### Data Storage Structure

**MINIMAL**

| What | Stored? | Where |
|------|---------|-------|
| User accounts | ✅ | PostgreSQL |
| Analysis history | ✅ | PostgreSQL |
| Evidence items | ❌ | Not persisted |
| Claim database | ❌ | No deduplication |
| Known misinfo DB | ⚠️ | JSON file (planned) |

### API-First Design Suitability

**GOOD** ✅

- FastAPI with OpenAPI docs
- Clean endpoint structure
- JSON responses
- Async throughout

---

## SECTION 11 – REALISTIC LIMITATIONS

> [!IMPORTANT]
> **Hard limitations that cannot be fixed with engineering:**

### 1. Cannot Determine Intent

The system can determine if content is FALSE but cannot determine if it was DELIBERATELY false. Disinformation detection requires:
- Author identification
- Historical behavior patterns
- Coordination network analysis
- None of which this system has.

### 2. Cannot Access Paywalled/Private Sources

Significant evidence may exist behind:
- Academic paywalls
- Mainstream news paywalls
- Court document databases
- Internal communications

### 3. Cannot Verify Very Recent Events

For breaking news within hours:
- No sources exist yet
- Reporting is fluid
- The "truth" is unknown even to experts

### 4. Cannot Handle Non-English Content

The entire pipeline assumes English:
- spaCy model: `en_core_web_sm`
- Search queries: English
- Entity matching: English names

### 5. Cannot Detect Deepfakes in Compressed Content

The EfficientNet model is trained on high-quality images. Heavily compressed WhatsApp/social media content may:
- Lose forensic artifacts
- Appear "real" due to compression smoothing

### 6. Cannot Compete with Professional Fact-Checkers

Human fact-checkers can:
- Call sources directly
- Access non-public information
- Apply institutional knowledge
- Spend hours on single claims

This system cannot replicate investigative journalism.

### 7. Ground Truth Problem

For genuinely contested facts (historical debates, scientific frontiers), there IS no authoritative truth. The system will:
- Return DISPUTED or UNVERIFIED
- Cannot resolve genuinely open questions

---

## SECTION 12 – PRIORITIZED ROADMAP

### Top 3 Architectural Improvements

#### 1. Implement Iterative Retrieval Engine

**What:** Replace single-pass search with multi-round investigation that follows leads.

**Why:** Current system retrieves once and synthesizes. Real investigation requires:
- Initial search → extract entities/claims from results → re-search
- Follow source chains to original reporting
- Verify quotes by finding primary sources

**How:**
```python
class IterativeInvestigator:
    MAX_ROUNDS = 3
    
    async def investigate(self, claim):
        evidence = EvidenceCollection()
        for round in range(self.MAX_ROUNDS):
            new_evidence = await self.search(claim, evidence.leads)
            evidence.merge(new_evidence)
            if evidence.is_sufficient():
                break
```

---

#### 2. Add Persistent Claim/Evidence Database

**What:** Store all claims and evidence with deduplication and linking.

**Why:**
- Same claim analyzed multiple times = wasted API calls
- Trending claim detection requires history
- Evidence accumulation over time improves accuracy

**How:**
- PostgreSQL tables: `claims`, `evidence`, `claim_evidence`, `entities`
- Embedding-based deduplication (Sentence Transformers)
- Canonical claim IDs for tracking

---

#### 3. Implement Entity Extraction-Linking-Disambiguation Pipeline

**What:** Systematic NER → Wikidata linking → disambiguation.

**Why:** Current entity handling is regex-based and incomplete. Real forensics requires:
- Knowing WHO/WHAT/WHERE/WHEN precisely
- Linking to knowledge graphs
- Disambiguating homonyms

**How:**
- spaCy NER is already loaded, use it
- Wikidata entity search for each entity
- Disambiguation via context (e.g., "Gandhi" + "assassination" → Mahatma Gandhi)

---

### Top 3 Research-Quality Improvements

#### 1. Add Source Authority Scoring

**What:** Dynamic source trust based on:
- Domain expertise (medical journals > blogs for medical claims)
- Recency of content
- Source independence (not copying from each other)

**Why:** Current trust scores are static. A blog with "85 trust" shouldn't outweigh a dedicated fact-checker with "80 trust" just because of domain preset.

---

#### 2. Implement Temporal Evidence Filtering

**What:** Extract publication dates, filter by claim timeframe, prefer recent sources.

**Why:** Claim "X happened yesterday" should not cite 2019 articles.

**How:**
- Parse dates from article metadata (trafilatura supports this)
- Store `published_at` in EvidenceItem
- Weight recent evidence higher

---

#### 3. Add Original Reporting Detection

**What:** Detect when multiple sources are copying the same original report.

**Why:** 10 articles that all cite the same AP wire story are not 10 independent sources.

**How:**
- Text similarity between evidence items
- Source domain deduplication (Reuters → AP → same story)
- Credit original, penalize copies

---

### Top 3 Reliability Improvements

#### 1. Add Adversarial Input Sanitization

**What:** Filter/flag sarcasm, rhetorical questions, obviously false framing.

**Why:** Current system will treat "Of course the moon landing was fake" as a serious claim.

**How:**
- Sarcasm detection model (lightweight)
- Rhetorical marker detection ("obviously," "clearly," "everyone knows")
- Flag for human review when detected

---

#### 2. Implement Confidence Calibration

**What:** Ensure 80% confidence means correct 80% of the time.

**Why:** Current confidence scores are algorithmic outputs, not calibrated probabilities.

**How:**
- Build evaluation dataset with ground truth
- Measure actual accuracy at each confidence level
- Apply calibration correction

---

#### 3. Add Fallback for API Failures

**What:** Graceful degradation when external APIs fail.

**Why:** DuckDuckGo can block, PubMed can timeout, Gemini has quota limits.

**How:**
- Circuit breaker pattern for each external service
- Local fallbacks (cached popular fact-checks)
- Clear user messaging: "Limited verification available due to service issues"

---

## FINAL VERDICT

### Readiness Assessment

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| System Architecture | 75/100 | 15% | 11.25 |
| Claim Forensics | 45/100 | 20% | 9.00 |
| Research Depth | 30/100 | 20% | 6.00 |
| Evidence Model | 55/100 | 15% | 8.25 |
| Conflict Handling | 40/100 | 10% | 4.00 |
| Verdict Quality | 60/100 | 10% | 6.00 |
| Robustness/Security | 35/100 | 10% | 3.50 |

### **OVERALL READINESS SCORE: 48/100**

---

### Justification

**What Works Well:**
- Clean modular architecture (strategies, services, models)
- Correct principle: LLM for explanation, not verdict
- Type-aware claim processing (scientific ≠ political)
- Multiple evidence sources (PubMed, Wikidata, DDG)
- Deepfake detection with explainability (Grad-CAM)

**What Needs Major Work:**
- Single-pass retrieval is fundamentally shallow
- No entity grounding or temporal awareness
- No persistent storage or claim deduplication
- No adversarial input handling
- Cannot distinguish mis/dis/malinformation
- Over-confidence in thin evidence

**Bottom Line:**

> This system is a **well-architected prototype** demonstrating correct principles for automated fact-checking. It is NOT a production-grade claim forensics platform. With the current implementation, it can:
>
> ✅ Quickly filter obvious viral hoaxes with existing fact-checks  
> ✅ Provide reasonable verdicts on simple factual claims  
> ✅ Detect obvious deepfakes in high-quality images  
>
> It CANNOT:
>
> ❌ Investigate novel claims with any reliability  
> ❌ Handle adversarial or manipulated inputs  
> ❌ Compete with professional fact-checkers  
> ❌ Distinguish misinformation from disinformation  

**Recommended Use Case:**
Academic demonstration, user education about claim verification, pre-screening for human fact-checkers.

**NOT Recommended For:**
Autonomous fact-checking, legal evidence, journalism verification, content moderation at scale.

---

*End of System Analysis*
