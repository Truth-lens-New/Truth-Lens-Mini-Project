"""
Stress Test Phase 2A Pipeline

Comprehensive testing of the TruthLens investigation pipeline with 15 diverse test cases.
Covers: Known Misinfo, Wikidata, Web Search, Opinions, Predictions, and Edge Cases.
"""

import sys
import os
import time
import json
from tabulate import tabulate

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../app'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.domain import TypedClaim, ClaimType
from app.services.investigation import get_verdict_engine

def run_stress_test():
    print("🚀 Starting Phase 2A Pipeline Stress Test (15 Cases)...\n")
    
    engine = get_verdict_engine()
    
    test_cases = [
        # --- Category 1: Known Misinformation (Internal DB) ---
        {
            "text": "COVID vaccines cause autism.", 
            "type": ClaimType.SCIENTIFIC_MEDICAL,
            "expected": "verified_false",
            "desc": "Known Misinfo DB"
        },
        {
            "text": "The earth is flat.", 
            "type": ClaimType.SCIENTIFIC_MEDICAL,
            "expected": "verified_false",
            "desc": "Known Misinfo DB"
        },
        
        # --- Category 2: Wikidata Facts (Structured) ---
        {
            "text": "New Delhi is the capital of India.", 
            "type": ClaimType.FACTUAL_STATEMENT,
            "expected": "verified_true",
            "desc": "Wikidata True"
        },
        {
            "text": "Mumbai is the capital of India.", 
            "type": ClaimType.FACTUAL_STATEMENT,
            "expected": "verified_false",
            "desc": "Wikidata False"
        },
        {
            "text": "Barack Obama was born in 1961.", 
            "type": ClaimType.FACTUAL_STATEMENT,
            "expected": "verified_true",
            "desc": "Wikidata Date"
        },
        
        # --- Category 3: Web Search (General Knowledge) ---
        {
            "text": "Python is a programming language.", 
            "type": ClaimType.FACTUAL_STATEMENT,
            "expected": "verified_true",
            "desc": "Web Search Basic"
        },
        {
            "text": "Smoking cigarettes causes lung cancer.", 
            "type": ClaimType.SCIENTIFIC_MEDICAL,
            "expected": "verified_true",
            "desc": "Web Search Medical"
        },
        {
            "text": "The moon is made of green cheese.", 
            "type": ClaimType.FACTUAL_STATEMENT,
            "expected": "verified_false",
            "desc": "Web Search False"
        },
        
        # --- Category 4: Complex/Disputed ---
        {
            "text": "Coffee is bad for your health.", 
            "type": ClaimType.SCIENTIFIC_MEDICAL,
            "expected": "disputed", # or unverified, difficult
            "desc": "Disputed/Nuanced"
        },
        {
            "text": "Elon Musk is the CEO of Tesla and Google.", 
            "type": ClaimType.FACTUAL_STATEMENT,
            "expected": "verified_false",
            "desc": "Partial Falsehood"
        },
        
        # --- Category 5: Historical/Attribution ---
        {
            "text": "France won the 2018 FIFA World Cup.", 
            "type": ClaimType.FACTUAL_STATEMENT,
            "expected": "verified_true",
            "desc": "Recent History"
        },
        {
            "text": "Albert Einstein said 'God does not play dice'.", 
            "type": ClaimType.QUOTE_ATTRIBUTION,
            "expected": "verified_true",
            "desc": "Quote Attribution"
        },
        
        # --- Category 6: Non-Checkable ---
        {
            "text": "Vanilla ice cream is the best flavor.", 
            "type": ClaimType.OPINION,
            "expected": "not_checkable",
            "desc": "Opinion"
        },
        {
            "text": "Humans will live on Mars by 2030.", 
            "type": ClaimType.OPINION,  # Predictions are opinions
            "expected": "not_checkable",
            "desc": "Prediction"
        },
        
        # --- Category 7: Edge Cases ---
        {
            "text": "Afjkh3489 sfdjk jklsdf89.", 
            "type": ClaimType.FACTUAL_STATEMENT,
            "expected": "insufficient_evidence",
            "desc": "Gibberish"
        }
    ]
    
    results_table = []
    
    start_total = time.time()
    
    for i, case in enumerate(test_cases):
        print(f"[{i+1}/15] Testing: '{case['text'][:50]}...' ({case['desc']})")
        
        claim = TypedClaim(
            text=case["text"],
            claim_type=case["type"],
            type_confidence=0.9,
            is_checkable=case["type"] not in [ClaimType.OPINION],
            evidence_strategy="test",
            status="pending_verification",
            sentence_index=0
        )
        
        t0 = time.time()
        result = engine.verify(claim)
        duration = (time.time() - t0) * 1000
        
        # Determine status
        pass_status = "✅ PASS" if result.verdict.value == case["expected"] else "❌ FAIL"
        
        # For disputed/unverified on complex topics, be lenient
        if case["expected"] in ["disputed", "unverified"] and result.verdict.value in ["disputed", "unverified", "insufficient_evidence"]:
             pass_status = "⚠️ OK"
             
        # For misinfo/web search, allow small variations if logic holds
        if case["expected"] == "verified_false" and result.verdict.value == "verified_false":
             pass_status = "✅ PASS"
        
        results_table.append([
            i+1,
            case["text"][:30] + "...",
            case["desc"],
            case["expected"],
            result.verdict.value,
            f"{result.confidence:.2f}",
            len(result.evidence_items),
            f"{duration:.0f}ms",
            pass_status
        ])
        
        # Wait a bit to avoid strict rate limits if serial
        time.sleep(1)

    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    print(tabulate(results_table, headers=["#", "Claim", "Category", "Expected", "Actual", "Conf", "Evid", "Time", "Status"]))
    
    total_time = time.time() - start_total
    print(f"\nTotal Test Time: {total_time:.2f}s")

if __name__ == "__main__":
    run_stress_test()
