import torch
import timm
from torchvision import transforms
from PIL import Image
import requests
import io

def load_model(model_name, path, is_b3=False):
    device = torch.device('cpu')
    arch = 'efficientnet_b3' if is_b3 else 'efficientnet_b0'
    model = timm.create_model(arch, pretrained=False, num_classes=2)
    
    try:
        checkpoint = torch.load(path, map_location=device, weights_only=False)
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
            print(f"{model_name} loaded from checkpoint dict.")
        else:
            model.load_state_dict(checkpoint)
            print(f"{model_name} loaded cleanly.")
    except Exception as e:
        print(f"{model_name} load failed: {e}")
        
    model.eval()
    
    size = 300 if is_b3 else 224
    transform = transforms.Compose([
        transforms.Resize((size, size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    return model, transform

def evaluate():
    print("Loading models...")
    m_b0, t_b0 = load_model("B0_Old", "models/best_effnetb0.pth", is_b3=False)
    m_b3_1, t_b3_1 = load_model("B3_Upload1", "models/efficientnet_b3_best.pth", is_b3=True)
    m_b3_2, t_b3_2 = load_model("B3_Upload2", "models/efficientnet_b3_production.pth", is_b3=True)
    
    models = {
        "B0 (Jan)": (m_b0, t_b0),
        "B3 (Upload 1)": (m_b3_1, t_b3_1),
        "B3 (Upload 2)": (m_b3_2, t_b3_2)
    }
    
    test_urls = {
        "Statue of Liberty (Real)": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Statue_of_Liberty%2C_NY.jpg/500px-Statue_of_Liberty%2C_NY.jpg",
        "Golden Retriever (Real)": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Golden_Retriever_with_tennis_ball.jpg/500px-Golden_Retriever_with_tennis_ball.jpg",
        "Cat (Real)": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/500px-Cat_November_2010-1a.jpg",
        "Barack Obama (Heavily Edited Real)": "https://upload.wikimedia.org/wikipedia/commons/8/8d/President_Barack_Obama.jpg",
        "AI Midjourney Man (Fake)": "https://upload.wikimedia.org/wikipedia/commons/4/41/AI-generated_portrait_of_a_man_%28Midjourney%29.jpg"
    }
    
    print("\n" + "="*50)
    print("--- 3-Way Model Comparison ---")
    headers = {'User-Agent': 'TruthLens-Evaluator/1.0'}
    
    for name, url in test_urls.items():
        print(f"\nEvaluating: {name}")
        try:
            r = requests.get(url, headers=headers, timeout=10)
            img = Image.open(io.BytesIO(r.content)).convert('RGB')
            
            for mod_name, (model, transform) in models.items():
                inp = transform(img).unsqueeze(0)
                with torch.no_grad():
                    probs = torch.softmax(model(inp), dim=1)
                    
                pred_class = torch.argmax(probs, dim=1).item()
                verdict = "FAKE" if pred_class == 1 else "REAL"
                conf = probs[0][pred_class].item() * 100
                
                print(f"  [{mod_name}] -> {verdict} ({conf:.1f}%) | Real: {probs[0][0]*100:.1f}%, Fake: {probs[0][1]*100:.1f}%")
                
        except Exception as e:
            print(f"Error evaluating {name}: {e}")

if __name__ == "__main__":
    evaluate()
