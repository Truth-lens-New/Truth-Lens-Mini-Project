#!/usr/bin/env python3
"""
TruthLens Comprehensive Test Suite
===================================
Intensive QA testing across all system dimensions.

Categories:
1. Scientific/Medical Claims
2. Factual/Historical Claims  
3. Political Claims
4. Opinion/Subjective Statements
5. Breaking News / Conspiracies
6. Known Misinformation (Database Hits)
7. Edge Cases (Short, Long, Multi-claim)
8. Regional/International Claims
9. Quote Attributions
10. Numerical/Statistical Claims
"""

import asyncio
import time
import json
from datetime import datetime
from typing import List, Dict, Any
import httpx

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v3/investigate"
ANALYZE_URL = f"{BASE_URL}/api/v3/analyze"
AUTH_URL = f"{BASE_URL}/auth"

# ============================================================
# TEST CASES - 50+ Comprehensive Tests
# ============================================================

TEST_CASES = {
    "Scientific/Medical": [
        {"text": "COVID-19 vaccines cause autism in children.", "expected_verdict": "verified_false", "expected_type": "scientific_medical", "priority": "HIGH"},
        {"text": "The Earth's climate is changing due to human activities.", "expected_verdict": "verified_true", "expected_type": "scientific_medical", "priority": "HIGH"},
        {"text": "Hydroxychloroquine is a proven cure for COVID-19.", "expected_verdict": "verified_false", "expected_type": "scientific_medical", "priority": "HIGH"},
        {"text": "Smoking causes lung cancer.", "expected_verdict": "verified_true", "expected_type": "scientific_medical", "priority": "MEDIUM"},
        {"text": "5G networks spread the coronavirus.", "expected_verdict": "verified_false", "expected_type": "scientific_medical", "priority": "HIGH"},
        {"text": "Drinking water daily is essential for human health.", "expected_verdict": "verified_true", "expected_type": "scientific_medical", "priority": "LOW"},
    ],
    
    "Factual/Historical": [
        {"text": "The capital of France is Paris.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "HIGH"},
        {"text": "India gained independence in 1947.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "HIGH"},
        {"text": "The Great Wall of China is visible from space with naked eye.", "expected_verdict": "verified_false", "expected_type": "factual_statement", "priority": "MEDIUM"},
        {"text": "Mount Everest is the tallest mountain on Earth.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "MEDIUM"},
        {"text": "World War II ended in 1945.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "MEDIUM"},
        {"text": "The Amazon is the longest river in the world.", "expected_verdict": "verified_false", "expected_type": "factual_statement", "priority": "LOW"},  # Nile is longer
    ],
    
    "Political": [
        {"text": "The 2020 US presidential election was stolen through widespread fraud.", "expected_verdict": "verified_false", "expected_type": "political_allegation", "priority": "HIGH"},
        {"text": "Joe Biden was elected President of the United States in 2020.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "HIGH"},
        {"text": "Donald Trump was the 45th President of the United States.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "HIGH"},
        {"text": "Narendra Modi became Prime Minister of India in 2014.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "MEDIUM"},
        {"text": "The United Kingdom left the European Union in 2020.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "MEDIUM"},
    ],
    
    "Opinions (Should be NOT_CHECKABLE)": [
        {"text": "Pizza is the best food in the world.", "expected_verdict": "not_checkable", "expected_type": "opinion", "priority": "HIGH"},
        {"text": "The government should lower taxes for everyone.", "expected_verdict": "not_checkable", "expected_type": "opinion", "priority": "HIGH"},
        {"text": "Blue is the prettiest color.", "expected_verdict": "not_checkable", "expected_type": "opinion", "priority": "MEDIUM"},
        {"text": "Cricket is more exciting than football.", "expected_verdict": "not_checkable", "expected_type": "opinion", "priority": "LOW"},
        {"text": "I think democracy is the best form of government.", "expected_verdict": "not_checkable", "expected_type": "opinion", "priority": "MEDIUM"},
    ],
    
    "Breaking News / Conspiracies": [
        {"text": "The Earth is flat and NASA fakes all space images.", "expected_verdict": "verified_false", "expected_type": "factual_statement", "priority": "HIGH"},
        {"text": "NASA faked the moon landing in 1969.", "expected_verdict": "verified_false", "expected_type": "factual_statement", "priority": "HIGH"},
        {"text": "The government is hiding evidence of alien contact.", "expected_verdict": "unverified", "expected_type": "political_allegation", "priority": "MEDIUM"},
        {"text": "Chemtrails are being used for mind control.", "expected_verdict": "verified_false", "expected_type": "scientific_medical", "priority": "MEDIUM"},
    ],
    
    "Known Misinformation (DB Hits)": [
        {"text": "Vaccines cause autism.", "expected_verdict": "verified_false", "expected_type": "scientific_medical", "priority": "HIGH"},  # Should hit local DB
        {"text": "5G causes COVID-19.", "expected_verdict": "verified_false", "expected_type": "scientific_medical", "priority": "HIGH"},  # Should hit local DB
        {"text": "Bill Gates created COVID-19.", "expected_verdict": "verified_false", "expected_type": "scientific_medical", "priority": "HIGH"},  # Should hit local DB
    ],
    
    "Edge Cases": [
        {"text": "Hi.", "expected_verdict": "not_checkable", "expected_type": "opinion", "priority": "LOW", "note": "Very short text"},
        {"text": "What is the capital of France?", "expected_verdict": "not_checkable", "expected_type": "question", "priority": "MEDIUM", "note": "Question, not assertion"},
        {"text": "Please share this important information.", "expected_verdict": "not_checkable", "expected_type": "command", "priority": "LOW", "note": "Command/Imperative"},
        {"text": "COVID vaccines cause autism and also the Earth is flat and the moon landing was faked.", "expected_verdict": "verified_false", "expected_type": "scientific_medical", "priority": "HIGH", "note": "Multiple claims in one sentence"},
        {"text": "The quick brown fox jumps over the lazy dog repeatedly for testing purposes in this very long sentence that contains no factual claims whatsoever but is designed to test how the system handles lengthy inputs without meaningful content.", "expected_verdict": "not_checkable", "expected_type": "opinion", "priority": "LOW", "note": "Long text, no claims"},
    ],
    
    "Regional/International": [
        {"text": "The Taj Mahal is located in Agra, India.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "MEDIUM"},
        {"text": "The Indian Constitution was adopted on 26th January 1950.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "MEDIUM"},  # It was adopted Nov 26 1949, enacted Jan 26 1950
        {"text": "Tokyo is the capital of Japan.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "MEDIUM"},
        {"text": "Paris is the capital of Germany.", "expected_verdict": "verified_false", "expected_type": "factual_statement", "priority": "HIGH"},
    ],
    
    "Quote Attributions": [
        {"text": "Mahatma Gandhi said 'Be the change you wish to see in the world.'", "expected_verdict": "disputed", "expected_type": "quote_attribution", "priority": "MEDIUM"},  # Disputed attribution
        {"text": "Albert Einstein invented the light bulb.", "expected_verdict": "verified_false", "expected_type": "factual_statement", "priority": "MEDIUM"},  # Edison, not Einstein
    ],
    
    "Numerical/Statistical": [
        {"text": "Pi equals exactly 3.14.", "expected_verdict": "verified_false", "expected_type": "factual_statement", "priority": "LOW"},  # Approximately, not exactly
        {"text": "India has a population of over 1 billion people.", "expected_verdict": "verified_true", "expected_type": "factual_statement", "priority": "MEDIUM"},
        {"text": "The speed of light is approximately 300,000 km per second.", "expected_verdict": "verified_true", "expected_type": "scientific_medical", "priority": "LOW"},
    ],
}

# ============================================================
# TESTING INFRASTRUCTURE
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

async def test_claim(client: httpx.AsyncClient, headers: dict, test: dict, category: str) -> dict:
    """Test a single claim and return results."""
    start = time.time()
    result = {
        "category": category,
        "text": test["text"][:60] + "..." if len(test["text"]) > 60 else test["text"],
        "expected_verdict": test["expected_verdict"],
        "expected_type": test["expected_type"],
        "priority": test.get("priority", "MEDIUM"),
        "note": test.get("note", ""),
    }
    
    try:
        resp = await client.post(API_URL, json={"content": test["text"], "input_type": "text"}, headers=headers, timeout=90)
        result["duration_ms"] = int((time.time() - start) * 1000)
        
        if resp.status_code != 200:
            result["status"] = "ERROR"
            result["actual_verdict"] = "N/A"
            result["actual_type"] = "N/A"
            result["error"] = f"HTTP {resp.status_code}"
            return result
        
        data = resp.json()
        claims = data.get("verified_claims", [])
        
        if not claims:
            result["status"] = "ERROR"
            result["actual_verdict"] = "N/A"
            result["actual_type"] = "N/A"
            result["error"] = "No claims returned"
            return result
        
        claim = claims[0]
        result["actual_verdict"] = claim.get("verdict", "N/A")
        result["actual_type"] = claim.get("claim_type", "N/A")
        result["confidence"] = claim.get("confidence", 0)
        result["evidence_count"] = len(claim.get("evidence", []))
        
        # Evaluate pass/fail
        verdict_match = result["actual_verdict"] == result["expected_verdict"]
        # Allow some flexibility: disputed can match unverified, verified_false can match disputed for conspiracies
        if not verdict_match:
            if result["expected_verdict"] in ["disputed", "unverified"] and result["actual_verdict"] in ["disputed", "unverified"]:
                verdict_match = True
        
        type_match = result["actual_type"] == result["expected_type"]
        # Allow conspiracy/factual flexibility
        if not type_match:
            if result["expected_type"] in ["factual_statement", "scientific_medical"] and result["actual_type"] in ["factual_statement", "scientific_medical", "breaking_event"]:
                type_match = True  # Close enough for routing
        
        if verdict_match and type_match:
            result["status"] = "PASS"
        elif verdict_match:
            result["status"] = "PARTIAL (Type Mismatch)"
        elif type_match:
            result["status"] = "PARTIAL (Verdict Mismatch)"
        else:
            result["status"] = "FAIL"
        
    except Exception as e:
        result["status"] = "EXCEPTION"
        result["actual_verdict"] = "N/A"
        result["actual_type"] = "N/A"
        result["error"] = str(e)
        result["duration_ms"] = int((time.time() - start) * 1000)
    
    return result

async def run_comprehensive_test():
    """Run all tests and generate report."""
    print("=" * 80)
    print("🔬 TRUTHLENS COMPREHENSIVE QA TEST SUITE")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    token = await get_auth_token()
    if not token:
        print("❌ FATAL: Could not authenticate. Is the backend running?")
        return
    
    print("✅ Authenticated successfully\n")
    
    headers = {"Authorization": f"Bearer {token}"}
    all_results = []
    category_stats = {}
    
    total_tests = sum(len(tests) for tests in TEST_CASES.values())
    current_test = 0
    
    async with httpx.AsyncClient() as client:
        for category, tests in TEST_CASES.items():
            print(f"\n{'='*60}")
            print(f"📂 CATEGORY: {category}")
            print(f"{'='*60}")
            
            category_results = []
            
            for test in tests:
                current_test += 1
                print(f"\n[{current_test}/{total_tests}] Testing: {test['text'][:50]}...")
                
                result = await test_claim(client, headers, test, category)
                category_results.append(result)
                all_results.append(result)
                
                # Print result
                status_icon = {
                    "PASS": "✅",
                    "PARTIAL (Type Mismatch)": "🟡",
                    "PARTIAL (Verdict Mismatch)": "🟠",
                    "FAIL": "❌",
                    "ERROR": "⚠️",
                    "EXCEPTION": "💥"
                }.get(result["status"], "❓")
                
                print(f"   {status_icon} {result['status']}")
                print(f"   Verdict: {result['actual_verdict']} (Expected: {result['expected_verdict']})")
                print(f"   Type: {result['actual_type']} (Expected: {result['expected_type']})")
                print(f"   Time: {result.get('duration_ms', 0)}ms | Evidence: {result.get('evidence_count', 0)}")
                
                if result.get("note"):
                    print(f"   Note: {result['note']}")
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.3)
            
            # Category summary
            passed = len([r for r in category_results if r["status"] == "PASS"])
            partial = len([r for r in category_results if "PARTIAL" in r["status"]])
            failed = len([r for r in category_results if r["status"] in ["FAIL", "ERROR", "EXCEPTION"]])
            
            category_stats[category] = {
                "total": len(tests),
                "passed": passed,
                "partial": partial,
                "failed": failed,
                "pass_rate": (passed / len(tests)) * 100 if tests else 0
            }
    
    # ============================================================
    # FINAL REPORT
    # ============================================================
    
    print("\n\n" + "=" * 80)
    print("📊 FINAL QA REPORT")
    print("=" * 80)
    
    total_passed = len([r for r in all_results if r["status"] == "PASS"])
    total_partial = len([r for r in all_results if "PARTIAL" in r["status"]])
    total_failed = len([r for r in all_results if r["status"] in ["FAIL", "ERROR", "EXCEPTION"]])
    
    print(f"\n{'CATEGORY':<40} {'PASS':<8} {'PARTIAL':<10} {'FAIL':<8} {'RATE':<8}")
    print("-" * 80)
    
    for category, stats in category_stats.items():
        print(f"{category:<40} {stats['passed']:<8} {stats['partial']:<10} {stats['failed']:<8} {stats['pass_rate']:.0f}%")
    
    print("-" * 80)
    overall_rate = (total_passed / total_tests) * 100 if total_tests else 0
    partial_rate = ((total_passed + total_partial) / total_tests) * 100 if total_tests else 0
    
    print(f"{'OVERALL':<40} {total_passed:<8} {total_partial:<10} {total_failed:<8} {overall_rate:.0f}%")
    
    print("\n" + "=" * 80)
    print("📈 VERDICT SUMMARY")
    print("=" * 80)
    print(f"   ✅ Strict Pass Rate:   {overall_rate:.1f}% ({total_passed}/{total_tests})")
    print(f"   🟡 Lenient Pass Rate:  {partial_rate:.1f}% ({total_passed + total_partial}/{total_tests})")
    print(f"   ❌ Failure Rate:       {(total_failed/total_tests)*100:.1f}% ({total_failed}/{total_tests})")
    
    # Performance Stats
    durations = [r.get("duration_ms", 0) for r in all_results if r.get("duration_ms")]
    if durations:
        print(f"\n   ⏱️  Avg Response Time:  {sum(durations)//len(durations)}ms")
        print(f"   ⏱️  Max Response Time:  {max(durations)}ms")
        print(f"   ⏱️  Min Response Time:  {min(durations)}ms")
    
    # Rating
    print("\n" + "=" * 80)
    if overall_rate >= 85:
        print("🏆 RATING: EXCELLENT - Production Ready!")
    elif overall_rate >= 70:
        print("👍 RATING: GOOD - Some edge cases need work")
    elif overall_rate >= 50:
        print("⚠️ RATING: FAIR - Significant improvements needed")
    else:
        print("❌ RATING: POOR - Major issues to address")
    print("=" * 80)
    
    # List failures
    failures = [r for r in all_results if r["status"] in ["FAIL", "ERROR", "EXCEPTION"]]
    if failures:
        print(f"\n\n{'='*80}")
        print("❌ DETAILED FAILURE ANALYSIS")
        print("="*80)
        for f in failures:
            print(f"\n• [{f['category']}] {f['text']}")
            print(f"  Expected: {f['expected_verdict']} ({f['expected_type']})")
            print(f"  Actual:   {f['actual_verdict']} ({f['actual_type']})")
            if f.get("error"):
                print(f"  Error:    {f['error']}")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
