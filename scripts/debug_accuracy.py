
import asyncio
import httpx
import json
import sys

API_URL = "http://localhost:7000/api/v3"
AUTH_URL = "http://localhost:7000/auth"

async def get_token():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{AUTH_URL}/login", json={"email": "stress@test.com", "password": "password123"})
            if resp.status_code == 200:
                print("✅ Authenticated")
                return resp.json()["access_token"]
        except Exception as e:
            print(f"Auth failed: {e}")
    return None

async def debug_claim(claim_text: str):
    token = await get_token()
    if not token: return

    print(f"\n🔬 Debugging Claim: {claim_text}")
    
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{API_URL}/investigate",
            json={"content": claim_text, "input_type": "text"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        
        if res.status_code == 200:
            data = res.json()
            verified_list = data.get("verified_claims", [])
            if not verified_list:
                print("No verified claims returned.")
                return
                
            verified = verified_list[0]
            print(f"Verdict: {verified['verdict']} (Conf: {verified['confidence']})")
            print(f"Summary: {verified['evidence_summary']}")
            print("-" * 40)
            
            # Inspect Evidence
            for idx, item in enumerate(verified.get("evidence", [])):
                print(f"[{idx+1}] Source: {item['source_domain']} ({item['source_type']})")
                print(f"    Stance: {item['stance']} (Conf: {item.get('stance_confidence')})")
                print(f"    Trust: {item.get('trust_score')}")
                print(f"    Text: {item['text_preview']}...")
                print("-" * 20)
        else:
            print(f"Error: {res.text}")

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "Hydroxychloroquine is a proven cure for COVID-19 according to major studies."
    asyncio.run(debug_claim(text))
