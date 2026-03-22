"""
30-Image Before vs After Benchmark — Single-Pass vs Multi-Patch (FUSED)
=======================================================================
Uses the 30-image dataset from ml_evaluation.py.
Runs inside Docker.

OLD: standalone single forward pass on 300x300 resized image (mimics old behavior)
NEW: actual live DeepfakeDetector.predict() which now includes Weighted Score Fusion
     combining global CNN (65%) + Multi-Patch (25%) + Metadata (10%).
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

# ── Same 30-image dataset as ml_evaluation.py ─────────────────────────────────
DATASET = [
    # Category 1: Real Portraits (5)
    {"url":"https://picsum.photos/id/1005/400/400","label":"REAL","cat":"Real Portrait"},
    {"url":"https://picsum.photos/id/1012/400/400","label":"REAL","cat":"Real Portrait"},
    {"url":"https://picsum.photos/id/1027/400/400","label":"REAL","cat":"Real Portrait"},
    {"url":"https://picsum.photos/id/1011/400/400","label":"REAL","cat":"Real Portrait"},
    {"url":"https://picsum.photos/id/64/400/400",  "label":"REAL","cat":"Real Portrait"},
    # Category 2: Real Nature (5)
    {"url":"https://picsum.photos/id/10/400/400",  "label":"REAL","cat":"Real Nature"},
    {"url":"https://picsum.photos/id/15/400/400",  "label":"REAL","cat":"Real Nature"},
    {"url":"https://picsum.photos/id/29/400/400",  "label":"REAL","cat":"Real Nature"},
    {"url":"https://picsum.photos/id/100/400/400", "label":"REAL","cat":"Real Nature"},
    {"url":"https://picsum.photos/id/106/400/400", "label":"REAL","cat":"Real Nature"},
    # Category 3: Real Objects / Architecture (5)
    {"url":"https://picsum.photos/id/119/400/400", "label":"REAL","cat":"Real Objects"},
    {"url":"https://picsum.photos/id/160/400/400", "label":"REAL","cat":"Real Objects"},
    {"url":"https://picsum.photos/id/180/400/400", "label":"REAL","cat":"Real Objects"},
    {"url":"https://picsum.photos/id/201/400/400", "label":"REAL","cat":"Real Objects"},
    {"url":"https://picsum.photos/id/249/400/400", "label":"REAL","cat":"Real Objects"},
    # Category 4: AI Faces — thispersondoesnotexist (5)
    {"url":"https://thispersondoesnotexist.com/?v=1","label":"FAKE","cat":"AI Face"},
    {"url":"https://thispersondoesnotexist.com/?v=2","label":"FAKE","cat":"AI Face"},
    {"url":"https://thispersondoesnotexist.com/?v=3","label":"FAKE","cat":"AI Face"},
    {"url":"https://thispersondoesnotexist.com/?v=4","label":"FAKE","cat":"AI Face"},
    {"url":"https://thispersondoesnotexist.com/?v=5","label":"FAKE","cat":"AI Face"},
    # Category 5: Heavily Edited Official Portraits (5) — labeled FAKE in original eval
    {"url":"https://upload.wikimedia.org/wikipedia/commons/8/8d/President_Barack_Obama.jpg","label":"FAKE","cat":"Edited Portrait"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/440px-Donald_Trump_official_portrait.jpg","label":"FAKE","cat":"Edited Portrait"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Official_portrait_of_Barack_Obama.jpg/440px-Official_portrait_of_Barack_Obama.jpg","label":"FAKE","cat":"Edited Portrait"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Elon_Musk_%28cropped%29.jpg/440px-Elon_Musk_%28cropped%29.jpg","label":"FAKE","cat":"Edited Portrait"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Narendra_Modi_2021.jpg/440px-Narendra_Modi_2021.jpg","label":"FAKE","cat":"Edited Portrait"},
    # Category 6: Real Landmarks & Animals (5)
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Statue_of_Liberty%2C_NY.jpg/500px-Statue_of_Liberty%2C_NY.jpg","label":"REAL","cat":"Real Landmark"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Empire_state_building.jpg/400px-Empire_state_building.jpg","label":"REAL","cat":"Real Landmark"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Sydney_Australia._%2821339175489%29.jpg/500px-Sydney_Australia._%2821339175489%29.jpg","label":"REAL","cat":"Real Landmark"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Image_created_with_a_mobile_phone.png/440px-Image_created_with_a_mobile_phone.png","label":"REAL","cat":"Real Landmark"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Golden_Retriever_with_tennis_ball.jpg/500px-Golden_Retriever_with_tennis_ball.jpg","label":"REAL","cat":"Real Landmark"},
]

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
    return {"verdict":"FAKE" if fp>=0.5 else "REAL",
            "fake_prob":round(fp*100,1),
            "lat_ms":round(lat*1000)}

def fetch(url):
    try:
        r=requests.get(url,headers={"User-Agent":"TruthLens/2.0"},timeout=12,verify=False)
        if r.status_code==200 and len(r.content)>1000: return r.content
    except: pass
    return None

def main():
    print("="*80)
    print("  30-Image Benchmark: Single-Pass vs Multi-Patch (WITH FUSION)")
    print("="*80)

    print("\n[1] Initializing API DeepfakeDetector (with Fusion)...")
    detector = get_deepfake_detector()
    
    print("[2] Loading raw OLD model reference...")
    old_model, old_dev = load_old_model()
    print("    OK")

    rows=[]
    cats={}

    print(f"\n[3] Running {len(DATASET)} images...\n")
    print(f"  {'#':>3}  {'Category':<20} {'GT':<5} {'OLD':<6} {'OLD%':>6} {'NEW (FUSED)':<15} {'Patches':>10}")
    print("  "+"-"*90)

    for i,item in enumerate(DATASET,1):
        img_bytes = fetch(item["url"])
        if img_bytes is None:
            rows.append({**item,"skipped":True})
            print(f"  {i:3d}  {item['cat']:<20} {item['label']:<5}  SKIPPED")
            continue

        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        
        # OLD
        old = single_pass(old_model, old_dev, img)
        
        # NEW
        t0 = time.time()
        new_res = detector.predict(img_bytes)
        lat = time.time() - t0
        
        pa = new_res.get("patch_analysis") or {}
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

        cat = item["cat"]
        if cat not in cats:
            cats[cat]={"old_ok":0,"new_ok":0,"total":0}
        cats[cat]["total"]+=1
        if old_ok: cats[cat]["old_ok"]+=1
        if new_ok: cats[cat]["new_ok"]+=1

        patch_info=f"{new['susp']}/{new['n']} susp"
        print(f"  {i:3d}  {cat:<20} {item['label']:<5}  {old['verdict']:<6} {old['fake_prob']:>5}%  {new['verdict']:<6} {new['fake_prob']:>5}%  {patch_info:>12}  {change}")
        rows.append({**item,"old":old,"new":new,"skipped":False})

    # Stats
    tested=[r for r in rows if not r.get("skipped")]
    n=len(tested)
    old_corr=sum(1 for r in tested if r["old"]["verdict"]==r["label"])
    new_corr=sum(1 for r in tested if r["new"]["verdict"]==r["label"])
    fixed   =sum(1 for r in tested if r["old"]["verdict"]!=r["label"] and r["new"]["verdict"]==r["label"])
    regressed=sum(1 for r in tested if r["old"]["verdict"]==r["label"] and r["new"]["verdict"]!=r["label"])

    print("\n"+"="*80)
    print(f"  OVERALL  OLD: {old_corr}/{n} = {old_corr/max(n,1)*100:.1f}%   NEW: {new_corr}/{n} = {new_corr/max(n,1)*100:.1f}%   Delta: {(new_corr-old_corr)/max(n,1)*100:+.1f}%")
    print(f"           Fixed: {fixed}   Regressed: {regressed}")
    print("="*80)
    
    # Save a quick JSON
    with open("/app/tests/benchmark_30_fused_results.json", "w") as f:
        json.dump({"cats": cats, "overall": {"old_acc": old_corr/max(n,1)*100, "new_acc": new_corr/max(n,1)*100, "fixed": fixed, "regressed": regressed}}, f)
    print("\nDone. Saved JSON results.")

if __name__=="__main__":
    main()
