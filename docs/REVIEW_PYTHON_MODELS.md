# Python Models Review Notes

This file is a quick walkthrough of the core Python models used by TruthLens.

## 1) Persistence Models (SQLAlchemy)

These models store authenticated users and their analysis history.

### `User` model

Source: `backend/app/models/user.py`

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    checks = relationship("Check", back_populates="user")
```

Why it matters:
- Stores auth identity + profile preferences.
- `checks` relation links one user to many verification runs.

### `Check` model

Source: `backend/app/models/check.py`

```python
class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    input_text = Column(Text, nullable=True)
    input_url = Column(String(2048), nullable=True)
    claim = Column(Text, nullable=True)

    domain_score = Column(String(50), nullable=True)
    factcheck_rating = Column(String(100), nullable=True)
    factcheck_summary = Column(Text, nullable=True)
    stance_summary = Column(JSON, nullable=True)

    verdict = Column(String(100), nullable=False)
    confidence = Column(String(20), nullable=False)
    explanation = Column(Text, nullable=True)

    pipeline_version = Column(String(20), nullable=True, default="0.1.0")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="checks")
```

Why it matters:
- This is the single source of truth for history shown in web + extension.
- Captures both verdict output and trace metadata (`factcheck`, `stance_summary`, `pipeline_version`).

## 2) Domain Models (Pipeline Data Contracts)

These dataclasses/Enums represent data moving through the v3 pipeline.

### Input + claim typing

Source: `backend/app/models/domain.py`

```python
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
    QUOTE_ATTRIBUTION = "quote_attribution"
    OPINION = "opinion"
    PREDICTION = "prediction"
    QUESTION = "question"
    COMMAND = "command"
    HYPOTHETICAL = "hypothetical"
    UNKNOWN = "unknown"
```

```python
@dataclass
class TypedClaim:
    text: str
    claim_type: ClaimType
    type_confidence: float
    is_checkable: bool
    evidence_strategy: str
    status: str
    sentence_index: int = 0
    canonical_id: Optional[str] = None
```

Why it matters:
- Separates checkable vs non-checkable claims early.
- `canonical_id` is used for dedupe/cache logic.

### Evidence + final verdict object

Source: `backend/app/models/evidence.py`

```python
@dataclass
class EvidenceItem:
    text: str
    source_url: str
    source_domain: str
    source_type: EvidenceType
    stance: Stance = Stance.NEUTRAL
    stance_confidence: float = 0.5
    trust_score: int = 50

    @property
    def weighted_score(self) -> float:
        type_weight = SOURCE_WEIGHTS.get(self.source_type, 0.5)
        trust_factor = self.trust_score / 100
        return self.stance_confidence * type_weight * trust_factor
```

```python
@dataclass
class VerifiedClaim:
    original_text: str
    claim_type: str
    verdict: Verdict
    confidence: float
    evidence_summary: str
    evidence_items: List[EvidenceItem]
    investigation_time_ms: int
    sources_checked: int
```

Why it matters:
- Weighted evidence scoring keeps verdict deterministic and explainable.
- `VerifiedClaim` is the object returned by verification engine and mapped to API response.

## What to say in review (short version)

- "`User` and `Check` are storage models; everything else are pipeline transport models."
- "Claim typing and checkability are decided before heavy investigation."
- "Evidence objects carry stance, trust, and source metadata so verdicts remain auditable."
