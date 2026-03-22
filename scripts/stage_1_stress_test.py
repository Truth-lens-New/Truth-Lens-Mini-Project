#!/usr/bin/env python3
"""
STAGE 1 STRESS TEST - CLASSIFICATION ACCURACY
Target: Verify ClaimClassifier correctly tags Medical, Political, and Opinion claims.
"""
import sys
import requests
import json

# Configuration
API_URL = "http://localhost:7000"
AUTH_URL = f"{API_URL}/auth/login"

def login():
    print("🔑 Authenticating...")
    payload = {"email": "tester@qa.com", "password": "testpass123"}
    try:
        response = requests.post(AUTH_URL, json=payload)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Authenticated")
            return {"Authorization": f"Bearer {token}"}
        else:
            print(f"❌ Login failed: {response.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)

def run_test(name, text_input, expected_type, headers):
    print(f"\nTEST: {name}")
    print(f"📝 Input: {text_input}")
    print(f"🎯 Expected: {expected_type}")
    
    payload = {"input_type": "text", "content": text_input}
    
    try:
        response = requests.post(f"{API_URL}/api/v3/analyze", json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            claims = data.get("claims", [])
            
            if not claims:
                print("❌ FAIL - No claims extracted")
                return False
                
            # Check the first claim's type (assuming simple input -> 1 claim)
            first_claim = claims[0]
            actual_type = first_claim.get("claim_type")
            text = first_claim.get("original_text")
            
            print(f"🔎 Extracted: '{text}'")
            print(f"🤖 Classified as: {actual_type}")
            
            if actual_type == expected_type:
                print("✅ PASS")
                return True
            else:
                # Allow FACTUAL_STATEMENT for CONSPIRACY as per mapping
                if expected_type == "factual_statement" and actual_type == "factual_statement":
                    print("✅ PASS")
                    return True
                
                print(f"❌ FAIL - Type Mismatch")
                return False
        else:
            print(f"⚠️ API Error {response.status_code}")
            return False
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False

def main():
    headers = login()
    
    tests = [
        {
            "name": "Medical Claim",
            "input": "Vaccines cause autism.",
            "expected": "scientific_medical"
        },
        {
            "name": "Political Allegation",
            "input": "The election was stolen by massive fraud.",
            "expected": "political_allegation"
        },
        {
            "name": "Opinion / Subjective",
            "input": "I hate apples, they taste terrible.",
            "expected": "opinion"
        },
        {
            "name": "Factual Statement",
            "input": "The Eiffel Tower is in Paris.",
            "expected": "factual_statement"
        },
        {
            "name": "Conspiracy Theory (Mapped to Factual)",
            "input": "The earth is flat and NASA lies.",
            "expected": "factual_statement" 
        },
        {
            "name": "Prediction (Should be Opinion/Non-checkable)",
            "input": "Bitcoin will reach $100k next year.",
            "expected": "prediction" # Check mapping
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for t in tests:
        # Note: 'prediction' logic in code returns NON_CHECKABLE but typed as 'prediction'?
        # Let's see what the backend returns.
        if run_test(t["name"], t["input"], t["expected"], headers):
            passed += 1
            
    print(f"\n📊 Result: {passed}/{total} Passed")
    
    if passed == total:
        print("🏆 STAGE 1 ACCURATE")
        sys.exit(0)
    else:
        print("❌ STAGE 1 NEEDS TUNING")
        sys.exit(1)

if __name__ == "__main__":
    main()
