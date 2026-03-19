import torch
path = 'models/efficientnet_b3_production.pth'
ckpt = torch.load(path, map_location='cpu', weights_only=False)
if isinstance(ckpt, dict) and 'model_state_dict' in ckpt:
    # Keep only the essential weights and metadata
    shrunk = {
        'model_state_dict': ckpt['model_state_dict'],
        'epoch': ckpt.get('epoch', 0),
        'val_acc': ckpt.get('val_acc', 0)
    }
    torch.save(shrunk, path)
    print("Shrunk model saved successfully.")
else:
    print("Model already raw or unknown format.")
