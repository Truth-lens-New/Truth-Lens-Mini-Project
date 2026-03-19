"""
Senior ML Engineer — B3 Triple Model Evaluation (No B0)
Compares: B3 Upload1, B3 Production, B3 OpenFake-Trained
"""
import torch, timm, requests, io, time, json, urllib3
from torchvision import transforms
from PIL import Image
urllib3.disable_warnings()

def load_model(name, path, input_size=300):
    device = torch.device('cpu')
    model = timm.create_model('efficientnet_b3', pretrained=False, num_classes=2)
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    info = {}
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
        info = {k: checkpoint.get(k) for k in ['epoch','val_acc','train_acc','f1_score','val_loss'] if k in checkpoint}
    else:
        model.load_state_dict(checkpoint)
    model.eval()
    tfm = transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    return model, tfm, info

def fetch(url):
    for _ in range(3):
        try:
            r = requests.get(url, headers={'User-Agent':'MLEval/3.0'}, timeout=8, verify=False)
            if r.status_code == 200 and len(r.content) > 1000:
                return Image.open(io.BytesIO(r.content)).convert('RGB')
        except: pass
        time.sleep(0.5)
    return None

DATASET = [
    # Real Portraits (5)
    {"url":"https://picsum.photos/id/1005/400/400","label":"REAL","cat":"Real Portrait"},
    {"url":"https://picsum.photos/id/1012/400/400","label":"REAL","cat":"Real Portrait"},
    {"url":"https://picsum.photos/id/1027/400/400","label":"REAL","cat":"Real Portrait"},
    {"url":"https://picsum.photos/id/1011/400/400","label":"REAL","cat":"Real Portrait"},
    {"url":"https://picsum.photos/id/64/400/400",  "label":"REAL","cat":"Real Portrait"},
    # Real Nature (5)
    {"url":"https://picsum.photos/id/10/400/400",  "label":"REAL","cat":"Real Nature"},
    {"url":"https://picsum.photos/id/15/400/400",  "label":"REAL","cat":"Real Nature"},
    {"url":"https://picsum.photos/id/29/400/400",  "label":"REAL","cat":"Real Nature"},
    {"url":"https://picsum.photos/id/100/400/400", "label":"REAL","cat":"Real Nature"},
    {"url":"https://picsum.photos/id/106/400/400", "label":"REAL","cat":"Real Nature"},
    # Real Objects (5)
    {"url":"https://picsum.photos/id/119/400/400", "label":"REAL","cat":"Real Objects"},
    {"url":"https://picsum.photos/id/160/400/400", "label":"REAL","cat":"Real Objects"},
    {"url":"https://picsum.photos/id/180/400/400", "label":"REAL","cat":"Real Objects"},
    {"url":"https://picsum.photos/id/201/400/400", "label":"REAL","cat":"Real Objects"},
    {"url":"https://picsum.photos/id/249/400/400", "label":"REAL","cat":"Real Objects"},
    # AI Faces (5)
    {"url":"https://thispersondoesnotexist.com/?v=100","label":"FAKE","cat":"AI Face"},
    {"url":"https://thispersondoesnotexist.com/?v=200","label":"FAKE","cat":"AI Face"},
    {"url":"https://thispersondoesnotexist.com/?v=300","label":"FAKE","cat":"AI Face"},
    {"url":"https://thispersondoesnotexist.com/?v=400","label":"FAKE","cat":"AI Face"},
    {"url":"https://thispersondoesnotexist.com/?v=500","label":"FAKE","cat":"AI Face"},
    # Edited Portraits (5)
    {"url":"https://upload.wikimedia.org/wikipedia/commons/8/8d/President_Barack_Obama.jpg","label":"FAKE","cat":"Edited Portrait"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/440px-Donald_Trump_official_portrait.jpg","label":"FAKE","cat":"Edited Portrait"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Official_portrait_of_Barack_Obama.jpg/440px-Official_portrait_of_Barack_Obama.jpg","label":"FAKE","cat":"Edited Portrait"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Elon_Musk_%28cropped%29.jpg/440px-Elon_Musk_%28cropped%29.jpg","label":"FAKE","cat":"Edited Portrait"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Narendra_Modi_2021.jpg/440px-Narendra_Modi_2021.jpg","label":"FAKE","cat":"Edited Portrait"},
    # Real Landmarks (5)
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Statue_of_Liberty%2C_NY.jpg/500px-Statue_of_Liberty%2C_NY.jpg","label":"REAL","cat":"Real Landmark"},
    {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Golden_Retriever_with_tennis_ball.jpg/500px-Golden_Retriever_with_tennis_ball.jpg","label":"REAL","cat":"Real Landmark"},
    {"url":"https://picsum.photos/id/365/400/400","label":"REAL","cat":"Real Landmark"},
    {"url":"https://picsum.photos/id/396/400/400","label":"REAL","cat":"Real Landmark"},
    {"url":"https://picsum.photos/id/429/400/400","label":"REAL","cat":"Real Landmark"},
]

def main():
    print("="*65)
    print("  B3 TRIPLE MODEL EVALUATION (Senior ML Engineer)")
    print("="*65)

    models_cfg = {
        "B3 (Upload1)":   ("models/efficientnet_b3_best.pth",),
        "B3 (Production)":("models/efficientnet_b3_production.pth",),
        "B3 (OpenFake)":  ("models/efficientnet_b3_openfake_best.pth",),
    }

    models = {}
    for name, (path,) in models_cfg.items():
        model, tfm, info = load_model(name, path)
        models[name] = (model, tfm)
        print(f"  {name}: {info if info else 'raw weights'}")

    data = {}
    for m in models:
        data[m] = {"correct_confs":[],"wrong_confs":[],"fake_prob_on_real":[],"fake_prob_on_fake":[],
                   "per_image":[],"TP":0,"FP":0,"TN":0,"FN":0}

    print(f"\nEvaluating {len(DATASET)} images...\n")
    for i, item in enumerate(DATASET):
        img = fetch(item["url"])
        if not img:
            print(f"  [{i+1:2d}] SKIP: {item['cat']}")
            continue
        truth_fake = item["label"] == "FAKE"
        for m_name, (model, tfm) in models.items():
            inp = tfm(img).unsqueeze(0)
            with torch.no_grad():
                probs = torch.softmax(model(inp), dim=1)
            real_p, fake_p = probs[0][0].item(), probs[0][1].item()
            pred_class = torch.argmax(probs, dim=1).item()
            verdict = "FAKE" if pred_class == 1 else "REAL"
            conf = probs[0][pred_class].item()
            correct = verdict == item["label"]
            d = data[m_name]
            (d["correct_confs"] if correct else d["wrong_confs"]).append(conf)
            (d["fake_prob_on_fake"] if truth_fake else d["fake_prob_on_real"]).append(fake_p)
            if truth_fake and verdict == "FAKE": d["TP"] += 1
            elif not truth_fake and verdict == "FAKE": d["FP"] += 1
            elif not truth_fake and verdict == "REAL": d["TN"] += 1
            elif truth_fake and verdict == "REAL": d["FN"] += 1
            d["per_image"].append({"cat":item["cat"],"truth":item["label"],"verdict":verdict,
                                   "conf":round(conf*100,1),"fake_p":round(fake_p*100,1),"correct":correct})
        print(f"  [{i+1:2d}/{len(DATASET)}] {item['cat']:18s} GT={item['label']}")

    print("\n" + "="*65)
    print("  RESULTS")
    print("="*65)

    for m_name in models:
        d = data[m_name]
        total = d["TP"]+d["FP"]+d["TN"]+d["FN"]
        acc = (d["TP"]+d["TN"])/total*100 if total else 0
        prec = d["TP"]/(d["TP"]+d["FP"])*100 if (d["TP"]+d["FP"]) else 0
        rec = d["TP"]/(d["TP"]+d["FN"])*100 if (d["TP"]+d["FN"]) else 0
        f1 = 2*prec*rec/(prec+rec) if (prec+rec) else 0
        avg_cc = sum(d["correct_confs"])/len(d["correct_confs"])*100 if d["correct_confs"] else 0
        avg_wc = sum(d["wrong_confs"])/len(d["wrong_confs"])*100 if d["wrong_confs"] else 0
        fp_real = sum(d["fake_prob_on_real"])/len(d["fake_prob_on_real"]) if d["fake_prob_on_real"] else 0
        fp_fake = sum(d["fake_prob_on_fake"])/len(d["fake_prob_on_fake"]) if d["fake_prob_on_fake"] else 0
        sep = fp_fake - fp_real
        oc = len([c for c in d["wrong_confs"] if c > 0.80])
        bias = (d["TP"]+d["FP"])/total if total else 0

        print(f"\n{'─'*65}")
        print(f"  {m_name}")
        print(f"{'─'*65}")
        print(f"  Accuracy:       {acc:6.1f}%  ({d['TP']+d['TN']}/{total})")
        print(f"  Precision:      {prec:6.1f}%")
        print(f"  Recall:         {rec:6.1f}%")
        print(f"  F1-Score:       {f1:6.1f}%")
        print(f"  Separation:     {sep:.3f}")
        print(f"  Conf (correct): {avg_cc:6.1f}%")
        print(f"  Conf (wrong):   {avg_wc:6.1f}%")
        print(f"  Conf Gap:       {avg_cc-avg_wc:6.1f}pp")
        print(f"  Overconf Errs:  {oc}/{len(d['wrong_confs'])}")
        print(f"  FAKE Bias:      {bias:.2f}")
        print(f"  Confusion:      TP={d['TP']} FP={d['FP']} TN={d['TN']} FN={d['FN']}")

        cats = {}
        for r in d["per_image"]:
            c = r["cat"]
            if c not in cats: cats[c] = {"ok":0,"n":0}
            cats[c]["n"] += 1
            if r["correct"]: cats[c]["ok"] += 1
        print(f"  Per-Category:")
        for cat, cr in cats.items():
            print(f"    {cat:20s}: {cr['ok']/cr['n']*100:5.1f}% ({cr['ok']}/{cr['n']})")

        wrongs = [r for r in d["per_image"] if not r["correct"]]
        if wrongs:
            print(f"  Errors ({len(wrongs)}):")
            for w in wrongs:
                print(f"    {w['cat']:20s} GT={w['truth']:4s} -> {w['verdict']:4s} ({w['conf']}%) fake_p={w['fake_p']}%")

if __name__ == "__main__":
    main()
