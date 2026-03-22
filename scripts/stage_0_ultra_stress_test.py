#!/usr/bin/env python3
"""
STAGE 0+ ULTRA STRESS TEST
Target: Robustness against MASSIVE, messy WhatsApp forwards and Hinglish.
"""
import sys
import os
import requests
import time
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:7000"
AUTH_URL = f"{API_URL}/auth/login"

def print_header(title):
    print("\n" + "="*70)
    print(title)
    print("="*70)

def login():
    print("🔑 Authenticating...")
    
    # Try default credentials
    payload = {"email": "tester@qa.com", "password": "testpass123"}
    
    try:
        response = requests.post(AUTH_URL, json=payload) # JSON data
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Authenticated")
            return {"Authorization": f"Bearer {token}"}
        else:
            print(f"❌ Login failed: {response.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print(f"Make sure backend is running on {API_URL}")
        sys.exit(1)

def run_test(name, text_input, min_claims, description, headers):
    print_header(f"TEST: {name}")
    print(f"📝 Input Size: {len(text_input)} chars")
    print(f"📋 Description: {description}")
    print(f"🎯 Target: Min {min_claims} claims")
    print("-" * 50)
    
    start_time = time.time()
    
    payload = {
        "input_type": "text",
        "content": text_input
    }
    
    try:
        response = requests.post(f"{API_URL}/api/v3/analyze", json=payload, headers=headers)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            claims = data.get("claims", [])
            claims_text = [c["original_text"] for c in claims]
            
            print(f"⏱️ extracted in {duration:.2f}s")
            
            if len(claims) >= min_claims:
                print(f"✅ PASS - Extracted {len(claims)} claims")
                for i, claim in enumerate(claims_text, 1):
                    print(f"   {i}. {claim[:80]}..." if len(claim) > 80 else f"   {i}. {claim}")
                return True
            else:
                print(f"❌ FAIL - Extracted only {len(claims)} claims (expected {min_claims}+)")
                print("Output:", json.dumps(claims_text, indent=2))
                return False
        else:
            print(f"⚠️ API Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    headers = login()
    
    tests = [
        {
            "name": "The Mega WhatsApp Forward",
            "min_claims": 5,
            "description": "Massive nested forward with emojis and multi-part misinformation.",
            "input": """
            ⏩ Forwarded
            ⏩ Forwarded as received
            
            ⚠️⚠️⚠️ URGENT ALERT FOR ALL INDIANS ⚠️⚠️⚠️
            
            Please read carefully and send to your family!!!
            
            Dr. Gupta from AIIMS has confirmed that the new variant is spreading through 5G waves 📡. Turn off your phone at night!
            
            Also, UNESCO has declared our national anthem as the best in the world 🇮🇳. Be proud!
            
            Did you know?
            1. Drinking hot water with turmeric kills 100% of cancer cells 🍵
            2. Applying cow dung protects from radiation 🐮
            3. The government is giving free laptops to all students, click here: bit.ly/scam 💻
            
            Don't ignore this message! If you don't forward to 10 people, bad luck will follow you for 7 years 😱.
            
            (End of message)
            
            Reply 'YES' to subscribe.
            """
        },
        {
            "name": "Hinglish (Mixed Language)",
            "min_claims": 2,
            "description": "Hindi + English code-switching common in India.",
            "input": """
            Bhai suno, vaccines se autism hota hai, ye scientist ne prove kiya hai.
            Government humse jhooth bol rahi hai. 
            Modi ji ne kaha hai ki plastic surgery ancient India mein invent hui thi.
            Is this true? Check karo.
            """
        },
        {
            "name": "Code Injection Attempt",
            "min_claims": 2,
            "description": "Text containing SQL and Script tags mixed with claims.",
            "input": """
            The election was rigged! <script>alert('hacked')</script>
            DROP TABLE users; SELECT * FROM passwords;
            They stored fake ballots in the basement.
            ' OR '1'='1
            """
        },
        {
            "name": "Deeply Nested Copy-Paste",
            "min_claims": 3,
            "description": "Messy copy-paste metadata from email/social media.",
            "input": """
            On Mon, Jan 20, 2025 at 10:00 AM, Uncle Bob <bob@example.com> wrote:
            > On Sun, Jan 19, 2025 at 8:00 PM, Aunt Alice wrote:
            >> Fwd: Fwd: Fwd: READ THIS NOW
            >> 
            >> ________________________________________
            >> From: Truth Seeker [truth@conspiracy.com]
            >> Sent: Sunday, January 19, 2025 7:55 PM
            >> To: Everyone
            >> Subject: The moon landing is fake!
            >> 
            >> Look at the shadows in the photos. They are wrong.
            >> The flag was waving but there is no wind on the moon.
            >> Stanley Kubrick filmed it in a studio.
            >> 
            >> -----------------------------------------
            >> Disclaimer: This email is scanned by Norton Antivirus.
            """
        },
        {
            "name": "Emoji Flood",
            "min_claims": 1,
            "description": "Text drowning in emojis.",
            "input": """
            💉💉💉☠️☠️☠️ NO VACCINE 🚫🚫🚫
            😡😡😡 THE GOVERNMENT 🏛️🏛️🏛️ IS POISONING 🧪🧪🧪 THE WATER 💧💧💧
            🧠🧠🧠 WAKE UP 👁️👁️👁️
            """
        },
        {
            "name": "Massive 2KB+ Random Text",
            "min_claims": 1,
            "description": "Huge block of text to test token limits.",
            "input": "This is a test of length. " * 50 + "The sky is green. " + "Test continues. " * 50
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for t in tests:
        if run_test(t["name"], t["input"], t["min_claims"], t["description"], headers):
            passed += 1
            
    print_header("ULTRA STRESS TEST REPORT")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🏆 ULTRA STEEL STRONG - Ready for WhatsApp viral madness!")
        sys.exit(0)
    else:
        print("❌ Verification Failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
