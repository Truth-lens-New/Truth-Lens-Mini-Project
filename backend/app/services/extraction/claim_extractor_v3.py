"""
TruthLens Claim Extractor V3 -- "spaCy and crux builder" patch
==============================================================

Drop-in replacement for the old ``claim_extractor_v3.py``.

Public surface is unchanged, so no other file has to be edited:

    from app.services.extraction import ClaimExtractorV3
    extractor = ClaimExtractorV3()
    extractor.extract(processed_input)        -> List[RawClaim]
    extractor.extract_crux(processed_input)   -> List[RawClaim]
    extractor.extract_from_text(text)         -> List[RawClaim]

What changed compared with the old version
------------------------------------------
* No more blind comma splitting.  A sentence is only split at ``,`` ``;`` or
  ``and/but/or`` when BOTH halves, parsed on their own, are complete clauses
  (own subject + verb).  "The study, which was published in Nature, found..."
  stays in one piece.
* Leading connectives ("Since", "But", "However", ...) are stripped, and a
  fragment such as "Since AI always gives 100% accurate claims." is recognised
  as a *premise* (the load-bearing claim of the sentence before it).
* Claims are scored for check-worthiness with lemma/entity/dependency features
  instead of substring keyword matches ("showers" no longer matches "show").
* A local "crux" ranking (check-worthiness + premise boost + lede bonus +
  centrality) picks the most important claims of long text / URLs.  Gemini is
  optional and OFF by default (``use_llm_crux=True`` or ``settings.use_llm_crux``).
* Near-duplicate removal has a negation/number guard, so "AI always..." and
  "AI never..." are never merged.
* Optional pronoun resolution (``resolve_pronouns=True``, off by default).
* ``extract_with_report`` returns a per-candidate report (score, role, why a
  candidate was dropped) that is handy for debugging and for tests.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple

from app.models.domain import InputType, ProcessedInput, RawClaim
from app.services.models import get_model_manager

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Tunables
# --------------------------------------------------------------------------- #
MAX_INPUT_CHARS = 100_000          # hard cap on text handed to spaCy
MAX_SENTENCE_TOKENS_TO_SPLIT = 60  # don't try to split monster sentences
MAX_SPLITS_PER_SENTENCE = 3
SPLIT_BUDGET_SECONDS = 3.0         # safety valve: stop clause-splitting past this
MIN_CLAUSE_TOKENS = 3              # non-punctuation tokens for a standalone clause

MIN_SCORE_TEXT = 0.10              # pasted text: keep nearly every assertion
MIN_SCORE_ARTICLE = 0.30           # articles: only reasonably check-worthy lines
DEFAULT_MAX_CLAIMS_TEXT = 10
DEFAULT_MAX_CLAIMS_ARTICLE = 7
DUPLICATE_JACCARD = 0.75
DUPLICATE_COSINE = 0.92
ASSERTION_FALLBACK_WORDS = 25      # short assertive text never returns 0 claims


# --------------------------------------------------------------------------- #
# Lexicons (matched on lemmas / whole tokens, never on substrings)
# --------------------------------------------------------------------------- #
_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.I)
_LIST_MARKER_RE = re.compile(r"^\s*(?:[-*\u2022\u25AA\u2023]+|\(?\d{1,3}[.)])\s+")
_WS_RE = re.compile(r"\s+")
_AI_RE = re.compile(r"\bai\b")      # lowercase "ai" is parsed as an auxiliary verb

_CONNECTIVES = (
    "and", "but", "so", "also", "then", "yet", "however", "moreover",
    "furthermore", "therefore", "thus", "hence", "meanwhile", "besides",
    "anyway", "plus", "still", "nevertheless", "nonetheless", "additionally",
    "instead", "otherwise", "indeed", "actually", "basically", "honestly",
    "clearly", "obviously", "finally", "firstly", "secondly", "thirdly",
    "lastly", "likewise",
)
_LEADING_CONNECTIVE_RE = re.compile(
    r"^(?:" + "|".join(_CONNECTIVES) + r")\b(?!\s+(?:far|much|many|long|that|called|on)\b)\s*[,:;\-]?\s+",
    re.I,
)
_LABEL_PREFIX_RE = re.compile(
    r"^(?:breaking(?:\s+news)?|update[sd]?|exclusive|watch|live|just\s+in)\s*[:\-\u2013\u2014]\s*", re.I
)
_PREMISE_MARKER_RE = re.compile(
    r"^(since|because|given that|considering that|seeing that)\s+", re.I
)

# Words that cannot start a standalone clause (relative / subordinating).
_SUBORDINATORS = frozenset({
    "which", "who", "whom", "whose", "that", "where", "when", "while", "whereas",
    "although", "though", "because", "since", "if", "unless", "as", "than",
    "whether", "so", "until", "after", "before", "once", "whenever", "wherever",
})

_BOILERPLATE_RE = re.compile(
    r"\b(subscribe|sign up|newsletter|cookies?|privacy policy|terms of (?:use|service)|"
    r"all rights reserved|click here|read more|advertisement|follow us|share this|"
    r"copyright|sponsored|accept all|log in|sign in)\b",
    re.I,
)
_OPINION_RE = re.compile(
    r"\b(i think|i believe|i feel|in my opinion|imo|imho|personally|i guess|"
    r"i suppose|i hope|i love|i hate|i wish)\b",
    re.I,
)
_ATTRIBUTION_RE = re.compile(r"\b(according to|said that|claims? that|reported that)\b", re.I)

_CLAIM_VERB_LEMMAS = frozenset({
    "cause", "lead", "link", "prevent", "cure", "treat", "kill", "increase",
    "decrease", "reduce", "raise", "lower", "trigger", "spread", "contain", "ban",
    "approve", "reject", "win", "lose", "die", "steal", "sign", "pass", "announce",
    "report", "confirm", "deny", "claim", "say", "state", "admit", "reveal", "show",
    "find", "prove", "discover", "cost", "earn", "owe", "own", "buy", "sell", "fire",
    "arrest", "charge", "convict", "elect", "resign", "launch", "invent", "create",
    "build", "destroy", "invade", "attack", "vote", "protect", "improve", "worsen",
    "affect", "guarantee", "contribute", "give", "make", "produce", "emit", "fall",
    "rise", "grow", "drop",
})
_ABSOLUTE_WORDS = frozenset({
    "always", "never", "every", "everyone", "everybody", "nobody", "none", "all",
    "entire", "whole", "only", "guaranteed", "impossible", "completely", "totally",
    "100%",
})
_HEDGE_WORDS = frozenset({"maybe", "perhaps", "possibly", "might", "probably"})
_NEGATION_WORDS = frozenset({
    "not", "no", "never", "none", "nobody", "nothing", "neither", "nor",
    "cannot", "without", "n't",
})
_NUMERIC_ENTS = frozenset({"PERCENT", "MONEY", "QUANTITY", "CARDINAL", "DATE"})
_NAMED_ENTS = frozenset({"PERSON", "ORG", "GPE", "NORP", "LOC", "EVENT", "LAW", "PRODUCT", "FAC"})
_FIRST_PERSON = frozenset({"i", "we", "my", "me", "our"})
_ACRONYMS = {"ai": "AI", "uk": "UK", "eu": "EU", "un": "UN", "uae": "UAE", "usa": "USA"}
_PRONOUN_PERSON = frozenset({"he", "she"})
_PRONOUN_THING = frozenset({"it", "they", "this", "these", "those"})


# --------------------------------------------------------------------------- #
# Internal candidate record
# --------------------------------------------------------------------------- #
@dataclass
class _Candidate:
    text: str
    sentence_no: int            # 1-based sentence ordinal in the document
    sub_idx: int                # 0-based index of the clause inside its sentence
    char_start: int
    char_end: int
    is_assertion: bool
    check_score: float
    role: str = "standalone"    # standalone | premise | conclusion
    lemmas: FrozenSet[str] = frozenset()
    polarity: Tuple = ()
    final_score: float = 0.0
    drop_reason: str = ""


def _jaccard(a: FrozenSet[str], b: FrozenSet[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class ClaimExtractorV3:
    """spaCy-based claim builder with a local "crux" ranking."""

    def __init__(
        self,
        use_llm_crux: Optional[bool] = None,
        resolve_pronouns: bool = False,
        max_claims_text: int = DEFAULT_MAX_CLAIMS_TEXT,
        max_claims_article: int = DEFAULT_MAX_CLAIMS_ARTICLE,
    ):
        self.models = get_model_manager()
        self.resolve_pronouns = resolve_pronouns
        self.max_claims_text = max_claims_text
        self.max_claims_article = max_claims_article
        if use_llm_crux is None:
            use_llm_crux = self._settings_flag("use_llm_crux")
        self.use_llm_crux = use_llm_crux
        self._crux_extractor = None  # lazy: only built if the LLM path is enabled

    # ------------------------------------------------------------------ #
    # Public API (unchanged signatures)
    # ------------------------------------------------------------------ #
    @property
    def crux_extractor(self):
        if self._crux_extractor is None:
            from app.services.extraction.crux_extractor import CruxExtractor
            self._crux_extractor = CruxExtractor()
        return self._crux_extractor

    def extract(self, processed_input: ProcessedInput) -> List[RawClaim]:
        claims, _ = self.extract_with_report(processed_input)
        return claims

    def extract_from_text(self, text: str, max_claims: Optional[int] = None) -> List[RawClaim]:
        claims, _ = self._build(text, article_mode=False, max_claims=max_claims or self.max_claims_text)
        return claims

    def extract_crux(self, processed_input: ProcessedInput) -> List[RawClaim]:
        """Most important claims of a long document / URL (article mode)."""
        if self.use_llm_crux:
            try:
                llm_claims = self.crux_extractor.extract(processed_input.text)
                cleaned = self._postprocess_llm_claims(llm_claims)
                if cleaned:
                    return cleaned
                logger.info("LLM crux returned nothing usable; using local crux")
            except Exception as exc:  # never let an optional LLM break the request
                logger.warning("LLM crux failed (%s); using local crux", exc)
        claims, _ = self._build(
            processed_input.text, article_mode=True, max_claims=self.max_claims_article
        )
        return claims

    def extract_with_report(self, processed_input: ProcessedInput) -> Tuple[List[RawClaim], List[Dict]]:
        article = processed_input.source_type == InputType.URL
        limit = self.max_claims_article if article else self.max_claims_text
        return self._build(processed_input.text, article_mode=article, max_claims=limit)

    # ------------------------------------------------------------------ #
    # Core build
    # ------------------------------------------------------------------ #
    def _build(self, text: str, article_mode: bool, max_claims: int) -> Tuple[List[RawClaim], List[Dict]]:
        text = (text or "")[:MAX_INPUT_CHARS]
        nlp = self.models.nlp
        candidates: List[_Candidate] = []
        sentence_no = 0
        deadline = time.monotonic() + SPLIT_BUDGET_SECONDS
        prev_ctx: Optional[Dict] = None

        for para_start, para in self._paragraphs(text):
            doc = nlp(para)
            for sent in doc.sents:
                if not sent.text.strip():
                    continue
                sentence_no += 1
                made = self._candidates_from_sentence(
                    nlp, sent, sentence_no, para_start, prev_ctx, article_mode, deadline
                )
                candidates.extend(made)
                prev_ctx = self._subject_context(sent)

        self._link_premises(candidates)
        self._score_and_filter(candidates, article_mode)

        # Fallback: a short, clearly assertive statement ("X is Y.") must
        # always stay checkable. If scoring dropped everything (transient
        # parsing/model variance), resurrect the strongest assertive
        # candidate instead of answering "No Verifiable Claims Found".
        if not any(c.drop_reason == "" for c in candidates):
            assertive = [c for c in candidates if c.is_assertion]
            if len(text.split()) <= ASSERTION_FALLBACK_WORDS and assertive:
                best = max(assertive, key=lambda c: c.final_score)
                best.drop_reason = ""
                logger.info("Assertion fallback: recovered '%s' after filter drop", best.text)

        kept = self._dedupe(candidates)
        kept = self._trim(kept, max_claims)

        claims = [
            RawClaim(
                text=c.text,
                sentence_index=(c.sentence_no - 1) * 100 + c.sub_idx,
                char_start=c.char_start,
                char_end=c.char_end,
                is_assertion=c.is_assertion,
            )
            for c in kept
        ]
        report = [
            {
                "text": c.text,
                "score": round(c.final_score, 3),
                "role": c.role,
                "is_assertion": c.is_assertion,
                "kept": c.drop_reason == "",
                "drop_reason": c.drop_reason,
            }
            for c in sorted(candidates, key=lambda c: (c.sentence_no, c.sub_idx))
        ]
        return claims, report

    # ------------------------------------------------------------------ #
    # Text segmentation
    # ------------------------------------------------------------------ #
    @staticmethod
    def _paragraphs(text: str):
        """Yield (char_offset, paragraph) so bullets/headlines never merge."""
        for m in re.finditer(r"[^\n]+", text):
            chunk = m.group(0)
            if chunk.strip():
                yield m.start(), chunk

    def _candidates_from_sentence(self, nlp, sent, sentence_no, para_start, prev_ctx, article_mode, deadline):
        base = para_start + sent.start_char
        pieces = self._split_clauses(nlp, sent, deadline)
        unsplit = len(pieces) == 1
        out: List[_Candidate] = []
        for sub_idx, (piece, p_start, p_end) in enumerate(pieces):
            cand = self._make_candidate(
                nlp, piece, sentence_no, sub_idx,
                base + p_start, base + p_end, prev_ctx, article_mode,
                reuse_span=sent if unsplit else None,
            )
            if cand is not None:
                out.append(cand)
        return out

    # -- clause splitting --------------------------------------------------- #
    def _split_clauses(self, nlp, sent, deadline) -> List[Tuple[str, int, int]]:
        """Split at , ; and/but/or only when both sides are complete clauses."""
        sent_text = sent.text
        whole = [(sent_text, 0, len(sent_text))]
        if (len(sent_text.strip()) < 20
                or len(sent) > MAX_SENTENCE_TOKENS_TO_SPLIT
                or time.monotonic() > deadline):
            return whole
        # two clauses need at least two verbs; cheap pre-check on the existing parse
        if sum(1 for t in sent if t.pos_ in ("VERB", "AUX")) < 2:
            return whole

        cuts = self._candidate_cuts(sent)
        if not cuts:
            return whole

        pieces: List[Tuple[str, int, int]] = []
        start = 0
        splits = 0
        for cut_start, cut_end in cuts:
            if splits >= MAX_SPLITS_PER_SENTENCE or time.monotonic() > deadline:
                break
            if cut_start <= start or self._inside_quotes(sent_text, cut_start):
                continue
            left, right = sent_text[start:cut_start], sent_text[cut_end:]
            if not self._both_standalone(nlp, left, right):
                continue
            pieces.append((left, start, cut_start))
            start = cut_end
            splits += 1
        if not splits:
            return whole
        pieces.append((sent_text[start:], start, len(sent_text)))
        return pieces

    @staticmethod
    def _candidate_cuts(sent) -> List[Tuple[int, int]]:
        """(cut_start, cut_end) char offsets, relative to the sentence, for each delimiter."""
        offset = sent.start_char
        toks = list(sent)
        cuts: List[Tuple[int, int]] = []
        i = 0
        while i < len(toks):
            t = toks[i]
            a = t.idx - offset
            if t.text == ";":
                cuts.append((a, a + 1))
            elif t.text == ",":
                end = a + 1
                # ", and" / ", but" / ", or" counts as a single delimiter
                if i + 1 < len(toks) and toks[i + 1].lower_ in ("and", "but", "or") and toks[i + 1].dep_ == "cc":
                    nxt = toks[i + 1]
                    end = nxt.idx - offset + len(nxt.text)
                    i += 1
                cuts.append((a, end))
            elif t.dep_ == "cc" and t.lower_ in ("and", "but", "or"):
                cuts.append((a, a + len(t.text)))
            i += 1
        return cuts

    @staticmethod
    def _inside_quotes(text: str, pos: int) -> bool:
        before = text[:pos]
        return (before.count('"') % 2 == 1) or (before.count("\u201c") > before.count("\u201d"))

    def _both_standalone(self, nlp, left: str, right: str) -> bool:
        """True when each half, parsed on its own, is a complete clause."""
        pair = []
        for piece in (left, right):
            piece = piece.strip(" \t,;:-")
            words = piece.split()
            if len(words) < MIN_CLAUSE_TOKENS or words[0].lower().strip("\"'") in _SUBORDINATORS:
                return False
            pair.append(_AI_RE.sub("AI", piece))
        for k, doc in enumerate(nlp.pipe(pair, disable=["ner"])):
            if not self._is_standalone_doc(doc, is_left=(k == 0)):
                return False
        return True

    @staticmethod
    def _is_standalone_doc(doc, is_left: bool) -> bool:
        words = [t for t in doc if not t.is_punct and not t.is_space]
        if len(words) < MIN_CLAUSE_TOKENS:
            return False
        root = next((t for t in doc if t.dep_ == "ROOT"), None)
        if root is None or root.pos_ not in ("VERB", "AUX"):
            return False
        if not any(c.dep_ in ("nsubj", "nsubjpass", "csubj", "csubjpass", "expl") for c in root.children):
            return False
        if is_left and any(c.dep_ == "ccomp" for c in root.children):
            # "X said that A, and B": B probably belongs to the reported clause.
            return False
        return True

    # -- candidate construction -------------------------------------------- #
    def _make_candidate(self, nlp, piece, sentence_no, sub_idx, c_start, c_end, prev_ctx, article_mode,
                        reuse_span=None):
        text = self._clean(piece)
        if not text:
            return None

        role = "standalone"
        # Premise fragment: "Since AI always gives 100% accurate claims."
        m = _PREMISE_MARKER_RE.match(text)
        if m:
            marker_doc = nlp(_AI_RE.sub("AI", text))
            first = marker_doc[0] if len(marker_doc) else None
            rest = text[m.end():]
            rest_is_temporal = bool(re.match(r"^(?:\d{4}\b|\d+\s|the\s+(?:war|start|beginning|last|\w+\s+(?:began|started)))", rest, re.I))
            if (first is not None and first.dep_ == "mark" and first.head.dep_ == "ROOT"
                    and "," not in text and not rest_is_temporal):
                text = self._clean(rest)
                role = "premise"

        if self.resolve_pronouns and prev_ctx:
            text = self._resolve_pronoun(nlp, text, prev_ctx)

        text = self._finalize_text(text)
        if len(text) < 8:
            return None

        if reuse_span is not None and self._same_text(text, reuse_span.text):
            sub = reuse_span.as_doc()      # no extra parse for untouched sentences
        else:
            sub = nlp(text)
        words = [t for t in sub if not t.is_punct and not t.is_space]
        if len(words) < MIN_CLAUSE_TOKENS:
            return None
        if text.endswith("?"):
            return None
        if article_mode and _BOILERPLATE_RE.search(text) and len(words) < 25:
            return None

        score, is_assertion = self._check_worthiness(sub, text)
        return _Candidate(
            text=text,
            sentence_no=sentence_no,
            sub_idx=sub_idx,
            char_start=c_start,
            char_end=c_end,
            is_assertion=is_assertion,
            check_score=score,
            role=role,
            lemmas=self._content_lemmas(sub),
            polarity=self._polarity(sub),
        )

    @staticmethod
    def _same_text(a: str, b: str) -> bool:
        return a.strip().rstrip(".!? ") == b.strip().rstrip(".!? ")

    @staticmethod
    def _clean(text: str) -> str:
        text = _URL_RE.sub("", text)
        text = _LIST_MARKER_RE.sub("", text)
        text = _WS_RE.sub(" ", text).strip(" \t\"'")
        text = _LABEL_PREFIX_RE.sub("", text, count=1)
        for _ in range(2):  # "But however, ..." -> strip up to two connectives
            stripped = _LEADING_CONNECTIVE_RE.sub("", text, count=1)
            if stripped == text:
                break
            text = stripped.strip()
        return text.strip(" ,;:-")

    @staticmethod
    def _finalize_text(text: str) -> str:
        text = _AI_RE.sub("AI", text.strip())
        if not text:
            return text
        first_word = text.split()[0]
        key = first_word.lower().strip(".,")
        if key in _ACRONYMS:
            text = _ACRONYMS[key] + text[len(first_word.rstrip('.,')):]
        elif first_word[0].isalpha() and first_word[0].islower():
            text = text[0].upper() + text[1:]
        if text[-1] not in ".!?\"'\u201d":
            text += "."
        return text

    # -- scoring ------------------------------------------------------------ #
    def _check_worthiness(self, sub, text: str) -> Tuple[float, bool]:
        words = [t for t in sub if not t.is_punct and not t.is_space]
        root = next((t for t in sub if t.dep_ == "ROOT"), None)
        has_subject = any(t.dep_ in ("nsubj", "nsubjpass", "csubj", "csubjpass", "expl") for t in sub)
        has_verb = any(t.pos_ in ("VERB", "AUX") for t in sub)
        is_assertion = bool(has_subject and has_verb)

        score = 0.15 if is_assertion else 0.05

        ent_labels = {e.label_ for e in sub.ents}
        if ent_labels & _NUMERIC_ENTS or any(t.like_num for t in sub):
            score += 0.20
        if ent_labels & _NAMED_ENTS:
            score += 0.15
        lowered = {t.lower_ for t in sub}
        if lowered & _ABSOLUTE_WORDS or "100%" in text or any(t.lower_ == "no" and t.dep_ == "det" for t in sub):
            score += 0.20
        if any(t.lemma_.lower() in _CLAIM_VERB_LEMMAS and t.pos_ == "VERB" for t in sub):
            score += 0.20
        if _ATTRIBUTION_RE.search(text):
            score += 0.10

        if _OPINION_RE.search(text):
            score -= 0.25
        if any(t.dep_ in ("nsubj", "nsubjpass") and t.lower_ in _FIRST_PERSON for t in sub):
            score -= 0.25
        if lowered & _HEDGE_WORDS:
            score -= 0.05
        if root is not None and root.pos_ == "VERB" and root.tag_ == "VB" and not has_subject:
            score -= 0.30  # imperative ("Click here", "Read the article")
        if len(words) > 80:
            score -= 0.05
        return max(0.0, min(1.0, score)), is_assertion

    @staticmethod
    def _content_lemmas(sub) -> FrozenSet[str]:
        return frozenset(
            t.lemma_.lower()
            for t in sub
            if t.pos_ in ("NOUN", "PROPN", "VERB", "NUM", "ADJ") and not t.is_stop
        )

    @staticmethod
    def _polarity(sub) -> Tuple:
        negated = any(t.dep_ == "neg" or t.lower_ in _NEGATION_WORDS for t in sub)
        numbers = frozenset(re.sub(r"[^\d.]", "", t.text) for t in sub if t.like_num and re.search(r"\d", t.text))
        return (negated, numbers)

    # -- premise linking / filtering / ranking ------------------------------ #
    @staticmethod
    def _link_premises(cands: List[_Candidate]) -> None:
        by_sentence: Dict[int, List[_Candidate]] = {}
        for c in cands:
            by_sentence.setdefault(c.sentence_no, []).append(c)
        for c in cands:
            if c.role == "premise":
                for prev in by_sentence.get(c.sentence_no - 1, []):
                    if prev.role == "standalone":
                        prev.role = "conclusion"

    def _score_and_filter(self, cands: List[_Candidate], article_mode: bool) -> None:
        min_score = MIN_SCORE_ARTICLE if article_mode else MIN_SCORE_TEXT
        centrality = self._centrality(cands)
        for c in cands:
            score = c.check_score
            if c.role == "premise":
                score += 0.15
            if article_mode and c.sentence_no <= 3:
                score += 0.10  # lede bonus: news puts the claim up front
            score += 0.15 * centrality.get(id(c), 0.0)
            c.final_score = min(1.0, score)

            keep = (c.is_assertion and c.check_score >= min_score) or c.check_score >= 0.30
            if c.role == "premise":
                keep = True
            if not keep:
                c.drop_reason = "low check-worthiness"

    @staticmethod
    def _centrality(cands: List[_Candidate]) -> Dict[int, float]:
        live = [c for c in cands if c.lemmas]
        if len(live) < 3:
            return {}
        raw = {}
        for c in live:
            others = [o for o in live if o is not c]
            raw[id(c)] = sum(_jaccard(c.lemmas, o.lemmas) for o in others) / len(others)
        top = max(raw.values()) or 1.0
        return {k: v / top for k, v in raw.items()}

    def _dedupe(self, cands: List[_Candidate]) -> List[_Candidate]:
        kept: List[_Candidate] = []
        for c in sorted((c for c in cands if not c.drop_reason), key=lambda c: -c.final_score):
            dup_of = next((k for k in kept if self._is_duplicate(c, k)), None)
            if dup_of is not None:
                c.drop_reason = "duplicate"
                continue
            kept.append(c)
        return kept

    def _is_duplicate(self, a: _Candidate, b: _Candidate) -> bool:
        if a.polarity != b.polarity:   # "always" vs "never", 20% vs 30% are NOT duplicates
            return False
        jac = _jaccard(a.lemmas, b.lemmas)
        if jac >= DUPLICATE_JACCARD:
            return True
        if jac >= 0.4:
            cos = self._cosine(a.text, b.text)
            return cos is not None and cos >= DUPLICATE_COSINE
        return False

    def _cosine(self, a: str, b: str) -> Optional[float]:
        embed = getattr(self.models, "get_embedding", None)
        if embed is None:
            return None
        try:
            import numpy as np
            va, vb = np.asarray(embed(a)), np.asarray(embed(b))
            denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
            return float(np.dot(va, vb) / denom) if denom else None
        except Exception:
            return None

    @staticmethod
    def _trim(kept: List[_Candidate], max_claims: int) -> List[_Candidate]:
        if len(kept) > max_claims:
            ranked = sorted(kept, key=lambda c: -c.final_score)
            for c in ranked[max_claims:]:
                c.drop_reason = "below crux cut-off"
            kept = ranked[:max_claims]
        return sorted(kept, key=lambda c: (c.sentence_no, c.sub_idx))

    # -- pronoun resolution (opt-in) ---------------------------------------- #
    @staticmethod
    def _subject_context(sent) -> Optional[Dict]:
        subj = next((t for t in sent if t.dep_ in ("nsubj", "nsubjpass")), None)
        if subj is None:
            return None
        chunk = next((nc for nc in sent.noun_chunks if nc.root.i == subj.i), None)
        ent = next((e for e in sent.ents if e.start <= subj.i < e.end), None)
        return {
            "text": (ent.text if ent else (chunk.text if chunk else subj.text)),
            "label": ent.label_ if ent else None,
        }

    @staticmethod
    def _resolve_pronoun(nlp, text: str, ctx: Dict) -> str:
        parts = text.split(None, 1)
        if len(parts) < 2:
            return text
        head, rest = parts[0], parts[1]
        key = head.lower()
        if key in _PRONOUN_PERSON and ctx.get("label") == "PERSON":
            return f"{ctx['text']} {rest}"
        if key in _PRONOUN_THING and ctx.get("label") in ("ORG", "GPE", "PRODUCT", "NORP", "EVENT", "LAW"):
            return f"{ctx['text']} {rest}"
        return text

    # -- LLM crux post-processing ------------------------------------------- #
    def _postprocess_llm_claims(self, llm_claims) -> List[RawClaim]:
        seen: List[str] = []
        out: List[RawClaim] = []
        for i, rc in enumerate(llm_claims or []):
            raw = getattr(rc, "text", rc)
            if not isinstance(raw, str):
                continue
            text = self._finalize_text(self._clean(raw))
            key = re.sub(r"\W+", " ", text.lower()).strip()
            if len(text) < 8 or key in seen:
                continue
            seen.append(key)
            out.append(RawClaim(text=text, sentence_index=i * 100, char_start=0,
                                char_end=len(text), is_assertion=True))
        return out[: self.max_claims_article]

    @staticmethod
    def _settings_flag(name: str) -> bool:
        try:
            from app.core.config import settings
            return bool(getattr(settings, name, False))
        except Exception:
            return False


# Friendlier alias for new code; the old import path keeps working.
ClaimBuilder = ClaimExtractorV3
