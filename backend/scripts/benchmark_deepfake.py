import torch
import timm
from torchvision import transforms
from PIL import Image
import requests
import io
import time
import urllib3

# Disable warnings for insecure requests just in case
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_model(name, path, is_b3=False):
    device = torch.device('cpu')
    arch = 'efficientnet_b3' if is_b3 else 'efficientnet_b0'
    model = timm.create_model(arch, pretrained=False, num_classes=2)
    
    try:
        checkpoint = torch.load(f"/app/{path}", map_location=device, weights_only=False)
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)
    except Exception as e:
        print(f"Failed to load {name}: {e}")
        return None, None
        
    model.eval()
    size = 300 if is_b3 else 224
    transform = transforms.Compose([
        transforms.Resize((size, size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    return model, transform

def get_image(url):
    headers = {'User-Agent': 'TruthLens-Benchmark/1.0'}
    for _ in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=5, verify=False)
            if r.status_code == 200:
                img = Image.open(io.BytesIO(r.content)).convert('RGB')
                return img
        except Exception:
            pass
        time.sleep(1)
    return None

def evaluate():
    print("="*60)
    print("DEEPFAKE MODEL ACCURACY BENCHMARK (FACES)")
    print("="*60)
    
    print("Loading models...")
    models = {
        "B0_Jan": load_model("B0_Jan", "models/best_effnetb0.pth", is_b3=False),
        "B3_Upload1": load_model("B3_Upload1", "models/efficientnet_b3_best.pth", is_b3=True),
        "B3_Production": load_model("B3_Production", "models/efficientnet_b3_production.pth", is_b3=True)
    }
    
    # Define dataset
    dataset = []
    
    # 10 Real faces from Picsum (Specific IDs that are human faces/people)
    real_ids = [1005, 1011, 1012, 1027, 22, 64, 65, 91, 129, 177]
    for i, pid in enumerate(real_ids):
        dataset.append({"url": f"https://picsum.photos/id/{pid}/400/400", "label": "REAL", "name": f"Real_Face_{i+1}"})
        
    # 10 Fake faces from ThisPersonDoesNotExist
    for i in range(10):
        # Appending timestamp to strictly bypass any caching
        dataset.append({"url": f"https://thispersondoesnotexist.com/?t={time.time()}_{i}", "label": "FAKE", "name": f"Fake_Face_{i+1}"})
    
    results = {
        "B0_Jan": {"correct": 0, "total": 0, "TP": 0, "FP": 0, "TN": 0, "FN": 0},
        "B3_Upload1": {"correct": 0, "total": 0, "TP": 0, "FP": 0, "TN": 0, "FN": 0},
        "B3_Production": {"correct": 0, "total": 0, "TP": 0, "FP": 0, "TN": 0, "FN": 0}
    }
    
    print(f"Testing {len(dataset)} images (10 REAL, 10 FAKE)...\n")
    
    for item in dataset:
        img = get_image(item['url'])
        if img is None:
            print(f"Failed to download {item['name']}. Skipping.")
            continue
            
        print(f"[{item['name']}] Ground Truth: {item['label']}")
            
        truth_is_fake = (item['label'] == "FAKE")
        
        for m_name, (model, transform) in models.items():
            if model is None: continue
            
            inp = transform(img).unsqueeze(0)
            with torch.no_grad():
                probs = torch.softmax(model(inp), dim=1)
                
            pred_class = torch.argmax(probs, dim=1).item()
            verdict = "FAKE" if pred_class == 1 else "REAL"
            predicted_fake = (verdict == "FAKE")
            
            # Metrics (Positive = FAKE)
            results[m_name]['total'] += 1
            if verdict == item['label']:
                results[m_name]['correct'] += 1
                
            if truth_is_fake and predicted_fake:
                results[m_name]['TP'] += 1
            elif not truth_is_fake and predicted_fake:
                results[m_name]['FP'] += 1
            elif not truth_is_fake and not predicted_fake:
                results[m_name]['TN'] += 1
            elif truth_is_fake and not predicted_fake:
                results[m_name]['FN'] += 1
                
            conf = probs[0][pred_class].item() * 100
            mark = "✅" if verdict == item['label'] else "❌"
            print(f"   {m_name:15}: {verdict} ({conf:5.1f}%) {mark}")
            
    print("\n" + "="*60)
    print("FINAL ACCURACY RESULTS")
    print("="*60)
    for m_name, metrics in results.items():
        if metrics['total'] == 0: continue
        acc = (metrics['correct'] / metrics['total']) * 100
        prec = (metrics['TP'] / (metrics['TP'] + metrics['FP'])) * 100 if (metrics['TP'] + metrics['FP']) > 0 else 0
        rec = (metrics['TP'] / (metrics['TP'] + metrics['FN'])) * 100 if (metrics['TP'] + metrics['FN']) > 0 else 0
        
        print(f"Model: {m_name}")
        print(f"  Accuracy:  {acc:.1f}% ({metrics['correct']}/{metrics['total']})")
        print(f"  Precision: {prec:.1f}% (When it says FAKE, how often is it right?)")
        print(f"  Recall:    {rec:.1f}% (Out of all FAKEs, how many did it catch?)")
        print(f"  Details:   TP:{metrics['TP']} FP:{metrics['FP']} TN:{metrics['TN']} FN:{metrics['FN']}")
        print("-"*60)

if __name__ == "__main__":
    evaluate()
