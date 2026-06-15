# TruthLens Project Summary

Last updated: 2026-04-09

## 1) What TruthLens Is
TruthLens is a full-stack misinformation verification platform.
It helps users check claims from text, URLs, and media inputs, and returns evidence-backed verdicts.

Core product goals:
- Reduce manual verification time.
- Show evidence sources, not just a black-box answer.
- Keep verdict logic deterministic (evidence first), with LLM used for explanation support.

---

## 2) Problem We Solved
People regularly consume claims that are:
- Out of context
- Partially true/misleading
- Fully false or hoax-level misinformation

Manual verification is slow and inconsistent.
TruthLens provides a single interface that combines multiple checks (fact-check APIs, evidence search, stance, trust, and media forensics).

---

## 3) High-Level Architecture

### Frontend
- React + TypeScript + Vite
- Main workflows: claim investigation, media upload analysis, history view

### Backend
- FastAPI
- Two parallel pipelines in same backend:
  - `v1`: classic end-to-end verification pipeline
  - `v3`: staged hybrid pipeline (`/analyze` then `/investigate`)

### Database
- PostgreSQL (containerized)
- Core tables: `users`, `checks`

### Extension
- Chrome extension (Manifest V3)
- Uses same backend and auth token model as web app

### Infra
- Docker Compose services: backend, client, client-prod, postgres, pgadmin

---

## 4) Main Verification Workflows

### 4.1 V1 Claim Verification (`/api/v1/analyze`)
Typical flow:
1. Input normalization and claim extraction
2. Domain trust scoring
3. Google Fact Check lookup
4. Related evidence retrieval (GNews)
5. Stance classification on evidence snippets
6. Deterministic verdict aggregation
7. Explanation text generation and persistence to history

Why this matters:
- It is fast and practical for day-to-day claim checks.
- It combines structured API checks + retrieval + rule-based final aggregation.

### 4.2 V3 Hybrid Pipeline (`/api/v3/analyze`, `/api/v3/investigate`)
- `/api/v3/analyze`: light phase (input -> claim extraction -> claim typing/checkability)
- `/api/v3/investigate`: deep phase
  - Quick checks first (known misinfo DB, Wikidata for factual claims, Google Fact Check)
  - Strategy-driven deep investigation next (type-aware)
  - Evidence synthesis produces final verdict + confidence + summary + evidence trail

Important design rule in v3:
- Verdict is evidence-driven.
- LLM is used to enrich explanation text, not to replace evidence aggregation logic.

---

## 5) How Fact-Checking Works (Detailed)

TruthLens fact-checking uses a layered approach:

1. **Google Fact Check Tools API**
- Endpoint used: `https://factchecktools.googleapis.com/v1alpha1/claims:search`
- Query is made with claim text and API key.

2. **Rating normalization**
- Raw fact-check ratings from different publishers are mapped to standard labels:
  - `True`, `False`, `Misleading`, `Unverifiable`
- This handles inconsistent naming across fact-check organizations.

3. **LLM fallback only for ambiguous ratings**
- If static rating normalization fails, an LLM fallback interprets unclear rating/context.
- The fallback is used as a helper when labels are non-standard.

4. **Other evidence in parallel**
- GNews retrieval provides corroborating/contradicting context.
- Stance analysis + trust weighting helps produce a robust final decision when no direct fact-check is definitive.

---

## 6) Tools and Technologies Used

### Backend/API
- FastAPI, Pydantic, SQLAlchemy (async), asyncpg, Uvicorn

### NLP/ML/LLM
- Google Gemini (stance/explanations/fallback interpretation in some flows)
- Transformers-based stance modules in v3 synthesis stack
- EasyOCR for image text extraction
- EfficientNet-B0 (PyTorch/timm) for deepfake image detection

### Data/Evidence
- Google Fact Check API
- GNews API
- Domain trust scoring data
- Known misinformation references

### Frontend
- React, TypeScript, Vite, Tailwind, component libraries

### Platform
- Docker, Docker Compose
- PostgreSQL + PgAdmin
- Chrome Extension (MV3)

---

## 7) How Image Detection Works

Media endpoint:
- `POST /api/v1/analyze-media`

Current deepfake image pipeline:
1. Accept uploaded media file and validate MIME/size.
2. Load EfficientNet-B0 model weights (`best_effnetb0.pth`).
3. Preprocess image to model input shape.
4. Run binary classification:
   - Class 0 = REAL
   - Class 1 = FAKE
5. Compute confidence + class probabilities.
6. Generate Grad-CAM heatmap for visual explainability.
7. Extract metadata/EXIF clues (software tags, missing camera info, etc.).
8. Return response with verdict, confidence, probabilities, evidence, and heatmap.

Performance design:
- ML inference is offloaded to a thread executor so FastAPI async event loop is not blocked.

---

## 8) Video Detection Status (Current Reality)

What is implemented now:
- Video MIME types are accepted in media endpoint validation.
- UI supports media upload/preview and analysis flow for image/video assets.

Current backend limitation:
- The media analysis path currently routes bytes through the image-oriented detector pipeline.
- A dedicated backend video forensics module (true frame extraction + temporal deepfake modeling) is not yet fully implemented as a separate production path in current code.

How to present this accurately:
- “Video support exists at input/product level, while advanced dedicated video deepfake modeling is part of future scope.”

---

## 9) OCR Path for Image Claims (Text Extraction)

In v3 input handling:
- `InputType.IMAGE` uses OCR processing via EasyOCR.
- Base64 image input -> OCR text extraction -> same claim extraction/classification pipeline as text.

Use case:
- Screenshots/memes containing textual claims can be investigated as claim text after OCR.

---

## 10) Database and Data Persistence

Primary tables:
- `users`: auth/profile
- `checks`: stored analysis outputs (claim, verdict, confidence, explanation, metadata, timestamps)

Why this is important:
- Unified history for web and extension clients.
- Every authenticated check can be traced and reviewed later.

History API:
- `/api/v1/history` for list/get/delete/clear operations.

---

## 11) Authentication and Security Model
- JWT-based authentication
- Password hashing with bcrypt-compatible flow
- Protected endpoints use auth dependency (`get_current_user`)

Extension + web sync note:
- Extension can reuse backend session token model for consistent user history.

---

## 12) Deployment and Local Run
Using Docker Compose, default local ports:
- Frontend dev: `5173`
- Frontend prod container: `8081`
- Backend API: `8000`
- PostgreSQL: `5432`
- PgAdmin: `5050`

---

## 13) Key Strengths
- Evidence-first verification philosophy
- Modular architecture with separate services and pipelines
- Strong image deepfake explainability (Grad-CAM + metadata evidence)
- Real product surface: web app + extension + history persistence

---

## 14) Current Limitations and Future Scope
Current limitations:
- Dependence on external APIs (rate limits/outages)
- Ambiguous claims can remain inconclusive
- Dedicated advanced video deepfake backend path still evolving
- LLM-dependent features require configured keys

Future scope:
- Dedicated frame-temporal video forensics model
- Larger benchmark/test datasets
- Better multilingual coverage
- Improved calibration and explainability metrics
- Production-grade migration/versioning strategy

---

## 15) Existing Docs You Already Have
If you want deeper detail, these files already exist:
- `docs/CODEBASE_DOCUMENTATION.md` (most complete file-by-file reference)
- `docs/REVIEW_BACKEND_OVERVIEW.md`
- `docs/REVIEW_DATABASE_OVERVIEW.md`
- `docs/REVIEW_FACTCHECK_IMAGE_MODEL.md`
- `docs/REVIEW_EXTENSION_OVERVIEW.md`
- `docs/SYSTEM_ANALYSIS_AUDIT.md`

This `PROJECT_SUMMARY.md` is the concise “one-file revision + presentation” version.
