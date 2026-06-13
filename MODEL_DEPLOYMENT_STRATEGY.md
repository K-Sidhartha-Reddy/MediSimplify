# Model Deployment Strategy for Hugging Face Spaces

## Problem

The repo contains ~19 GB of custom-trained model checkpoints:
- `models/biobert-condition` (~1.6 GB)
- `models/t5-medical` (~2.3 GB)
- `models/t5-medical-v2` (~5.0 GB)
- `models/t5-medical-new` (~10 GB)

Uploading these to Spaces as-is will:
1. Bloat the git context (~19 GB).
2. Slow down container builds and startups.
3. Waste Spaces persistent storage quota.

## Recommendation: Upload to Hugging Face Model Repos + Download at Startup

**Best practice:** Publish each model as a separate Hugging Face Model repo, then download them on first use (cached via HF_HOME).

### Why this approach

✅ Separates code from weights  
✅ Models are versioned on Hugging Face Hub  
✅ Caching via HF_HOME persists across Spaces restarts  
✅ Only one model loads at runtime (t5-medical-new)  
✅ Reduces deployment context to < 100 MB  

---

## Step 1: Create Hugging Face Model Repos

Create one repo for each model you need:

### a) Upload `models/t5-medical-new` (runtime model)

```bash
# Install Hugging Face Hub CLI
pip install huggingface-hub

# Log in
huggingface-cli login

# Create local Git LFS setup
cd /Users/ksidharthareddy/medicalreportsimplifier/models/t5-medical-new
git init
git lfs install

# Track model files
git lfs track "*.safetensors" "*.bin" "*.pt" "*.json" "*.model" "*.txt" "spiece.model" "tokenizer.json"

# Initialize and push
git add .gitattributes
git commit -m "Setup Git LFS"
git remote add origin https://huggingface.co/<your-username>/t5-medical-new
git branch -M main
git push -u origin main
```

### b) Upload `models/biobert-condition` (used by ml_pipeline)

```bash
cd /Users/ksidharthareddy/medicalreportsimplifier/models/biobert-condition
git init
git lfs install
git lfs track "*.safetensors" "*.bin" "*.json" "*.txt" "tokenizer.json"
git add .gitattributes
git commit -m "Setup Git LFS"
git remote add origin https://huggingface.co/<your-username>/biobert-condition
git branch -M main
git push -u origin main
```

### c) Optionally archive `t5-medical`, `t5-medical-v2`

These are intermediate checkpoints. If they're not used in production, do not upload them. If they are used, repeat the process above.

---

## Step 2: Update Backend Code to Download at Startup

### Update `backend/app/services/simplify.py`

Already done via config. Just ensure SIMPLIFIER_MODEL_NAME_OR_PATH points to a Hub repo ID:

```python
# This now comes from the env var
SIMPLIFIER_MODEL_NAME_OR_PATH = settings.simplifier_model_name_or_path
# e.g., "your-username/t5-medical-new" or a local path for development
```

### Update `backend/app/services/ml_pipeline.py` (if needed)

The ml_pipeline currently loads biobert-condition hardcoded paths. If you upload it to Hub, update line 184:

```python
# OLD:
return AutoModel.from_pretrained("dmis-lab/biobert-base-cased-v1.2")

# NEW (if you want to use your custom checkpoint):
biobert_repo = os.getenv("BIOBERT_MODEL_NAME_OR_PATH", "dmis-lab/biobert-base-cased-v1.2")
return AutoModel.from_pretrained(biobert_repo)
```

---

## Step 3: Set Environment Variables on Hugging Face Spaces

Create a space with the backend deployment and set these env vars in the Spaces UI:

### Required env vars

```
MONGODB_URL=mongodb+srv://<user>:<password>@<cluster>/<db>?retryWrites=true&w=majority
MONGODB_DB_NAME=medical_report_simplifier
SECRET_KEY=your-secure-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
UPLOAD_DIR=./uploads
TESSERACT_CMD=tesseract
CORS_ORIGINS=https://<your-vercel-app>.vercel.app,http://localhost:3000

# Model repositories
SIMPLIFIER_MODEL_NAME_OR_PATH=your-username/t5-medical-new
# BIOBERT_MODEL_NAME_OR_PATH=your-username/biobert-condition  (optional)

# Optional: if model repos are private
HF_TOKEN=hf_your_huggingface_token_here

# Cache directories (already set in Dockerfile)
HF_HOME=/data/.huggingface
TRANSFORMERS_CACHE=/data/.cache/huggingface
TORCH_HOME=/data/.cache/torch
```

---

## Step 4: Test Locally

Before deploying to Spaces, test the model download:

```bash
cd /Users/ksidharthareddy/medicalreportsimplifier/backend
export SIMPLIFIER_MODEL_NAME_OR_PATH="your-username/t5-medical-new"
export HF_HOME=~/.huggingface
uvicorn app.main:app --reload
```

The first call to `/reports/upload` or `/reports/simplify-text` will download the model from Hub, then cache it.

---

## Step 5: Deploy to Hugging Face Spaces

### Create a new Spaces repo

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Name: e.g., `medical-report-simplifier`
4. Space SDK: Docker
5. Set to private if using a private model repo

### Deploy the backend

```bash
cd /Users/ksidharthareddy/medicalreportsimplifier

# Extract and push backend to Spaces
git subtree split --prefix backend -b backend-spaces
git push https://huggingface.co/spaces/<your-username>/medical-report-simplifier backend-spaces:main
```

Spaces will:
1. Build the Docker image (using the updated Dockerfile).
2. Set environment variables you configured in the UI.
3. Start the FastAPI server on port 7860.
4. First request will download models to `/data/.huggingface` (persistent).

---

## Step 6: Deploy Frontend to Vercel

```bash
cd /Users/ksidharthareddy/medicalreportsimplifier/frontend

npm install
vercel login
vercel link

# Set env vars
vercel env add NEXT_PUBLIC_API_URL production
# Value: /api

vercel env add BACKEND_ORIGIN production
# Value: https://<your-username>-medical-report-simplifier.hf.space

vercel deploy --prod
```

---

## Troubleshooting

### Model not downloading

Check the Spaces logs:
1. Go to your Spaces page.
2. Click "Logs".
3. Look for lines like `Loading simplification model from: your-username/t5-medical-new`.

### Permission denied downloading model

Ensure:
1. The model repo is public, OR
2. HF_TOKEN is set and has permission to access the private repo.

### Out of disk space

Spaces provides ~50 GB persistent storage at `/data`. If you have many large models, upload only the ones you use in production.

### Model cache not persisting

Verify that `/data/.huggingface` is being used (already set in the Dockerfile).

---

## File Changes Required

Files already updated:
- `backend/Dockerfile` — now sets HF_HOME, TRANSFORMERS_CACHE, TORCH_HOME
- `backend/app/core/config.py` — added SIMPLIFIER_MODEL_NAME_OR_PATH setting
- `backend/app/services/simplify.py` — loads model from config instead of hardcoded path
- `backend/.dockerignore` — excludes local models from build context
- `backend/.env.production.example` — documents SIMPLIFIER_MODEL_NAME_OR_PATH

---

## Summary

| Step | Action | Tool | Time |
|------|--------|------|------|
| 1 | Create Hugging Face Model repos | huggingface-cli + git lfs | 5–10 min per model |
| 2 | Update env vars in code | Already done | — |
| 3 | Configure Spaces env vars | Spaces UI | 2 min |
| 4 | Test locally | uvicorn | 1 min |
| 5 | Deploy backend to Spaces | git subtree + git push | 2–5 min |
| 6 | Deploy frontend to Vercel | vercel CLI | 2–5 min |

Total: ~30 min to have a fully deployed system.
