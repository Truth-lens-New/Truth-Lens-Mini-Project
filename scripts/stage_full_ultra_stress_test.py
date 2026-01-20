#!/usr/bin/env python3
"""
FULL PIPELINE ULTRA STRESS TEST (PHASE 2B FINAL)
Target: End-to-End Verification (Input -> Search -> Verdict)
"""
import sys
import requests
import json
import time

# Configuration
API_URL = "http://localhost:7000"
AUTH_URL = f"{API_URL}/auth/login"

def login():
    print("🔑 Authenticating...")
    payload = {"email": "tester@qa.com", "password": "testpass123"}
    try:
        response = requests.post(AUTH_URL, json=payload, timeout=5)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Authenticated")
            return {"Authorization": f"Bearer {token}"}
        sys.exit(1)
    except Exception:
        sys.exit(1)

def run_test(name, input_text, expected_verdict_set, expected_min_evidence=1):
    print(f"\nTEST: {name}")
    print(f"📝 Input: {input_text}")
    print(f"🎯 Expect: One of {expected_verdict_set}")
    
    payload = {"input_type": "text", "content": input_text}
    
    try:
        start_t = time.time()
        # Use INVESTIGATE endpoint (Full Pipeline)
        response = requests.post(f"{API_URL}/api/v3/investigate", json=payload, headers=headers, timeout=60)
        duration = time.time() - start_t
        
        if response.status_code == 200:
            data = response.json()
            verified = data.get("verified_claims", [])
            
            if not verified:
                # If we expected NOT_CHECKABLE, and no claims were found, that's a PASS (Stage 0 filtered it)
                if "not_checkable" in expected_verdict_set:
                    print("✅ PASS (Correctly filtered as non-claim)")
                    return True
                
                print("❌ FAIL - No claims verified")
                return False
                
            # Check primary claim (usually first)
            claim = verified[0]
            verdict = claim.get("verdict")
            evidence = claim.get("evidence", [])
            ev_count = len(evidence)
            
            print(f"🔎 Result: {verdict} (Conf: {claim.get('confidence')})")
            print(f"📚 Evidence: {ev_count} items")
            print(f"⏱️ Time: {duration:.2f}s")
            
            # 1. Check Verdict
            if verdict not in expected_verdict_set:
                print(f"❌ FAIL - Verdict Mismatch (Got {verdict})")
                return False
                
            # 2. Check Evidence Count (if checkable)
            if "not_checkable" not in expected_verdict_set and "insufficient_evidence" not in expected_verdict_set:
                if ev_count < expected_min_evidence:
                    print(f"⚠️ WARNING - Low Evidence ({ev_count} < {expected_min_evidence})")
                    # Strict validation? Let's warn only for now as web search varies
                    
            print("✅ PASS")
            return True
            
        else:
            print(f"⚠️ API Error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False

headers = login()

tests = [
    # === 1. CLASSIC MISINFO ===
    {
        "name": "Flat Earth (Refute)",
        "input": "The earth is flat.",
        "expect": ["verified_false"], # Should be debunked
        "min_ev": 1
    },
    {
        "name": "Vaccine Autism (Refute)",
        "input": "Vaccines cause autism.",
        "expect": ["verified_false"],
        "min_ev": 1
    },
    
    # === 2. SCIENTIFIC TRUTH ===
    {
        "name": "Smoking Cancer (Support)",
        "input": "Smoking tobacco causes lung cancer.",
        "expect": ["verified_true"],
        "min_ev": 1
    },
    
    # === 3. HINGLISH (Translation + Verify) ===
    # "Vaccines se autism hota hai" -> Should be REFUTED
    {
        "name": "Hinglish Misinfo",
        "input": "Vaccines se autism hota hai.",
        "expect": ["verified_false"], 
        "min_ev": 1
    },
    
    # === 4. POLITICS (Hard) ===
    # "Biden 2020 Win" -> Fact
    {
        "name": "Political Fact",
        "input": "Joe Biden won the 2020 US Presidential Election.",
        "expect": ["verified_true"],
        "min_ev": 1
    },
    
    # === 5. OPINION / NON-CHECKABLE ===
    {
        "name": "Pure Opinion",
        "input": "Vanilla ice cream is the best.",
        "expect": ["not_checkable"],
        "min_ev": 0
    },
    
    # === 6. SARCASM / EDGE CASE ===
    # "Yeah sure the earth is flat" -> If interpreted as claim "Earth is flat" -> Refute.
    # If interpreted as sarcasm -> Opinion? 
    # Let's assess what system does.
    {
        "name": "Sarcastic Flat Earth",
        "input": "Yeah sure, the earth is flat.",
        "expect": ["verified_false", "not_checkable"], # Flexible
        "min_ev": 0
    }
]

print(f"🚀 STARTING FULL ULTRA TEST ({len(tests)} Cases)...")
passed = 0
for t in tests:
    if run_test(t["name"], t["input"], t["expect"], t["min_ev"]):
        passed += 1

print("\n" + "="*30)
print(f"📊 REPORT: {passed}/{len(tests)} PASSED")
print("="*30)
if passed == len(tests):
    print("🏆 SYSTEM IS ULTRA ROBUST")
else:
    print("⚠️ SOME FAILURES DETECTED")
