"""
TruthLens Services Module

Exports all analysis services.
"""

from app.services.domain_trust import score_domain, load_domain_trust_db
from app.services.claim_extractor import extract_claims, extract_candidates, refine_claims
from app.services.factcheck import search_factchecks
from app.services.news_search import search_news
from app.services.stance import classify_all_stances, weighted_stance
from app.services.aggregation import aggregate_verdict
from app.services.explanation import generate_explanation
from app.services.llm_verdict import llm_assess_claim
from app.services.deepfake import analyze_image_for_deepfake, get_deepfake_detector

__all__ = [
    "score_domain",
    "load_domain_trust_db",
    "extract_claims",
    "extract_candidates",
    "refine_claims",
    "search_factchecks",
    "search_news",
    "classify_all_stances",
    "weighted_stance",
    "aggregate_verdict",
    "generate_explanation",
    "llm_assess_claim",
    "analyze_image_for_deepfake",
    "get_deepfake_detector",
]

