
import sys
import os
import asyncio

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.normalization.normalizer import get_normalizer

async def test_normalization():
    print("🧠 Initializing Normalizer...")
    normalizer = get_normalizer()
    
    # Test 1: New Claim
    text1 = "Narendra Modi is the Prime Minister of India"
    print(f"\n📝 Processing Claim 1: '{text1}'")
    result1 = normalizer.normalize(text1)
    print(f"   Canonical ID: {result1['canonical_id']}")
    print(f"   Is Duplicate: {result1['is_duplicate']}")
    
    # Test 2: Semantic Duplicate
    text2 = "Modi is India's PM"
    print(f"\n📝 Processing Claim 2: '{text2}'")
    result2 = normalizer.normalize(text2)
    print(f"   Canonical ID: {result2['canonical_id']}")
    print(f"   Is Duplicate: {result2['is_duplicate']}")
    print(f"   Similarity: {result2['similarity_score']:.3f}")
    
    if result2['is_duplicate'] and result2['canonical_id'] == result1['canonical_id']:
        print("✅ SUCCESS: Semantic duplicate detected!")
    else:
        print("❌ FAILURE: Failed to detect duplicate.")

    # Test 3: Different Claim
    text3 = "Virat Kohli is a cricketer"
    print(f"\n📝 Processing Claim 3: '{text3}'")
    result3 = normalizer.normalize(text3)
    print(f"   Is Duplicate: {result3['is_duplicate']}")
    print(f"   Similarity: {result3['similarity_score']:.3f}")
    
    if not result3['is_duplicate']:
        print("✅ SUCCESS: Distinct claim correctly identified.")
    else:
        print("❌ FAILURE: False positive on distinct claim.")

if __name__ == "__main__":
    asyncio.run(test_normalization())
