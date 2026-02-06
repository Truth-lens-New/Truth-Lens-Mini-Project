"""
Deepfake Detection Service

Uses EfficientNet-B0 model trained to detect deepfake images.
"""

import torch
import torch.nn as nn
from torchvision import transforms
import timm
from PIL import Image
import io
from pathlib import Path


import cv2
import numpy as np
import base64

class DeepfakeDetector:
    """
    Deepfake detection using EfficientNet-B0 model (timm).
    
    The model outputs 2 classes:
    - Class 0: REAL
    - Class 1: FAKE
    """
    
    _instance = None
    _model_loaded = False
    
    def __new__(cls, model_path: str = None):
        """Singleton pattern to avoid loading model multiple times."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_path: str = None):
        """
        Initialize the deepfake detector.
        
        Args:
            model_path: Path to the .pth model file
        """
        if self._model_loaded:
            return
            
        if model_path is None:
            # Default path relative to backend directory
            model_path = Path(__file__).parent.parent.parent / "models" / "best_effnetb0.pth"
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Deepfake detector using device: {self.device}")
        
        # Load EfficientNet-B0 using timm (matches your trained model architecture)
        self.model = timm.create_model('efficientnet_b0', pretrained=False, num_classes=2)
        
        # Load trained weights
        try:
            state_dict = torch.load(model_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state_dict)
            print(f"Model loaded successfully from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
        
        self.model.to(self.device)
        self.model.eval()
        
        # Standard ImageNet preprocessing for EfficientNet
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Grad-CAM hooks
        self.gradients = None
        self.activations = None
        
        def hook_activations(module, input, output):
            self.activations = output
            
        def hook_gradients(module, grad_in, grad_out):
            self.gradients = grad_out[0]
            
        # Register hooks on the last convolutional layer (conv_head for EfficientNet)
        self.model.conv_head.register_forward_hook(hook_activations)
        self.model.conv_head.register_full_backward_hook(hook_gradients)
        
        self._model_loaded = True

    def _extract_metadata(self, image: Image.Image) -> dict:
        """
        Enhanced metadata extraction with comprehensive AI detection.
        
        Checks for:
        - AI software signatures (40+ tools)
        - Typical AI image dimensions
        - Missing camera EXIF data
        - PNG chunk analysis for generation parameters
        - Calculated risk score
        """
        metadata = {}
        evidence = []
        risk_score = 0  # 0-100 scale, higher = more likely AI
        
        # Get basic image info
        metadata["format"] = image.format or "Unknown"
        metadata["mode"] = image.mode
        metadata["size"] = f"{image.width}x{image.height}"
        
        # ============================================
        # 1. Comprehensive AI Software Detection
        # ============================================
        ai_software_signatures = [
            # Stable Diffusion family
            'stable diffusion', 'automatic1111', 'a1111', 'comfyui', 'invoke-ai',
            'invokeai', 'fooocus', 'forge', 'vladmandic', 'easy diffusion',
            # Commercial AI tools
            'midjourney', 'dall-e', 'dalle', 'adobe firefly', 'bing image creator',
            'leonardo.ai', 'leonardo ai', 'nightcafe', 'craiyon', 'wombo dream',
            'artbreeder', 'deepai', 'playground ai', 'ideogram', 'flux',
            # Open source models/tools
            'novelai', 'nai diffusion', 'waifu diffusion', 'animagine',
            'holara', 'pixai', 'tensor.art', 'civitai', 'runpod',
            # Image editors with AI features
            'photoshop', 'generative fill', 'neural filters',
            'luminar', 'topaz', 'remini', 'gigapixel',
            # Chinese AI tools
            'baidu', 'tencent', 'alibaba', 'wanx', 'tongyi',
            # Other indicators
            'diffusion', 'txt2img', 'img2img', 'inpaint', 'upscale'
        ]
        
        # Check EXIF data
        exif_data = {}
        try:
            exif = image._getexif()
            if exif:
                from PIL.ExifTags import TAGS
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8', errors='ignore')
                        except:
                            value = str(value)
                    exif_data[tag] = str(value)
                    if tag in ['Software', 'Make', 'Model', 'DateTime', 'Artist', 
                               'Copyright', 'ImageDescription', 'UserComment']:
                        metadata[tag] = str(value)
        except Exception:
            pass
        
        # Check software field for AI indicators
        software = metadata.get('Software', '').lower()
        for indicator in ai_software_signatures:
            if indicator in software:
                evidence.append(f"AI tool detected in metadata: '{metadata.get('Software')}'")
                risk_score += 40
                metadata['ai_software_detected'] = True
                break
        
        # ============================================
        # 2. Image Info / PNG Chunk Analysis
        # ============================================
        try:
            info = image.info or {}
            
            # Check for Stable Diffusion parameters (PNG tEXt chunks)
            sd_param_keys = ['parameters', 'prompt', 'negative_prompt', 'steps', 
                            'sampler', 'cfg_scale', 'seed', 'model', 'vae']
            for key in sd_param_keys:
                if key in info:
                    evidence.append(f"AI generation parameter '{key}' found in image metadata")
                    metadata['has_ai_params'] = True
                    risk_score += 35
                    break
            
            # Check Software in info dict
            if 'Software' in info:
                software_info = str(info['Software']).lower()
                metadata['Software'] = str(info['Software'])
                for indicator in ai_software_signatures:
                    if indicator in software_info:
                        if not metadata.get('ai_software_detected'):
                            evidence.append(f"AI tool detected: '{info['Software']}'")
                            risk_score += 40
                            metadata['ai_software_detected'] = True
                        break
            
            # Check Comment field
            if 'Comment' in info:
                comment = str(info['Comment']).lower()
                ai_comment_indicators = ['stable diffusion', 'ai generated', 'midjourney',
                                        'dall-e', 'generated by', 'created with ai']
                if any(ai in comment for ai in ai_comment_indicators):
                    evidence.append("Image comment indicates AI generation")
                    risk_score += 30
            
            # Check for ComfyUI workflow
            if 'workflow' in info or 'prompt' in info:
                if 'comfyui' in str(info.get('workflow', '')).lower():
                    evidence.append("ComfyUI workflow detected in metadata")
                    risk_score += 35
                    
        except Exception:
            pass
        
        # ============================================
        # 3. Typical AI Image Dimensions Check
        # ============================================
        ai_typical_dimensions = [
            # Square formats (common for most AI tools)
            (512, 512), (768, 768), (1024, 1024), (2048, 2048),
            # SDXL and newer models
            (1024, 1024), (896, 1152), (1152, 896),
            (832, 1216), (1216, 832), (640, 1536), (1536, 640),
            # Midjourney common sizes
            (1024, 1792), (1792, 1024), (1456, 816), (816, 1456),
            # DALL-E sizes
            (256, 256), (512, 512), (1024, 1024),
            # Portrait/Landscape AI ratios
            (768, 1024), (1024, 768), (768, 1152), (1152, 768),
            (576, 1024), (1024, 576), (640, 1024), (1024, 640)
        ]
        
        current_dims = (image.width, image.height)
        if current_dims in ai_typical_dimensions:
            evidence.append(f"Dimensions {image.width}x{image.height} are typical for AI-generated images")
            risk_score += 15
            metadata['ai_typical_dimensions'] = True
        
        # Check for exact square aspect ratio (very common in AI)
        if image.width == image.height and image.width >= 512:
            if not metadata.get('ai_typical_dimensions'):
                evidence.append(f"Perfect square dimensions ({image.width}x{image.height}) common in AI generation")
                risk_score += 10
        
        # ============================================
        # 4. Missing Camera EXIF Analysis
        # ============================================
        # Real camera photos typically have these EXIF fields
        camera_exif_fields = {
            'Make': 15,           # Camera manufacturer
            'Model': 15,          # Camera model
            'DateTime': 10,       # Capture date
            'ExposureTime': 5,    # Shutter speed
            'FNumber': 5,         # Aperture
            'ISOSpeedRatings': 5, # ISO
            'FocalLength': 5,     # Lens focal length
            'Flash': 3,           # Flash info
            'WhiteBalance': 3,    # White balance
            'ExifImageWidth': 2,  # Original dimensions
            'ExifImageHeight': 2  # Original dimensions
        }
        
        missing_fields = []
        missing_score = 0
        for field, weight in camera_exif_fields.items():
            if field not in exif_data:
                missing_fields.append(field)
                missing_score += weight
        
        # Calculate missing EXIF contribution to risk
        if len(missing_fields) >= 8:
            evidence.append(f"Missing {len(missing_fields)} camera EXIF fields - likely not from a camera")
            risk_score += min(25, missing_score // 3)
            metadata['missing_exif_fields'] = len(missing_fields)
        elif len(missing_fields) >= 5:
            evidence.append(f"Missing key camera metadata ({len(missing_fields)} fields)")
            risk_score += min(15, missing_score // 4)
        
        # Specific checks for completely missing camera info
        if not metadata.get('Make') and not metadata.get('Model'):
            if 'No camera information' not in str(evidence):
                evidence.append("No camera manufacturer/model found - typical for AI-generated images")
                risk_score += 10
        
        if not metadata.get('DateTime'):
            if 'No original capture date' not in str(evidence):
                evidence.append("No original capture date found in metadata")
                risk_score += 5
        
        # ============================================  
        # 5. Additional Suspicious Patterns
        # ============================================
        # Check for very round file sizes (sometimes indicates generation)
        # Check image mode
        if image.mode == 'RGBA' and metadata.get('format') == 'PNG':
            # PNG with alpha is common for AI art with transparent backgrounds
            pass  # Neutral indicator
        
        # Cap risk score at 100
        risk_score = min(100, risk_score)
        
        # Determine risk level
        if risk_score >= 60:
            metadata['metadata_risk_level'] = 'high'
        elif risk_score >= 30:
            metadata['metadata_risk_level'] = 'medium'
        else:
            metadata['metadata_risk_level'] = 'low'
        
        metadata['metadata_risk_score'] = risk_score
        
        return {"metadata": metadata, "evidence": evidence, "risk_score": risk_score}

    def _generate_heatmap(self, image_tensor, original_image):
        """Generate Grad-CAM heatmap."""
        try:
            # Global Average Pooling of gradients
            pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])
            
            # Weight the channels of the activations
            activations = self.activations.detach().clone()
            for i in range(activations.shape[1]):
                activations[:, i, :, :] *= pooled_gradients[i]
                
            # Average the channels of the weighted activations
            heatmap = torch.mean(activations, dim=1).squeeze()
            
            # ReLU on top
            heatmap = np.maximum(heatmap.cpu(), 0)
            
            # Normalize map
            if torch.max(heatmap) != 0:
                heatmap /= torch.max(heatmap)
            heatmap = heatmap.numpy()
            
            # Resize heatmap to match image size
            width, height = original_image.size
            heatmap = cv2.resize(heatmap, (width, height))
            heatmap = np.uint8(255 * heatmap)
            
            # Apply color map
            heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            
            # Superimpose
            original_cv = cv2.cvtColor(np.array(original_image), cv2.COLOR_RGB2BGR)
            heatmap_img = heatmap * 0.4 + original_cv
            
            # Encode to base64
            _, buffer = cv2.imencode('.jpg', heatmap_img)
            heatmap_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return heatmap_base64, "data:image/jpeg;base64," + heatmap_base64
            
        except Exception as e:
            print(f"Heatmap generation failed: {e}")
            return None, None
    
    def predict(self, image_bytes: bytes) -> dict:
        """
        Predict if an image is real or fake.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary with verdict, confidence, probabilities, metadata, evidence, and heatmap
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Extract metadata evidence
            meta_result = self._extract_metadata(image)
            
            # Convert for model
            image_rgb = image.convert('RGB')
            input_tensor = self.transform(image_rgb).unsqueeze(0).to(self.device)
            
            # Ensure gradients are calculated
            # Warning: efficientnet_b0 with timm might need require_grad for hooks to fire on inputs if mostly frozen
            # But usually for inference we don't need grad unless we explicitly do backward
            # So we need to switch on gradients briefly
            
            # Run inference with gradient tracking for Grad-CAM
            # We need to set model to eval but enable grad for input execution to capture gradients
            self.model.eval()
            
            # !!! CRITICAL: We need gradients for Grad-CAM !!!
            # Standard inference is with torch.no_grad(), but here we NEED grad
            # But only for the specific pass
            
            outputs = self.model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            
            # Get prediction
            predicted_class = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][predicted_class].item()
            
            real_prob = probabilities[0][0].item()
            fake_prob = probabilities[0][1].item()
            
            # Generate heatmap for the predicted class
            # Zero grads first
            self.model.zero_grad()
            
            # Backward pass for the predicted class score
            score = outputs[0, predicted_class]
            score.backward()
            
            # Generate heatmap
            heatmap_b64, heatmap_data_url = self._generate_heatmap(input_tensor, image_rgb)
            
            # Determine verdict
            verdict = "FAKE" if predicted_class == 1 else "REAL"
            
            # ============================================
            # Integrate metadata risk score with model prediction
            # ============================================
            metadata_risk = meta_result.get("risk_score", 0)
            evidence = meta_result["evidence"].copy()
            
            # Adjust probabilities based on metadata evidence
            # High metadata risk (≥60) suggests strong AI indicators
            adjusted_fake_prob = fake_prob
            if metadata_risk >= 60:
                # Strong metadata evidence of AI - boost fake probability
                adjustment = min(0.1, metadata_risk / 1000)  # Up to 10% boost
                adjusted_fake_prob = min(0.99, fake_prob + adjustment)
                evidence.insert(0, f"Metadata analysis indicates high AI risk ({metadata_risk}/100)")
            elif metadata_risk >= 30:
                # Moderate metadata evidence
                evidence.insert(0, f"Metadata analysis indicates moderate AI risk ({metadata_risk}/100)")
            else:
                # Low metadata risk - slight confidence in real
                if verdict == "REAL":
                    evidence.insert(0, f"Metadata analysis supports authenticity ({metadata_risk}/100 risk)")
            
            # Re-evaluate verdict if metadata strongly contradicts model
            # If model says REAL but metadata risk is very high (≥70), flag as uncertain
            if verdict == "REAL" and metadata_risk >= 70:
                evidence.insert(0, "⚠️ Warning: Model predicts REAL but metadata shows strong AI indicators")
            
            # If model is uncertain (low confidence) and metadata risk is high, lean toward FAKE
            if confidence < 0.6 and metadata_risk >= 50:
                if adjusted_fake_prob > real_prob:
                    verdict = "FAKE"
                    evidence.insert(0, "Combined analysis (model + metadata) suggests manipulation")
            
            # Add model-based evidence
            if verdict == "FAKE":
                evidence.insert(0, f"Neural network detected manipulation patterns with {round(fake_prob * 100, 1)}% confidence")
            else:
                evidence.insert(0, f"Neural network found authentic patterns with {round(real_prob * 100, 1)}% confidence")
            
            if heatmap_data_url:
                evidence.append("Analysis heatmap generated showing focus regions")

            # Confidence level description (now considers metadata)
            combined_confidence = confidence
            if metadata_risk >= 60 and verdict == "FAKE":
                combined_confidence = min(0.99, confidence + 0.05)  # Boost confidence
            
            if combined_confidence >= 0.9:
                confidence_level = "high"
            elif combined_confidence >= 0.7:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            return {
                "verdict": verdict,
                "confidence": round(combined_confidence * 100, 2),
                "confidence_level": confidence_level,
                "real_probability": round(real_prob * 100, 2),
                "fake_probability": round(adjusted_fake_prob * 100, 2),
                "model": "EfficientNet-B0",
                "metadata": meta_result["metadata"],
                "metadata_risk_score": metadata_risk,
                "evidence": evidence,
                "heatmap": heatmap_data_url
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            raise ValueError(f"Failed to process image: {str(e)}")
    
    def predict_from_file(self, file_path: str) -> dict:
        """
        Predict from a file path.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Prediction result dictionary
        """
        with open(file_path, 'rb') as f:
            return self.predict(f.read())


# Global detector instance (lazy loaded)
_detector: DeepfakeDetector = None


def get_deepfake_detector() -> DeepfakeDetector:
    """Get or create the global deepfake detector instance."""
    global _detector
    if _detector is None:
        _detector = DeepfakeDetector()
    return _detector


async def analyze_image_for_deepfake(image_bytes: bytes) -> dict:
    """
    Async wrapper for deepfake detection.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Detection result dictionary
    """
    detector = get_deepfake_detector()
    return detector.predict(image_bytes)
