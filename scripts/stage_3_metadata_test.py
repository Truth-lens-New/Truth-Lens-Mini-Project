#!/usr/bin/env python3
"""
STAGE 3 DIAGNOSTIC - EVIDENCE METADATA
Target: Verify 'source_type' is present and correct in /v3/investigate response.
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
        else:
            print(f"❌ Login failed: {response.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)

def run_test(name, text_input, headers):
    print(f"\nTEST: {name}")
    print(f"📝 Input: {text_input}")
    
    payload = {"input_type": "text", "content": text_input}
    
    try:
        # Call INVESTIGATE (not analyze) to get evidence
        start = time.time()
        print("🕵️ Investigating... (this may take 10-20s)")
        response = requests.post(f"{API_URL}/api/v3/investigate", json=payload, headers=headers, timeout=60)
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            verified_claims = data.get("verified_claims", [])
            
            if not verified_claims:
                print("❌ FAIL - No verified claims returned")
                return
                
            claim = verified_claims[0]
            evidence_list = claim.get("evidence", [])
            
            print(f"🔎 Verdict: {claim.get('verdict')} ({duration:.2f}s)")
            print(f"📚 Evidence Count: {len(evidence_list)}")
            
            if not evidence_list:
                print("⚠️ No evidence gathered (might be expected for obvious facts if optimization is on)")
                return
            
            # Check Metadata
            print("\n🔍 CHECKING EVIDENCE METADATA:")
            for i, ev in enumerate(evidence_list, 1):
                stype = ev.get("source_type")
                sdomain = ev.get("source_domain")
                url = ev.get("source_url", "")[:50]
                
                print(f"  {i}. Type: '{stype}' | Domain: '{sdomain}' | URL: {url}...")
                
                if stype is None or stype == "":
                    print("     ❌ MISSING SOURCE_TYPE!")
                
                if stype == "unknown":
                     print("     ⚠️ UNKNOWN SOURCE TYPE")

            # Validate presence of expected types
            types = [e.get("source_type") for e in evidence_list]
            if "wikipedia" in types or "google_fact_check" in types or "known_misinfo" in types or "academic_paper" in types:
                print("\n✅ SUCCESS - Found rich metadata")
            else:
                print("\n⚠️ WARNING - Only found generic types: " + str(types))
                
        else:
            print(f"⚠️ API Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

def main():
    headers = login()
    
    # Test 1: Known Misinfo/Wiki (Fastest)
    run_test("Wiki/Misinfo Check", "The earth is flat.", headers)
    
    # Test 2: Medical (PubMed)
    run_test("Medical Check", "Hydroxychloroquine cures COVID-19.", headers)

if __name__ == "__main__":
    main()
