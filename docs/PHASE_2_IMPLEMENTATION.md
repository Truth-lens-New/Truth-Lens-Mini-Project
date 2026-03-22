# 🔬 PHASE 2 IMPLEMENTATION BLUEPRINT

> **The Deep Investigation Engine**  
> **Goal:** Real internet digging, evidence gathering, verdict determination  
> **Estimated Time:** 2 weeks  
> **Status:** Planning

---

## 📋 Table of Contents

1. [Phase Overview](#-phase-overview)
2. [Architecture Diagram](#-architecture-diagram)
3. [Directory Structure](#-directory-structure)
4. [Dependencies](#-dependencies)
5. [Data Models](#-data-models)
6. [Component 1: Wikidata Verifier](#-component-1-wikidata-verifier)
7. [Component 2: Source Trust Database](#-component-2-source-trust-database)
8. [Component 3: Free Searchers](#-component-3-free-searchers)
9. [Component 4: Investigation Orchestrator](#-component-4-investigation-orchestrator)
10. [Component 5: Evidence Synthesizer](#-component-5-evidence-synthesizer)
11. [Component 6: Verdict Determiner](#-component-6-verdict-determiner)
12. [API Endpoints](#-api-endpoints)
13. [Testing Strategy](#-testing-strategy)
14. [Success Criteria](#-success-criteria)
15. [Task Breakdown](#-task-breakdown)

---

## 🎯 Phase Overview

### What Phase 2 Delivers

```
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 2: EVIDENCE ENGINE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INPUT: TypedClaim from Phase 1                                 │
│         (e.g., "COVID vaccines cause autism" → SCIENTIFIC)      │
│                                                                  │
│  PROCESS:                                                        │
│  ├── Level 1: Quick Check (Known facts, fact-checks)           │
│  ├── Level 2: Standard Search (DuckDuckGo, Wikipedia)          │
│  ├── Level 3: Deep Investigation (PubMed, sources)             │
│  └── Synthesis: Stance detection, weighted voting              │
│                                                                  │
│  OUTPUT: Verdict with evidence trail                             │
│         VERIFIED_TRUE | VERIFIED_FALSE | UNVERIFIED | DISPUTED  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 2A vs 2B

| Phase 2A (Core - SYNC) | Phase 2B (Optimization - ASYNC) |
|------------------------|----------------------------------|
| Wikidata verification | Convert to async |
| DuckDuckGo + Wikipedia | Parallel execution |
| Source trust database | Time bounds (45s max) |
| Keyword-based stance | RoBERTa stance detection |
| Verdict engine | Smart stopping |
| Sequential execution | PubMed + Archive.org |
| **May take 30-60s** | **Target: <30s** |

### Key Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2 PRINCIPLES                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ LLM is NEVER used for verdict (only explanation later)      │
│  ✅ Evidence determines verdict (weighted voting)               │
│  ✅ Sources are weighted by trust scores                        │
│  ✅ All evidence sources are traceable                          │
│                                                                  │
│  ❌ NO guessing                                                  │
│  ❌ NO LLM deciding TRUE/FALSE                                  │
│  ❌ NO single-source verdicts                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### ⚠️ Complexity Decision: Hybrid Approach (Option C)

> **Decision:** Start simple, optimize later.

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLEXITY STRATEGY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PHASE 2A: Simple & Synchronous                                 │
│  ══════════════════════════════                                  │
│  • NO time bounds                                                │
│  • NO async/parallel searches                                   │
│  • Sequential: Wikidata → DuckDuckGo → Wikipedia → Done         │
│  • Focus: Get it WORKING first                                  │
│  • Time: May take 30-60s per claim (acceptable for MVP)         │
│                                                                  │
│  PHASE 2B: Optimization Pass                                     │
│  ═══════════════════════════                                     │
│  • ADD time bounds (max 45s)                                    │
│  • ADD async parallel searches                                  │
│  • ADD smart stopping (stop early if confident)                 │
│  • Focus: Make it FAST after it works                          │
│                                                                  │
│  RATIONALE:                                                      │
│  ── Working > Perfect                                            │
│  ── Async adds 3x code complexity                               │
│  ── Easier to debug sync code                                   │
│  ── User can wait 30s for MVP                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation Order:**
1. ✅ Phase 2A: Build all searchers synchronously, test, verify
2. 🔄 Phase 2B: Convert to async, add time bounds, optimize

---

## 🏗️ Architecture Diagram

```
                    ┌────────────────────────────────────────────┐
                    │           Phase 1 Output                   │
                    │  TypedClaim (text, type, is_checkable)     │
                    └─────────────────────┬──────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INVESTIGATION ORCHESTRATOR                        │
│            Phase 2A: Sequential | Phase 2B: Time-bounded            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  STEP 1: Quick Check                                        │    │
│  │  ├── Known Misinformation DB (local JSON)                   │    │
│  │  ├── Google Fact Check API                                  │    │
│  │  └── Wikidata Quick Facts                                   │    │
│  │  → Phase 2A: Always continue to Step 2                      │    │
│  │  → Phase 2B: May STOP early if confident                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  STEP 2: Standard Search                                    │    │
│  │  ├── DuckDuckGo Search (general web)                        │    │
│  │  ├── Wikipedia Lookup (encyclopedia)                        │    │
│  │  └── News API Search (recent news)                          │    │
│  │  → Phase 2A: Run SEQUENTIALLY (simpler)                     │    │
│  │  → Phase 2B: Run in PARALLEL (asyncio.gather)               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  STEP 3: Deep Investigation (scientific claims only)        │    │
│  │  ├── PubMed Search (academic papers)                        │    │
│  │  ├── Archive.org (historical verification)                  │    │
│  │  └── Lead Follower (trace to original source)               │    │
│  │  → Phase 2A: Run SEQUENTIALLY                               │    │
│  │  → Phase 2B: Time-bounded (max 45s total)                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EVIDENCE SYNTHESIZER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. STANCE DETECTION (RoBERTa-large-mnli)                           │
│     For each evidence item:                                          │
│     → Does it SUPPORT, REFUTE, or is NEUTRAL to the claim?          │
│                                                                      │
│  2. SOURCE WEIGHTING                                                 │
│     → Academic paper: 1.5x                                           │
│     → Fact-check org: 1.3x                                           │
│     → News (trusted): 1.0x                                           │
│     → News (untrusted): 0.5x                                         │
│     → Social media: 0.3x                                             │
│                                                                      │
│  3. WEIGHTED VOTING                                                  │
│     support_score = Σ (stance_confidence × source_weight)           │
│     refute_score = Σ (stance_confidence × source_weight)            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    VERDICT DETERMINER                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  if refute_score > support_score * 1.5:                             │
│      verdict = "VERIFIED_FALSE"                                      │
│  elif support_score > refute_score * 1.5:                           │
│      verdict = "VERIFIED_TRUE"                                       │
│  elif evidence_count < 3:                                            │
│      verdict = "INSUFFICIENT_EVIDENCE"                               │
│  else:                                                               │
│      verdict = "DISPUTED"                                            │
│                                                                      │
│  confidence = |refute_score - support_score| / total                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
                    ┌────────────────────────────────────────────┐
                    │           Phase 2 Output                   │
                    │  VerifiedClaim with evidence trail         │
                    └────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

### New Files to Create

```
backend/app/
├── services/
│   ├── evidence/                          # Phase 2A
│   │   ├── __init__.py
│   │   ├── wikidata_verifier.py          # Wikidata SPARQL queries
│   │   ├── google_factcheck.py           # Google Fact Check API
│   │   └── source_trust.py               # Domain trust scores
│   │
│   ├── investigation/                     # Phase 2B
│   │   ├── __init__.py
│   │   ├── orchestrator.py               # Main orchestrator (time-bounded)
│   │   ├── searchers/
│   │   │   ├── __init__.py
│   │   │   ├── duckduckgo.py             # DuckDuckGo search
│   │   │   ├── wikipedia.py              # Wikipedia API
│   │   │   ├── pubmed.py                 # PubMed E-utilities
│   │   │   ├── archive_org.py            # Archive.org Wayback
│   │   │   └── gnews.py                  # GNews API (existing)
│   │   ├── synthesizer.py                # Evidence synthesis
│   │   ├── stance_detector.py            # RoBERTa stance detection
│   │   ├── verdict_engine.py             # Verdict determination
│   │   └── lead_follower.py              # Trace to original source
│   │
│   └── models/
│       └── model_manager.py              # UPDATE: Add RoBERTa
│
├── data/
│   ├── known_misinformation.json         # Local misinfo database
│   ├── domain_trust_scores.json          # Domain trust database
│   └── fact_check_patterns.json          # Common debunked claims
│
├── models/
│   └── evidence.py                       # Evidence data models
│
└── api/v3/endpoints/
    └── analyze.py                        # UPDATE: Add investigation
```

### File Count: 18 new files

---

## 📦 Dependencies

### New Packages Required

```txt
# Already installed (Phase 1)
transformers>=4.36.0
torch>=2.1.0
spacy>=3.7.0
httpx>=0.25.0

# New for Phase 2
aiohttp>=3.9.0          # Async HTTP for parallel searches
SPARQLWrapper>=2.0.0    # Wikidata SPARQL queries
```

### ML Models

| Model | HuggingFace ID | Purpose | Size | Load Time |
|-------|----------------|---------|------|-----------|
| spaCy | `en_core_web_sm` | NLP (existing) | 12 MB | ~2s |
| BART | `facebook/bart-large-mnli` | Claim typing (existing) | 1.6 GB | ~15s |
| RoBERTa | `roberta-large-mnli` | Stance detection | 1.4 GB | ~12s |

**Total first-load: ~30s, Memory: ~5 GB**

### Update `requirements.txt`

```txt
# Phase 2 Dependencies
aiohttp>=3.9.0
SPARQLWrapper>=2.0.0
```

---

## 📊 Data Models

### File: `app/models/evidence.py`

```python
"""
TruthLens Evidence Data Models

Models for evidence gathering and verdict determination.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


class EvidenceType(str, Enum):
    """Types of evidence sources."""
    FACT_CHECK = "fact_check"
    WIKIDATA = "wikidata"
    WIKIPEDIA = "wikipedia"
    NEWS_ARTICLE = "news_article"
    ACADEMIC_PAPER = "academic_paper"
    ARCHIVE = "archive"
    SOCIAL_MEDIA = "social_media"
    KNOWN_MISINFO = "known_misinfo"


class Stance(str, Enum):
    """Stance of evidence relative to claim."""
    SUPPORTS = "supports"
    REFUTES = "refutes"
    NEUTRAL = "neutral"


class Verdict(str, Enum):
    """Final verdict on a claim."""
    VERIFIED_TRUE = "verified_true"
    VERIFIED_FALSE = "verified_false"
    DISPUTED = "disputed"
    UNVERIFIED = "unverified"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_CHECKABLE = "not_checkable"


@dataclass
class EvidenceItem:
    """Single piece of evidence."""
    text: str
    source_url: str
    source_domain: str
    source_type: EvidenceType
    stance: Stance
    stance_confidence: float
    trust_score: int  # 0-100
    retrieved_at: datetime = field(default_factory=datetime.now)
    
    @property
    def weighted_score(self) -> float:
        """Calculate weighted score for synthesis."""
        type_weights = {
            EvidenceType.ACADEMIC_PAPER: 1.5,
            EvidenceType.FACT_CHECK: 1.3,
            EvidenceType.WIKIDATA: 1.2,
            EvidenceType.WIKIPEDIA: 1.0,
            EvidenceType.NEWS_ARTICLE: 0.8,
            EvidenceType.ARCHIVE: 0.7,
            EvidenceType.SOCIAL_MEDIA: 0.3,
            EvidenceType.KNOWN_MISINFO: 2.0,  # Known DB is highly trusted
        }
        return self.stance_confidence * type_weights.get(self.source_type, 0.5)


@dataclass
class EvidenceCollection:
    """Collection of evidence items from investigation."""
    items: List[EvidenceItem] = field(default_factory=list)
    investigation_time_ms: int = 0
    levels_completed: int = 0
    stopped_early: bool = False
    stop_reason: Optional[str] = None
    
    @property
    def support_score(self) -> float:
        return sum(e.weighted_score for e in self.items if e.stance == Stance.SUPPORTS)
    
    @property
    def refute_score(self) -> float:
        return sum(e.weighted_score for e in self.items if e.stance == Stance.REFUTES)
    
    def add(self, item: EvidenceItem):
        self.items.append(item)


@dataclass
class VerifiedClaim:
    """Final output: claim with verdict and evidence."""
    original_text: str
    claim_type: str
    verdict: Verdict
    confidence: float
    evidence_summary: str
    evidence_items: List[EvidenceItem]
    investigation_time_ms: int
    sources_checked: int
    verified_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "original_text": self.original_text,
            "claim_type": self.claim_type,
            "verdict": self.verdict.value,
            "confidence": round(self.confidence, 3),
            "evidence_summary": self.evidence_summary,
            "evidence_count": len(self.evidence_items),
            "sources_checked": self.sources_checked,
            "investigation_time_ms": self.investigation_time_ms,
            "evidence": [
                {
                    "source": e.source_domain,
                    "type": e.source_type.value,
                    "stance": e.stance.value,
                    "trust_score": e.trust_score
                }
                for e in self.evidence_items[:5]  # Top 5 evidence
            ]
        }
```

---

## 🔍 Component 1: Wikidata Verifier

### Purpose
Verify simple factual claims against Wikidata knowledge base.

### File: `app/services/evidence/wikidata_verifier.py`

```python
"""
Wikidata Verifier

Verifies factual claims against Wikidata using SPARQL.
"""

import httpx
from typing import Optional, Dict, Any
from SPARQLWrapper import SPARQLWrapper, JSON


class WikidataVerifier:
    """
    Verify factual claims against Wikidata.
    
    Examples:
    - "India's capital is Delhi" → Query P36 (capital) for Q668 (India)
    - "Modi was born in 1950" → Query P569 (birth date) for entity
    """
    
    WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
    
    # Common property mappings (Wikidata property IDs)
    PROPERTIES = {
        "capital": "P36",
        "population": "P1082",
        "birth_date": "P569",
        "death_date": "P570",
        "head_of_state": "P35",
        "head_of_government": "P6",
        "country": "P17",
        "located_in": "P131",
        "founder": "P112",
        "ceo": "P169",
    }
    
    def __init__(self):
        self.sparql = SPARQLWrapper(self.WIKIDATA_ENDPOINT)
        self.sparql.setReturnFormat(JSON)
    
    def verify_claim(self, entity_name: str, property_name: str, 
                     claimed_value: str) -> Dict[str, Any]:
        """
        Verify a factual claim.
        
        Args:
            entity_name: The subject (e.g., "India")
            property_name: The property (e.g., "capital")
            claimed_value: What the claim says (e.g., "Mumbai")
            
        Returns:
            {
                "verified": True/False/None,
                "actual_value": "New Delhi",
                "claimed_value": "Mumbai",
                "source": "Wikidata Q668"
            }
        """
        # Step 1: Find entity ID
        entity_id = self._find_entity(entity_name)
        if not entity_id:
            return {"verified": None, "reason": f"Entity '{entity_name}' not found"}
        
        # Step 2: Get property value
        property_id = self.PROPERTIES.get(property_name.lower())
        if not property_id:
            return {"verified": None, "reason": f"Property '{property_name}' not supported"}
        
        actual_value = self._get_property_value(entity_id, property_id)
        if not actual_value:
            return {"verified": None, "reason": "Property value not found"}
        
        # Step 3: Compare
        verified = self._compare_values(claimed_value, actual_value)
        
        return {
            "verified": verified,
            "actual_value": actual_value,
            "claimed_value": claimed_value,
            "source": f"Wikidata {entity_id}"
        }
    
    def _find_entity(self, name: str) -> Optional[str]:
        """Find Wikidata entity ID (Q-number) for a name."""
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "format": "json",
            "limit": 1
        }
        
        try:
            response = httpx.get(url, params=params, timeout=10)
            data = response.json()
            if data.get("search"):
                return data["search"][0]["id"]
        except Exception as e:
            print(f"Wikidata search error: {e}")
        return None
    
    def _get_property_value(self, entity_id: str, property_id: str) -> Optional[str]:
        """Get property value from Wikidata."""
        query = f"""
        SELECT ?valueLabel WHERE {{
            wd:{entity_id} wdt:{property_id} ?value.
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 1
        """
        
        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])
            if bindings:
                return bindings[0]["valueLabel"]["value"]
        except Exception as e:
            print(f"SPARQL query error: {e}")
        return None
    
    def _compare_values(self, claimed: str, actual: str) -> bool:
        """Compare claimed value with actual value."""
        claimed_normalized = claimed.lower().strip()
        actual_normalized = actual.lower().strip()
        
        # Exact match
        if claimed_normalized == actual_normalized:
            return True
        
        # Partial match (one contains the other)
        if claimed_normalized in actual_normalized or actual_normalized in claimed_normalized:
            return True
        
        return False
    
    def quick_fact_check(self, claim_text: str) -> Optional[Dict[str, Any]]:
        """
        Quick check for factual claims.
        
        Attempts to extract entity/property/value from claim text
        and verify against Wikidata.
        """
        # Simple pattern matching (to be improved)
        # "X is the capital of Y" → entity=Y, property=capital, claimed=X
        
        patterns = [
            (r"(.+) is the capital of (.+)", "capital"),
            (r"(.+) was born in (\d{4})", "birth_date"),
        ]
        
        import re
        for pattern, prop in patterns:
            match = re.search(pattern, claim_text, re.IGNORECASE)
            if match:
                if prop == "capital":
                    claimed_capital = match.group(1).strip()
                    country = match.group(2).strip()
                    return self.verify_claim(country, "capital", claimed_capital)
        
        return None
```

---

## 🏛️ Component 2: Source Trust Database

### Purpose
Provide trust scores for domains to weight evidence appropriately.

### File: `app/data/domain_trust_scores.json`

```json
{
  "fact_checkers": {
    "snopes.com": 95,
    "factcheck.org": 95,
    "politifact.com": 90,
    "altnews.in": 90,
    "boomlive.in": 90
  },
  "news_high_trust": {
    "reuters.com": 95,
    "apnews.com": 95,
    "bbc.com": 90,
    "theguardian.com": 85,
    "nytimes.com": 85,
    "thehindu.com": 85,
    "indianexpress.com": 80
  },
  "news_medium_trust": {
    "ndtv.com": 75,
    "hindustantimes.com": 75,
    "timesofindia.indiatimes.com": 70,
    "news18.com": 65
  },
  "news_low_trust": {
    "opindia.com": 40,
    "swarajyamag.com": 45,
    "thewire.in": 55,
    "scroll.in": 55
  },
  "academic": {
    "pubmed.ncbi.nlm.nih.gov": 95,
    "nature.com": 95,
    "science.org": 95,
    "thelancet.com": 95,
    "arxiv.org": 80
  },
  "reference": {
    "wikipedia.org": 75,
    "britannica.com": 85,
    "wikidata.org": 85
  },
  "social_media": {
    "twitter.com": 30,
    "x.com": 30,
    "facebook.com": 25,
    "reddit.com": 35,
    "youtube.com": 35
  },
  "default": 50
}
```

### File: `app/services/evidence/source_trust.py`

```python
"""
Source Trust Scoring

Provides trust scores for domains based on historical reliability.
"""

import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Tuple


class SourceTrustScorer:
    """
    Score sources by their trustworthiness.
    
    Scores:
    - 90-100: Highly trusted (fact-checkers, major wire services)
    - 70-89: Generally trusted (major newspapers)
    - 50-69: Mixed reliability (partisan sources)
    - 30-49: Low trust (tabloids, opinion sites)
    - 0-29: Very low trust (known misinformation sources)
    """
    
    def __init__(self, trust_file: str = "app/data/domain_trust_scores.json"):
        self.trust_scores = self._load_trust_scores(trust_file)
        self.default_score = 50
    
    def _load_trust_scores(self, filepath: str) -> dict:
        """Load trust scores from JSON file."""
        path = Path(filepath)
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                # Flatten nested structure
                flat = {}
                for category, domains in data.items():
                    if isinstance(domains, dict):
                        flat.update(domains)
                    else:
                        flat[category] = domains
                return flat
        return {}
    
    def get_trust_score(self, url_or_domain: str) -> Tuple[int, str]:
        """
        Get trust score for a URL or domain.
        
        Returns:
            (score, category)
        """
        # Extract domain from URL
        if url_or_domain.startswith("http"):
            domain = urlparse(url_or_domain).netloc
        else:
            domain = url_or_domain
        
        # Remove www prefix
        domain = domain.replace("www.", "")
        
        # Check for exact match
        if domain in self.trust_scores:
            score = self.trust_scores[domain]
            return score, self._categorize(score)
        
        # Check for subdomain match
        parts = domain.split(".")
        for i in range(len(parts) - 1):
            parent = ".".join(parts[i:])
            if parent in self.trust_scores:
                score = self.trust_scores[parent]
                return score, self._categorize(score)
        
        return self.default_score, "unknown"
    
    def _categorize(self, score: int) -> str:
        """Categorize trust score."""
        if score >= 90:
            return "highly_trusted"
        elif score >= 70:
            return "generally_trusted"
        elif score >= 50:
            return "mixed_reliability"
        elif score >= 30:
            return "low_trust"
        else:
            return "very_low_trust"
    
    def is_fact_checker(self, domain: str) -> bool:
        """Check if domain is a known fact-checking organization."""
        fact_checkers = [
            "snopes.com", "factcheck.org", "politifact.com",
            "altnews.in", "boomlive.in", "vishvasnews.com"
        ]
        domain = domain.replace("www.", "")
        return domain in fact_checkers
```

---

## 🔎 Component 3: Free Searchers

### Purpose
Search engines that don't require API keys.

### File: `app/services/investigation/searchers/duckduckgo.py`

```python
"""
DuckDuckGo Search

Free, no API key required.
"""

import httpx
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Single search result."""
    title: str
    url: str
    snippet: str
    source: str


class DuckDuckGoSearcher:
    """
    Search using DuckDuckGo Instant Answers API.
    No API key required, unlimited requests.
    """
    
    BASE_URL = "https://api.duckduckgo.com/"
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of SearchResult objects
        """
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.BASE_URL, 
                    params=params,
                    timeout=10
                )
                data = response.json()
                return self._parse_results(data, max_results)
            except Exception as e:
                print(f"DuckDuckGo search error: {e}")
                return []
    
    def _parse_results(self, data: dict, max_results: int) -> List[SearchResult]:
        """Parse DuckDuckGo response."""
        results = []
        
        # Abstract (main answer)
        if data.get("Abstract"):
            results.append(SearchResult(
                title=data.get("Heading", ""),
                url=data.get("AbstractURL", ""),
                snippet=data.get("Abstract", ""),
                source=data.get("AbstractSource", "")
            ))
        
        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append(SearchResult(
                    title=topic.get("Text", "")[:100],
                    url=topic.get("FirstURL", ""),
                    snippet=topic.get("Text", ""),
                    source="DuckDuckGo"
                ))
        
        return results[:max_results]


# For non-async usage
def duckduckgo_search_sync(query: str, max_results: int = 10) -> List[Dict]:
    """Synchronous wrapper."""
    import asyncio
    searcher = DuckDuckGoSearcher()
    results = asyncio.run(searcher.search(query, max_results))
    return [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results]
```

### File: `app/services/investigation/searchers/wikipedia.py`

```python
"""
Wikipedia Search

Free REST API, no key required.
"""

import httpx
from typing import Optional, Dict, Any, List


class WikipediaSearcher:
    """
    Search and retrieve Wikipedia articles.
    Uses the REST API - no key required.
    """
    
    BASE_URL = "https://en.wikipedia.org/api/rest_v1"
    SEARCH_URL = "https://en.wikipedia.org/w/api.php"
    
    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search Wikipedia articles.
        
        Returns list of article summaries.
        """
        params = {
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "format": "json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.SEARCH_URL, params=params, timeout=10)
                data = response.json()
                
                # OpenSearch returns [query, [titles], [descriptions], [urls]]
                if len(data) >= 4:
                    results = []
                    for i, title in enumerate(data[1]):
                        results.append({
                            "title": title,
                            "description": data[2][i] if i < len(data[2]) else "",
                            "url": data[3][i] if i < len(data[3]) else ""
                        })
                    return results
            except Exception as e:
                print(f"Wikipedia search error: {e}")
        return []
    
    async def get_summary(self, title: str) -> Optional[Dict]:
        """
        Get article summary by title.
        
        Returns:
            {"title": str, "extract": str, "url": str}
        """
        # URL-encode the title
        import urllib.parse
        encoded_title = urllib.parse.quote(title.replace(" ", "_"))
        
        url = f"{self.BASE_URL}/page/summary/{encoded_title}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "title": data.get("title", title),
                        "extract": data.get("extract", ""),
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        "description": data.get("description", "")
                    }
            except Exception as e:
                print(f"Wikipedia summary error: {e}")
        return None
    
    async def get_article_intro(self, title: str) -> Optional[str]:
        """Get first few paragraphs of an article."""
        summary = await self.get_summary(title)
        if summary:
            return summary.get("extract")
        return None
```

### File: `app/services/investigation/searchers/pubmed.py`

```python
"""
PubMed Search

Free E-utilities API for scientific papers.
"""

import httpx
from typing import List, Dict, Any
from xml.etree import ElementTree as ET


class PubMedSearcher:
    """
    Search PubMed for scientific papers.
    Uses E-utilities API - free, no key required.
    """
    
    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search PubMed for papers.
        
        Args:
            query: Search query
            max_results: Maximum papers to return
            
        Returns:
            List of paper metadata
        """
        # Step 1: Search for IDs
        ids = await self._search_ids(query, max_results)
        if not ids:
            return []
        
        # Step 2: Fetch paper details
        papers = await self._fetch_papers(ids)
        return papers
    
    async def _search_ids(self, query: str, max_results: int) -> List[str]:
        """Search for paper IDs."""
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.ESEARCH_URL, params=params, timeout=15)
                data = response.json()
                return data.get("esearchresult", {}).get("idlist", [])
            except Exception as e:
                print(f"PubMed search error: {e}")
        return []
    
    async def _fetch_papers(self, ids: List[str]) -> List[Dict]:
        """Fetch paper details by IDs."""
        params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.EFETCH_URL, params=params, timeout=15)
                return self._parse_papers(response.text)
            except Exception as e:
                print(f"PubMed fetch error: {e}")
        return []
    
    def _parse_papers(self, xml_text: str) -> List[Dict]:
        """Parse PubMed XML response."""
        papers = []
        
        try:
            root = ET.fromstring(xml_text)
            for article in root.findall(".//PubmedArticle"):
                title_elem = article.find(".//ArticleTitle")
                abstract_elem = article.find(".//AbstractText")
                pmid_elem = article.find(".//PMID")
                
                paper = {
                    "title": title_elem.text if title_elem is not None else "",
                    "abstract": abstract_elem.text if abstract_elem is not None else "",
                    "pmid": pmid_elem.text if pmid_elem is not None else "",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid_elem.text}/" if pmid_elem is not None else "",
                    "source": "PubMed"
                }
                papers.append(paper)
        except Exception as e:
            print(f"PubMed parse error: {e}")
        
        return papers
```

---

## 🎛️ Component 4: Investigation Orchestrator

### Purpose
Coordinate multi-level search with time bounds and smart stopping.

### File: `app/services/investigation/orchestrator.py`

```python
"""
Investigation Orchestrator

Coordinates multi-level search with time bounds and smart stopping.
"""

import asyncio
import time
from typing import Optional
from dataclasses import dataclass

from app.models.domain import TypedClaim, ClaimType
from app.models.evidence import EvidenceCollection, EvidenceItem, EvidenceType, Stance

from .searchers.duckduckgo import DuckDuckGoSearcher
from .searchers.wikipedia import WikipediaSearcher
from .searchers.pubmed import PubMedSearcher
from ..evidence.wikidata_verifier import WikidataVerifier
from ..evidence.source_trust import SourceTrustScorer
from .synthesizer import EvidenceSynthesizer


@dataclass
class InvestigationConfig:
    """Configuration for investigation."""
    max_time_seconds: int = 45
    level_1_timeout: int = 5
    level_2_timeout: int = 15
    level_3_timeout: int = 25
    min_evidence_for_verdict: int = 3
    confidence_threshold: float = 0.85


class InvestigationOrchestrator:
    """
    Orchestrate multi-level investigation.
    
    Levels:
    1. Quick Check (5s): Known misinfo, fact-checks, Wikidata
    2. Standard Search (15s): DuckDuckGo, Wikipedia, News
    3. Deep Investigation (25s): PubMed, Archive.org, lead following
    """
    
    def __init__(self, config: Optional[InvestigationConfig] = None):
        self.config = config or InvestigationConfig()
        
        # Initialize searchers
        self.duckduckgo = DuckDuckGoSearcher()
        self.wikipedia = WikipediaSearcher()
        self.pubmed = PubMedSearcher()
        self.wikidata = WikidataVerifier()
        self.trust_scorer = SourceTrustScorer()
        self.synthesizer = EvidenceSynthesizer()
        
        # Known misinformation database
        self.known_misinfo = self._load_known_misinfo()
    
    def _load_known_misinfo(self) -> dict:
        """Load known misinformation database."""
        import json
        from pathlib import Path
        
        path = Path("app/data/known_misinformation.json")
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return {}
    
    async def investigate(self, claim: TypedClaim) -> EvidenceCollection:
        """
        Investigate a claim across multiple levels.
        
        Returns:
            EvidenceCollection with all gathered evidence
        """
        start_time = time.time()
        evidence = EvidenceCollection()
        
        # Level 1: Quick Check
        level1_evidence = await self._level1_quick_check(claim)
        evidence.items.extend(level1_evidence)
        evidence.levels_completed = 1
        
        if self._should_stop(evidence, start_time):
            evidence.stopped_early = True
            evidence.stop_reason = "Confident after Level 1"
            return evidence
        
        # Level 2: Standard Search
        level2_evidence = await self._level2_standard_search(claim)
        evidence.items.extend(level2_evidence)
        evidence.levels_completed = 2
        
        if self._should_stop(evidence, start_time):
            evidence.stopped_early = True
            evidence.stop_reason = "Confident after Level 2"
            return evidence
        
        # Level 3: Deep Investigation (for scientific/complex claims)
        if claim.claim_type in [ClaimType.SCIENTIFIC_MEDICAL]:
            level3_evidence = await self._level3_deep_investigation(claim)
            evidence.items.extend(level3_evidence)
            evidence.levels_completed = 3
        
        evidence.investigation_time_ms = int((time.time() - start_time) * 1000)
        return evidence
    
    async def _level1_quick_check(self, claim: TypedClaim) -> list:
        """Level 1: Quick checks (5s timeout)."""
        evidence = []
        
        # Check known misinformation database
        misinfo_match = self._check_known_misinfo(claim.text)
        if misinfo_match:
            evidence.append(EvidenceItem(
                text=misinfo_match["reason"],
                source_url="local:known_misinformation",
                source_domain="TruthLens Known DB",
                source_type=EvidenceType.KNOWN_MISINFO,
                stance=Stance.REFUTES if misinfo_match["verdict"] == "FALSE" else Stance.SUPPORTS,
                stance_confidence=0.95,
                trust_score=100
            ))
        
        # Wikidata quick check
        wikidata_result = self.wikidata.quick_fact_check(claim.text)
        if wikidata_result and wikidata_result.get("verified") is not None:
            evidence.append(EvidenceItem(
                text=f"Wikidata: {wikidata_result.get('actual_value', 'N/A')}",
                source_url=wikidata_result.get("source", ""),
                source_domain="wikidata.org",
                source_type=EvidenceType.WIKIDATA,
                stance=Stance.SUPPORTS if wikidata_result["verified"] else Stance.REFUTES,
                stance_confidence=0.9,
                trust_score=90
            ))
        
        return evidence
    
    async def _level2_standard_search(self, claim: TypedClaim) -> list:
        """Level 2: Standard search (15s timeout)."""
        evidence = []
        
        # Run searches in parallel
        tasks = [
            self.duckduckgo.search(claim.text, max_results=5),
            self.wikipedia.search(claim.text, limit=3),
        ]
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.level_2_timeout
            )
            
            ddg_results, wiki_results = results
            
            # Process DuckDuckGo results
            if isinstance(ddg_results, list):
                for result in ddg_results[:3]:
                    trust_score, _ = self.trust_scorer.get_trust_score(result.url)
                    stance = self.synthesizer.detect_stance_simple(result.snippet, claim.text)
                    
                    evidence.append(EvidenceItem(
                        text=result.snippet[:500],
                        source_url=result.url,
                        source_domain=result.source,
                        source_type=EvidenceType.NEWS_ARTICLE,
                        stance=stance,
                        stance_confidence=0.6,
                        trust_score=trust_score
                    ))
            
            # Process Wikipedia results
            if isinstance(wiki_results, list):
                for result in wiki_results[:2]:
                    stance = self.synthesizer.detect_stance_simple(
                        result.get("description", ""), 
                        claim.text
                    )
                    evidence.append(EvidenceItem(
                        text=result.get("description", ""),
                        source_url=result.get("url", ""),
                        source_domain="wikipedia.org",
                        source_type=EvidenceType.WIKIPEDIA,
                        stance=stance,
                        stance_confidence=0.7,
                        trust_score=75
                    ))
                    
        except asyncio.TimeoutError:
            print("Level 2 search timed out")
        
        return evidence
    
    async def _level3_deep_investigation(self, claim: TypedClaim) -> list:
        """Level 3: Deep investigation for scientific claims."""
        evidence = []
        
        # PubMed search for scientific claims
        try:
            papers = await asyncio.wait_for(
                self.pubmed.search(claim.text, max_results=3),
                timeout=self.config.level_3_timeout
            )
            
            for paper in papers:
                stance = self.synthesizer.detect_stance_simple(
                    paper.get("abstract", ""),
                    claim.text
                )
                evidence.append(EvidenceItem(
                    text=paper.get("abstract", "")[:500],
                    source_url=paper.get("url", ""),
                    source_domain="pubmed.ncbi.nlm.nih.gov",
                    source_type=EvidenceType.ACADEMIC_PAPER,
                    stance=stance,
                    stance_confidence=0.8,
                    trust_score=95
                ))
                
        except asyncio.TimeoutError:
            print("Level 3 PubMed search timed out")
        
        return evidence
    
    def _check_known_misinfo(self, claim_text: str) -> Optional[dict]:
        """Check claim against known misinformation database."""
        claim_lower = claim_text.lower()
        
        for pattern, data in self.known_misinfo.items():
            if pattern.lower() in claim_lower:
                return data
        return None
    
    def _should_stop(self, evidence: EvidenceCollection, start_time: float) -> bool:
        """Determine if investigation should stop early."""
        elapsed = time.time() - start_time
        
        # Time exceeded
        if elapsed >= self.config.max_time_seconds:
            return True
        
        # Found authoritative fact-check
        if any(e.source_type == EvidenceType.KNOWN_MISINFO for e in evidence.items):
            return True
        
        # High source agreement
        if len(evidence.items) >= 3:
            total_score = evidence.support_score + evidence.refute_score
            if total_score > 0:
                agreement = max(evidence.support_score, evidence.refute_score) / total_score
                if agreement >= self.config.confidence_threshold:
                    return True
        
        return False
```

---

## 🧮 Component 5: Evidence Synthesizer

### Purpose
Analyze evidence stance and synthesize into verdict.

### File: `app/services/investigation/synthesizer.py`

```python
"""
Evidence Synthesizer

Analyzes evidence stance and synthesizes into verdict.
Uses RoBERTa-large-mnli for stance detection.
"""

from typing import List, Tuple
from app.models.evidence import EvidenceCollection, EvidenceItem, Stance, Verdict
from app.services.models import get_model_manager


class EvidenceSynthesizer:
    """
    Synthesize evidence into verdict.
    
    Steps:
    1. Detect stance for each evidence item
    2. Weight by source trust
    3. Calculate overall verdict
    """
    
    def __init__(self):
        self.models = get_model_manager()
    
    def detect_stance(self, evidence_text: str, claim_text: str) -> Tuple[Stance, float]:
        """
        Detect if evidence SUPPORTS, REFUTES, or is NEUTRAL to claim.
        
        Uses RoBERTa-large-mnli (Natural Language Inference).
        """
        if not evidence_text or not claim_text:
            return Stance.NEUTRAL, 0.5
        
        # NLI format: premise </s></s> hypothesis
        result = self.models.stance_detector(
            f"{evidence_text} </s></s> {claim_text}"
        )
        
        # Map NLI labels to stance
        label = result[0]["label"]
        score = result[0]["score"]
        
        label_map = {
            "ENTAILMENT": Stance.SUPPORTS,
            "CONTRADICTION": Stance.REFUTES,
            "NEUTRAL": Stance.NEUTRAL
        }
        
        return label_map.get(label, Stance.NEUTRAL), score
    
    def detect_stance_simple(self, evidence_text: str, claim_text: str) -> Stance:
        """Simple keyword-based stance detection (fallback)."""
        if not evidence_text:
            return Stance.NEUTRAL
        
        evidence_lower = evidence_text.lower()
        claim_lower = claim_text.lower()
        
        # Refutation keywords
        refute_keywords = [
            "false", "debunked", "myth", "fake", "incorrect",
            "no evidence", "not true", "misleading", "hoax",
            "conspiracy", "disinformation", "baseless"
        ]
        
        # Support keywords
        support_keywords = [
            "confirmed", "verified", "true", "correct",
            "study shows", "research confirms", "evidence supports",
            "scientists agree", "proven"
        ]
        
        refute_count = sum(1 for kw in refute_keywords if kw in evidence_lower)
        support_count = sum(1 for kw in support_keywords if kw in evidence_lower)
        
        if refute_count > support_count:
            return Stance.REFUTES
        elif support_count > refute_count:
            return Stance.SUPPORTS
        else:
            return Stance.NEUTRAL
    
    def synthesize(self, evidence: EvidenceCollection, claim_text: str) -> Tuple[Verdict, float, str]:
        """
        Synthesize all evidence into a verdict.
        
        Returns:
            (verdict, confidence, summary)
        """
        if not evidence.items:
            return Verdict.INSUFFICIENT_EVIDENCE, 0.0, "No evidence found"
        
        # Calculate scores
        support_score = evidence.support_score
        refute_score = evidence.refute_score
        total_score = support_score + refute_score
        
        if total_score == 0:
            return Verdict.UNVERIFIED, 0.0, "Evidence was neutral"
        
        # Determine verdict
        confidence = abs(support_score - refute_score) / total_score
        
        if len(evidence.items) < 3:
            verdict = Verdict.INSUFFICIENT_EVIDENCE
            summary = f"Only {len(evidence.items)} sources found"
        elif refute_score > support_score * 1.5:
            verdict = Verdict.VERIFIED_FALSE
            summary = f"Evidence strongly refutes claim ({len(evidence.items)} sources)"
        elif support_score > refute_score * 1.5:
            verdict = Verdict.VERIFIED_TRUE
            summary = f"Evidence supports claim ({len(evidence.items)} sources)"
        elif confidence < 0.3:
            verdict = Verdict.DISPUTED
            summary = f"Sources disagree ({len(evidence.items)} sources)"
        else:
            verdict = Verdict.UNVERIFIED
            summary = f"Insufficient agreement ({len(evidence.items)} sources)"
        
        return verdict, confidence, summary
```

---

## 🏛️ Component 6: Verdict Determiner

### Purpose
Finalize verdict with all evidence.

### File: `app/services/investigation/verdict_engine.py`

```python
"""
Verdict Engine

Final verdict determination with evidence aggregation.
"""

from app.models.domain import TypedClaim, ClaimType
from app.models.evidence import EvidenceCollection, VerifiedClaim, Verdict
from .synthesizer import EvidenceSynthesizer


class VerdictEngine:
    """
    Determine final verdict based on evidence.
    
    CRITICAL: This is where the verdict is made.
    NO LLM is used here - only evidence synthesis.
    """
    
    def __init__(self):
        self.synthesizer = EvidenceSynthesizer()
    
    def determine_verdict(self, claim: TypedClaim, 
                         evidence: EvidenceCollection) -> VerifiedClaim:
        """
        Determine final verdict for a claim.
        
        Args:
            claim: The typed claim from Phase 1
            evidence: Evidence collected from investigation
            
        Returns:
            VerifiedClaim with verdict and evidence trail
        """
        # Handle non-checkable claims
        if not claim.is_checkable:
            return VerifiedClaim(
                original_text=claim.text,
                claim_type=claim.claim_type.value,
                verdict=Verdict.NOT_CHECKABLE,
                confidence=1.0,
                evidence_summary="Opinion/value judgment - not fact-checkable",
                evidence_items=[],
                investigation_time_ms=0,
                sources_checked=0
            )
        
        # Synthesize evidence into verdict
        verdict, confidence, summary = self.synthesizer.synthesize(
            evidence, 
            claim.text
        )
        
        # Build result
        return VerifiedClaim(
            original_text=claim.text,
            claim_type=claim.claim_type.value,
            verdict=verdict,
            confidence=confidence,
            evidence_summary=summary,
            evidence_items=evidence.items,
            investigation_time_ms=evidence.investigation_time_ms,
            sources_checked=len(evidence.items)
        )
```

---

## 🌐 API Endpoints

### Update: `app/api/v3/endpoints/analyze.py`

Add investigation to the existing endpoint:

```python
# Add to existing analyze.py

from app.services.investigation.orchestrator import InvestigationOrchestrator
from app.services.investigation.verdict_engine import VerdictEngine

# Initialize investigation services
_investigation_orchestrator = None
_verdict_engine = None

def get_investigation_services():
    global _investigation_orchestrator, _verdict_engine
    if _investigation_orchestrator is None:
        _investigation_orchestrator = InvestigationOrchestrator()
    if _verdict_engine is None:
        _verdict_engine = VerdictEngine()
    return _investigation_orchestrator, _verdict_engine


@router.post("/investigate", response_model=InvestigateResponse)
async def investigate_claim(request: InvestigateRequest):
    """
    Full investigation of a claim (Phase 2).
    
    - Extracts and types claim (Phase 1)
    - Investigates across multiple sources (Phase 2)
    - Returns verdict with evidence trail
    """
    # Phase 1: Extract and type
    # ... (existing code)
    
    # Phase 2: Investigate
    orchestrator, verdict_engine = get_investigation_services()
    
    for typed_claim in typed_claims:
        if typed_claim.is_checkable:
            evidence = await orchestrator.investigate(typed_claim)
            verified = verdict_engine.determine_verdict(typed_claim, evidence)
            # Add to response
```

---

## 🧪 Testing Strategy

### Test Files

```
tests/
├── test_wikidata_verifier.py
├── test_source_trust.py
├── test_searchers.py
├── test_orchestrator.py
├── test_synthesizer.py
└── test_verdict_engine.py
```

### Sample Tests

```python
# tests/test_wikidata_verifier.py
import pytest
from app.services.evidence.wikidata_verifier import WikidataVerifier

class TestWikidataVerifier:
    @pytest.fixture
    def verifier(self):
        return WikidataVerifier()
    
    def test_india_capital_correct(self, verifier):
        result = verifier.verify_claim("India", "capital", "New Delhi")
        assert result["verified"] == True
    
    def test_india_capital_incorrect(self, verifier):
        result = verifier.verify_claim("India", "capital", "Mumbai")
        assert result["verified"] == False
```

---

## ✅ Success Criteria

### Phase 2A Complete When (Core Functionality):

```
✅ "India's capital is Mumbai" → VERIFIED_FALSE (Wikidata)
✅ "Modi was born in 1950" → VERIFIED_TRUE (Wikidata)  
✅ DuckDuckGo search returns results for any claim
✅ Wikipedia lookup works for entity-based claims
✅ Sources tagged with trust scores
✅ Evidence synthesis produces verdict (keyword-based stance)
✅ Verdicts are evidence-based, NOT LLM-decided
✅ API endpoint `/api/v3/investigate` working
✅ Full pipeline: claim → evidence → verdict
```

### Phase 2B Complete When (Optimization):

```
✅ All searchers converted to async
✅ Parallel execution working (asyncio.gather)
✅ Time limit respected (max 45 seconds)
✅ Smart stopping when confident (early exit)
✅ RoBERTa stance detection integrated
✅ PubMed working for scientific claims
✅ Archive.org for historical verification
✅ Performance: <30s for most claims
```

---

## 📋 Task Breakdown

### Week 1: Phase 2A (Basic Evidence - SYNCHRONOUS)

> **Focus:** Get it working. No async, no time bounds.

| Day | Tasks |
|-----|-------|
| Day 1 | Create `evidence.py` data models, `source_trust.py`, `domain_trust_scores.json` |
| Day 2 | Implement `wikidata_verifier.py` (sync), create `known_misinformation.json` |
| Day 3 | Implement `duckduckgo.py`, `wikipedia.py` (sync versions) |
| Day 4 | Implement `synthesizer.py` (simple keyword-based stance) |
| Day 5 | Implement `orchestrator.py` (sync, sequential), `verdict_engine.py` |
| Day 6 | Integration: Update `/api/v3/investigate` endpoint |
| Day 7 | Testing, debugging, commit |

### Week 2: Phase 2B (Optimization Pass - ASYNC)

> **Focus:** Make it fast. Add async, time bounds, smart stopping.

| Day | Tasks |
|-----|-------|
| Day 1 | Convert searchers to async, add `aiohttp` |
| Day 2 | Add RoBERTa stance detection to `synthesizer.py` |
| Day 3 | Update `orchestrator.py` with time bounds, parallel execution |
| Day 4 | Add smart stopping logic (early exit when confident) |
| Day 5 | Implement `pubmed.py`, `archive_org.py` for deep investigation |
| Day 6 | Full testing: time bounds, edge cases |
| Day 7 | Polish, documentation, commit |

---

## 🎯 Quick Reference

### Key Files

| Purpose | File |
|---------|------|
| Evidence models | `app/models/evidence.py` |
| Wikidata | `app/services/evidence/wikidata_verifier.py` |
| Trust scores | `app/services/evidence/source_trust.py` |
| Orchestrator | `app/services/investigation/orchestrator.py` |
| Synthesizer | `app/services/investigation/synthesizer.py` |
| Verdict | `app/services/investigation/verdict_engine.py` |

### Key Models

| Model | Purpose |
|-------|---------|
| `facebook/bart-large-mnli` | Claim typing (Phase 1) |
| `roberta-large-mnli` | Stance detection (Phase 2) |

### API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v3/analyze` | Phase 1: Extract & type claims |
| `POST /api/v3/investigate` | Phase 2: Full investigation |

---

**End of Phase 2 Implementation Blueprint**
