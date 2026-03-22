"""
30-Image Before vs After Benchmark — Single-Pass vs Multi-Patch
===============================================================
Uses the exact same 30-image dataset from ml_evaluation.py.
Runs inside Docker where torch/model are available.

OLD: single forward pass on 300x300 resized image
NEW: single pass + multi-patch (overlapping 300x300 crops, 50% stride, max 16 patches)
     verdict = majority vote across patches
"""
import sys, os, io, time, json, requests
sys.path.insert(0, "/app")

import torch, timm
from torchvision import transforms
from PIL import Image
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

# ── Model ─────────────────────────────────────────────────────────────────────
def load_model():
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

def infer(model, dev, t):
    with torch.no_grad():
        return torch.softmax(model(t.to(dev)), dim=1)

def single_pass(model, dev, img: Image.Image):
    t0 = time.time()
    probs = infer(model, dev, TFM(img).unsqueeze(0))
    lat = time.time()-t0
    fp = probs[0][1].item()
    return {"verdict":"FAKE" if fp>=0.5 else "REAL",
            "fake_prob":round(fp*100,1),
            "conf":round(max(fp,1-fp)*100,1),
            "lat_ms":round(lat*1000)}

def multi_patch(model, dev, img: Image.Image):
    w,h = img.size
    patch_size,stride = 300, 150
    t0 = time.time()

    if w<350 or h<350:
        probs = infer(model, dev, TFM(img).unsqueeze(0))
        fp = probs[0][1].item(); lat=time.time()-t0
        return {"verdict":"FAKE" if fp>=0.5 else "REAL",
                "fake_prob":round(fp*100,1),"conf":round(max(fp,1-fp)*100,1),
                "n":1,"susp":int(fp>=0.5),"max_fp":round(fp*100,1),"lat_ms":round(lat*1000)}

    coords=[(x,y) for y in range(0,h-patch_size+1,stride)
                   for x in range(0,w-patch_size+1,stride)][:16]
    fps=[]
    for x,y in coords:
        crop=img.crop((x,y,x+patch_size,y+patch_size))
        probs=infer(model,dev,TFM(crop).unsqueeze(0))
        fps.append(probs[0][1].item())

    lat=time.time()-t0
    n_fake=sum(1 for p in fps if p>=0.5)
    max_fp=max(fps); avg_fp=sum(fps)/len(fps)
    verdict="FAKE" if n_fake>len(fps)//2 else "REAL"
    return {"verdict":verdict,"fake_prob":round(avg_fp*100,1),
            "conf":round((max_fp if verdict=="FAKE" else 1-avg_fp)*100,1),
            "n":len(fps),"susp":n_fake,"max_fp":round(max_fp*100,1),"lat_ms":round(lat*1000)}

def fetch(url):
    try:
        r=requests.get(url,headers={"User-Agent":"TruthLens/2.0"},timeout=12,verify=False)
        if r.status_code==200 and len(r.content)>1000: return r.content
    except: pass
    return None

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("="*70)
    print("  30-Image Before vs After Benchmark: Single-Pass vs Multi-Patch")
    print("="*70)

    print("\n[1] Loading EfficientNet-B3...")
    model,dev = load_model()
    print("    OK")

    rows=[]
    cats={}

    print(f"\n[2] Running {len(DATASET)} images...\n")
    print(f"  {'#':>3}  {'Category':<20} {'GT':<5} {'OLD':<6} {'OLD%':>6} {'NEW':<6} {'NEW%':>6}  {'Patches':>10}  {'Result'}")
    print("  "+"-"*80)

    for i,item in enumerate(DATASET,1):
        img_bytes = fetch(item["url"])
        if img_bytes is None:
            rows.append({**item,"skipped":True})
            print(f"  {i:3d}  {item['cat']:<20} {item['label']:<5}  SKIPPED")
            continue

        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        old = single_pass(model,dev,img)
        new = multi_patch(model,dev,img)

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

    # ── Stats per category ────────────────────────────────────────────────────
    tested=[r for r in rows if not r.get("skipped")]
    n=len(tested)
    old_corr=sum(1 for r in tested if r["old"]["verdict"]==r["label"])
    new_corr=sum(1 for r in tested if r["new"]["verdict"]==r["label"])
    fixed   =sum(1 for r in tested if r["old"]["verdict"]!=r["label"] and r["new"]["verdict"]==r["label"])
    regressed=sum(1 for r in tested if r["old"]["verdict"]==r["label"] and r["new"]["verdict"]!=r["label"])
    avg_old_lat=sum(r["old"]["lat_ms"] for r in tested)/max(n,1)
    avg_new_lat=sum(r["new"]["lat_ms"] for r in tested)/max(n,1)

    print("\n"+"="*70)
    print(f"  OVERALL  OLD: {old_corr}/{n} = {old_corr/max(n,1)*100:.1f}%   NEW: {new_corr}/{n} = {new_corr/max(n,1)*100:.1f}%   Delta: {(new_corr-old_corr)/max(n,1)*100:+.1f}%")
    print(f"           Fixed: {fixed}   Regressed: {regressed}   Avg latency OLD={avg_old_lat:.0f}ms NEW={avg_new_lat:.0f}ms")
    print("="*70)
    print("\n  Per-Category:")
    for cat,c in cats.items():
        print(f"    {cat:<20}  OLD={c['old_ok']}/{c['total']} ({c['old_ok']/c['total']*100:.0f}%)  NEW={c['new_ok']}/{c['total']} ({c['new_ok']/c['total']*100:.0f}%)")

    # ── Markdown report ───────────────────────────────────────────────────────
    md=[]
    md.append("# 30-Image Multi-Patch Before vs After Report\n")
    md.append(f"**Date:** 2026-03-22  |  **Model:** EfficientNet-B3  |  **Images tested:** {n}\n")
    md.append("## Setup\n")
    md.append("| | OLD | NEW |\n|---|---|---|")
    md.append("| Inference | Single forward pass 300×300 | + Overlapping 300×300 patches (50% stride, max 16) |")
    md.append("| Verdict | CNN softmax | Majority vote across patches |\n")

    md.append("## Results by Category\n")
    md.append("| Category | GT | OLD Acc | NEW Acc | Delta |")
    md.append("|----------|----|---------|---------| ------|")
    for cat,c in cats.items():
        gt="REAL" if "real" in cat.lower() or "landmark" in cat.lower() else "FAKE"
        old_a=c["old_ok"]/c["total"]*100; new_a=c["new_ok"]/c["total"]*100
        md.append(f"| {cat} | {gt} | {old_a:.0f}% ({c['old_ok']}/{c['total']}) | {new_a:.0f}% ({c['new_ok']}/{c['total']}) | {new_a-old_a:+.0f}% |")

    md.append("\n## Per-Image Detail\n")
    md.append("| # | Category | GT | OLD | OLD% | NEW | NEW% | Patches | Change |")
    md.append("|---|----------|-----|-----|------|-----|------|---------|--------|")
    for i,r in enumerate([r for r in rows if not r.get("skipped")],1):
        old=r["old"]; new=r["new"]
        old_ok=old["verdict"]==r["label"]; new_ok=new["verdict"]==r["label"]
        chg="FIXED" if not old_ok and new_ok else ("REGRESSED" if old_ok and not new_ok else "Same")
        md.append(f"| {i} | {r['cat']} | {r['label']} | {old['verdict']} | {old['fake_prob']}% | {new['verdict']} | {new['fake_prob']}% | {new['susp']}/{new['n']} | {chg} |")

    md.append(f"\n## Overall Summary\n")
    md.append(f"| Metric | OLD (single-pass) | NEW (+ multi-patch) |")
    md.append(f"|--------|-------------------|---------------------|")
    md.append(f"| **Accuracy** | **{old_corr/max(n,1)*100:.1f}%** ({old_corr}/{n}) | **{new_corr/max(n,1)*100:.1f}%** ({new_corr}/{n}) |")
    md.append(f"| Delta | — | **{(new_corr-old_corr)/max(n,1)*100:+.1f}%** |")
    md.append(f"| Cases Fixed | — | {fixed} |")
    md.append(f"| Regressions | — | {regressed} |")
    md.append(f"| Avg Latency | {avg_old_lat:.0f}ms | {avg_new_lat:.0f}ms |")

    # TP/FP/TN/FN
    old_tp=sum(1 for r in tested if r["label"]=="FAKE" and r["old"]["verdict"]=="FAKE")
    old_tn=sum(1 for r in tested if r["label"]=="REAL" and r["old"]["verdict"]=="REAL")
    old_fp=sum(1 for r in tested if r["label"]=="REAL" and r["old"]["verdict"]=="FAKE")
    old_fn=sum(1 for r in tested if r["label"]=="FAKE" and r["old"]["verdict"]=="REAL")
    new_tp=sum(1 for r in tested if r["label"]=="FAKE" and r["new"]["verdict"]=="FAKE")
    new_tn=sum(1 for r in tested if r["label"]=="REAL" and r["new"]["verdict"]=="REAL")
    new_fp=sum(1 for r in tested if r["label"]=="REAL" and r["new"]["verdict"]=="FAKE")
    new_fn=sum(1 for r in tested if r["label"]=="FAKE" and r["new"]["verdict"]=="REAL")
    old_prec=old_tp/(old_tp+old_fp)*100 if (old_tp+old_fp)>0 else 0
    old_rec =old_tp/(old_tp+old_fn)*100 if (old_tp+old_fn)>0 else 0
    new_prec=new_tp/(new_tp+new_fp)*100 if (new_tp+new_fp)>0 else 0
    new_rec =new_tp/(new_tp+new_fn)*100 if (new_tp+new_fn)>0 else 0
    old_f1 =2*old_prec*old_rec/(old_prec+old_rec) if (old_prec+old_rec)>0 else 0
    new_f1 =2*new_prec*new_rec/(new_prec+new_rec) if (new_prec+new_rec)>0 else 0

    md.append(f"| Precision | {old_prec:.1f}% | {new_prec:.1f}% |")
    md.append(f"| Recall | {old_rec:.1f}% | {new_rec:.1f}% |")
    md.append(f"| F1 Score | {old_f1:.1f}% | {new_f1:.1f}% |")
    md.append(f"| TP/FP/TN/FN | {old_tp}/{old_fp}/{old_tn}/{old_fn} | {new_tp}/{new_fp}/{new_tn}/{new_fn} |")

    rpt="/app/tests/benchmark_30_report.md"
    with open(rpt,"w") as f: f.write("\n".join(md))
    print(f"\n  Report saved: {rpt}")

if __name__=="__main__":
    main()
