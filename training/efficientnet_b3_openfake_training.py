# =============================================================================
# EfficientNet-B3 Deepfake Detection Training on OpenFake Dataset
# Google Colab Notebook (Optimized for 12GB RAM)
# =============================================================================
# Copy each cell (marked with # %% [markdown] or # %%) into Google Colab

# %% [markdown]
"""
# 🎯 EfficientNet-B3 Deepfake Detection Training

**Dataset:** OpenFake (ComplexDataLab/OpenFake)  
**Model:** EfficientNet-B3 (ImageNet pretrained, auto-downloaded via `timm`)  
**Target:** Binary classification (REAL vs FAKE)  
**RAM Optimized:** 12GB limit

> ⚡ **No manual download needed!** The pretrained weights are automatically downloaded when you run `timm.create_model('efficientnet_b3', pretrained=True)`

---
"""

# %% [markdown]
"""
## Cell 1: Install Dependencies
"""

# %%
# Install required packages
!pip install -q torch torchvision timm datasets albumentations pillow tqdm wandb

# Check GPU availability
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

# %% [markdown]
"""
## Cell 2: Import Libraries
"""

# %%
import os
import gc
import numpy as np
from PIL import Image
from tqdm.auto import tqdm
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.cuda.amp import autocast, GradScaler  # Mixed precision for memory

import timm
from datasets import load_dataset
import albumentations as A
from albumentations.pytorch import ToTensorV2

# Memory management
def clear_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

clear_memory()

# %% [markdown]
"""
## Cell 3: Configuration
"""

# %%
class Config:
    # Model
    model_name = 'efficientnet_b3'
    num_classes = 2
    pretrained = True
    
    # Training
    batch_size = 16  # Reduced for 12GB RAM
    accumulation_steps = 2  # Effective batch size = 16 * 2 = 32
    epochs = 10
    learning_rate = 1e-4
    weight_decay = 1e-5
    
    # Data
    image_size = 300  # EfficientNet-B3 native size
    num_workers = 2  # Reduced for Colab
    
    # Paths
    output_dir = '/content/drive/MyDrive/truthlens_models'
    model_save_name = 'efficientnet_b3_openfake.pth'
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Mixed Precision (saves memory)
    use_amp = True
    
    # Subset for testing (set to None for full dataset)
    max_train_samples = None  # Set to 5000 for quick test
    max_val_samples = None    # Set to 1000 for quick test

config = Config()
print(f"Device: {config.device}")
print(f"Batch size: {config.batch_size} x {config.accumulation_steps} = {config.batch_size * config.accumulation_steps}")

# %% [markdown]
"""
## Cell 4: Mount Google Drive (for saving model)
"""

# %%
from google.colab import drive
drive.mount('/content/drive')

# Create output directory
os.makedirs(config.output_dir, exist_ok=True)
print(f"Models will be saved to: {config.output_dir}")

# %% [markdown]
"""
## Cell 5: Load OpenFake Dataset (Memory Efficient)
"""

# %%
print("Loading OpenFake dataset...")
print("⚠️ This may take a few minutes on first run (downloading)")

# Load dataset with streaming to save memory
dataset = load_dataset(
    "ComplexDataLab/OpenFake",
    streaming=False,  # We need to iterate multiple times
    trust_remote_code=True
)

print(f"\nDataset loaded!")
print(f"Train samples: {len(dataset['train'])}")
print(f"Test samples: {len(dataset['test'])}")

# Check label distribution
train_labels = [sample['label'] for sample in dataset['train']]
print(f"\nTrain label distribution:")
print(f"  Real: {train_labels.count('real')}")
print(f"  Fake: {train_labels.count('fake')}")

clear_memory()

# %% [markdown]
"""
## Cell 6: Data Augmentation & Transforms
"""

# %%
# Training augmentations (strong)
train_transform = A.Compose([
    A.RandomResizedCrop(config.image_size, config.image_size, scale=(0.8, 1.0)),
    A.HorizontalFlip(p=0.5),
    A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.3),
    A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=20, p=0.3),
    A.GaussianBlur(blur_limit=(3, 5), p=0.2),
    A.GaussNoise(var_limit=(10, 50), p=0.2),
    A.ImageCompression(quality_lower=60, quality_upper=100, p=0.3),  # Simulate JPEG
    A.CoarseDropout(max_holes=8, max_height=16, max_width=16, p=0.2),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2()
])

# Validation transforms (no augmentation)
val_transform = A.Compose([
    A.Resize(config.image_size, config.image_size),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2()
])

print("Transforms defined!")

# %% [markdown]
"""
## Cell 7: Custom Dataset Class (Memory Efficient)
"""

# %%
class OpenFakeDataset(Dataset):
    """
    Memory-efficient dataset that loads images on-demand.
    """
    def __init__(self, hf_dataset, transform=None, max_samples=None):
        self.dataset = hf_dataset
        self.transform = transform
        self.max_samples = max_samples
        
        # Label mapping
        self.label_map = {'real': 0, 'fake': 1}
        
        # Pre-compute length
        self.length = min(len(self.dataset), max_samples) if max_samples else len(self.dataset)
    
    def __len__(self):
        return self.length
    
    def __getitem__(self, idx):
        try:
            sample = self.dataset[idx]
            
            # Load image
            image = sample['image']
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            image = np.array(image)
            
            # Apply transforms
            if self.transform:
                transformed = self.transform(image=image)
                image = transformed['image']
            
            # Get label
            label = self.label_map[sample['label']]
            
            return image, label
            
        except Exception as e:
            print(f"Error loading sample {idx}: {e}")
            # Return a dummy sample on error
            dummy_image = torch.zeros(3, config.image_size, config.image_size)
            return dummy_image, 0

# Create datasets
print("Creating PyTorch datasets...")
train_dataset = OpenFakeDataset(
    dataset['train'], 
    transform=train_transform,
    max_samples=config.max_train_samples
)
val_dataset = OpenFakeDataset(
    dataset['test'], 
    transform=val_transform,
    max_samples=config.max_val_samples
)

print(f"Train dataset: {len(train_dataset)} samples")
print(f"Val dataset: {len(val_dataset)} samples")

# %% [markdown]
"""
## Cell 8: Create DataLoaders
"""

# %%
# DataLoaders with memory optimization
train_loader = DataLoader(
    train_dataset,
    batch_size=config.batch_size,
    shuffle=True,
    num_workers=config.num_workers,
    pin_memory=True,
    drop_last=True,
    prefetch_factor=2  # Reduce prefetching to save memory
)

val_loader = DataLoader(
    val_dataset,
    batch_size=config.batch_size,
    shuffle=False,
    num_workers=config.num_workers,
    pin_memory=True,
    prefetch_factor=2
)

print(f"Train batches: {len(train_loader)}")
print(f"Val batches: {len(val_loader)}")

# %% [markdown]
"""
## Cell 9: Build EfficientNet-B3 Model
"""

# %%
class DeepfakeDetector(nn.Module):
    """
    EfficientNet-B3 for Deepfake Detection.
    
    The pretrained ImageNet weights are AUTOMATICALLY DOWNLOADED by timm.
    No manual download required - just run the code!
    
    timm downloads from: https://github.com/huggingface/pytorch-image-models
    """
    def __init__(self, model_name='efficientnet_b3', num_classes=2, pretrained=True):
        super().__init__()
        
        # =====================================================
        # Load pretrained EfficientNet-B3 (AUTO-DOWNLOADED)
        # This downloads ~48MB of weights from HuggingFace/timm
        # =====================================================
        print(f"Loading {model_name} with pretrained={pretrained}...")
        print("(Weights will be auto-downloaded on first run)")
        
        self.model = timm.create_model(
            model_name,
            pretrained=pretrained,
            num_classes=num_classes  # Replaces final layer for 2-class output
        )
        
        # Freeze early layers to save memory and speed up training
        self._freeze_early_layers()
        
        print(f"Model loaded! Classifier output: {num_classes} classes")
    
    def _freeze_early_layers(self):
        """Freeze first 5 blocks to save memory and speed up training."""
        # Freeze stem
        for param in self.model.conv_stem.parameters():
            param.requires_grad = False
        for param in self.model.bn1.parameters():
            param.requires_grad = False
        
        # Freeze first 5 blocks (out of 7)
        for i, block in enumerate(self.model.blocks):
            if i < 5:
                for param in block.parameters():
                    param.requires_grad = False
    
    def forward(self, x):
        return self.model(x)

# Create model
model = DeepfakeDetector(
    model_name=config.model_name,
    num_classes=config.num_classes,
    pretrained=config.pretrained
)
model = model.to(config.device)

# Count parameters
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Total parameters: {total_params:,}")
print(f"Trainable parameters: {trainable_params:,} ({100*trainable_params/total_params:.1f}%)")

clear_memory()

# %% [markdown]
"""
## Cell 10: Loss, Optimizer, Scheduler
"""

# %%
# Loss function
criterion = nn.CrossEntropyLoss()

# Optimizer (only trainable params)
optimizer = optim.AdamW(
    filter(lambda p: p.requires_grad, model.parameters()),
    lr=config.learning_rate,
    weight_decay=config.weight_decay
)

# Learning rate scheduler
scheduler = optim.lr_scheduler.CosineAnnealingLR(
    optimizer,
    T_max=config.epochs * len(train_loader),
    eta_min=1e-6
)

# Mixed precision scaler
scaler = GradScaler() if config.use_amp else None

print("Optimizer and scheduler configured!")
print(f"Learning rate: {config.learning_rate}")
print(f"Mixed precision: {config.use_amp}")

# %% [markdown]
"""
## Cell 11: Training Functions
"""

# %%
def train_epoch(model, loader, criterion, optimizer, scheduler, scaler, device, accumulation_steps):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    optimizer.zero_grad()
    
    pbar = tqdm(loader, desc="Training", leave=False)
    for batch_idx, (images, labels) in enumerate(pbar):
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        
        # Mixed precision forward pass
        with autocast(enabled=scaler is not None):
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss = loss / accumulation_steps  # Scale loss for accumulation
        
        # Backward pass
        if scaler is not None:
            scaler.scale(loss).backward()
        else:
            loss.backward()
        
        # Gradient accumulation
        if (batch_idx + 1) % accumulation_steps == 0:
            if scaler is not None:
                scaler.step(optimizer)
                scaler.update()
            else:
                optimizer.step()
            optimizer.zero_grad()
            scheduler.step()
        
        # Statistics
        running_loss += loss.item() * accumulation_steps
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        # Update progress bar
        pbar.set_postfix({
            'loss': running_loss / (batch_idx + 1),
            'acc': 100. * correct / total,
            'lr': scheduler.get_last_lr()[0]
        })
    
    return running_loss / len(loader), 100. * correct / total


def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        pbar = tqdm(loader, desc="Validating", leave=False)
        for images, labels in pbar:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            
            with autocast(enabled=config.use_amp):
                outputs = model(images)
                loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
            pbar.set_postfix({
                'loss': running_loss / (pbar.n + 1),
                'acc': 100. * correct / total
            })
    
    return running_loss / len(loader), 100. * correct / total, all_preds, all_labels

# %% [markdown]
"""
## Cell 12: Training Loop 🚀
"""

# %%
print("=" * 60)
print("🚀 Starting Training")
print("=" * 60)

best_val_acc = 0.0
history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}

for epoch in range(config.epochs):
    print(f"\nEpoch {epoch+1}/{config.epochs}")
    print("-" * 40)
    
    # Train
    train_loss, train_acc = train_epoch(
        model, train_loader, criterion, optimizer, scheduler, scaler,
        config.device, config.accumulation_steps
    )
    
    # Validate
    val_loss, val_acc, val_preds, val_labels = validate(
        model, val_loader, criterion, config.device
    )
    
    # Log
    print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
    print(f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
    
    # Save history
    history['train_loss'].append(train_loss)
    history['train_acc'].append(train_acc)
    history['val_loss'].append(val_loss)
    history['val_acc'].append(val_acc)
    
    # Save best model
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        save_path = os.path.join(config.output_dir, config.model_save_name)
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'val_acc': val_acc,
            'config': {
                'model_name': config.model_name,
                'image_size': config.image_size,
                'num_classes': config.num_classes
            }
        }, save_path)
        print(f"✅ Best model saved! Val Acc: {val_acc:.2f}%")
    
    # Clear memory after each epoch
    clear_memory()

print("\n" + "=" * 60)
print(f"🎉 Training Complete! Best Val Acc: {best_val_acc:.2f}%")
print("=" * 60)

# %% [markdown]
"""
## Cell 13: Plot Training History
"""

# %%
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Loss plot
axes[0].plot(history['train_loss'], label='Train Loss', marker='o')
axes[0].plot(history['val_loss'], label='Val Loss', marker='o')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Loss')
axes[0].set_title('Training vs Validation Loss')
axes[0].legend()
axes[0].grid(True)

# Accuracy plot
axes[1].plot(history['train_acc'], label='Train Acc', marker='o')
axes[1].plot(history['val_acc'], label='Val Acc', marker='o')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Accuracy (%)')
axes[1].set_title('Training vs Validation Accuracy')
axes[1].legend()
axes[1].grid(True)

plt.tight_layout()
plt.savefig(os.path.join(config.output_dir, 'training_history.png'), dpi=150)
plt.show()

# %% [markdown]
"""
## Cell 14: Evaluation Metrics
"""

# %%
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns

# Load best model
best_model_path = os.path.join(config.output_dir, config.model_save_name)
checkpoint = torch.load(best_model_path)
model.load_state_dict(checkpoint['model_state_dict'])

# Final evaluation
val_loss, val_acc, val_preds, val_labels = validate(model, val_loader, criterion, config.device)

# Classification report
print("\n📊 Classification Report:")
print(classification_report(val_labels, val_preds, target_names=['REAL', 'FAKE']))

# Confusion matrix
cm = confusion_matrix(val_labels, val_preds)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['REAL', 'FAKE'], yticklabels=['REAL', 'FAKE'])
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title(f'Confusion Matrix (Acc: {val_acc:.2f}%)')
plt.savefig(os.path.join(config.output_dir, 'confusion_matrix.png'), dpi=150)
plt.show()

# %% [markdown]
"""
## Cell 15: Export Model for TruthLens
"""

# %%
# Export just the model weights (smaller file)
export_path = os.path.join(config.output_dir, 'efficientnet_b3_deepfake_weights.pth')
torch.save(model.state_dict(), export_path)
print(f"Model weights exported to: {export_path}")

# Also save the full checkpoint
full_path = os.path.join(config.output_dir, 'efficientnet_b3_deepfake_full.pth')
torch.save({
    'model_state_dict': model.state_dict(),
    'model_name': config.model_name,
    'image_size': config.image_size,
    'num_classes': config.num_classes,
    'val_accuracy': best_val_acc,
    'training_date': datetime.now().isoformat()
}, full_path)
print(f"Full checkpoint saved to: {full_path}")

# File sizes
import os
weights_size = os.path.getsize(export_path) / (1024 * 1024)
full_size = os.path.getsize(full_path) / (1024 * 1024)
print(f"\nWeights file size: {weights_size:.2f} MB")
print(f"Full checkpoint size: {full_size:.2f} MB")

# %% [markdown]
"""
## Cell 16: Download Model to Local Machine
"""

# %%
from google.colab import files

# Download the weights file
print("Downloading model weights...")
files.download(export_path)

# %% [markdown]
"""
## 🎉 Training Complete!

### Next Steps:
1. Download `efficientnet_b3_deepfake_weights.pth` from Google Drive
2. Place it in `backend/models/` directory
3. Update `deepfake.py` to use EfficientNet-B3 with these weights

### Expected Performance:
- Validation Accuracy: ~90-95% on OpenFake
- Inference Time: ~100-150ms on CPU
- Model Size: ~45-50 MB
"""
