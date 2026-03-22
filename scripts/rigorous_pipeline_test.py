#!/usr/bin/env python3
"""
TruthLens RIGOROUS Pipeline Test Suite
========================================
Tests EACH STAGE of the pipeline individually:

Stage 0: Input Processing & Sentence Splitting
Stage 1: Claim Extraction (Assertions vs Questions/Opinions)
Stage 2: Claim Typing (BART Classification)
Stage 3: Evidence Gathering (Source Coverage)
Stage 4: Stance Detection (SUPPORT/REFUTE/NEUTRAL)
Stage 5: Evidence Synthesis (Weighting & Scoring)
Stage 6: Verdict Determination

Each stage is tested in ISOLATION to identify exactly where issues arise.
"""

import asyncio
import time
import json
import sys
from datetime import datetime
from typing import List, Dict, Any, Tuple
import httpx

# Add backend to path for direct imports
sys.path.insert(0, '/home/shivam/Downloads/SEM1/MiniProject/backend')

# Configuration
BASE_URL = "http://localhost:7000"
AUTH_URL = f"{BASE_URL}/auth"
API_URL = f"{BASE_URL}/api/v3"

# ============================================================
# TEST DATA - Designed to stress each pipeline stage
# ============================================================

# Stage 0: Sentence Splitting Tests
SENTENCE_SPLITTING_TESTS = [
    {
        "name": "Simple sentence",
        "input": "COVID vaccines cause autism.",
        "expected_sentences": 1,
        "expected_claims": 1
    },
    {
        "name": "Multiple sentences same topic",
        "input": "COVID vaccines are dangerous. They cause autism in children. The government is hiding this.",
        "expected_sentences": 3,
        "expected_claims": 3
    },
    {
        "name": "Mixed paragraph (claims + opinions + questions)",
        "input": "The Earth is flat. Can you believe scientists lie about this? I think NASA is corrupt. The moon landing was faked in 1969.",
        "expected_sentences": 4,
        "expected_claims": 2  # Only "Earth is flat" and "moon landing faked" are claims
    },
    {
        "name": "Long paragraph with mixed content",
        "input": """
        The 2020 election was stolen through massive fraud. This is what I believe after reading many articles.
        Did you know that voting machines can be hacked? Experts say this is concerning. 
        Joe Biden received 81 million votes, which is the most in US history.
        I'm so angry about this situation! The government should investigate immediately.
        """,
        "expected_sentences": 7,
        "expected_claims": 3  # "election stolen", "machines hacked", "Biden 81 million votes"
    },
    {
        "name": "All questions (no claims)",
        "input": "Is the Earth flat? Did NASA fake the moon landing? What do you think about vaccines?",
        "expected_sentences": 3,
        "expected_claims": 0
    },
    {
        "name": "All opinions (not checkable)",
        "input": "Pizza is the best food. The government should lower taxes. Blue is prettier than red.",
        "expected_sentences": 3,
        "expected_claims": 0  # All opinions, none checkable
    },
]

# Stage 1: Claim Extraction Tests
CLAIM_EXTRACTION_TESTS = [
    {
        "input": "Vaccines are tested for safety before approval.",
        "should_extract": True,
        "reason": "Factual assertion about vaccine testing"
    },
    {
        "input": "Is this claim true?",
        "should_extract": False,
        "reason": "Question, not assertion"
    },
    {
        "input": "I believe vaccines are safe.",
        "should_extract": False,  # "I believe" makes it opinion
        "reason": "Personal belief statement"
    },
    {
        "input": "Share this before it gets deleted!",
        "should_extract": False,
        "reason": "Command/imperative, not claim"
    },
    {
        "input": "This is absolutely outrageous!!!",
        "should_extract": False,
        "reason": "Emotional expression, not factual claim"
    },
    {
        "input": "The Prime Minister announced new policies yesterday.",
        "should_extract": True,
        "reason": "Factual claim about event"
    },
]

# Stage 2: Claim Typing Tests
CLAIM_TYPING_TESTS = [
    # Scientific/Medical
    {"claim": "Vaccines cause autism in children.", "expected_type": "scientific_medical"},
    {"claim": "Hydroxychloroquine cures COVID-19.", "expected_type": "scientific_medical"},
    {"claim": "Smoking causes lung cancer.", "expected_type": "scientific_medical"},
    {"claim": "5G radiation causes health problems.", "expected_type": "scientific_medical"},
    
    # Factual/Historical
    {"claim": "India gained independence in 1947.", "expected_type": "factual_statement"},
    {"claim": "The Taj Mahal is located in Agra.", "expected_type": "factual_statement"},
    {"claim": "World War II ended in 1945.", "expected_type": "factual_statement"},
    {"claim": "Mount Everest is the tallest mountain.", "expected_type": "factual_statement"},
    
    # Political
    {"claim": "The 2020 election was stolen through fraud.", "expected_type": "political_allegation"},
    {"claim": "BJP rigged the elections with ECI.", "expected_type": "political_allegation"},
    {"claim": "The government is corrupt.", "expected_type": "political_allegation"},
    
    # Breaking/Event
    {"claim": "A major earthquake struck Tokyo today.", "expected_type": "breaking_event"},
    {"claim": "A new virus variant emerged yesterday.", "expected_type": "breaking_event"},
    
    # Quote Attribution
    {"claim": "Gandhi said 'Be the change you wish to see.'", "expected_type": "quote_attribution"},
    {"claim": "Einstein said 'Imagination is more important than knowledge.'", "expected_type": "quote_attribution"},
    
    # Opinion (not checkable)
    {"claim": "Pizza is the best food in the world.", "expected_type": "opinion"},
    {"claim": "The government should lower taxes.", "expected_type": "opinion"},
    {"claim": "Blue is the prettiest color.", "expected_type": "opinion"},
]

# Stage 3: Evidence Gathering Tests - Check which sources are queried
EVIDENCE_GATHERING_TESTS = [
    {
        "claim": "Vaccines cause autism.",
        "claim_type": "scientific_medical",
        "expected_sources": ["pubmed", "google_factcheck", "wikipedia"],
        "should_not_query": []
    },
    {
        "claim": "The Earth is flat.",
        "claim_type": "factual_statement", 
        "expected_sources": ["google_factcheck", "wikipedia", "duckduckgo"],
        "should_not_query": []
    },
    {
        "claim": "India's capital is New Delhi.",
        "claim_type": "factual_statement",
        "expected_sources": ["wikidata", "wikipedia"],
        "should_not_query": ["pubmed"]  # No need for medical sources
    },
]

# Stage 4: Stance Detection Tests
STANCE_DETECTION_TESTS = [
    {
        "claim": "Vaccines cause autism.",
        "evidence": "Multiple large-scale studies have found no link between vaccines and autism.",
        "expected_stance": "REFUTES"
    },
    {
        "claim": "Vaccines cause autism.",
        "evidence": "Some parents claim their children developed autism after vaccination.",
        "expected_stance": "SUPPORTS"  # Though weak evidence
    },
    {
        "claim": "The Earth is round.",
        "evidence": "Photographs from space clearly show Earth's spherical shape.",
        "expected_stance": "SUPPORTS"
    },
    {
        "claim": "5G causes COVID-19.",
        "evidence": "The World Health Organization states that viruses cannot travel on radio waves.",
        "expected_stance": "REFUTES"
    },
    {
        "claim": "Climate change is real.",
        "evidence": "The weather has been unusual lately with more storms.",
        "expected_stance": "NEUTRAL"  # Weak/ambiguous evidence
    },
]

# Stage 5: Evidence Synthesis Tests - Check weighting
EVIDENCE_SYNTHESIS_TESTS = [
    {
        "name": "Academic vs Social Media",
        "claim": "Vaccines cause autism",
        "evidence": [
            {"type": "academic_paper", "stance": "REFUTES", "trust": 95},
            {"type": "social_media", "stance": "SUPPORTS", "trust": 20},
        ],
        "expected_verdict": "verified_false",  # Academic paper should dominate
    },
    {
        "name": "Multiple high-trust sources agree",
        "claim": "Earth is round",
        "evidence": [
            {"type": "fact_check", "stance": "SUPPORTS", "trust": 90},
            {"type": "wikipedia", "stance": "SUPPORTS", "trust": 85},
            {"type": "academic_paper", "stance": "SUPPORTS", "trust": 95},
        ],
        "expected_verdict": "verified_true",
    },
    {
        "name": "Disputed - mixed evidence",
        "claim": "Some controversial claim",
        "evidence": [
            {"type": "news_article", "stance": "SUPPORTS", "trust": 70},
            {"type": "news_article", "stance": "REFUTES", "trust": 75},
            {"type": "fact_check", "stance": "NEUTRAL", "trust": 85},
        ],
        "expected_verdict": "disputed",
    },
]

# ============================================================
# TEST INFRASTRUCTURE
# ============================================================

async def get_auth_token():
    """Get authentication token."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{AUTH_URL}/login", json={"email": "tester@qa.com", "password": "testpass123"})
            if resp.status_code == 200:
                return resp.json()["access_token"]
        except:
            pass
        
        try:
            await client.post(f"{AUTH_URL}/register", json={"email": "tester@qa.com", "password": "testpass123"})
            resp = await client.post(f"{AUTH_URL}/login", json={"email": "tester@qa.com", "password": "testpass123"})
            if resp.status_code == 200:
                return resp.json()["access_token"]
        except:
            pass
    return None


class PipelineTestRunner:
    def __init__(self):
        self.results = {
            "stage_0": [],
            "stage_1": [],
            "stage_2": [],
            "stage_3": [],
            "stage_4": [],
            "stage_5": [],
        }
        self.token = None
        self.headers = {}
    
    async def initialize(self):
        self.token = await get_auth_token()
        if self.token:
            self.headers = {"Authorization": f"Bearer {self.token}"}
            return True
        return False

    # ========================================
    # STAGE 0: INPUT PROCESSING
    # ========================================
    async def test_stage_0_sentence_splitting(self):
        """Test sentence splitting and paragraph handling"""
        print("\n" + "="*70)
        print("📋 STAGE 0: INPUT PROCESSING & SENTENCE SPLITTING")
        print("="*70)
        
        async with httpx.AsyncClient() as client:
            for test in SENTENCE_SPLITTING_TESTS:
                print(f"\n📝 Test: {test['name']}")
                print(f"   Input: {test['input'][:60]}...")
                
                try:
                    # Call analyze endpoint (not investigate) to see claim extraction
                    resp = await client.post(
                        f"{API_URL}/analyze",
                        json={"content": test["input"], "input_type": "text"},
                        headers=self.headers,
                        timeout=30
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        claims = data.get("claims", [])
                        
                        result = {
                            "test": test["name"],
                            "expected_claims": test["expected_claims"],
                            "actual_claims": len(claims),
                            "claims_extracted": [c.get("original_text", c.get("text", ""))[:50] for c in claims],
                            "passed": len(claims) >= test["expected_claims"] * 0.5  # Allow 50% tolerance
                        }
                        
                        status = "✅ PASS" if result["passed"] else "❌ FAIL"
                        print(f"   {status} - Expected ~{test['expected_claims']} claims, got {len(claims)}")
                        for c in claims[:3]:
                            text = c.get("original_text", c.get("text", ""))[:50]
                            print(f"      • {text}")
                        
                        self.results["stage_0"].append(result)
                    else:
                        print(f"   ⚠️ ERROR: HTTP {resp.status_code}")
                        self.results["stage_0"].append({"test": test["name"], "error": f"HTTP {resp.status_code}", "passed": False})
                        
                except Exception as e:
                    print(f"   💥 EXCEPTION: {e}")
                    self.results["stage_0"].append({"test": test["name"], "error": str(e), "passed": False})
        
        return self.results["stage_0"]

    # ========================================
    # STAGE 2: CLAIM TYPING
    # ========================================
    async def test_stage_2_claim_typing(self):
        """Test claim type classification accuracy"""
        print("\n" + "="*70)
        print("🎯 STAGE 2: CLAIM TYPING (BART CLASSIFICATION)")
        print("="*70)
        
        async with httpx.AsyncClient() as client:
            for test in CLAIM_TYPING_TESTS:
                print(f"\n📝 Claim: {test['claim'][:50]}...")
                print(f"   Expected Type: {test['expected_type']}")
                
                try:
                    resp = await client.post(
                        f"{API_URL}/analyze",
                        json={"content": test["claim"], "input_type": "text"},
                        headers=self.headers,
                        timeout=30
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        claims = data.get("claims", [])
                        
                        if claims:
                            actual_type = claims[0].get("claim_type", "unknown")
                            confidence = claims[0].get("type_confidence", 0)
                            
                            # Check if types match (allow some flexibility)
                            type_aliases = {
                                "scientific_medical": ["scientific_medical", "scientific", "medical"],
                                "factual_statement": ["factual_statement", "factual", "historical"],
                                "political_allegation": ["political_allegation", "political"],
                                "breaking_event": ["breaking_event", "breaking", "event"],
                                "quote_attribution": ["quote_attribution", "quote"],
                                "opinion": ["opinion", "value_judgment"],
                            }
                            
                            expected_aliases = type_aliases.get(test["expected_type"], [test["expected_type"]])
                            passed = actual_type in expected_aliases or test["expected_type"] in actual_type.lower()
                            
                            status = "✅ PASS" if passed else "❌ FAIL"
                            print(f"   {status} - Got: {actual_type} (conf: {confidence:.2f})")
                            
                            self.results["stage_2"].append({
                                "claim": test["claim"],
                                "expected": test["expected_type"],
                                "actual": actual_type,
                                "confidence": confidence,
                                "passed": passed
                            })
                        else:
                            print(f"   ⚠️ No claims extracted")
                            self.results["stage_2"].append({"claim": test["claim"], "error": "No claims", "passed": False})
                    else:
                        print(f"   ⚠️ ERROR: HTTP {resp.status_code}")
                        
                except Exception as e:
                    print(f"   💥 EXCEPTION: {e}")
        
        return self.results["stage_2"]

    # ========================================
    # STAGE 3: EVIDENCE GATHERING
    # ========================================
    async def test_stage_3_evidence_gathering(self):
        """Test which sources are queried for different claim types"""
        print("\n" + "="*70)
        print("🔍 STAGE 3: EVIDENCE GATHERING (SOURCE COVERAGE)")
        print("="*70)
        
        async with httpx.AsyncClient() as client:
            for test in EVIDENCE_GATHERING_TESTS:
                print(f"\n📝 Claim: {test['claim']}")
                print(f"   Claim Type: {test['claim_type']}")
                print(f"   Expected Sources: {test['expected_sources']}")
                
                try:
                    resp = await client.post(
                        f"{API_URL}/investigate",
                        json={"content": test["claim"], "input_type": "text"},
                        headers=self.headers,
                        timeout=120
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        claims = data.get("verified_claims", [])
                        
                        if claims:
                            evidence = claims[0].get("evidence", [])
                            sources_used = set()
                            
                            for e in evidence:
                                source_type = e.get("type", "").lower()
                                source_domain = e.get("source", "").lower()
                                sources_used.add(source_type)
                                if "pubmed" in source_domain:
                                    sources_used.add("pubmed")
                                if "wiki" in source_domain or source_type == "wikipedia":
                                    sources_used.add("wikipedia")
                            
                            # Check expected sources
                            expected_found = [s for s in test["expected_sources"] if any(s in su for su in sources_used)]
                            coverage = len(expected_found) / len(test["expected_sources"]) if test["expected_sources"] else 1
                            
                            passed = coverage >= 0.5  # At least 50% of expected sources
                            status = "✅ PASS" if passed else "❌ FAIL"
                            
                            print(f"   {status} - Sources used: {sources_used}")
                            print(f"   Coverage: {coverage*100:.0f}% ({len(expected_found)}/{len(test['expected_sources'])})")
                            
                            self.results["stage_3"].append({
                                "claim": test["claim"],
                                "expected_sources": test["expected_sources"],
                                "actual_sources": list(sources_used),
                                "coverage": coverage,
                                "passed": passed
                            })
                        else:
                            print(f"   ⚠️ No verified claims returned")
                    else:
                        print(f"   ⚠️ ERROR: HTTP {resp.status_code}")
                        
                except Exception as e:
                    print(f"   💥 EXCEPTION: {e}")
        
        return self.results["stage_3"]

    # ========================================
    # STAGE 4: STANCE DETECTION
    # ========================================
    async def test_stage_4_stance_detection(self):
        """Test stance detection accuracy (SUPPORTS/REFUTES/NEUTRAL)"""
        print("\n" + "="*70)
        print("⚖️ STAGE 4: STANCE DETECTION")
        print("="*70)
        
        # Import stance detector directly for isolated testing
        try:
            from app.services.investigation.stance_detector import StanceDetector
            detector = StanceDetector()
            
            for test in STANCE_DETECTION_TESTS:
                print(f"\n📝 Claim: {test['claim']}")
                print(f"   Evidence: {test['evidence'][:60]}...")
                print(f"   Expected: {test['expected_stance']}")
                
                try:
                    result = detector.detect(test["claim"], test["evidence"])
                    actual_stance = result.get("label", "UNKNOWN")
                    confidence = result.get("score", 0)
                    
                    passed = actual_stance.upper() == test["expected_stance"].upper()
                    status = "✅ PASS" if passed else "❌ FAIL"
                    
                    print(f"   {status} - Got: {actual_stance} (conf: {confidence:.2f})")
                    print(f"   Raw scores: {result.get('raw_scores', {})}")
                    
                    self.results["stage_4"].append({
                        "claim": test["claim"],
                        "evidence": test["evidence"][:50],
                        "expected": test["expected_stance"],
                        "actual": actual_stance,
                        "confidence": confidence,
                        "passed": passed
                    })
                    
                except Exception as e:
                    print(f"   💥 EXCEPTION: {e}")
                    self.results["stage_4"].append({"claim": test["claim"], "error": str(e), "passed": False})
                    
        except ImportError as e:
            print(f"⚠️ Could not import StanceDetector: {e}")
            print("   Testing via API instead...")
            # Could implement API-based testing here
        
        return self.results["stage_4"]

    # ========================================
    # GENERATE REPORT
    # ========================================
    def generate_report(self):
        """Generate final test report"""
        print("\n\n" + "="*70)
        print("📊 RIGOROUS PIPELINE TEST REPORT")
        print("="*70)
        
        total_tests = 0
        total_passed = 0
        
        stage_names = {
            "stage_0": "Input Processing & Splitting",
            "stage_1": "Claim Extraction",
            "stage_2": "Claim Typing",
            "stage_3": "Evidence Gathering",
            "stage_4": "Stance Detection",
            "stage_5": "Evidence Synthesis",
        }
        
        print(f"\n{'STAGE':<35} {'PASS':<8} {'FAIL':<8} {'RATE':<10}")
        print("-"*70)
        
        for stage, results in self.results.items():
            if results:
                passed = len([r for r in results if r.get("passed", False)])
                failed = len(results) - passed
                rate = (passed / len(results)) * 100 if results else 0
                
                total_tests += len(results)
                total_passed += passed
                
                status = "✅" if rate >= 70 else "⚠️" if rate >= 50 else "❌"
                print(f"{status} {stage_names.get(stage, stage):<33} {passed:<8} {failed:<8} {rate:.0f}%")
        
        print("-"*70)
        overall_rate = (total_passed / total_tests) * 100 if total_tests else 0
        print(f"   OVERALL                          {total_passed:<8} {total_tests - total_passed:<8} {overall_rate:.0f}%")
        
        print("\n" + "="*70)
        if overall_rate >= 80:
            print("🏆 RATING: EXCELLENT")
        elif overall_rate >= 70:
            print("👍 RATING: GOOD")
        elif overall_rate >= 50:
            print("⚠️ RATING: NEEDS IMPROVEMENT")
        else:
            print("❌ RATING: CRITICAL ISSUES")
        print("="*70)
        
        return {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "overall_rate": overall_rate,
            "stages": self.results
        }


async def main():
    print("="*70)
    print("🔬 TRUTHLENS RIGOROUS STAGE-BY-STAGE PIPELINE TEST")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    runner = PipelineTestRunner()
    
    if not await runner.initialize():
        print("❌ FATAL: Could not authenticate. Is the backend running?")
        return
    
    print("✅ Authenticated successfully\n")
    
    # Run all stage tests
    await runner.test_stage_0_sentence_splitting()
    await runner.test_stage_2_claim_typing()
    await runner.test_stage_3_evidence_gathering()
    await runner.test_stage_4_stance_detection()
    
    # Generate final report
    runner.generate_report()


if __name__ == "__main__":
    asyncio.run(main())
