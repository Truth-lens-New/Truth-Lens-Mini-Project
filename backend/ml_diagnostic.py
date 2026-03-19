"""
Deep Diagnostic Analysis — Which model should be trained further?
Examines: confidence distributions, error severity, bias, decision boundary quality.
"""
import torch
import timm
from torchvision import transforms
from PIL import Image
import requests
import io
import time
import json
import urllib3
urllib3.disable_warnings()

def load_model(name, path, arch, input_size):
    device = torch.device('cpu')
    model = timm.create_model(arch, pretrained=False, num_classes=2)
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    info = {}
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
        info = {"epoch": checkpoint.get("epoch","?"), "val_acc": checkpoint.get("val_acc","?")}
    else:
        model.load_state_dict(checkpoint)
    model.eval()
    tfm = transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    return model, tfm, info

def fetch_image(url):
    headers = {'User-Agent': 'TruthLens-Diag/1.0'}
    for _ in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=8, verify=False)
            if r.status_code == 200 and len(r.content) > 1000:
                return Image.open(io.BytesIO(r.content)).convert('RGB')
        except: pass
        time.sleep(0.5)
    return None

DATASET = [
    # Real Portraits (5)
    {"url": "https://picsum.photos/id/1005/400/400", "label": "REAL", "cat": "Real Portrait"},
    {"url": "https://picsum.photos/id/1012/400/400", "label": "REAL", "cat": "Real Portrait"},
    {"url": "https://picsum.photos/id/1027/400/400", "label": "REAL", "cat": "Real Portrait"},
    {"url": "https://picsum.photos/id/1011/400/400", "label": "REAL", "cat": "Real Portrait"},
    {"url": "https://picsum.photos/id/64/400/400",   "label": "REAL", "cat": "Real Portrait"},
    # Real Nature (5)
    {"url": "https://picsum.photos/id/10/400/400",   "label": "REAL", "cat": "Real Nature"},
    {"url": "https://picsum.photos/id/15/400/400",   "label": "REAL", "cat": "Real Nature"},
    {"url": "https://picsum.photos/id/29/400/400",   "label": "REAL", "cat": "Real Nature"},
    {"url": "https://picsum.photos/id/100/400/400",  "label": "REAL", "cat": "Real Nature"},
    {"url": "https://picsum.photos/id/106/400/400",  "label": "REAL", "cat": "Real Nature"},
    # Real Objects (5)
    {"url": "https://picsum.photos/id/119/400/400",  "label": "REAL", "cat": "Real Objects"},
    {"url": "https://picsum.photos/id/160/400/400",  "label": "REAL", "cat": "Real Objects"},
    {"url": "https://picsum.photos/id/180/400/400",  "label": "REAL", "cat": "Real Objects"},
    {"url": "https://picsum.photos/id/201/400/400",  "label": "REAL", "cat": "Real Objects"},
    {"url": "https://picsum.photos/id/249/400/400",  "label": "REAL", "cat": "Real Objects"},
    # AI Faces (5)
    {"url": "https://thispersondoesnotexist.com/?v=10", "label": "FAKE", "cat": "AI Face"},
    {"url": "https://thispersondoesnotexist.com/?v=20", "label": "FAKE", "cat": "AI Face"},
    {"url": "https://thispersondoesnotexist.com/?v=30", "label": "FAKE", "cat": "AI Face"},
    {"url": "https://thispersondoesnotexist.com/?v=40", "label": "FAKE", "cat": "AI Face"},
    {"url": "https://thispersondoesnotexist.com/?v=50", "label": "FAKE", "cat": "AI Face"},
    # Edited Portraits (5)
    {"url": "https://upload.wikimedia.org/wikipedia/commons/8/8d/President_Barack_Obama.jpg", "label": "FAKE", "cat": "Edited Portrait"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/440px-Donald_Trump_official_portrait.jpg", "label": "FAKE", "cat": "Edited Portrait"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Official_portrait_of_Barack_Obama.jpg/440px-Official_portrait_of_Barack_Obama.jpg", "label": "FAKE", "cat": "Edited Portrait"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Elon_Musk_%28cropped%29.jpg/440px-Elon_Musk_%28cropped%29.jpg", "label": "FAKE", "cat": "Edited Portrait"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Narendra_Modi_2021.jpg/440px-Narendra_Modi_2021.jpg", "label": "FAKE", "cat": "Edited Portrait"},
    # Real Landmarks (5)
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Statue_of_Liberty%2C_NY.jpg/500px-Statue_of_Liberty%2C_NY.jpg", "label": "REAL", "cat": "Real Landmark"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Golden_Retriever_with_tennis_ball.jpg/500px-Golden_Retriever_with_tennis_ball.jpg", "label": "REAL", "cat": "Real Landmark"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Empire_state_building.jpg/400px-Empire_state_building.jpg", "label": "REAL", "cat": "Real Landmark"},
    {"url": "https://picsum.photos/id/365/400/400", "label": "REAL", "cat": "Real Landmark"},
    {"url": "https://picsum.photos/id/396/400/400", "label": "REAL", "cat": "Real Landmark"},
]

def main():
    print("="*65)
    print("  DEEP DIAGNOSTIC: MODEL TRAINABILITY ANALYSIS")
    print("="*65)

    models_cfg = {
        "B0 (Jan)":       ("models/best_effnetb0.pth",         "efficientnet_b0", 224),
        "B3 (Upload1)":   ("models/efficientnet_b3_best.pth",  "efficientnet_b3", 300),
        "B3 (Production)":("models/efficientnet_b3_production.pth","efficientnet_b3", 300),
    }

    models = {}
    for name, (path, arch, sz) in models_cfg.items():
        model, tfm, info = load_model(name, path, arch, sz)
        models[name] = (model, tfm, info)
        print(f"  Loaded {name}: {info if info else 'raw weights'}")

    # Per-model detailed tracking
    data = {}
    for m in models:
        data[m] = {
            "correct_confs": [],     # confidence when prediction is CORRECT
            "wrong_confs": [],       # confidence when prediction is WRONG
            "real_as_fake_confs": [], # FP: confidence when real flagged as fake
            "fake_as_real_confs": [], # FN: confidence when fake called real
            "fake_prob_on_real": [],  # raw fake_prob for REAL images
            "fake_prob_on_fake": [],  # raw fake_prob for FAKE images
            "per_image": [],
            "TP":0,"FP":0,"TN":0,"FN":0,
        }

    print(f"\nProcessing {len(DATASET)} images...\n")

    for i, item in enumerate(DATASET):
        img = fetch_image(item["url"])
        if img is None:
            print(f"  [{i+1:2d}] SKIP: {item['cat']}")
            continue

        truth_fake = (item["label"] == "FAKE")

        for m_name, (model, tfm, _) in models.items():
            inp = tfm(img).unsqueeze(0)
            with torch.no_grad():
                probs = torch.softmax(model(inp), dim=1)

            real_p = probs[0][0].item()
            fake_p = probs[0][1].item()
            pred_class = torch.argmax(probs, dim=1).item()
            verdict = "FAKE" if pred_class == 1 else "REAL"
            conf = probs[0][pred_class].item()
            correct = (verdict == item["label"])

            d = data[m_name]
            if correct:
                d["correct_confs"].append(conf)
            else:
                d["wrong_confs"].append(conf)

            if truth_fake:
                d["fake_prob_on_fake"].append(fake_p)
                if verdict == "FAKE": d["TP"] += 1
                else:
                    d["FN"] += 1
                    d["fake_as_real_confs"].append(conf)
            else:
                d["fake_prob_on_real"].append(fake_p)
                if verdict == "REAL": d["TN"] += 1
                else:
                    d["FP"] += 1
                    d["real_as_fake_confs"].append(conf)

            d["per_image"].append({
                "cat": item["cat"], "truth": item["label"],
                "verdict": verdict, "conf": round(conf*100,1),
                "real_p": round(real_p*100,1), "fake_p": round(fake_p*100,1),
                "correct": correct
            })

        print(f"  [{i+1:2d}/{len(DATASET)}] {item['cat']:18s} GT={item['label']}")

    # ─── Analysis ────────────────────────────────────────────────────────
    print("\n" + "="*65)
    print("  DIAGNOSTIC RESULTS")
    print("="*65)

    for m_name in models:
        d = data[m_name]
        total = d["TP"] + d["FP"] + d["TN"] + d["FN"]
        acc = (d["TP"] + d["TN"]) / total * 100 if total else 0
        
        avg_correct_conf = sum(d["correct_confs"])/len(d["correct_confs"])*100 if d["correct_confs"] else 0
        avg_wrong_conf = sum(d["wrong_confs"])/len(d["wrong_confs"])*100 if d["wrong_confs"] else 0
        
        # Separation score: how well does the model separate REAL from FAKE?
        avg_fake_p_on_real = sum(d["fake_prob_on_real"])/len(d["fake_prob_on_real"]) if d["fake_prob_on_real"] else 0
        avg_fake_p_on_fake = sum(d["fake_prob_on_fake"])/len(d["fake_prob_on_fake"]) if d["fake_prob_on_fake"] else 0
        separation = avg_fake_p_on_fake - avg_fake_p_on_real  # Higher = better separation
        
        # Overconfident wrongs: errors with >80% confidence (hardest to fix)
        overconf_wrongs = [c for c in d["wrong_confs"] if c > 0.80]
        
        # Uncertain corrects: correct but <60% confidence (fragile)
        uncertain_corrects = [c for c in d["correct_confs"] if c < 0.60]

        # FAKE bias: does the model lean towards predicting FAKE?
        total_fake_preds = d["TP"] + d["FP"]
        total_real_preds = d["TN"] + d["FN"]
        bias_ratio = total_fake_preds / total if total else 0

        print(f"\n{'─'*65}")
        print(f"  MODEL: {m_name}")
        print(f"{'─'*65}")
        print(f"  Accuracy:               {acc:.1f}% ({d['TP']+d['TN']}/{total})")
        print(f"  Avg Confidence (Correct): {avg_correct_conf:.1f}%")
        print(f"  Avg Confidence (Wrong):   {avg_wrong_conf:.1f}%")
        print(f"  Confidence Gap:           {avg_correct_conf - avg_wrong_conf:.1f}pp")
        print(f"  Class Separation Score:   {separation:.3f} (higher = better)")
        print(f"  Avg fake_prob on REAL imgs: {avg_fake_p_on_real:.3f}")
        print(f"  Avg fake_prob on FAKE imgs: {avg_fake_p_on_fake:.3f}")
        print(f"  FAKE Bias Ratio:          {bias_ratio:.2f} (0.5 = balanced)")
        print(f"  Overconfident Errors:     {len(overconf_wrongs)}/{len(d['wrong_confs'])} wrong predictions >80%")
        print(f"  Fragile Corrects:         {len(uncertain_corrects)}/{len(d['correct_confs'])} correct predictions <60%")
        print(f"  Confusion: TP={d['TP']} FP={d['FP']} TN={d['TN']} FN={d['FN']}")

        # Per-category error analysis
        cats = {}
        for r in d["per_image"]:
            c = r["cat"]
            if c not in cats: cats[c] = {"correct":0,"total":0,"confs":[]}
            cats[c]["total"] += 1
            cats[c]["confs"].append(r["conf"])
            if r["correct"]: cats[c]["correct"] += 1

        print(f"\n  Per-Category:")
        for cat, cr in cats.items():
            cat_acc = cr["correct"]/cr["total"]*100 if cr["total"] else 0
            avg_c = sum(cr["confs"])/len(cr["confs"]) if cr["confs"] else 0
            print(f"    {cat:20s}: {cat_acc:5.1f}% acc, {avg_c:5.1f}% avg_conf")

        # List the WRONG predictions with details
        wrongs = [r for r in d["per_image"] if not r["correct"]]
        if wrongs:
            print(f"\n  Errors ({len(wrongs)}):")
            for w in wrongs:
                print(f"    {w['cat']:20s} GT={w['truth']:4s} -> {w['verdict']:4s} ({w['conf']}% conf) fake_p={w['fake_p']}%")

    print("\n" + "="*65)
    print("  TRAINABILITY VERDICT")
    print("="*65)

    # Print raw JSON for report generation
    summary = {}
    for m_name in models:
        d = data[m_name]
        total = d["TP"]+d["FP"]+d["TN"]+d["FN"]
        avg_fake_p_on_real = sum(d["fake_prob_on_real"])/len(d["fake_prob_on_real"]) if d["fake_prob_on_real"] else 0
        avg_fake_p_on_fake = sum(d["fake_prob_on_fake"])/len(d["fake_prob_on_fake"]) if d["fake_prob_on_fake"] else 0
        overconf_wrongs = len([c for c in d["wrong_confs"] if c > 0.80])
        uncertain_corrects = len([c for c in d["correct_confs"] if c < 0.60])
        summary[m_name] = {
            "accuracy": round((d["TP"]+d["TN"])/total*100,1) if total else 0,
            "separation_score": round(avg_fake_p_on_fake - avg_fake_p_on_real, 3),
            "avg_correct_conf": round(sum(d["correct_confs"])/len(d["correct_confs"])*100,1) if d["correct_confs"] else 0,
            "avg_wrong_conf": round(sum(d["wrong_confs"])/len(d["wrong_confs"])*100,1) if d["wrong_confs"] else 0,
            "overconfident_errors": overconf_wrongs,
            "fragile_corrects": uncertain_corrects,
            "total_errors": len(d["wrong_confs"]),
            "info": models[m_name][2],
        }

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
