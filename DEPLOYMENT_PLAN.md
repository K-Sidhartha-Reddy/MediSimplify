# Deployment Plan

## Target architecture

- Frontend: Vercel-hosted Next.js app from `frontend/`
- Backend: Hugging Face Spaces Docker app from `backend/`
- Database: MongoDB Atlas

## Current runtime entrypoints

- FastAPI entry point: `backend/app/main.py`
- Vercel shim: `backend/api/index.py`
- Frontend API client: `frontend/lib/api.ts`
- Backend settings: `backend/app/core/config.py`
- Runtime simplifier loader: `backend/app/services/simplify.py`

## Required code changes

- `backend/app/core/config.py`
  - Adds `SIMPLIFIER_MODEL_NAME_OR_PATH` so the runtime summarizer can be a local path or a Hugging Face repo ID.
- `backend/app/services/simplify.py`
  - Loads the simplifier from the configured model path/Hub repo instead of a hardcoded local folder.
- `backend/Dockerfile`
  - Builds the backend for Hugging Face Spaces.
- `backend/.dockerignore`
  - Excludes local model folders so the 19 GB checkpoint tree is not shipped in the Docker build context.

## Environment variables

### Frontend on Vercel

- `NEXT_PUBLIC_API_URL=/api`
- `BACKEND_ORIGIN=https://<your-backend-space>.hf.space`

### Backend on Hugging Face Spaces

- `MONGODB_URL=mongodb+srv://...`
- `MONGODB_DB_NAME=medical_report_simplifier`
- `SECRET_KEY=...`
- `CORS_ORIGINS=https://<your-vercel-app>.vercel.app,http://localhost:3000`
- `TESSERACT_CMD=tesseract`
- `SIMPLIFIER_MODEL_NAME_OR_PATH=your-username/t5-medical-new`
- Optional: `HF_TOKEN=` if the model repo is private
- Recommended cache envs:
  - `HF_HOME=/data/.huggingface`
  - `TRANSFORMERS_CACHE=/data/.cache/huggingface`

## Model audit

Current model directories:

- `models/biobert-condition`
- `models/t5-medical`
- `models/t5-medical-v2`
- `models/t5-medical-new`

### 1) `models/biobert-condition`

- Custom trained: yes
- Hugging Face Hub replacement available: not in this repo
- Likely base model: `dmis-lab/biobert-base-cased-v1.2`
- Approx size: ~1.6 GB

### 2) `models/t5-medical`

- Custom trained: yes
- Hugging Face Hub replacement available: not in this repo
- Likely base model: `t5-small`
- Approx size: ~2.3 GB

### 3) `models/t5-medical-v2`

- Custom trained: yes
- Hugging Face Hub replacement available: not in this repo
- Likely base model: `t5-small`
- Approx size: ~5.0 GB

### 4) `models/t5-medical-new`

- Custom trained: yes
- Hugging Face Hub replacement available: not in this repo
- Likely base model: `t5-small`
- Approx size: ~10 GB

## Can the 19 GB of model files be avoided?

Yes, but only if you publish the fine-tuned checkpoints to Hugging Face Hub and load them at startup by repo ID. The current repo does not contain Hub IDs for the custom checkpoints, so you cannot fully replace them yet without uploading the weights first.

Recommended strategy:

1. Push each custom checkpoint you actually need to a Hugging Face model repo.
2. Keep only the runtime model that the backend uses.
3. Point `SIMPLIFIER_MODEL_NAME_OR_PATH` to the Hub repo ID.
4. Exclude `models/` from the backend deployment context.

If the extra training checkpoints are not needed in production, do not upload them.

## Deployment commands

### 1) Deploy backend to Hugging Face Spaces

```bash
cd /Users/ksidharthareddy/medicalreportsimplifier
git subtree split --prefix backend -b backend-spaces
git push https://huggingface.co/spaces/<username>/<space-name> backend-spaces:main
```

Before pushing, log in once:

```bash
huggingface-cli login
```

### 2) Deploy frontend to Vercel

```bash
cd /Users/ksidharthareddy/medicalreportsimplifier/frontend
npm install
vercel login
vercel link
vercel env add NEXT_PUBLIC_API_URL production
vercel env add BACKEND_ORIGIN production
vercel deploy --prod
```

## Why this platform split

- Vercel is ideal for the Next.js frontend.
- Hugging Face Spaces is a better fit for Transformers, Torch, OCR, and model downloads than Vercel.
- The backend needs a container-friendly runtime and model cache, which Spaces supports well.

## Vercel note

The backend is not a good Vercel serverless target because of large ML dependencies, heavy startup, and local model loading.