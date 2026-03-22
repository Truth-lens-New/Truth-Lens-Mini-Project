"""
100-Image Before vs After Benchmark — Single-Pass vs Multi-Patch (FUSED)
========================================================================
Runs inside Docker. Tests 50 REAL (Picsum) and 50 FAKE (AI Faces).

OLD: standalone single forward pass on 300x300 resized image
NEW: DeepfakeDetector.predict() with global+patch+meta fusion
"""
import sys, os, io, time, json, requests
sys.path.insert(0, "/app")

import torch, timm
from torchvision import transforms
from PIL import Image
from app.services.deepfake import get_deepfake_detector
import urllib3
urllib3.disable_warnings()

MODEL_PATH = "/app/models/efficientnet_b3_production.pth"

# ── Dynamic Dataset ──────────────────────────────────────────────────────────
RAW_DATASET = []

# REAL: 80 from picsum (we will stop after 50 successes)
for i in range(1, 80):
    RAW_DATASET.append({"url": f"https://picsum.photos/id/{i}/800/800", "label": "REAL", "cat": "Real (Picsum)"})

# FAKE: 80 from AI generator (stop after 50)
for i in range(1, 80):
    RAW_DATASET.append({"url": f"https://thispersondoesnotexist.com/?v={time.time()}_{i}", "label": "FAKE", "cat": "AI Face"})

def load_old_model():
    dev = torch.device("cpu")
    m = timm.create_model("efficientnet_b3", pretrained=False, num_classes=2)
    ckpt = torch.load(MODEL_PATH, map_location=dev, weights_only=False)
    m.load_state_dict(ckpt["model_state_dict"] if isinstance(ckpt,dict) and "model_state_dict" in ckpt else ckpt)
    m.eval()
    return m, dev

TFM = transforms.Compose([
    transforms.Resize((300,300)),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
])

def single_pass(model, dev, img: Image.Image):
    t0 = time.time()
    with torch.no_grad():
        probs = torch.softmax(model(TFM(img).unsqueeze(0).to(dev)), dim=1)
    lat = time.time()-t0
    fp = probs[0][1].item()
    return {"verdict":"FAKE" if fp>=0.5 else "REAL", "fake_prob":round(fp*100,1), "lat_ms":round(lat*1000)}

def fetch(url):
    try:
        r=requests.get(url,headers={"User-Agent":"TruthLens/2.0"},timeout=8,verify=False)
        if r.status_code==200 and len(r.content)>5000: return r.content
    except: pass
    return None

def main():
    print("="*85)
    print("  100-Image Benchmark: Single-Pass vs Multi-Patch FUSION")
    print("="*85)

    print("\n[1] Initializing API DeepfakeDetector...")
    detector = get_deepfake_detector()
    
    print("[2] Loading raw OLD model reference...")
    old_model, old_dev = load_old_model()
    print("    OK")

    rows=[]
    real_count = 0
    fake_count = 0

    print(f"\n[3] Running evaluations (targeting 50 REAL + 50 FAKE)...\n")
    print(f"  {'#':>3}  {'Category':<20} {'GT':<5} {'OLD':<6} {'OLD%':>6} {'NEW (FUSED)':<15} {'Patches':>10}")
    print("  "+"-"*85)

    i = 0
    for item in RAW_DATASET:
        if item["label"] == "REAL" and real_count >= 50: continue
        if item["label"] == "FAKE" and fake_count >= 50: continue

        img_bytes = fetch(item["url"])
        if img_bytes is None:
            continue

        try:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            # Enforce minimum size to actually trigger patches
            if img.width < 350 or img.height < 350:
                continue
        except:
            continue
            
        i += 1
        if item["label"] == "REAL": real_count += 1
        else: fake_count += 1

        # OLD
        old = single_pass(old_model, old_dev, img)
        
        # NEW
        t0 = time.time()
        new_res = detector.predict(img_bytes)
        lat = time.time() - t0
        
        pa = new_res.get("patch_analysis", {})
        new = {
            "verdict": new_res["verdict"],
            "fake_prob": new_res["fake_probability"],
            "susp": pa.get("suspicious_patches", 0),
            "n": pa.get("total_patches", 1),
            "lat_ms": round(lat*1000)
        }

        old_ok = old["verdict"]==item["label"]
        new_ok = new["verdict"]==item["label"]
        change = "FIXED" if not old_ok and new_ok else ("REGD" if old_ok and not new_ok else ("OK" if new_ok else "X"))

        patch_info=f"{new['susp']}/{new['n']} susp"
        print(f"  {i:3d}  {item['cat']:<15} ({r'{:.1f}MB'.format(len(img_bytes)/1024/1024)}) {item['label']:<5}  {old['verdict']:<6} {old['fake_prob']:>5}%  {new['verdict']:<6} {new['fake_prob']:>5}%  {patch_info:>12}  {change}")
        rows.append({**item,"old":old,"new":new})
        
        if real_count >= 50 and fake_count >= 50: break

    # Stats
    n=len(rows)
    old_corr=sum(1 for r in rows if r["old"]["verdict"]==r["label"])
    new_corr=sum(1 for r in rows if r["new"]["verdict"]==r["label"])
    fixed   =sum(1 for r in rows if r["old"]["verdict"]!=r["label"] and r["new"]["verdict"]==r["label"])
    regressed=sum(1 for r in rows if r["old"]["verdict"]==r["label"] and r["new"]["verdict"]!=r["label"])

    print("\n"+"="*85)
    print(f"  OVERALL  OLD: {old_corr}/{n} = {old_corr/max(n,1)*100:.1f}%   NEW: {new_corr}/{n} = {new_corr/max(n,1)*100:.1f}%   Delta: {(new_corr-old_corr)/max(n,1)*100:+.1f}%")
    print(f"           Fixed: {fixed}   Regressed: {regressed}")
    print("="*85)
    
    # Save a quick JSON
    with open("/app/tests/benchmark_100_fused_results.json", "w") as f:
        json.dump({"overall": {"total": n, "old_acc": old_corr/max(n,1)*100, "new_acc": new_corr/max(n,1)*100, "fixed": fixed, "regressed": regressed}}, f)

        # Markdown report
    md = []
    md.append(f"# 100-Image Fused Benchmark Report\n")
    md.append(f"**Total images evaluated:** {n} (REAL: {real_count}, FAKE: {fake_count})\n")
    md.append(f"| Metric | OLD (single-pass) | NEW (fused multi-patch) |")
    md.append(f"|---|---|---|")
    md.append(f"| **Accuracy** | {old_corr/max(n,1)*100:.1f}% | {new_corr/max(n,1)*100:.1f}% |")
    md.append(f"| Fixed | — | {fixed} |")
    md.append(f"| Regressed | — | {regressed} |")
    
    with open("/app/tests/benchmark_100_fused_report.md", "w") as f:
        f.write("\n".join(md))

    print("\nDone. Saved Markdown report.")

if __name__=="__main__":
    main()
