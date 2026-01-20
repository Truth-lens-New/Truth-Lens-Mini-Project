
import asyncio
import time
import json
from typing import List, Dict
import httpx

# Configuration
BASE_URL = "http://localhost:7000"
API_URL = f"{BASE_URL}/api/v3/investigate"
AUTH_URL = f"{BASE_URL}/auth"

TEST_CASES = [
    # SCIENTIFIC (4)
    {"text": "Hydroxychloroquine is a proven cure for COVID-19.", "expected_type": "scientific_medical", "expected_verdict": "verified_false"},
    {"text": "Vaccines cause autism.", "expected_type": "scientific_medical", "expected_verdict": "verified_false"},
    {"text": "Climate change is caused by human activity.", "expected_type": "scientific_medical", "expected_verdict": "verified_true"},
    {"text": "Water boils at 100 degrees Celsius at sea level.", "expected_type": "scientific_medical", "expected_verdict": "verified_true"},
    
    # FACTUAL (4)
    {"text": "The capital of France is Paris.", "expected_type": "factual_statement", "expected_verdict": "verified_true"},
    {"text": "The Great Wall of China is visible from space with the naked eye.", "expected_type": "factual_statement", "expected_verdict": "verified_false"},
    {"text": "Mount Everest is the highest mountain in the world.", "expected_type": "factual_statement", "expected_verdict": "verified_true"},
    {"text": "Earth is the third planet from the Sun.", "expected_type": "factual_statement", "expected_verdict": "verified_true"},
    
    # POLITICAL (4)
    {"text": "The 2020 US election was stolen.", "expected_type": "political_allegation", "expected_verdict": "verified_false"},
    {"text": "Donald Trump was the 45th President of the US.", "expected_type": "factual_statement", "expected_verdict": "verified_true"},
    {"text": "The Indian Constitution was adopted in 1950.", "expected_type": "factual_statement", "expected_verdict": "verified_true"},
    {"text": "The UK left the European Union in 2020.", "expected_type": "factual_statement", "expected_verdict": "verified_true"},
    
    # OPINION (3)
    {"text": "Pizza is the best food in the world.", "expected_type": "opinion", "expected_verdict": "not_checkable"},
    {"text": "The government should lower taxes.", "expected_type": "opinion", "expected_verdict": "not_checkable"},
    {"text": "Blue is the prettiest color.", "expected_type": "opinion", "expected_verdict": "not_checkable"},
    
    # BREAKING / CONSPIRACY (5)
    {"text": "The earth is flat and NASA fakes images.", "expected_type": "factual_statement", "expected_verdict": "verified_false"},
    {"text": "5G networks spread COVID-19.", "expected_type": "scientific_medical", "expected_verdict": "verified_false"},
    {"text": "NASA faked the moon landing in 1969.", "expected_type": "factual_statement", "expected_verdict": "verified_false"},
    {"text": "A new large-scale earthquake occurred in Tokyo today.", "expected_type": "breaking_event", "expected_verdict": "disputed"},
    {"text": "Scientists found a cure for all types of cancer yesterday.", "expected_type": "scientific_medical", "expected_verdict": "verified_false"}
]

async def get_token():
    async with httpx.AsyncClient() as client:
        # Try login first
        try:
            resp = await client.post(f"{AUTH_URL}/login", json={"email": "stress@test.com", "password": "password123"})
            if resp.status_code == 200:
                return resp.json()["access_token"]
        except Exception:
            pass

        # Try register if login failed
        try:
            reg_data = {"email": "stress@test.com", "password": "password123"}
            await client.post(f"{AUTH_URL}/register", json=reg_data)
            resp = await client.post(f"{AUTH_URL}/login", json={"email": "stress@test.com", "password": "password123"})
            if resp.status_code == 200:
                return resp.json()["access_token"]
        except Exception:
            pass
            
    return None

async def run_benchmark():
    print("="*70)
    print("TRUTHLENS ACCURACY BENCHMARK (20 TEST CASES)")
    print("="*70)
    
    token = await get_token()
    if not token:
        print("❌ Failed to get auth token. Ensure backend is running.")
        return

    type_correct = 0
    verdict_correct = 0
    total = len(TEST_CASES)
    
    results = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        for i, test in enumerate(TEST_CASES):
            print(f"\n[{i+1}/{total}] Testing: {test['text'][:50]}...")
            
            try:
                start_time = time.time()
                response = await client.post(API_URL, json={"content": test["text"], "input_type": "text"}, headers=headers)
                duration = time.time() - start_time
                
                if response.status_code != 200:
                    print(f"   ❌ Error: Status {response.status_code}")
                    print(f"      {response.text[:200]}")
                    results.append({"text": test["text"], "error": f"Status {response.status_code}"})
                    continue
                
                data = response.json()
                verified_claims = data.get("verified_claims", [])
                if not verified_claims:
                    print("   ❌ Error: No claims extracted")
                    results.append({"text": test["text"], "error": "No claims extracted"})
                    continue
                
                # Usually one claim for our simple inputs
                claim = verified_claims[0]
                
                actual_type = claim.get("claim_type")
                actual_verdict = claim.get("verdict")
                
                is_type_match = actual_type == test["expected_type"]
                is_verdict_match = actual_verdict == test["expected_verdict"]
                
                if is_type_match: type_correct += 1
                if is_verdict_match: verdict_correct += 1
                
                print(f"   Type:    {actual_type:20} ({'✅' if is_type_match else '❌ Exp: ' + test['expected_type']})")
                print(f"   Verdict: {actual_verdict:20} ({'✅' if is_verdict_match else '❌ Exp: ' + test['expected_verdict']})")
                print(f"   Time:    {duration:.2f}s")
                
                results.append({
                    "text": test["text"],
                    "actual_type": actual_type,
                    "expected_type": test["expected_type"],
                    "actual_verdict": actual_verdict,
                    "expected_verdict": test["expected_verdict"],
                    "type_match": is_type_match,
                    "verdict_match": is_verdict_match,
                    "duration": duration
                })
                
                # Small delay to keep it realistic
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                results.append({"text": test["text"], "exception": str(e)})

    print("\n" + "="*70)
    print("FINAL ACCURACY METRICS")
    print("="*70)
    print(f"Claim Typing Accuracy:  {type_correct}/{total} ({type_correct/total:.1%})")
    print(f"Verdict Accuracy:       {verdict_correct}/{total} ({verdict_correct/total:.1%})")
    print("="*70)
    
    # Stance details if any
    print("\nBreakdown by Type Match:")
    for r in results:
        if not r.get("type_match"):
            print(f"❌ '{r['text'][:30]}...' -> {r['actual_type']} (Exp: {r['expected_type']})")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
