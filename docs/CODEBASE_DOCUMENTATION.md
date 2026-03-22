# TruthLens — Complete Codebase Documentation

> **Exhaustive, file-by-file reference** for the TruthLens misinformation-analysis platform.
> Generated 2026-02-12 — V3 Hybrid Pipeline Architecture

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Tech Stack](#2-tech-stack)
3. [Repository Root](#3-repository-root)
4. [Backend — Full File Map](#4-backend--full-file-map)
5. [Frontend — Full File Map](#5-frontend--full-file-map)
6. [End-to-End Data Flow](#6-end-to-end-data-flow)
7. [ML Model Stack](#7-ml-model-stack)
8. [API Reference](#8-api-reference)
9. [Docker Infrastructure](#9-docker-infrastructure)

---

## 1. System Overview

TruthLens is a **full-stack misinformation analysis platform** that takes user input (text, URL, or image), extracts claims, classifies them by type, gathers evidence from multiple sources, and produces **evidence-based verdicts** — never relying on an LLM for the verdict itself.

### Core Principles

| Principle | Meaning |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
|-----------|---------|
| **Evidence-driven verdicts** | Verdicts come from weighted evidence synthesis, never LLM hallucination |
| **LLM-as-Explainer only** | Gemini / Groq used *only* for generating human-readable summaries |
| **Type-aware investigation** | Different claim types lead to different evidence strategies |
| **Non-binary verdicts** | 6 verdict levels: VERIFIED_TRUE, VERIFIED_FALSE, DISPUTED, UNVERIFIED, INSUFFICIENT_EVIDENCE, NOT_CHECKABLE |
| **Zero-cost tools** | Free APIs: DuckDuckGo, Wikipedia, PubMed, Wikidata, Archive.org |

### Two-Phase Architecture

```
Phase 1 — FAST (~1-3 seconds)
  POST /api/v3/analyze
  Input → Extraction → Typing
  Returns claims with "pending" status

Phase 2 — DEEP (~10-45 seconds)
  POST /api/v3/investigate
  Evidence Gathering → Verdict Engine
  Returns verdicts + evidence trail
```

---

## 2. Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Frontend | React 18, TypeScript, Vite |
| Database | PostgreSQL 15 (async via SQLAlchemy + asyncpg) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| ML Models | spaCy, HuggingFace Transformers (BART), Sentence Transformers (MiniLM) |
| LLM Providers | Google Gemini 2.5 Flash (primary), Groq Llama 3 (fallback) |
| Web Scraping | Trafilatura, Requests |
| OCR | EasyOCR |
| Search | DuckDuckGo (ddgs), PubMed (NCBI), Wikipedia REST, Archive.org |
| UI Components | shadcn/ui (Radix primitives), Lucide icons, Recharts, Three.js |
| Containerization | Docker Compose (4 services) |

---

## 3. Repository Root

```
TruthLens/
├── backend/              # FastAPI Python backend
│   ├── app/              # Application source code
│   ├── Dockerfile
│   └── requirements.txt
├── client/               # React + Vite frontend
│   ├── src/
│   ├── Dockerfile        # Dev container
│   └── Dockerfile.prod   # Production Nginx container
├── data/                 # Shared data files (mounted into backend)
├── docs/                 # Architecture docs, implementation plans
│   ├── HYBRID_PIPELINE_V3.md
│   ├── IMPLEMENTATION_PHASES.md
│   └── CODEBASE_DOCUMENTATION.md  (this file)
├── docker-compose.yml    # Multi-service orchestration
├── .env                  # Environment variables (API keys, DB creds)
└── README.md
```

---

## 4. Backend — Full File Map

Base path: `backend/app/`

### 4.1 Entry Point — main.py

Configures and starts the FastAPI application:
- Creates the FastAPI app instance with metadata
- Sets up a lifespan handler that calls `init_db()` on startup to auto-create all database tables
- Configures CORS middleware with origins from `settings.cors_origins`
- Includes all API routers: `auth_router` (/auth), `v1_history_router` (/api/v1/history), `v3_router` (/api/v3)
- Exposes `GET /` (root) and `GET /health` (health check)

---

### 4.2 Core Layer — core/

#### core/config.py — Application Configuration

**Class: Settings(BaseSettings)** — Loads all environment variables using pydantic_settings.

| Setting | Default | Purpose |
|---------|---------|---------|
| database_url | postgresql+asyncpg://truthlens:truthlens_secret@localhost:5432/truthlens | PostgreSQL connection |
| jwt_secret_key | "your_super_secret..." | JWT signing key |
| jwt_algorithm | HS256 | JWT algorithm |
| jwt_expire_minutes | 1440 (24h) | Token expiry |
| gemini_api_key | "" | Google Gemini API key |
| google_factcheck_api_key | "" | Google Fact Check Tools API key |
| gnews_api_key | "" | GNews API key |
| groq_api_key | "" | Groq API key (Llama 3 fallback) |
| backend_cors_origins | JSON array of localhost origins | CORS whitelist |
| pipeline_version | "0.1.0" | Version tag for saved results |

Singleton: `settings = Settings()` — one global instance.

#### core/database.py — Async Database Connection

- Creates an AsyncEngine (SQLAlchemy) from settings.database_url
- Creates an async_sessionmaker factory with expire_on_commit=False
- Defines `Base = declarative_base()` — all ORM models inherit from this
- `get_db()` — FastAPI dependency that yields an AsyncSession per request
- `init_db()` — Calls Base.metadata.create_all to auto-create tables on startup

#### core/security.py — Authentication and Security

| Function | Purpose |
|----------|---------|
| hash_password(password) | Hash with bcrypt (truncates to 72 bytes for bcrypt limit) |
| verify_password(plain, hashed) | Verify bcrypt hash |
| create_access_token(data, expires_delta) | Generate JWT with exp claim |
| verify_token(token) | Decode + validate JWT, return payload or None |
| get_current_user(credentials) | FastAPI Depends — extracts user_id and email from Bearer token |

---

### 4.3 Data Models — models/

#### models/domain.py — Pipeline Domain Types

Defines the data structures that flow through the 6-stage pipeline.

**Enums:**

| Enum | Values | Purpose |
|------|--------|---------|
| InputType | TEXT, URL, IMAGE, SOCIAL | Classifies the source input |
| ClaimType | 11 values (5 checkable + 6 non-checkable) | "The Fork" — determines investigation strategy |
| TemporalState | STABILIZED, DEVELOPING, CONTESTED, HISTORICAL, UNKNOWN | Time-based claim state |

**Checkable ClaimTypes:** SCIENTIFIC_MEDICAL, POLITICAL_ALLEGATION, FACTUAL_STATEMENT, BREAKING_EVENT, QUOTE_ATTRIBUTION

**Non-checkable ClaimTypes:** OPINION, PREDICTION, QUESTION, COMMAND, HYPOTHETICAL, UNKNOWN

**Dataclasses:**

| Class | Stage | Fields |
|-------|-------|--------|
| ProcessedInput | Stage 1 output | text, source_type, source_url, source_domain |
| RawClaim | Stage 2 output | text, sentence_index, char_start, char_end, is_assertion, canonical_id |
| TypedClaim | Stage 3 output | text, claim_type, type_confidence, is_checkable, evidence_strategy, status |
| TemporalContext | Post-investigation | first_seen, last_updated, state, stability_score |

**Constants:**
- EVIDENCE_STRATEGIES — Maps each ClaimType to a human-readable strategy description
- CHECKABLE_TYPES — Set of 5 claim types that can be investigated

#### models/evidence.py — Evidence and Verdict Types

**Enums:**

| Enum | Values |
|------|--------|
| EvidenceType | 11 source types (Google FC, Wikidata, Wikipedia, News, Academic, Archive, Social, Known Misinfo, Web Search, Fact Check, Official Record) |
| Stance | SUPPORTS, REFUTES, NEUTRAL |
| Verdict | VERIFIED_TRUE, VERIFIED_FALSE, DISPUTED, UNVERIFIED, INSUFFICIENT_EVIDENCE, NOT_CHECKABLE |

**SOURCE_WEIGHTS — Weighting table for evidence synthesis:**

| Source Type | Weight | Rationale |
|-------------|--------|-----------|
| OFFICIAL_RECORD | 2.0 | Most authoritative |
| KNOWN_MISINFO | 2.0 | Our verified DB |
| ACADEMIC_PAPER | 1.5 | Peer-reviewed |
| FACT_CHECK / GOOGLE_FACT_CHECK | 1.4 | Professional checkers |
| WIKIDATA | 1.2 | Structured knowledge |
| WIKIPEDIA | 1.0 | Encyclopedic |
| NEWS_ARTICLE | 0.8 | General news |
| WEB_SEARCH | 0.7 | Generic web |
| ARCHIVE | 0.7 | Historical |
| SOCIAL_MEDIA | 0.3 | Least reliable |

**Key Dataclasses:**

| Class | Purpose | Key Property |
|-------|---------|--------------|
| EvidenceItem | Single piece of evidence | weighted_score = stance_confidence x type_weight x trust/100 |
| EvidenceCollection | Container for all evidence | support_score, refute_score, override_verdict |
| VerifiedClaim | Final output — claim + verdict + evidence trail | to_dict() for API response |

#### models/user.py — User ORM Model

SQLAlchemy model mapping to `users` table:

| Column | Type | Notes |
|--------|------|-------|
| id | Integer (PK) | Auto-increment |
| email | String(255) | Unique, indexed |
| hashed_password | String(255) | bcrypt hash |
| full_name | String(255) | Optional profile field |
| avatar_url | String(512) | Optional avatar URL |
| preferences | JSON | User settings dict |
| created_at | DateTime | UTC timestamp |

Relationship: `checks` — one-to-many to Check model.

#### models/check.py — Analysis Result ORM Model

SQLAlchemy model mapping to `checks` table:

| Column | Type | Notes |
|--------|------|-------|
| id | Integer (PK) | Auto-increment |
| user_id | Integer (FK to users.id) | Owner |
| input_text | Text | Original input |
| input_url | String(2048) | Source URL if applicable |
| claim | Text | Extracted claim text |
| domain_score | String(50) | trusted / mixed / low / unknown |
| factcheck_rating | String(100) | External rating |
| factcheck_summary | Text | Summary of fact check |
| stance_summary | JSON | {"supports": N, "refutes": N, ...} |
| verdict | String(100) | Final verdict string |
| confidence | String(20) | high / medium / low |
| explanation | Text | LLM-generated explanation |
| pipeline_version | String(20) | "0.1.0" |
| created_at | DateTime | UTC timestamp |

---

### 4.4 Services — services/

This is the heart of the system — all business logic lives here.

```
services/
├── models/              # ML model singleton
│   └── model_manager.py
├── input/               # Stage 1: Input Processing
│   ├── gateway.py
│   ├── text_handler.py
│   ├── url_scraper.py
│   └── ocr_engine.py
├── extraction/          # Stage 2: Claim Extraction
│   ├── claim_extractor_v3.py
│   └── crux_extractor.py
├── normalization/       # Stage 3: Claim Deduplication
│   └── normalizer.py
├── typing/              # Stage 4: Claim Classification ("The Fork")
│   └── claim_classifier.py
├── investigation/       # Stage 5: Deep Investigation
│   ├── orchestrator.py
│   ├── verdict_engine.py
│   ├── synthesizer.py
│   ├── stance_detector.py
│   ├── explanation.py
│   ├── strategies/      # Strategy Pattern (per claim type)
│   │   ├── base.py
│   │   ├── factory.py
│   │   ├── scientific.py
│   │   ├── political.py
│   │   ├── breaking.py
│   │   └── generic.py
│   └── searchers/       # Evidence Source Adapters
│       ├── duckduckgo.py
│       ├── pubmed.py
│       ├── wikipedia.py
│       └── archive.py
├── evidence/            # External Evidence Services
│   ├── known_misinfo_checker.py
│   ├── google_factcheck.py
│   ├── wikidata_verifier.py
│   └── source_trust.py
└── temporal/            # Time Context Analysis
    └── time_context.py
```

#### services/models/model_manager.py — ML Model Singleton

**Class: ModelManager** — Singleton pattern, loads all ML models once at startup.

| Model | Library | Purpose |
|-------|---------|---------|
| en_core_web_sm | spaCy | Sentence splitting, POS tagging, NER, dependency parsing |
| facebook/bart-large-mnli | HuggingFace | Zero-shot classification for both claim typing AND stance detection |
| all-MiniLM-L6-v2 | SentenceTransformers | Semantic embeddings for claim normalization/deduplication |

One BART model serves two tasks (claim classification + stance detection). This saves ~1GB RAM compared to loading separate models.

**Key methods:** `get_model_manager()`, `get_embedding(text)`, `reset()`

#### services/input/gateway.py — Input Router (Stage 1)

**Class: InputGateway** — Routes input to the correct handler based on InputType:

| InputType | Handler |
|-----------|---------|
| TEXT | TextHandler.process() |
| URL | URLScraper.process() |
| IMAGE | OCREngine.process() |
| SOCIAL | TextHandler.process() (fallback) |

All handlers return `ProcessedInput(text=..., source_type=..., ...)`.

#### services/input/text_handler.py

**Class: TextHandler** — Simplest handler. Validates non-empty input, normalizes whitespace, returns ProcessedInput.

#### services/input/url_scraper.py

**Class: URLScraper** — Web content extraction.
- Validates URL format (scheme + netloc)
- Fetches page with custom User-Agent (Chrome impersonation to bypass 403s)
- Falls back to trafilatura.fetch_url() if requests fails
- Extracts main article text using trafilatura.extract()
- Returns ProcessedInput with source_url and source_domain

#### services/input/ocr_engine.py

**Class: OCREngine** — Image-to-text via EasyOCR.
- Lazy-loaded — EasyOCR reader initialized only on first use (heavy import)
- Handles data:image/...;base64,... format
- Decodes base64 to temp file, runs reader.readtext(path, paragraph=True), combines text
- Cleans up temp file after processing

#### services/extraction/claim_extractor_v3.py — Claim Extraction (Stage 2)

**Class: ClaimExtractorV3** — Over-extraction strategy (false positives OK, false negatives NOT OK).

Two extraction modes:

| Method | Engine | Use Case |
|--------|--------|----------|
| extract(input) | spaCy NLP | Default — splits sentences, checks for assertions |
| extract_crux(input) | Gemini LLM | For long articles — extracts core "crux" claims |

**extract() logic:**
1. Parse text with spaCy: self.models.nlp(text)
2. Iterate over sentences
3. Split compound sentences by comma if parts >= 3 words
4. For each sub-sentence, check:
   - `_is_assertion()` — Has subject + verb, >= 3 words, not a question
   - `_might_be_claim()` — Has entities, numbers, claim keywords, or opinion keywords
5. If either passes, create RawClaim

**CLAIM_KEYWORDS:** cause, proven, linked, study, research, confirmed, announced, reported, according, claim, found, show, reveal, discover, evidence, scientist, expert, official

#### services/extraction/crux_extractor.py — LLM-Based Claim Extraction

**Class: CruxExtractor** — Uses Gemini 2.5 Flash to extract "crux" claims.
- Disabled if GEMINI_API_KEY is not set
- Prompt instructs the LLM to extract top N most critical, verifiable factual claims
- Returns as JSON list of strings, converted to RawClaim objects
- Falls back gracefully on failure

#### services/normalization/normalizer.py — Claim Deduplication (Stage 3)

**Class: ClaimNormalizer** — Singleton, in-memory vector store.

**How it works:**
1. Get embedding for input text using MiniLM: self.models.get_embedding(text)
2. Compute cosine similarity against all known claims
3. If similarity >= 0.80 — claim is a duplicate, return cached result
4. If no match — register as new canonical claim, generate MD5 hash ID

Cache structure: `List[Tuple[np.ndarray, Dict]]` — embedding + claim metadata.

Production note: Would be replaced with pgvector or Pinecone for persistent vector search.

#### services/typing/claim_classifier.py — Claim Classification (Stage 4 — "The Fork")

**Class: ClaimClassifier** — The critical routing decision.

**Three-tier classification logic:**

```
Input: RawClaim text

TIER 1: Quick Keyword Checks (fast, no ML)
  ? → QUESTION
  "do this", "subscribe" → COMMAND
  "what if", "imagine" → HYPOTHETICAL
  "will be", "by 2030" → PREDICTION
  "best", "i think" → OPINION

TIER 2: Domain Keyword Boosting (fast, no ML)
  "vaccine", "covid", "cancer" → SCIENTIFIC_MEDICAL (0.95 confidence)
  "election", "trump", "biden" → POLITICAL_ALLEGATION (0.95)
  "fake", "scam", "hoax" → FACTUAL_STATEMENT (0.95)

TIER 3: Zero-Shot Classification (BART-large-mnli)
  Runs only if tiers 1-2 don't match
  Labels: scientific, political, factual, misconception, breaking, opinion, quote
  Maps result to ClaimType enum
```

Why this hybrid approach? Keyword boosting handles obvious cases instantly without waiting for ML inference (~200ms per call). The ML model handles ambiguous cases.

#### services/investigation/orchestrator.py — Investigation Pipeline (Stage 5)

**Class: InvestigationOrchestrator** — Runs the two-phase investigation.

```
InvestigationOrchestrator.investigate(claim)

PHASE 1: Quick Checks (fast, cheap, authoritative)
  KnownMisinfoChecker.check() → if matched → RETURN immediately
  WikidataVerifier.quick_fact_check() → if verified → RETURN
  GoogleFactCheck.search() → if definitive → RETURN

PHASE 2: Deep Investigation (Strategy Pattern)
  StrategyFactory.get_strategy(claim_type) → select strategy class
  strategy.execute(context) → gather evidence (with 45s timeout)
  Merge results into EvidenceCollection
  Propagate strategy verdict + stats
```

Early termination: If Phase 1 finds a definitive answer (known misinfo, Wikidata fact, or high-confidence fact check), the system skips Phase 2 entirely.

#### services/investigation/verdict_engine.py — Verdict Determination

**Class: VerdictEngine** — Main entry point for Phase 2.

```
VerdictEngine.verify(typed_claim)
  Non-checkable? → return NOT_CHECKABLE immediately
  orchestrator.investigate(claim) → gather evidence
  No evidence? → return INSUFFICIENT_EVIDENCE
  Strategy override exists? → use it directly
  Otherwise → synthesizer.synthesize(evidence, claim_text)
  explanation_service.generate_explanation(result) → enrich summary
```

**CRITICAL RULE:** The verdict is NEVER determined by an LLM. The explanation service only generates the human-readable summary text.

#### services/investigation/synthesizer.py — Evidence Synthesis

**Class: EvidenceSynthesizer**

**Step 1: Stance Detection** — For each evidence item with NEUTRAL stance, run StanceDetector.detect() to determine SUPPORTS, REFUTES, or NEUTRAL. Exception: OFFICIAL_RECORD items are never re-evaluated.

**Step 2: Trust Scoring** — Ensure each item has a trust score via SourceTrustScorer.

**Step 3: Weighted Voting**
```
support_score = sum(item.weighted_score for SUPPORTS items)
refute_score  = sum(item.weighted_score for REFUTES items)
```

**Step 4: Verdict Determination**

| Condition | Verdict | Confidence |
|-----------|---------|------------|
| Authoritative source REFUTES | VERIFIED_FALSE | >= 0.95 (VETO POWER) |
| Authoritative source SUPPORTS | VERIFIED_TRUE | >= 0.90 |
| Total < 2 items AND score < 0.2 | INSUFFICIENT_EVIDENCE | 0.0 |
| Refute > Support x 1.5 | VERIFIED_FALSE | refute/total |
| Support > Refute x 1.5 | VERIFIED_TRUE | support/total |
| Mixed | DISPUTED | 0.5 |

**Veto Power:** If ANY authoritative source (Known Misinfo DB, Wikidata, Fact Checker) refutes the claim, it overrides all web snippets that might "support" the myth.

#### services/investigation/stance_detector.py — AI Stance Detection

**Class: StanceDetector** — Uses BART-large-mnli for NLI-based stance detection.

Input: Claim text + evidence text.
Output: `{label: SUPPORTS|REFUTES|NEUTRAL, score: float, raw_scores: {...}}`

Hypothesis template: "Based on this text, the claim '{claim}' is {true/false/unrelated/discussing}."

Four candidate labels: true, false, unrelated, discussing the myth

**Debunk Guardrail:** If evidence contains ["myth", "hoax", "debunk", "disproven", ...], Support score is zeroed out, and that weight is redistributed to Refute (80%) and Discuss (20%). This prevents a Wikipedia debunking article from being classified as "supporting" the myth just because it mentions it.

Threshold: A label needs > 0.40 score to win.

#### services/investigation/explanation.py — LLM Explanation Service (Stage 6)

**Class: ExplanationService** — Generates human-readable explanations.

Provider cascade:
1. **Gemini 2.5 Flash** (primary) — if GEMINI_API_KEY is set
2. **Groq Llama 3-70B** (fallback) — if GROQ_API_KEY is set
3. **None** — returns raw synthesizer summary

Prompt customization per ClaimType:
- Scientific claims — mention consensus, methodology quality
- Political claims — mention source bias, official records
- Breaking news — mention velocity, developing situation
- Default — balanced analysis

Also supports: explain_media() for image analysis using Gemini Vision.

---

### Investigation Strategies — services/investigation/strategies/

#### strategies/base.py — Strategy Contract

| Class | Purpose |
|-------|---------|
| InvestigationDepth | Enum: QUICK, STANDARD, DEEP |
| InvestigationContext | Immutable dataclass passed to strategies (frozen=True) |
| InvestigationResult | Standard return type: verdict, confidence, evidence, stats |
| InvestigationStrategy | ABC with execute(ctx) -> InvestigationResult |

#### strategies/factory.py — Strategy Registry

**Class: StrategyFactory** — Maps ClaimType to Strategy class.

| ClaimType | Strategy |
|-----------|----------|
| SCIENTIFIC_MEDICAL | ScientificStrategy |
| POLITICAL_ALLEGATION | PoliticalStrategy |
| BREAKING_EVENT | BreakingNewsStrategy |
| All others | GenericStrategy (fallback) |

#### strategies/scientific.py — Scientific Claims

**Class: ScientificStrategy** — Searches PubMed for academic evidence.

Process:
1. Hierarchical search: Meta-analyses → Systematic reviews → Consensus → Raw query
2. Deduplicate results by URL
3. Stance detection on each paper's snippet
4. Retraction handling: If title/snippet contains "retracted" → force REFUTES stance
5. Weighting: Meta-analyses x2.0, Systematic reviews x1.5
6. Consensus calculation: net_score = (weighted_support - weighted_refute) / total_weight
7. Verdict: If confidence < 0.3 → UNVERIFIED; else follows net direction

Returns: strategy_stats: {weighted_support, weighted_refute, total_papers}

#### strategies/political.py — Political Claims

**Class: PoliticalStrategy** — Multi-source verification with bias awareness.

**BIAS_MAP:** Hardcoded bias directions for major news domains:
- RIGHT: foxnews.com, dailymail.co.uk, breitbart.com
- LEFT: msnbc.com, cnn.com, huffpost.com
- CENTER: reuters.com, apnews.com, bbc.com

Process:
1. Official records search: DuckDuckGo with site:gov filters
2. Broad web search: General DuckDuckGo search
3. Wikidata verification: Attempts structured fact check
4. Bias analysis: Categorizes sources by political leaning
5. Consensus calculation: Weighs official records higher (trust=100)
6. Verdict: Considers bias balance when evidence is mixed

Returns: strategy_stats: {consensus_score, source_bias}

#### strategies/breaking.py — Breaking News Claims

**Class: BreakingNewsStrategy** — Focuses on recency and confirmation velocity.

STABILITY_MARKERS_UNSTABLE: "developing story", "unconfirmed", "reportedly", "just in", "breaking", "preliminary"

Process:
1. Temporal search: DuckDuckGo with time='d' filter (last 24 hours)
2. Source counting: Track unique source domains
3. Stability analysis: Count unstable keyword occurrences

| Condition | Verdict | Status |
|-----------|---------|--------|
| 0 sources | UNVERIFIED | SILENT |
| < 3 sources | UNVERIFIED | LOW_VELOCITY |
| > 30% unstable markers | DEVELOPING | Developing |
| Multiple stable sources | VERIFIED_TRUE | STABLE |

Returns: strategy_stats: {velocity, unstable_ratio, status}

#### strategies/generic.py — Fallback Strategy

**Class: GenericStrategy** — Broad search for unspecialized claims.

Runs in parallel:
- DuckDuckGo web search (5 results)
- Wikipedia article extraction (1 article)

Returns UNVERIFIED verdict with raw evidence (lets the synthesizer make the call).

---

### Search Adapters — services/investigation/searchers/

#### searchers/duckduckgo.py

**Class: DuckDuckGoSearcher** — Free web search, no API key needed.
- Uses ddgs library (v8+ sync)
- Runs sync search in asyncio.to_thread() to avoid blocking
- 3 retries with exponential backoff (2s, 4s, 6s)
- Supports time filters: 'd' (day), 'w' (week), 'm' (month), 'y' (year)
- Returns List[SearchResult] with title, URL, snippet, domain

#### searchers/pubmed.py

**Class: PubMedSearcher** — Scientific literature via NCBI Entrez API.
- Step 1: esearch.fcgi — Search for PubMed IDs matching query
- Step 2: esummary.fcgi — Fetch metadata (title, journal, date) for those IDs
- Async via httpx.AsyncClient
- No API key required (uses email for NCBI compliance)

#### searchers/wikipedia.py

**Class: WikipediaSearcher** — Wikipedia REST + Search API.
- search() — OpenSearch API for article discovery
- get_summary() — REST API /page/summary/{title} for article extract
- get_extract_for_claim() — Combined search + summary pipeline
- Custom User-Agent: "TruthLens/1.0 (fact-checking)"

#### searchers/archive.py

**Class: ArchiveOrgSearcher** — Wayback Machine snapshot lookup.
- Checks if a URL has archived versions via archive.org/wayback/available
- Returns closest snapshot with timestamp

---

### Evidence Services — services/evidence/

#### evidence/known_misinfo_checker.py

**Class: KnownMisinfoChecker** — Pattern-matching against a local JSON database.
- Loads data/known_misinformation.json on init
- Each entry has patterns (keyword list), verdict, confidence, reason, sources
- Matching: Requires >= max(2, len(patterns)-1) of all patterns to match
- Example: "covid vaccines cause autism" matches ["vaccine", "autism", "cause"]
- Returns MisinfoMatch dataclass

#### evidence/google_factcheck.py

**Class: GoogleFactCheck** — Google Fact Check Tools API.
- GET factchecktools.googleapis.com/v1alpha1/claims:search
- Requires API key (tries gemini_api_key as fallback)
- Returns raw claim review data with publisher, rating, URL

#### evidence/wikidata_verifier.py

**Class: WikidataVerifier** — Structured fact verification via Wikidata SPARQL.

quick_fact_check(claim_text) — Attempts to parse and verify factual claims.

Supported patterns:
- "X's capital is Y" → lookup P36 (capital)
- "X is the president of Y" → lookup P6 (head of government)
- "X was born in Y" → lookup P19 (place of birth)
- And 20+ more property patterns

Process:
1. Regex to extract entity + property + claimed value
2. _find_entity() → Wikidata entity search API → get Q-number
3. _get_property_value() → SPARQL query → get actual value
4. _compare_values() → Fuzzy string match (case-insensitive, synonym handling)

#### evidence/source_trust.py

**Class: SourceTrustScorer** — Domain reputation scoring.

Loads data/domain_trust_scores.json:

| Score Range | Category | Examples |
|-------------|----------|----------|
| 90-100 | highly_trusted | Reuters, AP, PubMed, WHO |
| 70-89 | generally_trusted | NYT, BBC, Guardian |
| 50-69 | mixed_reliability | Partisan outlets |
| 30-49 | low_trust | Tabloids, opinion sites |
| 0-29 | very_low_trust | Known misinfo sources |

Helper methods: is_fact_checker(domain), is_academic(domain), is_government(domain)

---

### services/temporal/time_context.py — Time Analysis

**Class: TimeContextService** — Analyzes evidence age.
- Extracts dates from evidence text via regex (YYYY-MM-DD)
- Falls back to keyword detection ("today", "yesterday")
- Determines temporal state:
  - < 24h → DEVELOPING (stability: 0.2)
  - > 30 days → STABILIZED (stability: 0.9)
  - > 1 year → HISTORICAL (stability: 1.0)
  - Otherwise → CONTESTED (stability: 0.6)

---

### 4.5 API Layer — api/

```
api/
├── auth/
│   └── auth.py       # POST /auth/register, /auth/login, GET/PATCH /auth/me
├── v1/
│   ├── analyze.py     # Legacy V1 endpoint
│   └── history.py     # GET/DELETE /api/v1/history
└── v3/
    ├── router.py      # Router config (prefix: /api/v3)
    └── endpoints/
        └── analyze.py # POST /api/v3/analyze, POST /api/v3/investigate
```

#### api/auth/auth.py — Authentication Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| /auth/register | POST | None | Create user account |
| /auth/login | POST | None | Get JWT token |
| /auth/me | GET | Bearer | Get user profile + analysis count |
| /auth/me | PATCH | Bearer | Update profile (name, avatar, preferences, password) |

#### api/v1/history.py — Analysis History CRUD

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| /api/v1/history | GET | Bearer | List analyses (paginated: skip, limit) |
| /api/v1/history/{id} | GET | Bearer | Get single analysis detail |
| /api/v1/history/{id} | DELETE | Bearer | Delete single analysis |
| /api/v1/history | DELETE | Bearer | Clear all history |

#### api/v3/endpoints/analyze.py — Core V3 Pipeline Endpoints

**POST /api/v3/analyze — Phase 1 (Fast)**

Input: `{text: string}` or `{content: string, input_type: "text"|"url"|"image"}`
Auth: None required

Pipeline:
1. InputGateway.process() → ProcessedInput
2. ClaimExtractorV3.extract_crux() → List[RawClaim]
3. ClaimClassifier.classify() → List[TypedClaim]

Output:
```json
{
  "success": true,
  "claims": [
    {
      "original_text": "COVID vaccines cause autism",
      "claim_type": "scientific_medical",
      "type_confidence": 0.95,
      "is_checkable": true,
      "evidence_strategy": "Scientific consensus check (PubMed, WHO)",
      "status": "Pending evidence analysis"
    }
  ],
  "metadata": { "total_claims": 2, "checkable_claims": 1 }
}
```

**POST /api/v3/investigate — Phase 2 (Deep)**

Input: `{content: string, input_type: "text"|"url"|"image"}`
Auth: Bearer JWT required

Pipeline:
1. InputGateway.process() → ProcessedInput
2. ClaimExtractorV3.extract_crux() → List[RawClaim]
3. ClaimNormalizer.normalize() → Check for cached results
4. ClaimClassifier.classify() → List[TypedClaim]
5. Parallel: asyncio.gather(*[verdict_engine.verify(c) for c in claims]) → List[VerifiedClaim]
6. Save each result to Check table
7. Update normalizer cache

Output:
```json
{
  "success": true,
  "results": [
    {
      "original_text": "COVID vaccines cause autism",
      "claim_type": "scientific_medical",
      "verdict": "verified_false",
      "confidence": 0.97,
      "evidence_summary": "Scientific consensus overwhelmingly refutes...",
      "evidence": [],
      "sources_checked": 8,
      "investigation_time_ms": 4200,
      "strategy_stats": { "weighted_support": 0.2, "weighted_refute": 3.4 }
    }
  ],
  "metadata": { "total_claims": 1, "investigation_time_ms": 4500 }
}
```

### 4.6 Data Files — data/

| File | Purpose |
|------|---------|
| known_misinformation.json | Database of pre-verified false claims with keyword patterns |
| domain_trust_scores.json | Categorized trust scores for ~200+ domains |

---

## 5. Frontend — Full File Map

Base path: `client/src/`

### 5.1 App Shell

| File | Purpose |
|------|---------|
| main.tsx | React entry point, renders App into DOM |
| App.tsx | Root component — React Router, theme provider, auth context |
| index.css | Global styles, CSS variables, design tokens |

### 5.2 Pages

| Component | Route | Purpose |
|-----------|-------|---------|
| LandingPage.tsx | / | Marketing landing page with animated sections |
| LoginPage.tsx | /login | Email/password login form |
| RegisterPage.tsx | /register | User registration form |
| Dashboard.tsx | /dashboard | Main app — text/URL/image input + claim analysis |
| InvestigationPage.tsx | /investigate | Deep investigation UI with loading animation + results |
| HistoryPage.tsx | /history | Past analyses list |
| SettingsPage.tsx | /settings | User profile + preferences |
| OrganizationPage.tsx | /organization | Team/org management (placeholder) |
| ProjectsPage.tsx | /projects | Projects view (placeholder) |

### 5.3 Landing Components

| Component | Purpose |
|-----------|---------|
| HeroSection.tsx | Main hero area with headline + CTA |
| HeroGlobe3D.tsx | Three.js interactive 3D globe with city markers and arcs |
| HeroGlobe.tsx | Alternative globe component |
| HeroForensicsDash.tsx | Animated forensics dashboard mockup |
| HeroLiveAnalysis.tsx | Live analysis demo animation |
| HeroMorphingCards.tsx | Morphing card animations |
| FinalHybridStoryComponent.tsx | Scroll-triggered story section |
| BentoGraph.tsx | Bento grid feature highlights |
| ScrollDemo.tsx | Scroll-driven demo section |
| SiteFooter.tsx | Footer with links and branding |
| SmoothScroll.tsx | Smooth scroll wrapper (Lenis) |
| LandingScrollContext.tsx | Shared scroll state context |

### 5.4 Shared / UI Library

Uses shadcn/ui — a component library built on Radix UI primitives.

**shadcn/ui components (in components/ui/):** accordion, alert, alert-dialog, aspect-ratio, avatar, badge, breadcrumb, button, calendar, card, carousel, chart, checkbox, collapsible, command, dialog, dropdown-menu, form, hover-card, input, input-otp, label, menubar, navigation-menu, pagination, popover, progress, radio-group, resizable, scroll-area, select, separator, sheet, sidebar, skeleton, slider, sonner, switch, table, tabs, textarea, toast, toaster, toggle, toggle-group, tooltip

**Custom shared components:**

| Component | Purpose |
|-----------|---------|
| HybridTruthGauge.tsx | Minimalist truth gauge visualization |
| TruthSpectrum.tsx | Verdict spectrum bar |
| StrategyBadge.tsx | Badge showing which strategy was used |
| NeuralStream.tsx | Animated loading (neural synapse animation) |
| ComparisonSlider.tsx | Before/after image slider |
| ComingSoonOverlay.tsx | Coming soon placeholder |
| Navigation.tsx | Top navigation bar |
| ResultsBasic.tsx | Results layout (Basic tier) |
| ResultsCreator.tsx | Results layout (Creator tier) |
| ResultsProfessional.tsx | Results layout (Professional tier) |
| ArticleVerification.tsx | Article-specific verification view |
| ImageVideoUpload.tsx | Image/video upload component |

### 5.5 API Client — lib/

#### lib/api.ts — Backend Communication Layer

All backend API calls are centralized here.

| Function | Backend Endpoint | Purpose |
|----------|-----------------|---------|
| analyzeClaimV3(text) | POST /api/v3/analyze | Phase 1: extract + type claims |
| investigateClaim(content, inputType) | POST /api/v3/investigate | Phase 2: full investigation |
| register(email, password) | POST /auth/register | User registration |
| login(email, password) | POST /auth/login | User login to get JWT |
| getCurrentUser() | GET /auth/me | Get user profile |
| updateProfile(data) | PATCH /auth/me | Update profile |
| getHistory(skip, limit) | GET /api/v1/history | List past analyses |
| deleteHistoryItem(id) | DELETE /api/v1/history/{id} | Delete analysis |
| clearHistory() | DELETE /api/v1/history | Clear all history |

Auth handling: Automatically attaches `Authorization: Bearer <token>` header from localStorage.

---

## 6. End-to-End Data Flow

Example trace for the claim: "COVID vaccines cause autism"

```
USER INPUT
  |
  v
Frontend: Dashboard.tsx → analyzeClaimV3(text)
  |
  | POST /api/v3/analyze
  v
STAGE 1: Input Processing
  InputGateway → TextHandler.process()
  Output: ProcessedInput{text: "covid vaccines cause autism"}
  |
  v
STAGE 2: Claim Extraction
  ClaimExtractorV3.extract_crux()
  → Try Gemini Crux extraction first
  → Fallback to spaCy sentence analysis
  Output: [RawClaim{text: "covid vaccines cause autism"}]
  |
  v
STAGE 4: Claim Typing (THE FORK)
  ClaimClassifier._classify_single()
  → Tier 1: Not a question/command/prediction
  → Tier 2: "vaccine" keyword → SCIENTIFIC_MEDICAL
  Output: TypedClaim{type: SCIENTIFIC, conf: 0.95}
  |
  | Returns to frontend (claims + types)
  v
Frontend: InvestigationPage.tsx → investigateClaim(text, "text")
  |
  | POST /api/v3/investigate
  v
STAGE 3: Normalization
  ClaimNormalizer.normalize()
  → Embed with MiniLM → cosine search
  → Cache miss → register as new canonical claim
  |
  v
STAGE 5: Deep Investigation

  VerdictEngine.verify() → Orchestrator.investigate()

  Phase A (Quick Checks):
    KnownMisinfoChecker → MATCH! "vaccines cause autism"
    Verdict: VERIFIED_FALSE (conf: 0.97)
    → RETURN EARLY (skip Deep Search)

  Phase B (Deep Search - if Phase A didn't return):
    StrategyFactory → ScientificStrategy
    PubMed: "vaccines autism meta-analysis" → 3 papers
    StanceDetector: All REFUTE (Wakefield retracted)
    Consensus: net_score = -0.92 → VERIFIED_FALSE

  |
  v
STAGE 5b: Evidence Synthesis
  EvidenceSynthesizer.synthesize()
  → Detect stance for each evidence item
  → Authoritative VETO check
  → Weighted voting → Verdict
  |
  v
STAGE 6: Explanation Generation
  ExplanationService.generate_explanation()
  → Gemini 2.5 Flash with scientific prompt
  → "The scientific consensus overwhelmingly..."
  |
  v
Save to Database
  Check(user_id, claim, verdict, explanation...)
  Update NormalizerCache
  Return VerifiedClaim.to_dict()
  |
  v
Frontend: Display Results
  HybridTruthGauge, Evidence cards, Strategy badge
```

---

## 7. ML Model Stack

| Model | Library | Size | Loaded At | Used For |
|-------|---------|------|-----------|----------|
| en_core_web_sm | spaCy | ~13MB | Startup | Sentence splitting, NER, POS tagging, dependency parsing |
| facebook/bart-large-mnli | HuggingFace | ~1.6GB | Startup | Zero-shot classification (claim typing) AND stance detection (NLI) |
| all-MiniLM-L6-v2 | SentenceTransformers | ~80MB | Startup | 384-dim embeddings for semantic claim dedup |
| gemini-2.5-flash | Google GenAI | Cloud | On-demand | Crux extraction + explanation generation |
| llama-3-70b-8192 | Groq | Cloud | On-demand | Fallback explanation generation |

Total startup RAM: ~2GB for local models.

---

## 8. API Reference

### Authentication

| Endpoint | Method | Body | Response |
|----------|--------|------|----------|
| /auth/register | POST | {email, password} | {id, email} |
| /auth/login | POST | {email, password} | {access_token, token_type} |
| /auth/me | GET | — | {id, email, full_name, avatar_url, preferences, member_since, total_analyses} |
| /auth/me | PATCH | {full_name?, avatar_url?, preferences?, password?} | Updated profile |

### V3 Pipeline

| Endpoint | Method | Auth | Body | Response |
|----------|--------|------|------|----------|
| /api/v3/analyze | POST | None | {text} | {success, claims[], metadata} |
| /api/v3/investigate | POST | Bearer | {content, input_type} | {success, results[], metadata} |

### History

| Endpoint | Method | Auth | Response |
|----------|--------|------|----------|
| /api/v1/history | GET | Bearer | {items[], total} |
| /api/v1/history/{id} | GET | Bearer | Full check detail |
| /api/v1/history/{id} | DELETE | Bearer | 204 No Content |
| /api/v1/history | DELETE | Bearer | 204 (clears all) |

### Health

| Endpoint | Method | Response |
|----------|--------|----------|
| / | GET | {status: "TruthLens API is running"} |
| /health | GET | {status: "healthy", pipeline_version} |

---

## 9. Docker Infrastructure

### Services

```
postgres:        PostgreSQL 15 Alpine, port 5432
                 Volumes: postgres_data + init scripts
                 Healthcheck: pg_isready

pgadmin:         Database admin UI, port 5050
                 Credentials: admin@truthlens.com / admin123

backend:         FastAPI + ML models, port 8000
                 Depends on: postgres (healthy)
                 Volumes: ./backend → /app (live reload)
                 env_file: .env

client:          React dev server (Vite), port 5173
                 Volumes: ./client/src → /app/src (hot reload)

client-prod:     Nginx production build, port 8080
```

### Environment Variables (.env)

| Variable | Required | Purpose |
|----------|----------|---------|
| POSTGRES_USER | Yes | DB username |
| POSTGRES_PASSWORD | Yes | DB password |
| POSTGRES_DB | Yes | DB name |
| GEMINI_API_KEY | Recommended | Crux extraction + explanations |
| GROQ_API_KEY | Optional | Fallback LLM |
| GOOGLE_FACTCHECK_API_KEY | Optional | Google Fact Check API |
| JWT_SECRET_KEY | Yes (prod) | Token signing |
| GNEWS_API_KEY | Optional | News evidence retrieval (V1 pipeline) |
| DOMAIN_TRUST_CSV_PATH | Optional | Custom path to domain trust CSV |

---

## 10. V1 Legacy Pipeline — Full Documentation

> The V1 pipeline is a **separate, independently-functional** 7-step analysis system that runs alongside V3. It is accessed via `/api/v1/analyze` and uses a different set of service modules. Both pipelines coexist in the same codebase and share the same database.

### 10.1 V1 Architecture Overview

```
V1 Pipeline (7 Steps — Sequential)
  POST /api/v1/analyze

  Step 1: Domain Trust Scoring    → domain_trust.py
  Step 2: Claim Extraction        → claim_extractor.py (spaCy + Gemini)
  Step 3: Fact-Check Lookup       → factcheck.py (Google FC API)
  Step 4: Evidence Retrieval      → news_search.py (GNews API)
  Step 5: Stance Classification   → stance.py (Gemini LLM)
  Step 6: Verdict Aggregation     → aggregation.py (deterministic rules)
  Step 6b: LLM Fallback           → llm_verdict.py (Gemini, only if Step 6 is inconclusive)
  Step 7: Explanation Generation  → explanation.py (Gemini LLM)
```

### 10.2 V1 Services — services/ (root-level, non-subdirectory)

```
services/
├── __init__.py           # Exports all V1 service functions
├── domain_trust.py       # CSV-based domain trust scoring
├── claim_extractor.py    # V1 claim extraction (spaCy + Gemini)
├── factcheck.py          # Google Fact Check API with LLM rating interpretation
├── news_search.py        # GNews API news evidence
├── stance.py             # Gemini-based stance classification
├── aggregation.py        # Deterministic verdict rules
├── llm_verdict.py        # LLM fallback verdict for inconclusive cases
├── explanation.py        # Gemini explanation generation (V1)
└── deepfake.py           # EfficientNet-B0 deepfake detection
```

#### services/__init__.py — V1 Service Registry

Exports all V1 service functions for clean imports in api/v1/analyze.py:

```python
from app.services.domain_trust import score_domain, load_domain_trust_db
from app.services.claim_extractor import extract_claims, extract_candidates, refine_claims
from app.services.factcheck import search_factchecks
from app.services.news_search import search_news
from app.services.stance import classify_all_stances, weighted_stance
from app.services.aggregation import aggregate_verdict
from app.services.explanation import generate_explanation
from app.services.llm_verdict import llm_assess_claim
from app.services.deepfake import analyze_image_for_deepfake, get_deepfake_detector
```

#### services/domain_trust.py — CSV-Based Domain Scoring (V1)

**Functions:**

| Function | Purpose |
|----------|---------|
| load_domain_trust_db() | Loads data/domain_trust_seed.csv into in-memory dict (lazy, singleton) |
| extract_domain(url) | Parses URL, strips www. prefix |
| score_domain(url) | Returns trust_level, trust_score (0-100), category, label, reason |
| get_default_score(trust_level) | Converts label to default numeric score |

**Trust Levels (from CSV):**

| Level | Default Score | Meaning |
|-------|---------------|---------|
| trusted | 85 | Reliable mainstream sources |
| mixed | 55 | Partisan or variable quality |
| low | 20 | Tabloids, opinion-heavy |
| unknown | 50 | Not in database — exercise caution |

**Difference from V3:** V1 uses a CSV file (domain_trust_seed.csv), V3 uses a JSON file (domain_trust_scores.json) with more granular score ranges (0-100).

#### services/claim_extractor.py — V1 Claim Extraction

**Functions:**

| Function | Purpose |
|----------|---------|
| get_nlp() | Lazy-loads spaCy en_core_web_sm (auto-downloads if missing) |
| extract_candidates(text) | Splits text into sentences via spaCy, filters short/question sentences |
| refine_claims(candidates) | Uses Gemini 2.5 Flash to distill top 1-3 verifiable factual claims |
| get_primary_claim(claims) | Returns first (most important) claim |
| extract_claims(text) | Full pipeline: candidates → refine → primary |

**Difference from V3:** V1 uses Gemini for refinement at extraction time. V3 uses CruxExtractor (Gemini) or spaCy-only extraction with assertion detection, then defers classification to a separate step.

#### services/factcheck.py — Google Fact Check API with LLM Interpretation

**RATING_NORMALIZATION** — 60+ static mappings from raw fact-checker ratings to 4 standard labels:

| Standard Label | Maps From |
|----------------|-----------|
| True | true, mostly true, correct, accurate, confirmed, verified, factual |
| False | false, mostly false, pants on fire, incorrect, debunked, hoax, fake, disproven |
| Misleading | misleading, half true, mixture, partly false, out of context, exaggerated |
| Unverifiable | unproven, unverified, no evidence, needs context, insufficient evidence |

**Functions:**

| Function | Purpose |
|----------|---------|
| normalize_rating(rating) | Static mapping lookup, returns None if no match (triggers LLM) |
| llm_interpret_rating(rating, summary, claim, url, source) | Uses Gemini 2.5 Flash to interpret unclear ratings with full context |
| search_factchecks(claim) | Queries Google FC API, normalizes rating (static → LLM fallback) |

**Key Design:** The LLM interpretation step examines the URL pattern (e.g., "debunks-X" in URL → REFUTES) to correctly handle cases where the summary field contains the *claim being checked*, not the conclusion.

#### services/news_search.py — GNews API

**Function: search_news(claim, max_results=5)**
- Calls gnews.io/api/v4/search with API key
- Returns list of articles with title, description, domain, url, source, published_at
- Query truncated to 200 chars
- 10-second timeout

#### services/stance.py — V1 Stance Classification (Gemini-Based)

**Functions:**

| Function | Purpose |
|----------|---------|
| classify_stance(claim, snippet) | Classifies a single snippet's stance using Gemini 2.5 Flash |
| classify_all_stances(claim, articles) | Classifies all articles sequentially |
| weighted_stance(stances_with_domains) | Aggregates stance counts weighted by domain trust |

**Stance Labels:** SUPPORTS, REFUTES, DISCUSS, UNRELATED

**Fallback (no API key):** Simple keyword overlap — if 3+ words match between claim and snippet, returns DISCUSS.

**Weighted Scoring:**
| Trust Level | Weight |
|-------------|--------|
| trusted | 1.0 |
| mixed | 0.5 |
| low | 0.1 |
| unknown | 0.3 |

**Difference from V3:** V1 uses Gemini LLM for stance (expensive, slow). V3 uses BART-large-mnli for NLI-based stance (local, fast, free, with debunk guardrails).

#### services/aggregation.py — V1 Verdict Aggregation

**Function: aggregate_verdict(factcheck_result, stance_summary, domain_trust)**

Deterministic rules — no ML, no LLM:

| Priority | Condition | Verdict | Confidence | Basis |
|----------|-----------|---------|------------|-------|
| 1 | Fact-check found with rating | Map rating → verdict | high | fact_check |
| 2 | refute_score ≥ 1.5 AND > 2× support | Likely False | medium/low | evidence_refutes |
| 3 | support_score ≥ 1.5 AND > 2× refute | Likely True | medium/low | evidence_supports |
| 4 | Mixed scores > 0 | Needs More Verification | low | mixed_evidence |
| 5 | No evidence | Needs More Verification | low | insufficient_evidence |

**Difference from V3:** V1 has 4 verdicts (Likely True, Likely False, Misleading, Needs More Verification). V3 has 6 verdicts (VERIFIED_TRUE, VERIFIED_FALSE, DISPUTED, UNVERIFIED, INSUFFICIENT_EVIDENCE, NOT_CHECKABLE) plus the authoritative veto power system.

#### services/llm_verdict.py — V1 LLM Fallback

**Function: llm_assess_claim(claim)**

Used as FALLBACK when Steps 3-6 produce "insufficient_evidence" or "mixed_evidence":
- Prompts Gemini 2.5 Flash with explicit instructions for known misinformation
- Returns: verdict (Likely True/Likely False/None), confidence (high/medium/low), reasoning
- Maps results: TRUE → "Likely True", FALSE → "Likely False", UNCERTAIN → None (no override)

**Safety:** Only used as last resort. The deterministic aggregator takes priority over the LLM.

#### services/explanation.py — V1 Explanation Service

**Function: generate_explanation(signals)**

Takes all analysis signals and generates a 2-3 sentence user-friendly explanation:
- Primary: Gemini 2.5 Flash with context about claim, verdict, fact-check, stance, domain trust
- Fallback: Template-based explanation using string formatting

**Difference from V3:** V1 explanation is simpler (single function). V3 ExplanationService is a class with provider cascade (Gemini → Groq → None) and claim-type-specific prompts.

### 10.3 V1 API Endpoints — api/v1/analyze.py

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| /api/v1/extract-claim | POST | Bearer | Extract claims for user confirmation before full analysis |
| /api/v1/analyze | POST | Bearer | Run full 7-step verification pipeline |
| /api/v1/analyze-media | POST | Bearer | Deepfake detection on uploaded image/video |

**POST /api/v1/analyze** — Full pipeline execution:
```
Input → Domain Trust → Claim Extraction → Fact-Check → News Search
→ Stance Classification → Verdict Aggregation → (LLM Fallback?) → Explanation
→ Save to DB → Return AnalyzeResponse
```

**POST /api/v1/analyze-media** — Media analysis:
- Accepts: image/jpeg, image/png, image/webp, video/mp4, video/webm, video/quicktime
- Max file size: 50MB
- Routes to deepfake.py → returns MediaAnalysisResponse
- Saves result to Check table with pipeline_version="deepfake-v1"

---

## 11. Deepfake Detection System

> The deepfake detection system is a **fully independent subsystem** that operates outside the text analysis pipelines. It uses a pre-trained EfficientNet-B0 CNN model for binary classification (REAL vs FAKE) and provides visual explanations via Grad-CAM heatmaps.

### 11.1 Architecture

```
services/deepfake.py — DeepfakeDetector class

Model: EfficientNet-B0 (timm)
Weights: backend/models/best_effnetb0.pth
Input: 224×224 RGB image (ImageNet normalization)
Output: 2 classes — Class 0: REAL, Class 1: FAKE
Device: CUDA (GPU) if available, else CPU
```

### 11.2 DeepfakeDetector — Singleton Class

**Initialization (loaded once):**
1. Create EfficientNet-B0 via `timm.create_model('efficientnet_b0', pretrained=False, num_classes=2)`
2. Load trained weights from `backend/models/best_effnetb0.pth`
3. Set up ImageNet preprocessing (Resize 224×224, Normalize mean/std)
4. Register Grad-CAM hooks on `model.conv_head` (last conv layer)

### 11.3 Image Analysis — predict(image_bytes)

**Step 1: Metadata Extraction** — `_extract_metadata(image)`
- Reads EXIF data (Software, Make, Model, DateTime, Artist, Copyright)
- AI Indicator Detection: Checks Software field for Stable Diffusion, Midjourney, DALL-E, ComfyUI, NovelAI, etc.
- Checks image.info for Stable Diffusion generation parameters
- Missing camera info → flagged as suspicious (typical for AI-generated)
- Missing DateTime → flagged

**Step 2: Neural Network Inference**
- Convert to RGB → apply ImageNet transforms → unsqueeze to batch dim
- Forward pass through EfficientNet-B0
- Softmax to get probabilities for REAL and FAKE
- Get predicted class (argmax)

**Step 3: Grad-CAM Heatmap** — `_generate_heatmap(tensor, original_image)`
- Uses gradients captured by backward hooks on conv_head
- Global average pooling of gradients → weight activations
- ReLU → normalize → resize to original image size
- Apply JET colormap → overlay on original image (40% opacity)
- Encode to base64 JPEG → return as data URL

**Step 4: Evidence Assembly**
- Combines metadata evidence + model prediction
- Assigns confidence_level: ≥90% → high, ≥70% → medium, <70% → low

### 11.4 Video Analysis — predict_video(video_bytes)

1. Save bytes to temp file (OpenCV needs file path)
2. Extract 5 evenly-spaced frames using cv2.VideoCapture
3. Run predict() on each frame independently
4. Aggregate results:
   - Average confidence, real_prob, fake_prob across all frames
   - Find the frame with highest fake_probability
5. Final verdict logic:
   - avg_fake > 50% OR max single frame > 80% → **FAKE**
   - Otherwise → **REAL**
6. Cleanup temp file

### 11.5 AI Forensic Enhancement

After neural network prediction, the system optionally calls:
- `ExplanationService.explain_media(image_bytes, verdict, confidence)` — Uses Gemini Vision to provide a natural-language forensic analysis
- Result is prepended to evidence list as "AI Forensic Analysis: ..."

### 11.6 ML Model Details

| Property | Value |
|----------|-------|
| Architecture | EfficientNet-B0 |
| Library | timm (PyTorch Image Models) |
| Weights File | backend/models/best_effnetb0.pth |
| Weight Size | ~20MB |
| Input Resolution | 224 × 224 pixels |
| Classes | 2 (REAL=0, FAKE=1) |
| Normalization | ImageNet (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]) |
| Explainability | Grad-CAM on conv_head layer |
| Video Support | 5-frame sampling with aggregation |
| Device | Auto-detect (CUDA/CPU) |

---

## 12. Complete ML Model Stack (Updated)

| Model | Library | Size | Type | Loaded At | Used For | Pipeline |
|-------|---------|------|------|-----------|----------|----------|
| en_core_web_sm | spaCy | ~13MB | Local | Startup | Sentence splitting, NER, POS tagging, dependency parsing | V1 + V3 |
| facebook/bart-large-mnli | HuggingFace | ~1.6GB | Local | Startup | Zero-shot classification: claim typing AND stance detection (NLI) | V3 |
| all-MiniLM-L6-v2 | SentenceTransformers | ~80MB | Local | Startup | 384-dim embeddings for semantic claim deduplication | V3 |
| EfficientNet-B0 | timm (PyTorch) | ~20MB | Local | On-demand | Binary image classification (REAL vs FAKE) + Grad-CAM heatmaps | Deepfake |
| gemini-2.5-flash | Google GenAI | Cloud | API | On-demand | Crux extraction, V1 stance, V1 claim refinement, rating interpretation, explanation generation | V1 + V3 |
| llama-3-70b-8192 | Groq | Cloud | API | On-demand | Fallback explanation generation | V3 |

**Total local model RAM at startup: ~2GB** (spaCy + BART + MiniLM). EfficientNet adds ~20MB when deepfake is first used.

---

## 13. Data Files

### 13.1 Backend Internal Data — backend/app/data/

| File | Format | Size | Loaded By | Purpose |
|------|--------|------|-----------|---------|
| known_misinformation.json | JSON | ~5KB | KnownMisinfoChecker (V3) | Pre-verified false claims with keyword patterns for instant matching |
| domain_trust_scores.json | JSON | ~15KB | SourceTrustScorer (V3) | Trust scores for ~200+ domains categorized by reliability |

### 13.2 Shared Data — data/ (project root)

| File | Format | Loaded By | Purpose |
|------|--------|-----------|---------|
| domain_trust_seed.csv | CSV | domain_trust.py (V1) | V1 domain trust database with trust_level, category, score, label, notes |
| test_claims.json | JSON | Testing | Pre-defined test claims for manual QA |
| test_results.json | JSON | Testing | Saved results from test runs |

### 13.3 Trained Models — backend/models/

| File | Size | Purpose |
|------|------|---------|
| best_effnetb0.pth | ~20MB | Pre-trained EfficientNet-B0 weights for deepfake detection (2 classes) |

---

## 14. Utility & Testing Scripts

### 14.1 backend/comprehensive_qa_test.py — Full QA Test Suite

Comprehensive automated testing with **50+ test cases** across 10 categories:

| Category | # Tests | Tests For |
|----------|---------|-----------|
| Scientific/Medical | 6 | Vaccines, climate change, 5G, COVID treatments |
| Factual/Historical | 6 | Capitals, historical dates, geography |
| Political | 5 | Election claims, world leaders |
| Opinions | 5 | Subjective statements → should be NOT_CHECKABLE |
| Breaking News / Conspiracies | 4 | Flat earth, moon landing, chemtrails |
| Known Misinformation (DB Hits) | 3 | Should trigger instant match |
| Edge Cases | 5 | Short text, questions, commands, multi-claim, long nonsense |
| Regional/International | 4 | India, Japan, Germany geography |
| Quote Attributions | 2 | Disputed quotes, misattributions |
| Numerical/Statistical | 3 | Pi, population, speed of light |

**Features:**
- Auto-registers/authenticates a test user
- Runs all tests against the V3 investigate endpoint
- Evaluates verdict accuracy AND claim type accuracy
- Lenient matching: "disputed" ≈ "unverified" for scoring
- Generates final report with pass/fail rates, response times, and detailed failure analysis
- Rating system: ≥85% = Excellent, ≥70% = Good, ≥50% = Fair, <50% = Poor

**Usage:** `python comprehensive_qa_test.py` (requires backend running on localhost:8000)

### 14.2 backend/add_user_columns.py — Database Migration

Ad-hoc async migration script that adds 3 columns to the `users` table:
- `full_name` VARCHAR(255)
- `avatar_url` VARCHAR(512)
- `preferences` JSON (default: `{}`)

Handles "duplicate column" errors gracefully (idempotent).

### 14.3 backend/reproduce_stance.py — Stance Debug Script

Standalone test script for debugging NLI stance detection using `roberta-large-mnli`. Tests the premise/hypothesis format with a real claim ("Modi is the first PM...") to verify entailment/contradiction/neutral classification.

---

## 15. Frontend API Client — lib/api.ts (Complete)

### V1 API Functions

| Function | Endpoint | Purpose |
|----------|---------|---------|
| analyzeClaim(data) | POST /api/v1/analyze | V1 full pipeline analysis |
| extractClaim(data) | POST /api/v1/extract-claim | Extract claims for user confirmation |
| analyzeMedia(file) | POST /api/v1/analyze-media | Deepfake detection (FormData upload) |

### V3 API Functions

| Function | Endpoint | Purpose |
|----------|---------|---------|
| analyzeClaimV3(text) | POST /api/v3/analyze | Phase 1: extract + classify claims |
| investigateClaim(content, inputType) | POST /api/v3/investigate | Phase 2: full investigation |
| checkV3Health() | GET /api/v3/health | API health check |

### Auth Functions

| Function | Endpoint | Purpose |
|----------|---------|---------|
| login(data) | POST /auth/login | Login, stores token in localStorage |
| register(data) | POST /auth/register | Create account |
| getUserStats() | GET /auth/me | Get profile + analysis count |
| updateProfile(data) | PATCH /auth/me | Update profile |
| logout() | — | Clears localStorage token |
| isAuthenticated() | — | Checks for token |

### History Functions

| Function | Endpoint | Purpose |
|----------|---------|---------|
| getHistory() | GET /api/v1/history | List past analyses |
| deleteHistoryItem(id) | DELETE /api/v1/history/{id} | Delete single |
| clearAllHistory() | DELETE /api/v1/history | Clear all |

### TypeScript Interfaces

| Interface | Purpose |
|-----------|---------|
| AuthResponse | { access_token, token_type, user? } |
| AnalyzeResponse | V1 analysis result (claim, verdict, confidence, evidence, explanation) |
| V3AnalyzeResponse | V3 Phase 1 (claims with types) |
| V3InvestigateResponse | V3 Phase 2 (verified_claims with evidence) |
| V3VerifiedClaim | Single claim with verdict, evidence[], strategy_stats |
| V3EvidenceItem | Single evidence piece with stance, trust_score, source |
| MediaAnalysisResponse | Deepfake result (verdict, confidence, heatmap, evidence) |
| UserStats | User profile with preferences |
| HistoryItem | Saved analysis record |

### authFetch() — Centralized HTTP Client

- Automatically attaches `Authorization: Bearer <token>` from localStorage
- On 401 → calls logout(), redirects to /login
- On error → parses error body for detail message
- Returns parsed JSON

---

## 16. Frontend Components — Deepfake & Article Verification

### ImageVideoUpload.tsx — Deepfake Analysis UI

| Feature | Detail |
|---------|--------|
| File Input | Drag-and-drop + file picker for images and videos |
| Preview | Shows uploaded image/video preview with base64 data URL |
| Processing Steps | Visual stepper: Preprocessing → Deepfake Model → Forensic Checks → Heatmap Generation → Final Verdict |
| Results | Delegates to ResultsBasic / ResultsCreator / ResultsProfessional based on userMode |
| API | Calls analyzeMedia(file) → MediaAnalysisResponse |

### ArticleVerification.tsx — V1 Article Analysis UI

| Feature | Detail |
|---------|--------|
| Two-Step Flow | Step 1: Extract claim (user confirmation) → Step 2: Full analysis |
| Source Metrics | Displays Credibility, Bias Score, Fact Record, Source Age, Citations |
| Results | Displays verdict with color coding, evidence list with stance badges |
| History | Saves results via addToHistory() + saveCurrentResult() |
| API | Calls extractClaim() then analyzeClaim() |

---

## 17. Complete Dependency List — requirements.txt

| Category | Package | Version | Purpose |
|----------|---------|---------|---------|
| **Core** | fastapi | ≥0.104.0 | Web framework |
| | uvicorn[standard] | ≥0.24.0 | ASGI server |
| | pydantic | ≥2.5.0 | Data validation |
| | pydantic-settings | ≥2.1.0 | Environment config |
| **Database** | sqlalchemy | ≥2.0.0 | Async ORM |
| | asyncpg | ≥0.29.0 | PostgreSQL async driver |
| | alembic | ≥1.12.0 | Database migrations |
| **Auth** | python-jose[cryptography] | ≥3.3.0 | JWT tokens |
| | passlib[bcrypt] | ≥1.7.4 | Password hashing |
| | bcrypt | ≥4.0.0, <5.0.0 | Bcrypt backend (pinned: v5 enforces 72-byte limit) |
| **HTTP** | httpx | ≥0.25.0 | Async HTTP client |
| **NLP** | spacy | ≥3.7.0 | Sentence splitting, NER |
| | google-generativeai | ≥0.3.0 | Gemini API |
| **ML** | transformers | ≥4.36.0 | BART model |
| | torch | ≥2.1.0 | PyTorch runtime |
| | sentence-transformers | ≥2.2.2 | MiniLM embeddings |
| **Scraping** | trafilatura | ≥1.6.0 | Web article extraction |
| | easyocr | ≥1.7.1 | Image text extraction |
| **Search** | ddgs | latest | DuckDuckGo search |
| **LLM** | groq | ≥0.4.0 | Groq Llama 3 fallback |
| **Deepfake** | timm | ≥0.9.12 | EfficientNet model zoo |
| | opencv-python-headless | ≥4.8.0 | Video frame extraction + heatmap |
| | pillow | ≥10.0.0 | Image processing |
| **Uploads** | python-multipart | ≥0.0.6 | File upload parsing |
| **Validation** | email-validator | ≥2.1.0 | Email validation |

---

## 18. V1 vs V3 Pipeline Comparison

| Feature | V1 Pipeline | V3 Pipeline |
|---------|-------------|-------------|
| **Endpoint** | POST /api/v1/analyze | POST /api/v3/analyze + /investigate |
| **Architecture** | Sequential 7-step | Two-phase (Fast + Deep) |
| **Claim Extraction** | spaCy + Gemini refinement | spaCy + CruxExtractor (Gemini) + assertion detection |
| **Claim Classification** | None (single claim) | 11-type classifier (BART + keyword boosting) |
| **Claim Dedup** | None | MiniLM semantic normalization |
| **Evidence Sources** | GNews API (paid) | DuckDuckGo + Wikipedia + PubMed + Archive.org (free) |
| **Fact-Check** | Google FC API + LLM interpretation | Google FC + Known Misinfo DB + Wikidata SPARQL |
| **Stance Detection** | Gemini LLM (expensive) | BART-mnli NLI (local, free) + debunk guardrails |
| **Verdict Logic** | Deterministic rules (4 outcomes) | Strategy-based weighted synthesis (6 outcomes) + veto power |
| **Type-Specific Strategy** | None | Scientific, Political, Breaking News, Generic |
| **Temporal Analysis** | None | TimeContextService (developing vs stabilized) |
| **LLM Usage** | Extraction, stance, interpretation, explanation | Explanation only (LLM-as-Explainer) |
| **Deepfake** | Shared (via V1 endpoint) | Shared (via V1 endpoint) |
| **Verdicts** | Likely True, Likely False, Misleading, Needs More Verification | VERIFIED_TRUE, VERIFIED_FALSE, DISPUTED, UNVERIFIED, INSUFFICIENT_EVIDENCE, NOT_CHECKABLE |
| **Speed** | ~5-15s (sequential API calls) | Phase 1: ~1-3s, Phase 2: ~10-45s (parallel) |
| **Cost** | GNews API key + Gemini tokens per analysis | Free APIs only (Gemini only for explanations) |
