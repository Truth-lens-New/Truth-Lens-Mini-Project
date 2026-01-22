import asyncio
import httpx
import time
import json

API_URL = "http://localhost:7000"
INVESTIGATE_URL = f"{API_URL}/api/v3/investigate"
AUTH_URL = f"{API_URL}/auth"

CLAIMS = [
    {"content": "The earth is flat.", "expected": "verified_false", "type": "FACTUAL"},
    {"content": "Python was created by Guido van Rossum.", "expected": "verified_true", "type": "FACTUAL"}, 
    {"content": "Hydroxychloroquine is a proven cure for COVID-19.", "expected": "verified_false", "type": "SCIENTIFIC"}, 
    {"content": "The capital of France is Paris.", "expected": "verified_true", "type": "FACTUAL"}
]

async def get_token():
    async with httpx.AsyncClient() as client:
        # Try login first
        print("Authenticating...")
        try:
            resp = await client.post(f"{AUTH_URL}/login", json={"email": "stress@test.com", "password": "password123"})
            if resp.status_code == 200:
                print("Login successful.")
                return resp.json()["access_token"]
        except Exception as e:
            print(f"Login error: {e}")

        # Try register if login failed
        print("Login failed. Registering new user...")
        try:
            reg_data = {"email": "stress@test.com", "password": "password123"}
            resp = await client.post(f"{AUTH_URL}/register", json=reg_data)
            if resp.status_code == 201:
                print("Registration successful. Logging in...")
                # Login after register
                resp = await client.post(f"{AUTH_URL}/login", json={"email": "stress@test.com", "password": "password123"})
                if resp.status_code == 200:
                    return resp.json()["access_token"]
            else:
                print(f"Registration failed: {resp.text}")
        except Exception as e:
            print(f"Register error: {e}")
            
    return None

async def check_claim(client, claim, token):
    print(f"Starting: {claim['content']}")
    start = time.time()
    try:
        response = await client.post(
            INVESTIGATE_URL, 
            json={"content": claim["content"], "input_type": "text"}, 
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            verified_claims = data.get("verified_claims", [])
            if verified_claims:
                result = verified_claims[0]
                verdict = result["verdict"]
                print(f"Finished: {claim['content']} | {duration:.2f}s | Verdict: {verdict}")
                return {"claim": claim["content"], "verdict": verdict, "duration": duration, "success": True, "expected": claim["expected"]}
        
        print(f"Failed: {claim['content']} | {duration:.2f}s | Status: {response.status_code}")
        # print(response.text[:200])
        return {"claim": claim["content"], "verdict": f"Error {response.status_code}", "duration": duration, "success": False, "expected": claim["expected"]}
    except Exception as e:
        print(f"Error: {claim['content']} - {e}")
        return {"claim": claim["content"], "verdict": "Exception", "duration": 0, "success": False, "expected": claim["expected"]}

async def main():
    token = await get_token()
    if not token:
        print("Failed to get auth token. Exiting.")
        return

    print(f"Token acquired. Starting stress test with {len(CLAIMS)} concurrent claims...")
    start_global = time.time()
    
    async with httpx.AsyncClient() as client:
        # Use asyncio.gather to run all investigations concurrently
        tasks = [check_claim(client, c, token) for c in CLAIMS]
        results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_global
    
    print("\n" + "="*60)
    print(f"PHASE 2B STRESS TEST REPORT (Total Group Time: {total_time:.2f}s)")
    print("="*60)
    print(f"{'Claim':<50} | {'Verdict':<15} | {'Exp':<15} | {'Time':<6}")
    print("-" * 92)
    
    passed = 0
    for r in results:
        match = r['verdict'] == r['expected']
        status_icon = "✅" if match else "❌"
        if match: passed += 1
        print(f"{r['claim'][:47]:<47}... | {r['verdict']:<15} | {r['expected']:<15} | {r['duration']:.2f}s {status_icon}")
        
    print("-" * 92)
    print(f"Success Rate: {passed}/{len(CLAIMS)} ({passed/len(CLAIMS)*100:.0f}%)")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
