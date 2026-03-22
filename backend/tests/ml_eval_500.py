"""
Large-Scale Independent Evaluation — 500 Images
Sources NOT used in any model's training:
  - REAL: Picsum Photos (250 random real photographs)
  - FAKE: ThisPersonDoesNotExist (250 StyleGAN AI faces)
"""
import torch, timm, requests, io, time, json, sys, urllib3
from torchvision import transforms
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
urllib3.disable_warnings()

REAL_COUNT = 250
FAKE_COUNT = 250

def load_model(name, path):
    device = torch.device('cpu')
    model = timm.create_model('efficientnet_b3', pretrained=False, num_classes=2)
    ckpt = torch.load(path, map_location=device, weights_only=False)
    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        model.load_state_dict(ckpt)
    model.eval()
    tfm = transforms.Compose([
        transforms.Resize((300, 300)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    return model, tfm

def main():
    print("="*65)
    print("  500-IMAGE INDEPENDENT EVALUATION (No Training Data Overlap)")
    print("="*65)

    print("\nLoading 3 models...")
    models = {
        "B3_Upload1":    load_model("B3_Upload1",   "models/efficientnet_b3_best.pth"),
        "B3_Production": load_model("B3_Production","models/efficientnet_b3_production.pth"),
        "B3_OpenFake":   load_model("B3_OpenFake",  "models/efficientnet_b3_openfake_best.pth"),
    }
    print("  All models loaded.\n")

    metrics = {}
    for m in models:
        metrics[m] = {"TP":0,"FP":0,"TN":0,"FN":0,"confs_correct":[],"confs_wrong":[]}

    session = requests.Session()
    session.headers.update({"User-Agent": "TruthLens-LargeEval/1.0"})
    total_tested = 0
    total_skipped = 0

    # ─── Phase A: 250 REAL images from Picsum ────────────────
    print(f"[PHASE A] Downloading & evaluating {REAL_COUNT} REAL images (Picsum Photos)...")
    # Use IDs 1-500 range, skip known non-existent
    real_done = 0
    pid = 0
    while real_done < REAL_COUNT and pid < 1100:
        pid += 1
        try:
            r = session.get(f"https://picsum.photos/id/{pid}/300/300", timeout=6, verify=False)
            if r.status_code != 200 or len(r.content) < 2000:
                continue
            img = Image.open(io.BytesIO(r.content)).convert('RGB')
        except:
            continue

        for m_name, (model, tfm) in models.items():
            inp = tfm(img).unsqueeze(0)
            with torch.no_grad():
                probs = torch.softmax(model(inp), dim=1)
            pred = torch.argmax(probs, dim=1).item()
            conf = probs[0][pred].item()
            verdict = "FAKE" if pred == 1 else "REAL"
            m = metrics[m_name]
            if verdict == "REAL":
                m["TN"] += 1
                m["confs_correct"].append(conf)
            else:
                m["FP"] += 1
                m["confs_wrong"].append(conf)

        real_done += 1
        total_tested += 1
        if real_done % 25 == 0:
            print(f"  REAL: {real_done}/{REAL_COUNT} done")

    print(f"  ✅ {real_done} REAL images evaluated.\n")

    # ─── Phase B: 250 FAKE images from ThisPersonDoesNotExist ─
    print(f"[PHASE B] Downloading & evaluating {FAKE_COUNT} FAKE images (AI-generated faces)...")
    fake_done = 0
    while fake_done < FAKE_COUNT:
        try:
            r = session.get(
                f"https://thispersondoesnotexist.com/",
                timeout=8, verify=False
            )
            if r.status_code != 200 or len(r.content) < 5000:
                total_skipped += 1
                time.sleep(0.3)
                continue
            img = Image.open(io.BytesIO(r.content)).convert('RGB')
        except:
            total_skipped += 1
            time.sleep(0.5)
            continue

        for m_name, (model, tfm) in models.items():
            inp = tfm(img).unsqueeze(0)
            with torch.no_grad():
                probs = torch.softmax(model(inp), dim=1)
            pred = torch.argmax(probs, dim=1).item()
            conf = probs[0][pred].item()
            verdict = "FAKE" if pred == 1 else "REAL"
            m = metrics[m_name]
            if verdict == "FAKE":
                m["TP"] += 1
                m["confs_correct"].append(conf)
            else:
                m["FN"] += 1
                m["confs_wrong"].append(conf)

        fake_done += 1
        total_tested += 1
        if fake_done % 25 == 0:
            print(f"  FAKE: {fake_done}/{FAKE_COUNT} done")
        # Small delay to avoid rate limiting
        time.sleep(0.2)

    print(f"  ✅ {fake_done} FAKE images evaluated.\n")

    # ─── Results ─────────────────────────────────────────────
    print("="*65)
    print(f"  FINAL RESULTS — {total_tested} images ({real_done} REAL + {fake_done} FAKE)")
    print("="*65)

    for m_name in models:
        m = metrics[m_name]
        total = m["TP"] + m["FP"] + m["TN"] + m["FN"]
        acc = (m["TP"]+m["TN"])/total*100
        prec = m["TP"]/(m["TP"]+m["FP"])*100 if (m["TP"]+m["FP"]) else 0
        rec = m["TP"]/(m["TP"]+m["FN"])*100 if (m["TP"]+m["FN"]) else 0
        f1 = 2*prec*rec/(prec+rec) if (prec+rec) else 0
        fpr = m["FP"]/(m["FP"]+m["TN"])*100 if (m["FP"]+m["TN"]) else 0
        avg_cc = sum(m["confs_correct"])/len(m["confs_correct"])*100 if m["confs_correct"] else 0
        avg_wc = sum(m["confs_wrong"])/len(m["confs_wrong"])*100 if m["confs_wrong"] else 0

        print(f"\n  {m_name}")
        print(f"  {'─'*55}")
        print(f"  Accuracy:            {acc:6.1f}%  ({m['TP']+m['TN']}/{total})")
        print(f"  Precision:           {prec:6.1f}%")
        print(f"  Recall (Sensitivity):{rec:6.1f}%")
        print(f"  F1-Score:            {f1:6.1f}%")
        print(f"  False Positive Rate: {fpr:6.1f}%")
        print(f"  Avg Conf (correct):  {avg_cc:6.1f}%")
        print(f"  Avg Conf (wrong):    {avg_wc:6.1f}%")
        print(f"  Confusion: TP={m['TP']} FP={m['FP']} TN={m['TN']} FN={m['FN']}")
        print(f"  Real imgs correct:   {m['TN']}/{real_done} ({m['TN']/real_done*100:.1f}%)")
        print(f"  Fake imgs caught:    {m['TP']}/{fake_done} ({m['TP']/fake_done*100:.1f}%)")

    print(f"\n  Skipped downloads: {total_skipped}")

if __name__ == "__main__":
    main()
