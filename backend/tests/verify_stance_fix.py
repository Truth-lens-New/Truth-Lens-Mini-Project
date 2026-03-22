
import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.investigation.stance_detector import StanceDetector

def test_green_cheese():
    print("\n--- Testing 'Green Cheese' Myth ---")
    claim = "The moon is made of green cheese"
    # This snippet caused the hallucination
    evidence = "The Moon is made of green cheese is a statement referring to a fanciful belief that the Moon is composed of cheese."
    
    detector = StanceDetector()
    result = detector.detect(claim, evidence)
    
    print(f"Claim: {claim}")
    print(f"Evidence: {evidence}")
    print(f"Result: {result['label']} (Score: {result['score']:.4f})")
    print(f"Raw Scores: {result['raw_scores']}")
    
    # We expect REFUTES or NEUTRAL, definitely NOT SUPPORTS
    if result['label'] == 'SUPPORTS':
        print("❌ FAILED: Still detecting as SUPPORTS")
    else:
        print("✅ PASSED: Correctly identified as NOT supporting")

if __name__ == "__main__":
    test_green_cheese()
