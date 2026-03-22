import sys
import os
# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from transformers import pipeline

def test_stance():
    print("⏳ Loading model...")
    classifier = pipeline("text-classification", model="roberta-large-mnli")
    
    premise = "The first ever Prime Minister to be born after Independence, Shri Modi has previously served as the Chief Minister of Gujarat."
    hypothesis = "Narendra modi is the first prime minister of india"
    
    input_text = f"{premise} </s></s> {hypothesis}"
    result = classifier(input_text)
    
    print(f"\nPremise: {premise}")
    print(f"Hypothesis: {hypothesis}")
    print(f"Result: {result}")
    
    # Check mapping
    label = result[0]['label']
    score = result[0]['score']
    
    print(f"\nInterpretation:")
    if label == "ENTAILMENT": print(f"✅ SUPPORTS ({score:.4f})")
    elif label == "CONTRADICTION": print(f"❌ REFUTES ({score:.4f})")
    elif label == "NEUTRAL": print(f"🤷 NEUTRAL ({score:.4f})")

if __name__ == "__main__":
    test_stance()
