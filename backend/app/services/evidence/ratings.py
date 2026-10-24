"""
Fact-Check Rating Normalization

Shared, tested mapping from human fact-check ratings ("Pants on Fire",
"Half true", "not true", ...) to the four canonical TruthLens categories:
True / False / Misleading / Unverifiable.

Ordering matters: more specific phrases are matched before their generic
suffixes so "not true" can never match the bare "true" pattern.
"""

import re
from typing import Optional

# Canonical categories
TRUE = "True"
FALSE = "False"
MISLEADING = "Misleading"
UNVERIFIABLE = "Unverifiable"

# Hedged/qualified ratings: real fact-checkers use these when the claim is
# partly right ("Mostly True — not entirely accurate as presented"). They must
# NOT trigger the definitive early-stop override.
_HEDGED_RATING_RE = re.compile(r"\bmostly\s+(?:true|false)\b")

# Ordered (most-specific first) regex -> category mapping.
# Every pattern uses \b word boundaries so substrings cannot lie
# (e.g. "not true" must not hit the bare-word "true" pattern).
_RATING_PATTERNS = [
    # Negated forms FIRST so they win over their positive counterparts.
    (r"\bnot\s+true\b", FALSE),
    (r"\bnot\s+correct\b", FALSE),
    (r"\bnot\s+accurate\b", FALSE),
    (r"\bno\s+evidence\b", UNVERIFIABLE),
    # Multi-word specific ratings.
    (r"\bpants\s+on\s+fire\b", FALSE),
    (r"\bmostly\s+true\b", TRUE),
    (r"\bmostly\s+false\b", FALSE),
    (r"\bhalf\s+true\b", MISLEADING),
    (r"\bpart(?:ly|ially)\s+true\b", MISLEADING),
    (r"\bpart(?:ly|ially)\s+false\b", MISLEADING),
    (r"\bout\s+of\s+context\b", MISLEADING),
    (r"\black(?:s)?\s+of\s+context\b", MISLEADING),
    (r"\bneeds?\s+context\b", UNVERIFIABLE),
    (r"\binsufficient\s+evidence\b", UNVERIFIABLE),
    (r"\bunproven\b", UNVERIFIABLE),
    (r"\bunverified\b", UNVERIFIABLE),
    (r"\bevidence\s+supports\b", TRUE),
    # Single-word / generic ratings.
    (
        r"\btrue\b|\bcorrect\b|\baccurate\b|\bconfirmed\b|\bverified\b|\bfactual\b|\bsupported\b",
        TRUE,
    ),
    (
        r"\bfalse\b|\bincorrect\b|\bwrong\b|\bdebunked\b|\bhoax\b|\bfake\b|\bunfounded\b|\bbaseless\b|\bdisproven\b",
        FALSE,
    ),
    (r"\bmisleading\b|\bmixture\b|\bexaggerated\b|\bdistorted\b", MISLEADING),
    (r"\bunclear\b|\buncertain\b", UNVERIFIABLE),
]


def normalize_rating(rating_text) -> Optional[str]:
    """
    Map a raw textual rating to True/False/Misleading/Unverifiable.

    Returns None when no confident mapping exists so callers can fall back to
    an LLM interpretation or treat the result as neutral.
    """
    if not rating_text:
        return None
    text = str(rating_text).lower().strip()
    for pattern, category in _RATING_PATTERNS:
        if re.search(pattern, text):
            return category
    return None


def stance_from_rating(rating_text):
    """
    Map a raw fact-check rating to (Stance, stance_confidence):

        True           -> SUPPORTS  (0.95)  Professional fact-checker confirms.
        False          -> REFUTES   (0.95)  Professional fact-checker refutes.
        Misleading     -> NEUTRAL   (0.70)  Real but missing context: not definitive.
        Unverifiable   -> NEUTRAL   (0.50)
        None           -> NEUTRAL   (0.30)  Unmapped/weak rating: low confidence.

    Hedged qualifiers ("mostly true", "mostly false") still carry their stance
    but at 0.80 confidence — below the 0.9 early-stop gate — so a qualified
    rating (e.g. Snopes "Mostly True: not entirely accurate as presented")
    contributes evidence without hard-overriding the final verdict.
    """
    from app.models.evidence import Stance

    text = str(rating_text or "").lower()

    if normalize_rating(rating_text) == TRUE:
        if _HEDGED_RATING_RE.search(text):
            return Stance.SUPPORTS, 0.80
        return Stance.SUPPORTS, 0.95
    if normalize_rating(rating_text) == FALSE:
        if _HEDGED_RATING_RE.search(text):
            return Stance.REFUTES, 0.80
        return Stance.REFUTES, 0.95
    if normalize_rating(rating_text) == MISLEADING:
        return Stance.NEUTRAL, 0.70
    return Stance.NEUTRAL, 0.30


_STOPWORD_TOKENS = frozenset({
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "is", "are", "was", "were", "be", "been", "that", "this", "it", "its",
    "with", "by", "from", "as", "says", "said", "claim", "claims", "claimed",
})


def _content_tokens(text: str) -> set:
    """Lowercase alphanumeric tokens minus a tiny stopword list."""
    return {
        token for token in re.findall(r"[a-z0-9]{3,}", (text or "").lower())
        if token not in _STOPWORD_TOKENS
    }


def factcheck_is_relevant(claim_text: str, factcheck_text: str, min_jaccard: float = 0.10) -> bool:
    """
    Cheap relevance check between the claim being investigated and the checked
    text of a matched fact-check result, so an unrelated search hit is never
    treated as a definitive verdict.
    """
    claim_tokens = _content_tokens(claim_text)
    match_tokens = _content_tokens(factcheck_text)
    if not claim_tokens or not match_tokens:
        return False
    overlap = len(claim_tokens & match_tokens) / len(claim_tokens | match_tokens)
    return overlap >= min_jaccard


# Temporal qualifiers: two claims about the same subject with different time
# qualifiers ("grows taller in summer" vs "grows taller every year") read as
# the same text to token-overlap matching. Bucket them so a mismatch can be
# detected deterministically.
_TEMPORAL_QUALIFIER_PATTERNS = {
    "annual": re.compile(
        r"\b(?:every|each)\s+year\b|\bannually\b|\bper\s+year\b|\byearly\b"
    ),
    "monthly": re.compile(r"\bevery\s+month\b|\bmonthly\b|\bmonth[-\s]over[-\s]month\b"),
    "daily": re.compile(r"\bevery\s+day\b|\bdaily\b"),
    "summer": re.compile(r"\bsummertime\b|\b(?:in|during)\s+(?:the\s+)?summer\b"),
    "winter": re.compile(r"\bwintertime\b|\b(?:in|during)\s+(?:the\s+)?winter\b"),
    "spring": re.compile(r"\b(?:in|during)\s+(?:the\s+)?spring\b"),
    "autumn": re.compile(r"\b(?:in|during)\s+(?:the\s+)?(?:autumn|fall)\b"),
}


def temporal_qualifiers(text: str) -> frozenset:
    """Buckets of temporal qualifiers asserted in the text (may be empty)."""
    lowered = (text or "").lower()
    return frozenset(
        name for name, pattern in _TEMPORAL_QUALIFIER_PATTERNS.items()
        if pattern.search(lowered)
    )


def qualifier_conflict(claim_text: str, evidence_text: str) -> bool:
    """
    True when claim and evidence BOTH assert temporal qualifiers and share none
    ("tower grows 15 cm taller every year" vs. fact-check "... taller in the
    summer"): the professional check confirms a different variant than asked.
    """
    claim_qualifiers = temporal_qualifiers(claim_text)
    evidence_qualifiers = temporal_qualifiers(evidence_text)
    if not claim_qualifiers or not evidence_qualifiers:
        return False
    return not (claim_qualifiers & evidence_qualifiers)
