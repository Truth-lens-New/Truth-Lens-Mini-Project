# Fact-Checking and Image Model Review Notes

This file explains the fact-checking path (text claims) and the deepfake image model path.

## 1) Fact-Check Service (Google Fact Check + Normalization)

Source: `backend/app/services/factcheck.py`

```python
FACTCHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

async with httpx.AsyncClient() as client:
    response = await client.get(
        FACTCHECK_API_URL,
        params={
            'key': settings.google_factcheck_api_key,
            'query': claim,
            'languageCode': 'en'
        },
        timeout=10.0
    )
```

```python
normalized_rating = normalize_rating(original_rating)

if normalized_rating is None:
    normalized_rating = await llm_interpret_rating(
        rating=original_rating,
        summary=summary_text,
        claim=claim,
        url=article_url,
        source=source_name
    )
```

What to say:
- First pass uses deterministic rating normalization rules.
- LLM interpretation is fallback only for unclear rating strings.
- Output always returns normalized classes (`True`, `False`, `Misleading`, `Unverifiable`) + source URL.

## 2) LLM Claim Fallback (When Evidence Is Inconclusive)

Source: `backend/app/services/llm_verdict.py`

```python
if not settings.gemini_api_key:
    return {
        'verdict': None,
        'confidence': None,
        'reasoning': 'LLM not configured',
        'used': False
    }

model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content(prompt)
```

What to say:
- This module is a fallback for ambiguous cases with insufficient retrieved evidence.
- It emits structured output (`verdict`, `confidence`, `reasoning`, `used`).

## 3) Deepfake Image Model (EfficientNet-B0)

Source: `backend/app/services/deepfake.py`

```python
self.model = timm.create_model('efficientnet_b0', pretrained=False, num_classes=2)
state_dict = torch.load(model_path, map_location=self.device, weights_only=True)
self.model.load_state_dict(state_dict)
self.model.eval()
```

```python
outputs = self.model(input_tensor)
probabilities = torch.softmax(outputs, dim=1)
predicted_class = torch.argmax(probabilities, dim=1).item()

score = outputs[0, predicted_class]
score.backward()  # for Grad-CAM
heatmap_b64, heatmap_data_url = self._generate_heatmap(input_tensor, image_rgb)
```

What to say:
- Binary classifier: class 0 = real, class 1 = fake.
- Returns probability scores and Grad-CAM heatmap for visual explanation.
- Metadata/EXIF checks are added as extra supporting evidence.

## 4) Async Wrapper for Non-Blocking API

Source: `backend/app/services/deepfake.py`

```python
async def analyze_image_for_deepfake(image_bytes: bytes, content_type: str = "image/jpeg") -> dict:
    detector = get_deepfake_detector()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, functools.partial(detector.predict, image_bytes)
    )
```

What to say:
- PyTorch inference is CPU/GPU heavy, so it is moved to a thread executor.
- This prevents blocking the FastAPI event loop.

## 5) API Endpoint Using the Image Model

Source: `backend/app/api/v1/analyze.py`

```python
@router.post("/analyze-media", response_model=MediaAnalysisResponse)
async def analyze_media(file: UploadFile = File(...), ...):
    contents = await file.read()
    result = await analyze_image_for_deepfake(contents, content_type=file.content_type)
```

What to say:
- Uploaded media is validated, scored, and then persisted to history as a `Check` entry.

## 30-Second Review Pitch

- "Fact-checking prefers deterministic API + rule normalization, with LLM only as fallback."
- "Image detection uses EfficientNet-B0 plus Grad-CAM and metadata evidence for explainability."
- "Heavy model inference is offloaded so the async API stays responsive."
