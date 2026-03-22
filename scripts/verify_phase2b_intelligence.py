
import asyncio
import httpx
import time
import json
import logging

# Configuration
API_URL = "http://localhost:7000/api/v3"
AUTH_URL = "http://localhost:7000/auth"

# Test Claims
CLAIMS = [
    {
        "content": "Hydroxychloroquine is a proven cure for COVID-19 according to major studies.",
        "expected_type": "scientific_medical",
        "expected_verdict": "VERIFIED_FALSE",
        "desc": "Scientific Claim (Should trigger PubMed)"
    },
    {
        "content": "The earth is flat and NASA fakes images.",
        "expected_type": "factual_statement", # or conspiracy
        "expected_verdict": "VERIFIED_FALSE",
        "desc": "General Conspiracy (Strong Refutation)"
    },
    {
        "content": "Joe Biden was elected President of the United States in 2020.",
        "expected_type": "political_allegation", # or factual
        "expected_verdict": "VERIFIED_TRUE",
        "desc": "Political Fact (Strong Support)"
    }
]

async def get_token():
    async with httpx.AsyncClient() as client:
        # Try login first
        print("Authenticating...")
        try:
            resp = await client.post(f"{AUTH_URL}/login", json={"email": "stress@test.com", "password": "password123"})
            if resp.status_code == 200:
                return resp.json()["access_token"]
        except Exception:
            pass

        # Try register if login failed
        try:
            reg_data = {"email": "stress@test.com", "password": "password123"}
            resp = await client.post(f"{AUTH_URL}/register", json=reg_data)
            if resp.status_code == 201:
                resp = await client.post(f"{AUTH_URL}/login", json={"email": "stress@test.com", "password": "password123"})
                if resp.status_code == 200:
                    return resp.json()["access_token"]
        except Exception as e:
            print(f"Auth error: {e}")
            
    return None

async def check_claim(client, claim, token):
    print(f"\n🔍 Testing: {claim['desc']}")
    print(f"   Claim: {claim['content']}")
    
    start = time.time()
    try:
        response = await client.post(
            f"{API_URL}/investigate", 
            json={"content": claim["content"], "input_type": "text"}, 
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            # print(json.dumps(data, indent=2))
            
            verified_claims = data.get("verified_claims", [])
            if verified_claims:
                result = verified_claims[0]
                verdict = result["verdict"]
                confidence = result["confidence"]
                evidence_count = len(result.get("evidence", []))
                
                print(f"   ✅ Finished in {duration:.2f}s")
                print(f"   Verdict: {verdict} (Confidence: {confidence})")
                print(f"   Evidence Items: {evidence_count}")
                
                # Check for sources
                sources = set()
                for e in result.get("evidence", []):
                    domain = e.get("source_domain")
                    sources.add(domain)
                    # print(f"      - {domain}: {e['stance']} ({e['stance_confidence']:.2f})")
                
                print(f"   Sources: {', '.join(sources)}")
                
                return {
                    "claim": claim["content"],
                    "verdict": verdict,
                    "expected": claim["expected_verdict"],
                    "duration": duration,
                    "sources": sources
                }
        
        print(f"   ❌ Failed: Status {response.status_code}")
        print(response.text[:200])
        return None
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

async def main():
    print("="*60)
    print("PHASE 2B INTELLIGENCE VERIFICATION")
    print("="*60)
    
    token = await get_token()
    if not token:
        print("Failed to get auth token.")
        return

    results = []
    async with httpx.AsyncClient() as client:
        for claim in CLAIMS:
            res = await check_claim(client, claim, token)
            if res:
                results.append(res)
            # Small delay to prevent rate limit during test if needed
            await asyncio.sleep(1)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = 0
    for r in results:
        is_match = r['verdict'] == r['expected']
        icon = "✅" if is_match else "❌"
        if is_match: passed += 1
        print(f"{icon} {r['claim'][:40]}... -> {r['verdict']} (Exp: {r['expected']})")
        if "pubmed.ncbi.nlm.nih.gov" in r['sources']:
            print("   🔬 PubMed Source Found!")
            
    print("-" * 60)
    print(f"Success Rate: {passed}/{len(CLAIMS)}")

if __name__ == "__main__":
    asyncio.run(main())
