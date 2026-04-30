"""
Deepfake Detection Service

Uses EfficientNet-B0 model trained to detect deepfake images.
"""

import asyncio
import functools
import hashlib
import io
import base64
import tempfile
import os
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
import timm
from PIL import Image

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

            # ── Fix 1: Pre-resize large images ─────────────────────────────────
            # Caps preprocessing time for huge uploads (4K, 8K etc.).
            # B3 transform will resize to 300×300 anyway, so we lose nothing.
            MAX_DIM = 1024
            if image.width > MAX_DIM or image.height > MAX_DIM:
                image.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
            # ───────────────────────────────────────────────────────────────────

            # Extract metadata evidence
            meta_result = self._extract_metadata(image)

            # Convert for model
            image_rgb = image.convert('RGB')
            input_tensor = self.transform(image_rgb).unsqueeze(0).to(self.device)
            
            # Ensure gradients are calculated
            # Warning: efficientnet_b0 with timm might need require_grad for hooks to fire on inputs if mostly frozen
            # But usually for inference we don't need grad unless we explicitly do backward
            # So we need to switch on gradients briefly
            
            heatmap_b64, heatmap_data_url = None, None

            # Single forward pass with gradients retained — same as Uday's original.
            # DO NOT wrap in torch.no_grad(): that destroys the gradient graph and
            # forces a SECOND forward pass just for Grad-CAM (2× CPU time on B3).
            self.model.eval()
            self.model.zero_grad()
            outputs = self.model(input_tensor)          # one pass, graph kept
            probabilities = torch.softmax(outputs, dim=1)
            predicted_class = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][predicted_class].item()
            real_prob = probabilities[0][0].item()
            fake_prob = probabilities[0][1].item()

            # Backward on the SAME outputs tensor — graph is still intact
            try:
                score = outputs[0, predicted_class]
                score.backward()
                heatmap_b64, heatmap_data_url = self._generate_heatmap(input_tensor, image_rgb)
            except Exception as e:
                print(f"⚠️ Grad-CAM heatmap generation failed: {e}")
                # Proceed without heatmap — inference result is still valid
            
            # ── Fix 2: Calibrated classification threshold ──────────────────
            # Raw argmax flips to FAKE at 50.01% which is too hair-trigger.
            # Require fake_prob > 55% for a FAKE call; below that → UNCERTAIN.
            FAKE_THRESHOLD = 0.55
            if fake_prob > FAKE_THRESHOLD:
                verdict = "FAKE"
            elif real_prob > FAKE_THRESHOLD:
                verdict = "REAL"
            else:
                # Model is genuinely uncertain — let metadata break the tie
                verdict = "FAKE" if metadata_risk >= 40 else "REAL"
            # ───────────────────────────────────────────────────────────────────
            
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

            # Confidence level — thresholds on 0-1 scale:
            # ≥75% = high, ≥55% = medium, <55% = low
            combined_confidence = confidence
            if metadata_risk >= 60 and verdict == "FAKE":
                combined_confidence = min(0.99, confidence + 0.05)

            if combined_confidence >= 0.75:
                confidence_level = "high"
            elif combined_confidence >= 0.55:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            return {
                "verdict": verdict,
                "confidence": round(combined_confidence * 100, 2),
                "confidence_level": confidence_level,
                "real_probability": round(real_prob * 100, 2),
                "fake_probability": round(adjusted_fake_prob * 100, 2),
                "model": "EfficientNet-B3",
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

    def analyze_video(self, video_bytes: bytes, n_frames: int = 8) -> dict:
        """
        Analyze a video for deepfakes by sampling N evenly-spaced keyframes.

        Strategy:
        - Write video bytes to a named temp file (OpenCV needs a file path)
        - Sample n_frames evenly across the total frame count
        - Run EfficientNet-B3 inference on each frame
        - Aggregate: majority verdict, averaged probabilities

        Args:
            video_bytes: Raw video file bytes
            n_frames: Number of frames to sample (default 8)

        Returns:
            Aggregated result dict (same shape as predict())
        """
        # Write to temp file so OpenCV can open it
        suffix = ".mp4"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        try:
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                raise ValueError("Could not open video file — unsupported format or corrupt file.")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            duration_s = total_frames / fps

            if total_frames < 1:
                raise ValueError("Video has no readable frames.")

            # Pick n_frames evenly-spaced positions (skip very first/last frames)
            sample_count = min(n_frames, total_frames)
            frame_indices = [
                int(total_frames * (i + 0.5) / sample_count)
                for i in range(sample_count)
            ]

            frame_results = []
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if not ret:
                    continue

                # Convert BGR (OpenCV) → RGB → PIL → bytes → predict()
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=90)
                frame_bytes = buf.getvalue()

                try:
                    result = self.predict(frame_bytes)
                    frame_results.append(result)
                except Exception as e:
                    print(f"⚠️ Frame {idx} analysis failed: {e}")
                    continue

            cap.release()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        if not frame_results:
            raise ValueError("No frames could be analyzed from the video.")

        # ── Aggregate frame results ────────────────────────────────────────────
        fake_votes = sum(1 for r in frame_results if r["verdict"] == "FAKE")
        real_votes = len(frame_results) - fake_votes
        verdict = "FAKE" if fake_votes > real_votes else "REAL"

        avg_real = sum(r["real_probability"] for r in frame_results) / len(frame_results)
        avg_fake = sum(r["fake_probability"] for r in frame_results) / len(frame_results)
        avg_conf = sum(r["confidence"] for r in frame_results) / len(frame_results)
        avg_meta_risk = sum(r.get("metadata_risk_score", 0) for r in frame_results) / len(frame_results)

        # Confidence level — thresholds on 0-100 scale (avg_conf is already ×100):
        # ≥75 = high, ≥55 = medium, <55 = low
        if avg_conf >= 75:
            confidence_level = "high"
        elif avg_conf >= 55:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Use heatmap from the most confident frame (first FAKE frame, or first frame)
        best_frame = next((r for r in frame_results if r["verdict"] == verdict), frame_results[0])
        heatmap = best_frame.get("heatmap")

        # Collect unique evidence from all frames (deduplicated)
        seen = set()
        all_evidence = []
        for r in frame_results:
            for e in r.get("evidence", []):
                if e not in seen:
                    seen.add(e)
                    all_evidence.append(e)

        # Prepend video-level summary
        all_evidence.insert(0,
            f"Video analyzed: {sample_count} frames sampled over {duration_s:.1f}s "
            f"| {fake_votes}/{len(frame_results)} frames classified as FAKE"
        )

        return {
            "verdict": verdict,
            "confidence": round(avg_conf, 2),
            "confidence_level": confidence_level,
            "real_probability": round(avg_real, 2),
            "fake_probability": round(avg_fake, 2),
            "model": "EfficientNet-B3 (video)",
            "metadata": {"format": "video", "frames_sampled": sample_count, "duration_s": round(duration_s, 1)},
            "metadata_risk_score": round(avg_meta_risk),
            "evidence": all_evidence[:10],
            "heatmap": heatmap
        }
        # ─────────────────────────────────────────────────────────────────────



# Global detector instance (lazy loaded)
_detector: Optional[DeepfakeDetector] = None
# Cached error string if model init fails — prevents confusing silent retry loops
_init_error: Optional[str] = None

# ── Fix 3: MD5-based result cache ──────────────────────────────────────────
# Maps sha256(image_bytes) → prediction dict.  Gives instant responses for
# repeat uploads without re-running the model.
_result_cache: dict = {}
_CACHE_MAX_SIZE = 128   # evict oldest when cache exceeds this
# ───────────────────────────────────────────────────────────────────────────


def get_deepfake_detector() -> DeepfakeDetector:
    """
    Get or create the global deepfake detector instance.

    If the model previously failed to load, raises RuntimeError immediately
    with a clear message instead of retrying inside PyTorch.
    """
    global _detector, _init_error

    if _init_error is not None:
        raise RuntimeError(
            f"Deepfake model failed to load at startup: {_init_error}"
        )

    if _detector is None:
        try:
            _detector = DeepfakeDetector()
        except Exception as exc:
            _init_error = str(exc)  # cache so next call surfaces it fast
            raise RuntimeError(
                f"Deepfake model failed to load: {exc}"
            ) from exc

    return _detector


async def analyze_image_for_deepfake(image_bytes: bytes, content_type: str = "image/jpeg") -> dict:
    """
    Async wrapper for deepfake detection.

    Includes:
    - MD5 result cache: identical images return instantly
    - 30s hard timeout: prevents indefinite hangs on the event loop
    - Thread pool offload: keeps FastAPI responsive during heavy inference

    Args:
        image_bytes: Raw image bytes
        content_type: MIME type — used to route image vs video

    Returns:
        Detection result dictionary
    """
    global _result_cache

    # ── Video routing ────────────────────────────────────────────────────────
    # Videos cannot be opened by PIL. Extract frames first, then aggregate.
    VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/avi", "video/x-msvideo"}
    if content_type in VIDEO_TYPES:
        img_hash = hashlib.md5(image_bytes).hexdigest()
        if img_hash in _result_cache:
            print(f"🎯 Cache hit for video {img_hash[:8]}… — skipping inference")
            cached = dict(_result_cache[img_hash])
            cached["cache_hit"] = True
            return cached

        detector = get_deepfake_detector()
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None, functools.partial(detector.analyze_video, image_bytes)
                ),
                timeout=120.0  # videos need more time — allow 2 minutes
            )
        except asyncio.TimeoutError:
            raise ValueError(
                "Video analysis timed out after 120 seconds. "
                "Try a shorter clip (under 30 seconds)."
            )
        # Store in cache
        if len(_result_cache) >= _CACHE_MAX_SIZE:
            del _result_cache[next(iter(_result_cache))]
        _result_cache[img_hash] = result
        return result
    # ────────────────────────────────────────────────────────────────────────

    # ── Cache check (images) ─────────────────────────────────────────────────
    img_hash = hashlib.md5(image_bytes).hexdigest()
    if img_hash in _result_cache:
        print(f"🎯 Cache hit for image {img_hash[:8]}… — skipping inference")
        cached = dict(_result_cache[img_hash])  # shallow copy
        cached["cache_hit"] = True
        return cached
    # ────────────────────────────────────────────────────────────────────────

    detector = get_deepfake_detector()
    loop = asyncio.get_event_loop()

    # ── Fix 4: 30s hard timeout — never hang forever ─────────────────────
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None, functools.partial(detector.predict, image_bytes)
            ),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        raise ValueError(
            "Media analysis timed out after 30 seconds. "
            "Try a smaller image or re-upload."
        )
    # ────────────────────────────────────────────────────────────────────────

    # Store in cache (evict oldest entry if full)
    if len(_result_cache) >= _CACHE_MAX_SIZE:
        oldest_key = next(iter(_result_cache))
        del _result_cache[oldest_key]
    _result_cache[img_hash] = result

    return result
