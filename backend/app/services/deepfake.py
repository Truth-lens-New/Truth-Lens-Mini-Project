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
import google.generativeai as genai
from app.core.config import settings



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
            model_path = Path(__file__).parent.parent.parent / "models" / "efficientnet_b3_production.pth"
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Deepfake detector using device: {self.device}")
        
        # Load EfficientNet-B3 using timm
        self.model = timm.create_model('efficientnet_b3', pretrained=False, num_classes=2)
        
        # Load trained weights (handles both raw state_dicts and training checkpoints)
        try:
            checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                self.model.load_state_dict(checkpoint["model_state_dict"])
            else:
                self.model.load_state_dict(checkpoint)
            print(f"Model loaded successfully from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
        
        self.model.to(self.device)
        self.model.eval()
        
        # Standard ImageNet preprocessing for EfficientNet (B3 optimal resolution is 300x300)
        self.transform = transforms.Compose([
            transforms.Resize((300, 300)),
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
    
    def _multi_patch_predict(self, image: Image.Image) -> dict:
        """
        Multi-Patch Analysis — classify overlapping image patches independently.

        Extracts 300x300 overlapping crops at 50% stride from the image at native
        resolution and runs each through the model. This catches localised
        manipulations (e.g. face-swap in a larger scene) that can be missed when
        the whole image is resized to a single 300x300 tensor.

        Args:
            image: PIL Image in RGB mode (any size)

        Returns:
            dict with:
              suspicious_patches   — number of patches classified as FAKE
              total_patches        — total patches analysed
              max_patch_fake_prob  — highest fake probability across all patches
              avg_patch_fake_prob  — average fake probability
              patch_agreement      — fraction of patches agreeing on majority class
              evidence             — list of human-readable evidence strings
        """
        try:
            w, h = image.size
            patch_size = 300
            evidence = []

            # Skip patching for small images — just do full-image predict
            if w < 350 or h < 350:
                tensor = self.transform(image).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    probs = torch.softmax(self.model(tensor), dim=1)
                fake_p = probs[0][1].item()
                return {
                    "suspicious_patches" : 1 if fake_p >= 0.5 else 0,
                    "total_patches"      : 1,
                    "max_patch_fake_prob": fake_p,
                    "avg_patch_fake_prob": fake_p,
                    "patch_agreement"    : 1.0,
                    "evidence"           : [],
                }

            # Stride = 50% overlap
            stride = patch_size // 2

            fake_probs = []
            xs = list(range(0, w - patch_size + 1, stride))
            ys = list(range(0, h - patch_size + 1, stride))

            # Cap at 16 patches to keep latency reasonable
            coords = [(x, y) for y in ys for x in xs][:16]

            for (x, y) in coords:
                crop = image.crop((x, y, x + patch_size, y + patch_size))
                tensor = self.transform(crop).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    probs = torch.softmax(self.model(tensor), dim=1)
                fake_probs.append(probs[0][1].item())

            if not fake_probs:
                return {"suspicious_patches": 0, "total_patches": 0,
                        "max_patch_fake_prob": 0, "avg_patch_fake_prob": 0,
                        "patch_agreement": 1.0, "evidence": []}

            n_fake       = sum(1 for p in fake_probs if p >= 0.5)
            n_real       = len(fake_probs) - n_fake
            majority     = max(n_fake, n_real)
            agreement    = majority / len(fake_probs)
            max_fake     = max(fake_probs)
            avg_fake     = sum(fake_probs) / len(fake_probs)

            if n_fake > 0:
                evidence.append(
                    f"Patch scan: {n_fake}/{len(fake_probs)} patches flagged "
                    f"(max={round(max_fake*100,1)}%, avg={round(avg_fake*100,1)}%)"
                )
            else:
                evidence.append(
                    f"Patch scan: all {len(fake_probs)} patches appear authentic "
                    f"(max fake={round(max_fake*100,1)}%)"
                )

            return {
                "suspicious_patches" : n_fake,
                "total_patches"      : len(fake_probs),
                "max_patch_fake_prob": max_fake,
                "avg_patch_fake_prob": avg_fake,
                "patch_agreement"    : agreement,
                "evidence"           : evidence,
            }

        except Exception as e:
            print(f"Multi-patch predict failed: {e}")
            return {"suspicious_patches": 0, "total_patches": 0,
                    "max_patch_fake_prob": 0, "avg_patch_fake_prob": 0,
                    "patch_agreement": 1.0, "evidence": []}

    def _check_gemini_synthid(self, image_bytes: bytes) -> bool:
        """
        Send image to Gemini to check for SynthID watermark or definitive AI signature.
        """
        if not settings.gemini_api_key:
            return False
            
        try:
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Format the image for Gemini
            # We assume it's JPEG or PNG; just pass bytes directly as image
            img_part = {
                "mime_type": "image/jpeg", 
                "data": image_bytes
            }
            
            prompt = (
                "Analyze this image. Does it contain a Google SynthID watermark, "
                "or is it definitively and obviously an AI-generated image according to your filters? "
                "Reply with ONLY the word 'TRUE' if it is AI-generated or has a SynthID, "
                "or 'FALSE' if it does not."
            )
            
            response = model.generate_content([prompt, img_part])
            text = response.text.strip().upper()
            
            if "TRUE" in text:
                return True
                
            return False
        except Exception as e:
            print(f"Gemini SynthID check failed: {e}")
            return False

    def _compute_fusion_score(self, base_fake_prob: float, patch_result: dict, metadata_risk: int) -> tuple[float, str, list]:
        """
        Combines the base CNN probability with multi-patch and metadata signals.
        Uses a weighted approach where the global CNN score remains the primary driver.
        """
        evidence = []
        is_high_conf = base_fake_prob >= 0.85 or base_fake_prob <= 0.15
        
        # Weight allocation
        w_base = 0.65
        w_patch = 0.25
        w_meta = 0.10
        
        # Base
        fused_score = base_fake_prob * w_base
        
        # Patch
        n_suspicious = patch_result.get("suspicious_patches", 0)
        n_total = patch_result.get("total_patches", 1)
        patch_ratio = n_suspicious / max(n_total, 1)
        fused_score += patch_ratio * w_patch
        
        # Meta
        meta_ratio = min(100, metadata_risk) / 100.0
        fused_score += meta_ratio * w_meta
        
        if is_high_conf:
            max_deviation = 0.05
            capped_score = max(base_fake_prob - max_deviation, min(base_fake_prob + max_deviation, fused_score))
            if abs(capped_score - fused_score) > 0.001:
                fusion_method = "high_conf_capped"
                evidence.append("Score fusion safely capped (max ±5%) to preserve strong model certainty.")
            else:
                fusion_method = "weighted"
            fused_score = capped_score
        else:
            fusion_method = "weighted"
            if abs(fused_score - base_fake_prob) > 0.05:
                # Significant shift
                shifted_to = "FAKE" if fused_score > base_fake_prob else "REAL"
                evidence.append(f"Secondary signals shifted probability by {round(abs(fused_score - base_fake_prob)*100,1)}% toward {shifted_to}.")
                
        return fused_score, fusion_method, evidence

    def predict(self, image_bytes: bytes) -> dict:

        """
        Predict if an image is real or fake.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary with verdict, confidence, probabilities, metadata, evidence, and heatmap
        """
        try:
            # 1. First Pass: Check for SynthID via Gemini API
            if self._check_gemini_synthid(image_bytes):
                return {
                    "verdict": "FAKE",
                    "confidence": 99.0,
                    "confidence_level": "high",
                    "real_probability": 1.0,
                    "fake_probability": 99.0,
                    "model": "Gemini SynthID Detector",
                    "metadata": {},
                    "metadata_risk_score": 100,
                    "patch_analysis": None,
                    "evidence": ["Google Gemini definitively detected a SynthID watermark or AI generation signature."],
                    "heatmap": None
                }
                
            # 2. Proceed to standard pipeline if Gemini says FALSE
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

            # ============================================
            # Multi-Patch Analysis
            # ============================================
            patch_result = self._multi_patch_predict(image_rgb)

            # ============================================
            # Score Fusion
            # ============================================
            metadata_risk = meta_result.get("risk_score", 0)
            
            fused_fake_prob, fusion_method, fusion_evidence = self._compute_fusion_score(
                base_fake_prob=fake_prob,
                patch_result=patch_result,
                metadata_risk=metadata_risk
            )
            
            # Final Verdict
            verdict = "FAKE" if fused_fake_prob >= 0.5 else "REAL"
            confidence = max(fused_fake_prob, 1.0 - fused_fake_prob)
            
            if confidence >= 0.9:
                confidence_level = "high"
            elif confidence >= 0.7:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            # Compile evidence
            evidence = meta_result["evidence"].copy()
            
            if verdict == "FAKE":
                evidence.insert(0, f"Analysis (CNN + Patch + Meta) detected manipulation patterns ({round(fused_fake_prob * 100, 1)}% fakeness)")
            else:
                evidence.insert(0, f"Analysis (CNN + Patch + Meta) found authentic patterns ({round((1 - fused_fake_prob) * 100, 1)}% realness)")
                
            for ev in patch_result.get("evidence", []):
                evidence.append(ev)
                
            for ev in fusion_evidence:
                evidence.append(ev)

            if heatmap_data_url:
                evidence.append("Analysis heatmap generated showing focus regions")
            
            return {
                "verdict": verdict,
                "confidence": round(confidence * 100, 2),
                "confidence_level": confidence_level,
                "real_probability": round((1.0 - fused_fake_prob) * 100, 2),
                "fake_probability": round(fused_fake_prob * 100, 2),
                "model": "EfficientNet-B3 + MultiPatch (Fused)",
                "metadata": meta_result["metadata"],
                "metadata_risk_score": metadata_risk,
                "patch_analysis": {
                    "suspicious_patches": patch_result.get("suspicious_patches", 0),
                    "total_patches"     : patch_result.get("total_patches", 0),
                    "max_fake_prob"     : round(patch_result.get("max_patch_fake_prob", 0) * 100, 1),
                    "avg_fake_prob"     : round(patch_result.get("avg_patch_fake_prob", 0) * 100, 1),
                    "patch_agreement"   : round(patch_result.get("patch_agreement", 1.0) * 100, 1),
                },
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
