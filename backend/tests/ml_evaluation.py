"""
Senior ML Engineer — Comprehensive Deepfake Model Evaluation
Evaluates 3 EfficientNet models across diverse image categories.
Computes: Accuracy, Precision, Recall, F1-Score, Avg Confidence, Inference Time.
"""
import torch
import timm
from torchvision import transforms
from PIL import Image
import requests
import io
import time
import json
import sys

# ─── Model Loading ───────────────────────────────────────────────────────────

def load_model(name, path, arch, input_size):
    device = torch.device('cpu')
    model = timm.create_model(arch, pretrained=False, num_classes=2)
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
        ckpt_info = f"checkpoint (epoch={checkpoint.get('epoch','?')}, val_acc={checkpoint.get('val_acc','?')})"
    else:
        model.load_state_dict(checkpoint)
        ckpt_info = "raw state_dict"
    model.eval()
    tfm = transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    print(f"  Loaded {name} ({arch}, {input_size}px) from {ckpt_info}")
    return model, tfm

# ─── Image Fetcher ───────────────────────────────────────────────────────────

def fetch_image(url):
    headers = {'User-Agent': 'TruthLens-MLEval/2.0'}
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=8, verify=False)
            if r.status_code == 200 and len(r.content) > 1000:
                return Image.open(io.BytesIO(r.content)).convert('RGB')
        except Exception:
            time.sleep(1)
    return None

# ─── Predict ─────────────────────────────────────────────────────────────────

def predict(model, tfm, img):
    inp = tfm(img).unsqueeze(0)
    t0 = time.time()
    with torch.no_grad():
        probs = torch.softmax(model(inp), dim=1)
    latency = time.time() - t0
    pred_class = torch.argmax(probs, dim=1).item()
    verdict = "FAKE" if pred_class == 1 else "REAL"
    conf = probs[0][pred_class].item()
    return verdict, conf, latency

# ─── Dataset ─────────────────────────────────────────────────────────────────
# Curated benchmark: 30 images across 6 categories
# Ground truth labels are determined by origin

DATASET = [
    # ── Category 1: Real Unedited Human Portraits (5) ──
    {"url": "https://picsum.photos/id/1005/400/400", "label": "REAL", "cat": "Real Portrait"},
    {"url": "https://picsum.photos/id/1012/400/400", "label": "REAL", "cat": "Real Portrait"},
    {"url": "https://picsum.photos/id/1027/400/400", "label": "REAL", "cat": "Real Portrait"},
    {"url": "https://picsum.photos/id/1011/400/400", "label": "REAL", "cat": "Real Portrait"},
    {"url": "https://picsum.photos/id/64/400/400",   "label": "REAL", "cat": "Real Portrait"},
    
    # ── Category 2: Real Nature / Scenic (5) ──
    {"url": "https://picsum.photos/id/10/400/400",   "label": "REAL", "cat": "Real Nature"},
    {"url": "https://picsum.photos/id/15/400/400",   "label": "REAL", "cat": "Real Nature"},
    {"url": "https://picsum.photos/id/29/400/400",   "label": "REAL", "cat": "Real Nature"},
    {"url": "https://picsum.photos/id/100/400/400",  "label": "REAL", "cat": "Real Nature"},
    {"url": "https://picsum.photos/id/106/400/400",  "label": "REAL", "cat": "Real Nature"},
    
    # ── Category 3: Real Objects / Architecture (5) ──
    {"url": "https://picsum.photos/id/119/400/400",  "label": "REAL", "cat": "Real Objects"},
    {"url": "https://picsum.photos/id/160/400/400",  "label": "REAL", "cat": "Real Objects"},
    {"url": "https://picsum.photos/id/180/400/400",  "label": "REAL", "cat": "Real Objects"},
    {"url": "https://picsum.photos/id/201/400/400",  "label": "REAL", "cat": "Real Objects"},
    {"url": "https://picsum.photos/id/249/400/400",  "label": "REAL", "cat": "Real Objects"},
    
    # ── Category 4: AI-Generated Faces (5) ──
    {"url": "https://thispersondoesnotexist.com/?v=1", "label": "FAKE", "cat": "AI Face"},
    {"url": "https://thispersondoesnotexist.com/?v=2", "label": "FAKE", "cat": "AI Face"},
    {"url": "https://thispersondoesnotexist.com/?v=3", "label": "FAKE", "cat": "AI Face"},
    {"url": "https://thispersondoesnotexist.com/?v=4", "label": "FAKE", "cat": "AI Face"},
    {"url": "https://thispersondoesnotexist.com/?v=5", "label": "FAKE", "cat": "AI Face"},
    
    # ── Category 5: Heavily Edited Official Portraits (5) ──
    {"url": "https://upload.wikimedia.org/wikipedia/commons/8/8d/President_Barack_Obama.jpg", "label": "FAKE", "cat": "Edited Portrait"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/440px-Donald_Trump_official_portrait.jpg", "label": "FAKE", "cat": "Edited Portrait"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Official_portrait_of_Barack_Obama.jpg/440px-Official_portrait_of_Barack_Obama.jpg", "label": "FAKE", "cat": "Edited Portrait"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Elon_Musk_%28cropped%29.jpg/440px-Elon_Musk_%28cropped%29.jpg", "label": "FAKE", "cat": "Edited Portrait"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Narendra_Modi_2021.jpg/440px-Narendra_Modi_2021.jpg", "label": "FAKE", "cat": "Edited Portrait"},
    
    # ── Category 6: Known Real Landmarks & Animals (5) ──
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Statue_of_Liberty%2C_NY.jpg/500px-Statue_of_Liberty%2C_NY.jpg", "label": "REAL", "cat": "Real Landmark"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Empire_state_building.jpg/400px-Empire_state_building.jpg", "label": "REAL", "cat": "Real Landmark"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Sydney_Australia._%2821339175489%29.jpg/500px-Sydney_Australia._%2821339175489%29.jpg", "label": "REAL", "cat": "Real Landmark"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Image_created_with_a_mobile_phone.png/440px-Image_created_with_a_mobile_phone.png", "label": "REAL", "cat": "Real Landmark"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Golden_Retriever_with_tennis_ball.jpg/500px-Golden_Retriever_with_tennis_ball.jpg", "label": "REAL", "cat": "Real Landmark"},
]

# ─── Main Evaluation ─────────────────────────────────────────────────────────

def main():
    import urllib3
    urllib3.disable_warnings()

    print("="*65)
    print("  TRUTHLENS DEEPFAKE MODEL EVALUATION — Senior ML Engineer Report")
    print("="*65)

    print("\nLoading models...")
    models = {
        "B0 (Jan)": load_model("B0 (Jan)", "models/best_effnetb0.pth", "efficientnet_b0", 224),
        "B3 (Upload1)": load_model("B3 (Upload1)", "models/efficientnet_b3_best.pth", "efficientnet_b3", 300),
        "B3 (Production)": load_model("B3 (Production)", "models/efficientnet_b3_production.pth", "efficientnet_b3", 300),
    }

    # Per-model metrics accumulators
    metrics = {}
    for m in models:
        metrics[m] = {"TP":0,"FP":0,"TN":0,"FN":0,"total":0,"confidences":[],"latencies":[],"cat_results":{}}

    print(f"\nEvaluating {len(DATASET)} images across 6 categories...\n")

    for i, item in enumerate(DATASET):
        img = fetch_image(item["url"])
        if img is None:
            print(f"  [{i+1:2d}] SKIP (download failed): {item['cat']}")
            continue

        truth_fake = (item["label"] == "FAKE")
        cat = item["cat"]

        for m_name, (model, tfm) in models.items():
            verdict, conf, latency = predict(model, tfm, img)
            pred_fake = (verdict == "FAKE")
            correct = (verdict == item["label"])

            m = metrics[m_name]
            m["total"] += 1
            m["confidences"].append(conf)
            m["latencies"].append(latency)

            if truth_fake and pred_fake:     m["TP"] += 1
            elif not truth_fake and pred_fake: m["FP"] += 1
            elif not truth_fake and not pred_fake: m["TN"] += 1
            elif truth_fake and not pred_fake: m["FN"] += 1

            if cat not in m["cat_results"]:
                m["cat_results"][cat] = {"correct": 0, "total": 0}
            m["cat_results"][cat]["total"] += 1
            if correct:
                m["cat_results"][cat]["correct"] += 1

        print(f"  [{i+1:2d}/{len(DATASET)}] {item['cat']:18s} GT={item['label']:4s}")

    # ─── Results ─────────────────────────────────────────────────────────
    print("\n" + "="*65)
    print("  FINAL RESULTS")
    print("="*65)

    results_json = {}

    for m_name in models:
        m = metrics[m_name]
        if m["total"] == 0: continue

        acc = (m["TP"] + m["TN"]) / m["total"] * 100
        prec = m["TP"] / (m["TP"] + m["FP"]) * 100 if (m["TP"] + m["FP"]) > 0 else 0
        rec  = m["TP"] / (m["TP"] + m["FN"]) * 100 if (m["TP"] + m["FN"]) > 0 else 0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        avg_conf = sum(m["confidences"]) / len(m["confidences"]) * 100
        avg_lat = sum(m["latencies"]) / len(m["latencies"]) * 1000

        print(f"\n  Model: {m_name}")
        print(f"  {'─'*50}")
        print(f"  Accuracy:       {acc:6.1f}%  ({m['TP']+m['TN']}/{m['total']})")
        print(f"  Precision:      {prec:6.1f}%")
        print(f"  Recall:         {rec:6.1f}%")
        print(f"  F1-Score:       {f1:6.1f}%")
        print(f"  Avg Confidence: {avg_conf:6.1f}%")
        print(f"  Avg Latency:    {avg_lat:6.1f}ms")
        print(f"  Confusion:      TP={m['TP']} FP={m['FP']} TN={m['TN']} FN={m['FN']}")
        
        print(f"\n  Per-Category Breakdown:")
        for cat, cr in m["cat_results"].items():
            cat_acc = cr["correct"] / cr["total"] * 100 if cr["total"] > 0 else 0
            print(f"    {cat:20s}: {cat_acc:5.1f}% ({cr['correct']}/{cr['total']})")

        results_json[m_name] = {
            "accuracy": round(acc, 1), "precision": round(prec, 1),
            "recall": round(rec, 1), "f1": round(f1, 1),
            "avg_confidence": round(avg_conf, 1), "avg_latency_ms": round(avg_lat, 1),
            "confusion": {"TP": m["TP"], "FP": m["FP"], "TN": m["TN"], "FN": m["FN"]},
            "categories": {c: {"accuracy": round(r["correct"]/r["total"]*100, 1), "correct": r["correct"], "total": r["total"]} for c, r in m["cat_results"].items()}
        }

    # Dump JSON for report generation
    print("\n\n--- JSON_RESULTS_START ---")
    print(json.dumps(results_json, indent=2))
    print("--- JSON_RESULTS_END ---")

if __name__ == "__main__":
    main()
