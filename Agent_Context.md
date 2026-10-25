# Agent Context & Decisions Log

## Overview
This document logs major decisions, architectural notes, and operational context for TruthLens development and environment management.

## Decisions Log

### [2026-10-25] Project Startup & Environment Strategy
- **Decision**: Initialize Docker Compose orchestration for running TruthLens (`postgres`, `backend`, and `client`).
- **Context**: The user requested to run the project. TruthLens consists of a PostgreSQL database with initialization scripts, a FastAPI backend with PyTorch/NLP dependencies, and a React Vite client configured to proxy requests to `http://backend:8000`. Running via Docker Compose satisfies the multi-container architecture and isolated dependencies defined in `docker-compose.yml`.

### [2026-10-25] SQLAlchemy Asyncio Greenlet Dependency & Layer Caching Fix
- **Decision**: Added `greenlet>=3.0.0` and `sqlalchemy[asyncio]>=2.0.0` to `backend/requirements.txt` and separated PyTorch CPU wheel installation into its own layer in `backend/Dockerfile`.
- **Context**: The FastAPI backend crashed on startup because SQLAlchemy 2.0's asyncio engine (`postgresql+asyncpg`) requires the `greenlet` library to function, which was missing from `requirements.txt`. Separating the heavy PyTorch download into its own Docker layer prevents subsequent requirements changes from invalidating the PyTorch cache.

### [2026-10-25] Service Health Verification
- **Decision**: Verified full operational status across all services (PostgreSQL database healthy, FastAPI backend healthy at `:8000`, Vite development server active at `:5173`, and `/api` reverse proxy verified).
- **Context**: Successfully validated container connectivity, health checks, and API routing.

### [2026-10-25] Switch Deepfake Detector Weights to Production Model
- **Decision**: Updated default checkpoint path in `backend/app/services/deepfake.py` from `models/efficientnet_b3_best.pth` to `models/efficientnet_b3_production.pth`.
- **Context**: The user instructed to use `efficientnet_b3_production.pth`, which provides the validated production weights for EfficientNet-B3 deepfake detection and multi-patch analysis.

### [2026-10-25] Migration from Deprecated `google-generativeai` to `google-genai` & Model Update
- **Decision**: 
  1. Replaced the deprecated `google-generativeai` library with the modern Google GenAI SDK (`google-genai>=1.0.0`) across all backend services.
  2. Upgraded legacy `gemini-2.5-flash` / `gemini-1.5-flash` model references to `gemini-3.5-flash` (with support for `gemini-3.8-flash`).
  3. Added `gemini_model: str = "gemini-3.5-flash"` to `backend/app/core/config.py` to centralize model selection.
- **Context**: 
  Google terminated support for the legacy `google.generativeai` package and returned `404 NOT_FOUND` for `gemini-2.5-flash` / `gemini-1.5-flash` indicating that older models are no longer available to new users. The official `google-genai` SDK is now used across all 8 AI services (`claim_extractor.py`, `stance.py`, `llm_verdict.py`, `factcheck.py`, `explanation.py`, `crux_extractor.py`, `deepfake.py`, and `investigation/explanation.py`).


### [2026-10-25] Fix Text Investigation Crash (`OverflowError: Python int too large to convert to C ssize_t`)
- **Decision**: 
  1. Updated `ModelManager` (`backend/app/services/models/model_manager.py`) to load spaCy using `spacy.load("en_core_web_sm", exclude=["tokenizer"])`.
  2. Updated `claim_extractor.py` (`backend/app/services/claim_extractor.py`) and `scripts/download_models.py` with `exclude=["tokenizer"]`.
- **Context**: 
  When investigating text via `/api/v3/investigate`, the request crashed with `500 Internal Server Error: Investigation failed: Python int too large to convert to C ssize_t`. 
  This failure occurs because spaCy's `en_core_web_sm` model deserializes tokenizer rules via `Tokenizer.from_disk() -> self.rules = {} -> self._flush_specials()`. In `Tokenizer._flush_specials()`, spaCy iterates over `self._specials` (a `PreshMap` from `preshed`) and executes `del self._specials[k]`. The keys in `PreshMap` are 64-bit uint hashes (`uint64_t`), many of which exceed `2**63 - 1` (`SSIZE_MAX`). Because `PreshMap` implements Cython's sequence slot (`sq_ass_item`), Python's item deletion invokes `PyNumber_AsSsize_t(k)` which raises an `OverflowError` on 64-bit systems.
  Specifying `exclude=["tokenizer"]` instructs spaCy to use its standard English tokenizer (which handles sentence splitting, punctuation, words, and contractions identically) without deserializing the custom binary special-case rules that cause the overflow. All core NLP components (`tok2vec`, `tagger`, `parser`, `senter`, `ner`, `attribute_ruler`, `lemmatizer`) remain fully loaded and operational for claim extraction and linguistic analysis.


### [2026-10-25] Investigation Pacing & 85% Progress UX Enhancement
- **Decision**: 
  1. Enhanced `NeuralStream.tsx` to dynamically crawl progress from 85% towards 94% during `analyzing_stance` instead of freezing flat at 85%.
  2. Updated rotating thought stream messages during `analyzing_stance` to make live neural processing explicit.
  3. Added a 60-second safety timeout race in `InvestigationPage.tsx` to ensure requests never hang indefinitely without a descriptive error.
- **Context**: 
  The frontend fast-tracks setup steps (extracting, querying misinfo records, and Wikidata) within ~4.4 seconds using brief pacing delays, reaching step 5 (`analyzing_stance`, mapped to 85%). At 85%, the UI awaits the backend's live multi-source investigation (web search, scraping, and CPU-bound BART-large-mnli zero-shot stance detection across 3-5 articles), which takes ~10-20 seconds on CPU. Because the progress bar previously hard-stopped at flat 85%, users perceived the application as stuck or frozen. The dynamic crawl and updated indicators provide continuous visual confirmation of ongoing neural processing.


### [2026-10-25] Fix Political & Factual Leader Claims Verification (Wikidata Verifier)
- **Decision**: 
  1. Updated `User-Agent` in `backend/app/services/evidence/wikidata_verifier.py` to `TruthLensApp/1.0 (contact@truthlens.com; https://truthlens.digital)` to prevent Wikimedia API from blocking requests with HTTP 403 Forbidden.
  2. Added extraction patterns for `president`, `prime minister`, and `ceo` to `quick_fact_check` in `wikidata_verifier.py`.
  3. Structured the `reason` field on verification mismatch to explicitly state the actual office holder: `"Records show {actual_value} is the {property_name} of {entity_name}, not {claimed_value}."`
- **Context**: 
  Claims like `"Donald trump is the president of India"` were erroneously returning `unverified` instead of `verified_false`. Investigation revealed two issues:
  1. Wikimedia API rejected requests from `TruthLens/1.0` with `403 Forbidden` because Wikimedia requires a contact email in the User-Agent header.
  2. `quick_fact_check` only matched `first prime minister`, `capital`, and `birth year` patterns, omitting current presidents, prime ministers, and CEOs.
  With the updated User-Agent and patterns, `PoliticalStrategy` and `InvestigationOrchestrator` now verify these claims against official Wikidata records in ~1 second, definitively returning `verified_false` (confidence: 1.0) with refuting evidence citing the actual office holder (`Droupadi Murmu`).


### [2026-10-25] Dependency Synchronization & Dockerfile Modernization
- **Decision**: 
  1. Synchronized ackend/requirements.txt with all application runtime imports:
     - Verified google-genai>=1.0.0 for Gemini 3.5 API calls.
     - Added greenlet>=3.0.0 and sqlalchemy[asyncio]>=2.0.0 for async PostgreSQL sessions.
     - Pinned crypt>=4.0.0,<5.0.0 to prevent breaking 72-byte password length assertions.
     - Added 
equests>=2.31.0 explicitly for URL content scraping fallbacks.
  2. Synchronized frontend dependencies in client/package.json and generated reproducible lock entries in client/package-lock.json.
  3. Optimized Dockerfiles:
     - ackend/Dockerfile: Consolidated build stages; isolated CPU PyTorch wheel installation; combined pip install, spaCy model download, and build-essential cleanup in a single cache-efficient layer.
     - client/Dockerfile & client/Dockerfile.prod: Modernized package installation with 
pm ci --no-audit --no-fund ensuring consistent, repeatable image builds across development and production environments.
     - docker-compose.yml: Configured TOKENIZERS_PARALLELISM=false to prevent tokenizer deadlocks, explicit container resource limits, and development watch synchronization.
- **Context**: 
  Requested to ensure all library changes are codified in dependency managers and Dockerfiles, enabling deterministic builds in local, containerized, and CI/CD pipelines.


### [2026-10-26] Shivam Branch Text Verification Audit & Frontend Video Upload Enablement
- **Decision**: 
  1. **Investigated Shivam Branch (`origin/shivam`) vs `uday` for Text Verification Performance**:
     - *Root Cause Analysis*: On `origin/shivam`, all strategies directly invoke `DuckDuckGoSearcher`, fetching concise ~150-character snippets that CPU-bound BART-Large-MNLI evaluates in ~0.5s each (~2.5s total). On `uday`, the addition of Firecrawl returned full-page markdown scrapes (up to 6,500 characters) into evidence snippets, multiplying CPU inference time to 10-15s per snippet (totaling 50-75s). Furthermore, `origin/shivam` deduplicated compound sub-claims in `ClaimExtractorV3`, while `uday` extracted duplicate sub-claims.
     - *Performance Fix*: Deduplicated sub-claims in `backend/app/services/extraction/claim_extractor_v3.py` via `sub_text not in [c.text for c in claims]`. Bounded stance snippet length to 500 characters in `backend/app/services/investigation/synthesizer.py` and 800 characters in `firecrawl.py`, preventing heavy transformer attention stalls on CPU while retaining full factual accuracy and Wikidata/spaCy fixes.
  2. **Preserved Video Pipeline Integrity**:
     - As explicitly instructed by the user, zero modifications were made to the backend image and video deepfake pipeline (`backend/app/services/deepfake.py`).
  3. **Enabled Frontend Video Uploads (`client/src/components/ImageVideoUpload.tsx`)**:
     - Replaced memory-stalling `FileReader.readAsDataURL` with zero-copy `URL.createObjectURL(file)`, instantly generating previews for videos and images without freezing the browser thread.
     - Added `URL.revokeObjectURL` cleanup on file removal and unmount.
     - Expanded input file accept pattern to `accept="image/*,video/*,.mp4,.mov,.avi,.webm,.mkv"` to ensure Windows file explorer does not filter out video extensions.
     - Changed upload button label from "Select Image" to "Select Image or Video" with an upload icon.
     - Added robust video MIME and extension detection for `<video>` rendering and UI indicators.
- **Context**: 
  User requested to compare text verification between `uday` and `origin/shivam` to explain why the friend's PC takes less time, optimize text verification without altering the backend image/video pipeline, and resolve the frontend blocking video file uploads.


### [2026-10-26] Video Pipeline Keyframe SynthID Screening Architecture
- **Decision**:
  1. Updated `DeepfakeDetector.predict` in `backend/app/services/deepfake.py` with a `check_gemini: bool = True` parameter.
  2. Implemented `DeepfakeDetector.analyze_video(video_bytes, n_frames=8)` with the following pipeline rule:
     - Sample $N$ evenly spaced keyframes across the video using OpenCV.
     - **Only ONE frame** (Keyframe 0) is sent to Gemini to check SynthID watermarking (`check_gemini=True`).
     - If Gemini flags SynthID, immediately early-exit with 100% confidence FAKE (`Google Gemini AI Detector (SynthID)`).
     - If no SynthID watermark is found on that keyframe, Keyframe 0 completes inference on the local model and **ALL other frames** bypass Gemini completely (`check_gemini=False`), running directly through the local `EfficientNet-B3` + Grad-CAM + MultiPatch fusion pipeline.
     - Frame predictions and evidence are aggregated into a unified video forensic report.
  3. Updated `analyze_image_for_deepfake` to route video MIME types (`video/mp4`, `video/quicktime`, `video/webm`, `video/avi`, `video/*`) to `detector.analyze_video`.
- **Context**: 
  User requested that for videos taking multiple frames, all frames should not go to Gemini; only ONE frame must go to Gemini to check SynthID, and all the remaining frames must go directly to our local model. This eliminates rate limits, reduces API quota consumption by ~88%, and prevents multi-second network roundtrips.
