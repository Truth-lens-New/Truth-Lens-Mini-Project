import sys, os, time
sys.path.insert(0, "/app")

from app.services.deepfake import get_deepfake_detector
import urllib3
urllib3.disable_warnings()

images = [
    r"/app/tests/synthid_1.png",
    r"/app/tests/synthid_2.png",
    r"/app/tests/synthid_3.png",
    r"/app/tests/synthid_4.png",
    r"/app/tests/synthid_5.png",
]

print("==================================================")
print("  TESTING GOOGLE SYNTHID EARLY-EXIT DETECTION     ")
print("==================================================")

detector = get_deepfake_detector()

for img_path in images:
    name = os.path.basename(img_path)
    try:
        with open(img_path, "rb") as f:
            image_bytes = f.read()
            
        res = detector.predict(image_bytes)
        model = res.get("model")
        verdict = res.get("verdict")
        conf = res.get("confidence")
        evidence = res.get("evidence", [])
        
        ok = "[OK]" if verdict == "FAKE" and "Gemini SynthID Detector" in model else "[FAIL]"
        print(f"\n{ok} {name} | Verdict: {verdict} ({conf}%)")
        print(f"     Model: {model}")
        if evidence:
            print(f"     Evidence: {evidence[0]}")
    except Exception as e:
        print(f"\n[ERROR] Failed {name}: {e}")

print("\nFinished testing.")
