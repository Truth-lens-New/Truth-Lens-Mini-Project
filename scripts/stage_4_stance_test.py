#!/usr/bin/env python3
"""
STAGE 4 STRESS TEST - STANCE DETECTION
Target: Verify BART-NLI Stance Detection Thresholds.
"""
import sys
import os
import asyncio

# Add backend to path to import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.services.investigation.stance_detector import StanceDetector

async def run_test():
    print("🚀 Initializing StanceDetector (Loading BART-Large-MNLI)...")
    detector = StanceDetector()
    
    tests = [
        {
            "name": "Direct Refutation",
            "claim": "The earth is flat.",
            "evidence": "Satellite imagery and physics prove the Earth is an oblate spheroid, confirming it is round.",
            "expected": "REFUTES"
        },
        {
            "name": "Direct Support",
            "claim": "Smoking causes cancer.",
            "evidence": "Extensive studies have shown a direct link between smoking tobacco and lung cancer.",
            "expected": "SUPPORTS"
        },
        {
            "name": "Subtle Refutation",
            "claim": "Hydroxychloroquine cures COVID-19.",
            "evidence": "Randomized clinical trials showed no significant benefit of hydroxychloroquine in treating COVID-19 patients.",
            "expected": "REFUTES"
        },
        {
            "name": "Subtle Support",
            "claim": "Exercise improves mental health.",
            "evidence": "Physical activity releases endorphins which are known to reduce stress and improve mood.",
            "expected": "SUPPORTS"
        },
        {
            "name": "Neutral / Unrelated",
            "claim": "The sky is blue.",
            "evidence": "The stock market crashed on Monday due to inflation fears.",
            "expected": "NEUTRAL" # or UNRELATED, code uses NEUTRAL label for unrelated hypothesis
        },
        {
            "name": "Partial/Discuss (Challenge)",
            "claim": "Coffee is good for you.",
            "evidence": "Coffee contains antioxidants but can also cause anxiety in some people.",
            "expected": "NEUTRAL" # Or Discuss? Model maps to Neutral if not robust support/refute
        }
    ]
    
    passed = 0
    total = len(tests)
    
    print("\n🧪 Running Stance Tests...")
    print("="*60)
    
    for t in tests:
        print(f"Test: {t['name']}")
        result = detector.detect(t['claim'], t['evidence'])
        
        label = result['label']
        score = result['score']
        raw = result['raw_scores']
        
        print(f"  Claim: {t['claim']}")
        print(f"  Evid : {t['evidence'][:50]}...")
        print(f"  -> Result: {label} (Score: {score:.3f})")
        print(f"  -> Raw   : Sup={raw['support']:.3f}, Ref={raw['refute']:.3f}, Neu={raw['neutral']:.3f}")
        
        if label == t['expected']:
            print("  ✅ PASS")
            passed += 1
        else:
            # If expected REFUTES but got NEUTRAL, it implies threshold too high
            print(f"  ❌ FAIL (Expected {t['expected']})")
            
        print("-" * 40)
        
    print(f"\n📊 Result: {passed}/{total} Passed")
    
    if passed == total:
        print("🏆 STAGE 4 TUNED")
    else:
        print("⚠️ STAGE 4 NEEDS TUNING")

if __name__ == "__main__":
    asyncio.run(run_test())
