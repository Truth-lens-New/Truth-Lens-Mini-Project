"""
Deepfake Detection Service

Uses EfficientNet-B0 model trained to detect deepfake images.
"""

import asyncio
import functools
import io
import math
import os
import base64
import tempfile
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
        # 3. Image Dimensions (removed as risk factor)
        # ============================================
        # Canvas size is no longer treated as AI evidence: dimensions like
        # 512x512 / 1024x1024 are extremely common for normal icons, logos,
        # crops, and screenshots, and produced overwhelming false FAKE pushes.
        metadata['ai_typical_dimensions'] = False

        
        # ============================================
        # 4. Camera EXIF Analysis (WEAK signal)
        # ============================================
        # Absence of camera EXIF is deliberately scored LOW: screenshots,
        # downloads, and re-shared images lose EXIF without being
        # AI-generated. Only positive AI indicators drive risk up.
        if not metadata.get('Make') and not metadata.get('Model'):
            camera_exif_fields = (
                'Make', 'Model', 'DateTime', 'ExposureTime', 'FNumber',
                'ISOSpeedRatings', 'FocalLength', 'Flash', 'WhiteBalance',
                'ExifImageWidth', 'ExifImageHeight',
            )
            missing_fields = [f for f in camera_exif_fields if f not in exif_data]
            metadata['missing_exif_fields'] = len(missing_fields)
            metadata['camera_exif_present'] = False
            risk_score += 5
            evidence.append(
                f"No camera EXIF ({len(missing_fields)} fields missing) - "
                f"common for screenshots and downloads, weak AI signal only"
            )
        else:
            metadata['camera_exif_present'] = True
        
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

    # =========================================================================
    # Calibration
    # =========================================================================
    # models/deepfake_calibration.json (optional, produced by
    # backend/scripts/calibrate_deepfake.py) tunes the decision boundary:
    #   threshold   - verdict cuts at fake_prob >= threshold (argmax 0.5
    #                 inherits any training-set class imbalance)
    #   temperature - softmax<T> sharpness; >1 flattens overconfident scores
    # Defaults (0.5 / 1.0) keep raw model behavior until calibration is run.
    CALIBRATION_FILE = Path(__file__).parent.parent.parent / "models" / "deepfake_calibration.json"

    @classmethod
    def _load_calibration(cls) -> tuple:
        """Read (threshold, temperature) from the calibration file, or defaults."""
        threshold, temperature = 0.5, 1.0
        try:
            import json
            if cls.CALIBRATION_FILE.exists():
                with open(cls.CALIBRATION_FILE, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                threshold = float(data.get("threshold", 0.5))
                temperature = float(data.get("temperature", 1.0))
        except Exception as exc:
            print(f"Calibration load failed ({exc}); using defaults 0.5/1.0")
        # Sanity clamps
        return (
            min(0.85, max(0.15, threshold)),
            min(4.0, max(0.2, temperature)),
        )

    def _apply_calibration(self, logits):
        """Temperature-scale raw logits and softmax them."""
        _, temperature = self._load_calibration()
        if temperature != 1.0:
            logits = logits / temperature
        return torch.softmax(logits, dim=1)

    def _verdict_at_threshold(self, fake_prob: float) -> str:
        """FAKE when fake_prob >= calibrated threshold, else REAL."""
        threshold, _ = self._load_calibration()
        return "FAKE" if fake_prob >= threshold else "REAL"

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
            probabilities = self._apply_calibration(outputs)
            
            # Get prediction
            predicted_class = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][predicted_class].item()
            
            real_prob = probabilities[0][0].item()
            fake_prob = probabilities[0][1].item()
            
            # Generate heatmap for the predicted class (raw logits, unaffected
            # by temperature scaling). Calibration file is re-read per
            # prediction, so a new deepfake_calibration.json applies without
            # a restart.
            # Zero grads first
            self.model.zero_grad()
            
            # Backward pass for the predicted class score
            score = outputs[0, predicted_class]
            score.backward()
            
            # Generate heatmap
            heatmap_b64, heatmap_data_url = self._generate_heatmap(input_tensor, image_rgb)
            
            # Determine verdict using the calibrated decision boundary
            verdict = "FAKE" if fake_prob >= self._load_calibration()[0] else "REAL"
            
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
            
            # If model is uncertain but metadata shows strong AI indicators,
            # the model's verdict STANDS — metadata no longer flips FAKE.
            # (Previously: confidence < 0.6 and metadata_risk >= 50 flipped
            # the verdict, pushing every EXIF-less screenshot to FAKE.)
            
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

    def _predict_frames(self, rgb_images: list) -> list:
        """
        Run the binary REAL/FAKE classifier over a batch of RGB frames.

        Unlike `predict()` this path performs no still-image EXIF/metadata
        heuristics (extracted video frames never carry camera EXIF) and no
        Grad-CAM backward pass — pure model probabilities.

        Args:
            rgb_images: List of PIL RGB images (decoded video frames)

        Returns:
            List of dicts with per-frame verdict and normalized probabilities
        """
        # Grad-CAM hooks stay registered but see no backward pass here
        self.model.eval()
        tensors = torch.stack(
            [self.transform(Image.fromarray(img).convert("RGB")) for img in rgb_images]
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensors)
            probabilities = self._apply_calibration(outputs)

        per_frame = []
        for probs in probabilities:
            real_prob = probs[0].item()
            fake_prob = probs[1].item()
            per_frame.append({
                "verdict": self._verdict_at_threshold(fake_prob),
                "confidence": max(real_prob, fake_prob),
                "real_probability": real_prob,
                "fake_probability": fake_prob,
            })
        return per_frame


# Global detector instance (lazy loaded)
_detector: Optional[DeepfakeDetector] = None
# Cached error string if model init fails — prevents confusing silent retry loops
_init_error: Optional[str] = None


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

    PyTorch inference (forward + Grad-CAM backward) is CPU-bound and can
    take several seconds. Running it directly inside an async function blocks
    FastAPI's event loop. We offload to the default ThreadPoolExecutor instead.

    Args:
        image_bytes: Raw image bytes
        content_type: MIME type — used to route image vs video

    Returns:
        Detection result dictionary
    """
    detector = get_deepfake_detector()
    loop = asyncio.get_event_loop()

    # Offload CPU-intensive ML inference to a thread pool
    return await loop.run_in_executor(
        None, functools.partial(detector.predict, image_bytes)
    )


# ==========================================================================
# Video analysis
# ==========================================================================
# Videos are limited to 50 MB (enforced in the API) and MAX_VIDEO_DURATION
# seconds (mirrors the UI's "0–30s" limit). Up to MAX_VIDEO_FRAMES evenly
# spaced frames are sampled and classified; the clip verdict is the average
# of the per-frame model probabilities.
MAX_VIDEO_DURATION_SECONDS = 30
MAX_VIDEO_FRAMES = 8


def _fourcc_to_string(fourcc_int: int) -> str:
    """Convert OpenCV's FOURCC integer to its four-character codec string."""
    try:
        return "".join(chr((int(fourcc_int) >> (8 * i)) & 0xFF) for i in range(4)).strip()
    except Exception:
        return ""


def _decode_video_frames(video_bytes: bytes, max_duration: float, max_frames: int) -> tuple:
    """
    Decode an uploaded video and sample up to `max_frames` evenly spaced frames.

    The bytes are written to a temporary file (OpenCV needs a seekable path)
    which is always removed in `finally` — on success and on failure.

    Returns:
        (frames_bgr, timestamps, video_info) where frames are RGB arrays,
        timestamps are the sampled frame times in seconds, and video_info
        holds real container/file facts for the response metadata.

    Raises:
        ValueError: For empty, corrupt, undecodable, no-frame, or
            over-duration videos (client-friendly messages).
    """
    if not video_bytes:
        raise ValueError("The uploaded video is empty.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise ValueError(
                "Could not decode the uploaded video. The file may be corrupt "
                "or in an unsupported format."
            )

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        codec = _fourcc_to_string(cap.get(cv2.CAP_PROP_FOURCC))

        if not fps or not math.isfinite(fps) or fps <= 0 or frame_count <= 0:
            cap.release()
            raise ValueError(
                "Could not read the video stream. The file may be corrupt "
                "or in an unsupported format."
            )
        if width <= 0 or height <= 0:
            cap.release()
            raise ValueError(
                "Could not read video dimensions. The file may be corrupt."
            )

        duration = frame_count / fps
        if duration > max_duration + 1.0:  # 1s tolerance for container rounding
            cap.release()
            raise ValueError(
                f"Video is {duration:.1f}s long. Maximum allowed duration is "
                f"{max_duration:.0f} seconds."
            )

        # --- Choose evenly spaced, distinct frame indices ---
        if frame_count <= max_frames:
            indices = list(range(frame_count))
        else:
            step = (frame_count - 1) / (max_frames - 1)
            indices = [min(int(round(i * step)), frame_count - 1) for i in range(max_frames)]
            seen, unique = set(), []
            for idx in indices:
                if idx not in seen:
                    seen.add(idx)
                    unique.append(idx)
            indices = unique

        frames = []
        timestamps = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue  # skip undecodable frames (e.g. torn tail frames)
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            timestamps.append(round(idx / fps, 2))
        cap.release()

        if not frames:
            raise ValueError(
                "Could not extract any frames from the uploaded video. "
                "The file may be corrupt."
            )

        video_info = {
            "codec": codec or "unknown",
            "duration_seconds": round(duration, 2),
            "resolution": f"{width}x{height}",
            "fps": round(fps, 2),
            "total_frames": frame_count,
            "frames_sampled": len(frames),
            "frame_sampling": "evenly spaced",
        }
        return frames, timestamps, video_info

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Failed to decode video: {exc}")
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


async def analyze_video_for_deepfake(video_bytes: bytes, content_type: str = "video/mp4") -> dict:
    """
    Analyze an uploaded video for deepfakes by sampling evenly spaced frames
    and running the existing binary REAL/FAKE model on them.

    Sampling, decoding, and inference run in a thread pool (CPU-bound).
    The clip result is the average of the per-frame model probabilities.
    No Grad-CAM heatmap is produced and no still-image EXIF heuristics are
    applied to extracted frames.

    Response keeps the MediaAnalysisResponse shape and optionally adds
    `frames_analyzed` and timestamped `frame_results`.

    Raises:
        ValueError: On invalid/undecodable/over-limit videos.
    """
    detector = get_deepfake_detector()
    loop = asyncio.get_event_loop()

    def _run() -> dict:
        frames, timestamps, video_info = _decode_video_frames(
            video_bytes,
            max_duration=MAX_VIDEO_DURATION_SECONDS,
            max_frames=MAX_VIDEO_FRAMES,
        )
        frame_predictions = detector._predict_frames(frames)
        total = len(frame_predictions)

        frame_results = []
        for ts, pred in zip(timestamps, frame_predictions):
            frame_results.append({
                "timestamp": ts,
                "verdict": pred["verdict"],
                "real_probability": round(pred["real_probability"] * 100, 2),
                "fake_probability": round(pred["fake_probability"] * 100, 2),
            })

        # --- Aggregate verdict: average model probabilities across frames ---
        avg_real = sum(p["real_probability"] for p in frame_predictions) / total
        avg_fake = sum(p["fake_probability"] for p in frame_predictions) / total
        verdict = detector._verdict_at_threshold(avg_fake)
        confidence = avg_fake if verdict == "FAKE" else avg_real

        if confidence >= 0.9:
            confidence_level = "high"
        elif confidence >= 0.7:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        fake_count = sum(1 for p in frame_predictions if p["verdict"] == "FAKE")
        real_count = total - fake_count
        evidence = [
            f"Analyzed {total} evenly spaced frames across the "
            f"{video_info['duration_seconds']}s clip ({video_info['resolution']}, "
            f"{video_info['fps']} fps)",
            f"Neural network detected "
            f"{'manipulation patterns' if verdict == 'FAKE' else 'authentic patterns'} "
            f"with {round(confidence * 100, 1)}% average frame probability",
            f"Sampled frame verdicts: {fake_count} FAKE / {real_count} REAL",
        ]
        fake_probs = [p["fake_probability"] for p in frame_predictions]
        if max(fake_probs) - min(fake_probs) > 0.25:
            evidence.append(
                f"Large frame-to-frame variation in FAKE probability "
                f"({round(min(fake_probs) * 100, 1)}%–{round(max(fake_probs) * 100, 1)}%), "
                f"interpreting individual frames together"
            )

        return {
            "verdict": verdict,
            "confidence": round(confidence * 100, 2),
            "confidence_level": confidence_level,
            "real_probability": round(avg_real * 100, 2),
            "fake_probability": round(avg_fake * 100, 2),
            "model": "EfficientNet-B3",
            "metadata": video_info,
            "evidence": evidence,
            "heatmap": None,
            "frames_analyzed": total,
            "frame_results": frame_results,
        }

    return await loop.run_in_executor(None, _run)
