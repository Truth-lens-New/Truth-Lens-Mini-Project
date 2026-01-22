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
import tempfile
import os

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
        """Extract metadata from image as evidence."""
        metadata = {}
        evidence = []
        
        # Get basic image info
        metadata["format"] = image.format or "Unknown"
        metadata["mode"] = image.mode
        metadata["size"] = f"{image.width}x{image.height}"
        
        # Try to get EXIF data
        try:
            exif = image._getexif()
            if exif:
                # Map EXIF tag IDs to names
                from PIL.ExifTags import TAGS
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8', errors='ignore')
                        except:
                            value = str(value)
                    if tag in ['Software', 'Make', 'Model', 'DateTime', 'Artist', 'Copyright']:
                        metadata[tag] = str(value)
                        
                # Check for AI software indicators
                software = metadata.get('Software', '').lower()
                ai_indicators = ['stable diffusion', 'midjourney', 'dall-e', 'adobe firefly', 
                               'automatic1111', 'comfyui', 'novelai', 'photoshop', 'gimp']
                for indicator in ai_indicators:
                    if indicator in software:
                        evidence.append(f"Software '{metadata.get('Software')}' is commonly used for AI generation or manipulation")
                        break
        except Exception as e:
            pass
        
        # Check image info dict
        try:
            info = image.info
            if 'Software' in info:
                metadata['Software'] = str(info['Software'])
            if 'parameters' in info:  # Stable Diffusion puts generation params here
                evidence.append("Image contains AI generation parameters in metadata")
                metadata['has_ai_params'] = True
            if 'Comment' in info:
                comment = str(info['Comment']).lower()
                if any(ai in comment for ai in ['stable diffusion', 'ai generated', 'midjourney']):
                    evidence.append("Image comment indicates AI generation")
        except:
            pass
        
        # No EXIF = suspicious for photos
        if not metadata.get('Make') and not metadata.get('Model'):
            evidence.append("No camera information found - typical for AI-generated images")
        
        if not metadata.get('DateTime'):
            evidence.append("No original capture date found in metadata")
            
        return {"metadata": metadata, "evidence": evidence}

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
            
            # Add model-based evidence
            evidence = meta_result["evidence"].copy()
            if verdict == "FAKE":
                evidence.insert(0, f"Neural network detected manipulation patterns with {round(fake_prob * 100, 1)}% confidence")
            else:
                evidence.insert(0, f"Neural network found authentic patterns with {round(real_prob * 100, 1)}% confidence")
            
            if heatmap_data_url:
                evidence.append("Analysis heatmap generated showing focus regions")

            # Confidence level description
            if confidence >= 0.9:
                confidence_level = "high"
            elif confidence >= 0.7:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            return {
                "verdict": verdict,
                "confidence": round(confidence * 100, 2),
                "confidence_level": confidence_level,
                "real_probability": round(real_prob * 100, 2),
                "fake_probability": round(fake_prob * 100, 2),
                "model": "EfficientNet-B0",
                "metadata": meta_result["metadata"],
                "evidence": evidence,
                "heatmap": heatmap_data_url
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            raise ValueError(f"Failed to process image: {str(e)}")
    
    def predict_video(self, video_bytes: bytes) -> dict:
        """
        Analyze a video file by extracting frames and averaging predictions.
        
        Args:
            video_bytes: Raw video content
            
        Returns:
            Aggregated prediction result
        """
        # Save bytes to temp file because cv2.VideoCapture requires path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(video_bytes)
            temp_path = temp_file.name
            
        try:
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise ValueError("Could not open video file")
                
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            duration = frame_count / fps
            
            # Extract 5 evenly spaced frames
            frames_to_extract = 5
            extracted_frames = []
            frame_indices = np.linspace(0, frame_count - 1, frames_to_extract, dtype=int)
            
            for index in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, index)
                ret, frame = cap.read()
                if ret:
                    # Convert BGR (OpenCV) to RGB (PIL)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    
                    # Store bytes for predict() reuse
                    img_byte_arr = io.BytesIO()
                    pil_image.save(img_byte_arr, format='JPEG')
                    extracted_frames.append(img_byte_arr.getvalue())
                    
            cap.release()
            
            if not extracted_frames:
                raise ValueError("Could not extract any frames from video")
                
            # Run prediction on each frame
            results = []
            for frame_bytes in extracted_frames:
                try:
                    results.append(self.predict(frame_bytes))
                except Exception as e:
                    print(f"Skipping bad frame: {e}")
                    
            if not results:
                raise ValueError("Analysis failed on all extracted frames")
                
            # Aggregate results
            avg_conf = np.mean([r["confidence"] for r in results])
            avg_real = np.mean([r["real_probability"] for r in results])
            avg_fake = np.mean([r["fake_probability"] for r in results])
            
            # Use the frame with highest confidence (or "fakeness") as the representative result (heatmap etc)
            # If any frame is strongly fake (>80%), treat video as fake
            max_fake_result = max(results, key=lambda x: x["fake_probability"])
            
            # Final Verdict Logic for Video:
            # If average fake prob > 50% OR if we found a highly suspicious frame
            if avg_fake > 50 or max_fake_result["fake_probability"] > 80:
                final_verdict = "FAKE"
                final_conf = max(avg_conf, max_fake_result["confidence"]) # Be cautious
                # Use the fake frame evidence
                final_result = max_fake_result.copy()
            else:
                final_verdict = "REAL"
                final_conf = avg_conf
                # Use the first frame as representative
                final_result = results[0].copy()
                
            final_result["verdict"] = final_verdict
            final_result["confidence"] = round(final_conf, 2)
            final_result["real_probability"] = round(avg_real, 2)
            final_result["fake_probability"] = round(avg_fake, 2)
            
            # Enhance Evidence
            final_result["evidence"].insert(0, f"Video Analysis: Processed {len(extracted_frames)} frames. Average Fake Probability: {round(avg_fake, 1)}%")
            if max_fake_result["fake_probability"] > 80:
                 final_result["evidence"].append(f"Suspicious Content: Frame at index {results.index(max_fake_result)} showed high signs of manipulation.")
            
            return final_result
            
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
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


async def analyze_image_for_deepfake(image_bytes: bytes, content_type: str = "image/jpeg") -> dict:
    """
    Async wrapper for deepfake detection.
    
    Args:
        image_bytes: Raw image or video bytes
        content_type: MIME type of the file
        
    Returns:
        Detection result dictionary
    """
    detector = get_deepfake_detector()
    
    if "video" in content_type.lower():
        result = detector.predict_video(image_bytes)
    else:
        result = detector.predict(image_bytes)
        
    # Phase 6: Explainable AI (Gemini Vision)
    try:
        from app.services.investigation.explanation import get_explanation_service
        explainer = get_explanation_service()
        
        # Only explain if we have a clear verdict (optional, but good for saving tokens)
        ai_explanation = await explainer.explain_media(
            image_bytes, 
            result["verdict"], 
            result["confidence"]
        )
        
        # Insert as top evidence
        result["evidence"].insert(0, f"AI Forensic Analysis: {ai_explanation}")
        
    except Exception as e:
        print(f"Explanation injection failed: {e}")
        
    return result
