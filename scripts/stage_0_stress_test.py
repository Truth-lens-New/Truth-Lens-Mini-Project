#!/usr/bin/env python3
"""
Stage 0 STRESS TEST - Make Input Processing STEEL STRONG
==========================================================
Tests the most challenging edge cases for input processing:

1. Typos and bad grammar
2. Multiple paragraphs
3. Very long text
4. Mixed languages
5. Social media style (no punctuation, all caps, emojis)
6. Copy-pasted web content with junk
7. Multi-line with weird formatting
8. Run-on sentences
9. Sentence fragments
10. Questions, commands, opinions all mixed
"""

import asyncio
import sys
from typing import List, Dict

sys.path.insert(0, '/home/shivam/Downloads/SEM1/MiniProject/backend')

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# EXTREME EDGE CASE TESTS
# ============================================================

STAGE_0_STRESS_TESTS = [
    # ============ TYPOS & BAD GRAMMAR ============
    {
        "name": "Typos and misspellings",
        "input": "Vacciens casue autizm in childern. The eath is flatt.",
        "min_claims": 2,
        "description": "Should still extract claims despite typos"
    },
    {
        "name": "Bad grammar / broken English",
        "input": "Government they hiding truth. Vaccine is make people sick always. Election was fraud many people say.",
        "min_claims": 3,
        "description": "Non-native English patterns"
    },
    {
        "name": "No punctuation at all",
        "input": "vaccines cause autism the earth is flat nasa faked moon landing bill gates created covid",
        "min_claims": 2,  # At least some should be extracted
        "description": "Social media style no punctuation"
    },
    
    # ============ PARAGRAPHS & LONG TEXT ============
    {
        "name": "Multi-paragraph essay",
        "input": """
        The COVID-19 pandemic has raised many questions about vaccines. Some people claim vaccines are dangerous and cause autism. This has been debunked by scientific studies.
        
        However, misinformation continues to spread on social media. Many believe that 5G towers spread the coronavirus. This is completely false according to scientists.
        
        The 2020 US election also generated controversy. Some claim it was stolen through fraud. Courts have rejected these claims repeatedly.
        """,
        "min_claims": 4,
        "description": "Multi-paragraph with multiple claims"
    },
    {
        "name": "Very long single paragraph",
        "input": "The Earth is flat and NASA has been lying to us for decades, they fake all the images using CGI and Hollywood special effects, also the moon landing was staged in a film studio, and vaccines are actually designed to insert microchips into people for tracking purposes, plus Bill Gates created COVID-19 in a lab in China to reduce world population, and 5G towers emit radiation that weakens the immune system making people susceptible to the virus, while the government is covering all of this up because they want to control us through fear and misinformation.",
        "min_claims": 5,
        "description": "Run-on sentence with many claims"
    },
    
    # ============ SOCIAL MEDIA STYLE ============
    {
        "name": "ALL CAPS angry post",
        "input": "VACCINES ARE KILLING OUR CHILDREN!!! THE GOVERNMENT IS LYING TO US ALL!!! WAKE UP PEOPLE!!!",
        "min_claims": 2,
        "description": "All caps with multiple exclamation marks"
    },
    {
        "name": "Emojis and hashtags",
        "input": "🚨 BREAKING: Vaccines cause autism!!! 💉😱 #VaccinesDanger #WakeUp The government doesn't want you to know this! 🤫 #Truth",
        "min_claims": 1,
        "description": "Tweet-style with emojis and hashtags"
    },
    {
        "name": "WhatsApp forward style",
        "input": """
        *URGENT MESSAGE*
        
        🚨🚨🚨 FORWARD TO ALL 🚨🚨🚨
        
        Scientists have confirmed that drinking warm water with lemon kills coronavirus!!!
        
        This message is from a doctor at AIIMS Delhi. Please share with everyone!!!
        
        Also, 5G towers near your house are spreading the virus. Stay away from them!!!
        
        Forward to 10 people or bad luck will follow you!!!
        """,
        "min_claims": 2,
        "description": "Typical WhatsApp forward"
    },
    
    # ============ WEB COPY-PASTE JUNK ============
    {
        "name": "Copy-pasted article with junk",
        "input": """
        Home > News > Health
        
        BREAKING NEWS | Updated 5 mins ago
        
        Study claims vaccines linked to autism - Experts disagree
        
        Share: Facebook Twitter WhatsApp
        
        By Staff Reporter
        
        A controversial new study claims to have found a link between childhood vaccines and autism. However, leading scientists have dismissed the findings as flawed.
        
        Advertisement
        
        "This study has serious methodological problems," said Dr. Smith.
        
        Related Articles:
        - Is 5G safe?
        - COVID vaccine myths debunked
        
        Comments (234)
        """,
        "min_claims": 2,
        "description": "Web article with navigation, ads, etc."
    },
    
    # ============ WEIRD FORMATTING ============
    {
        "name": "Bullet points and lists",
        "input": """
        Things they don't want you to know:
        • Vaccines contain dangerous chemicals
        • The Earth is actually flat
        • Moon landing was filmed in Hollywood
        - 5G causes cancer
        - Bill Gates wants to microchip everyone
        1. NASA lies about space
        2. Climate change is a hoax
        """,
        "min_claims": 5,
        "description": "List format claims"
    },
    {
        "name": "Mixed newlines and spaces",
        "input": """
        
        
        The government    is   hiding    aliens.
        
        
            NASA    faked     the    moon   landing.
        
        
        Vaccines         are        dangerous.
        
        """,
        "min_claims": 3,
        "description": "Excessive whitespace and newlines"
    },
    
    # ============ MIXED CONTENT ============
    {
        "name": "Questions, statements, opinions mixed",
        "input": """
        Is the Earth really flat? I believe it is. NASA has been lying for decades.
        Do vaccines cause autism? Many parents say yes. The government covers it up.
        Why won't they tell us the truth? It's outrageous! Wake up people!
        """,
        "min_claims": 3,  # "NASA lying", "vaccines cause autism", "government covers"
        "description": "Questions converted to claims + statements"
    },
    {
        "name": "Sentence fragments",
        "input": "Vaccines. Dangerous. Very bad for children. Autism. Government cover-up. Wake up sheeple!",
        "min_claims": 1,  # At least try to extract something
        "description": "Fragment-style posting"
    },
    
    # ============ EDGE CASES ============
    {
        "name": "Single word",
        "input": "Vaccines",
        "min_claims": 0,
        "description": "Too short to extract"
    },
    {
        "name": "Only punctuation",
        "input": "!!! ??? ... ,,, ---",
        "min_claims": 0,
        "description": "No actual content"
    },
    {
        "name": "Empty after cleanup",
        "input": "   \n\n\t\t   \n   ",
        "min_claims": 0,
        "description": "Only whitespace"
    },
    {
        "name": "URLs and links",
        "input": "Check this out: https://example.com/vaccines-cause-autism The link proves vaccines are dangerous! Also see bit.ly/5g-danger",
        "min_claims": 1,
        "description": "Text with URLs"
    },
    {
        "name": "Numbers and statistics",
        "input": "90% of doctors agree vaccines are safe but 10% say they cause autism. In 2020, 500,000 people reported side effects. The death rate increased by 50%.",
        "min_claims": 2,
        "description": "Statistical claims"
    },
]


async def run_stage_0_stress_test():
    """Run comprehensive Stage 0 stress tests."""
    import httpx
    
    print("=" * 70)
    print("🔬 STAGE 0 STRESS TEST - STEEL STRONG INPUT PROCESSING")
    print("=" * 70)
    
    # Get auth token
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post("http://localhost:7000/auth/login", 
                                    json={"email": "tester@qa.com", "password": "testpass123"})
            if resp.status_code != 200:
                await client.post("http://localhost:7000/auth/register", 
                                 json={"email": "tester@qa.com", "password": "testpass123"})
                resp = await client.post("http://localhost:7000/auth/login", 
                                        json={"email": "tester@qa.com", "password": "testpass123"})
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
        except Exception as e:
            print(f"❌ Auth failed: {e}")
            return
    
    print("✅ Authenticated\n")
    
    results = []
    passed = 0
    failed = 0
    
    async with httpx.AsyncClient() as client:
        for i, test in enumerate(STAGE_0_STRESS_TESTS, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(STAGE_0_STRESS_TESTS)}] {test['name']}")
            print(f"{'='*60}")
            print(f"📝 Input preview: {test['input'][:80].replace(chr(10), ' ')}...")
            print(f"📋 Description: {test['description']}")
            print(f"🎯 Min claims expected: {test['min_claims']}")
            
            try:
                resp = await client.post(
                    "http://localhost:7000/api/v3/analyze",
                    json={"content": test["input"], "input_type": "text"},
                    headers=headers,
                    timeout=30
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    claims = data.get("claims", [])
                    claim_count = len(claims)
                    
                    test_passed = claim_count >= test["min_claims"]
                    
                    if test_passed:
                        passed += 1
                        print(f"✅ PASS - Extracted {claim_count} claims (min: {test['min_claims']})")
                    else:
                        failed += 1
                        print(f"❌ FAIL - Extracted {claim_count} claims (min: {test['min_claims']})")
                    
                    # Show extracted claims
                    for j, c in enumerate(claims[:5], 1):
                        text = c.get("original_text", c.get("text", ""))[:60]
                        claim_type = c.get("claim_type", "?")
                        print(f"   {j}. [{claim_type}] {text}")
                    
                    if len(claims) > 5:
                        print(f"   ... and {len(claims) - 5} more")
                    
                    results.append({
                        "name": test["name"],
                        "passed": test_passed,
                        "expected": test["min_claims"],
                        "actual": claim_count
                    })
                    
                else:
                    failed += 1
                    print(f"⚠️ HTTP Error: {resp.status_code}")
                    results.append({"name": test["name"], "passed": False, "error": f"HTTP {resp.status_code}"})
                    
            except Exception as e:
                failed += 1
                print(f"💥 Exception: {e}")
                results.append({"name": test["name"], "passed": False, "error": str(e)})
            
            await asyncio.sleep(0.2)
    
    # Final Report
    print("\n\n" + "=" * 70)
    print("📊 STAGE 0 STRESS TEST REPORT")
    print("=" * 70)
    
    total = len(STAGE_0_STRESS_TESTS)
    rate = (passed / total) * 100 if total else 0
    
    print(f"\n✅ Passed: {passed}/{total} ({rate:.0f}%)")
    print(f"❌ Failed: {failed}/{total}")
    
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for r in results:
            if not r.get("passed"):
                print(f"   • {r['name']}: Expected >= {r.get('expected', '?')}, Got {r.get('actual', r.get('error', '?'))}")
    
    print("\n" + "=" * 70)
    if rate >= 90:
        print("🏆 STEEL STRONG - Stage 0 is production ready!")
    elif rate >= 75:
        print("👍 GOOD - Minor improvements needed")
    elif rate >= 50:
        print("⚠️ NEEDS WORK - Several edge cases failing")
    else:
        print("❌ CRITICAL - Major issues with input processing")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_stage_0_stress_test())
