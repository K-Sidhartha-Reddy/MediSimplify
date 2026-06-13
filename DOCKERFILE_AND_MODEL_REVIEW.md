# Dockerfile Review & Model Deployment Strategy

## Dockerfile: Will It Work?

**Yes**, the updated Dockerfile will successfully run all required dependencies on Hugging Face Spaces.

### Verification Checklist

✅ **FastAPI** — Comes from `requirements.txt` (fastapi==0.115.6, uvicorn[standard]==0.32.1)

✅ **torch** — Installed separately before requirements.txt to optimize disk usage and avoid conflicts (torch==2.6.0)

✅ **transformers** — Comes from `requirements.txt` (transformers==4.47.1)

✅ **pytesseract** — Comes from `requirements.txt` (pytesseract==0.3.13) + system package `tesseract-ocr`

✅ **PyMuPDF (fitz)** — Comes from `requirements.txt` (PyMuPDF==1.25.1)

### System Dependencies Added

- **tesseract-ocr** — Required for pytesseract OCR
- **libglib2.0-0, libsm6, libxext6, libxrender1** — Required for PIL/Image processing
- **libc6** — Required for torch on some systems (now explicitly included)
- **git** — For potential git operations or future model management

### Hugging Face Spaces Optimizations

The updated Dockerfile now includes:

1. **Environment variables for model caching**
   ```dockerfile
   HF_HOME=/data/.huggingface
   TRANSFORMERS_CACHE=/data/.cache/huggingface
   TORCH_HOME=/data/.cache/torch
   ```
   These persist model downloads across Spaces restarts, reducing download time.

2. **Torch installed separately**
   ```dockerfile
   RUN pip install --no-cache-dir torch==2.6.0 && \
       pip install --no-cache-dir -r requirements.txt
   ```
   This prevents disk space issues during build and allows torch to finish downloading independently.

3. **Port 7860**
   ```dockerfile
   EXPOSE 7860
   ```
   Spaces default port. FastAPI runs on this port as configured.

---

## Model Deployment: Recommended Strategy

### The Question

You have ~19 GB of custom model files. Should they be:
1. Uploaded to the Space repository?
2. Uploaded to a Hugging Face Model repository?
3. Downloaded during startup?

### The Answer: Option 2 + 3 Combined

**Upload to Hugging Face Model repositories and download at startup.**

### Why Not the Alternatives

❌ **Option 1 (Upload to Space repo)**
- Bloats git context by 19 GB
- Slows container builds significantly
- Wastes Spaces persistent storage quota

❌ **Option 3 alone (Download during startup)**
- Without uploading to Hub first, where would they download from?
- Still requires hosting the models somewhere

✅ **Option 2 + 3 (Upload to Hub, download at startup)**
- Separates code from weights
- Models are versioned and accessible
- Caching via HF_HOME persists across restarts
- Fast subsequent starts (model cached)
- Only runtime model (t5-medical-new) needs to download
- Reduces deployment footprint to < 100 MB

---

## How It Works

1. **Upload once to Hub**
   ```bash
   huggingface-cli login
   # Then upload each model repo
   ```

2. **Reference in environment variable**
   ```
   SIMPLIFIER_MODEL_NAME_OR_PATH=your-username/t5-medical-new
   ```

3. **Backend downloads on first request**
   ```python
   model = pipeline("summarization", model=MODEL_NAME_OR_PATH)
   # Hugging Face SDK automatically:
   # 1. Downloads to HF_HOME if not cached
   # 2. Caches it for future use
   ```

4. **Subsequent requests use cached model** (instant)

---

## Generated Files

1. **backend/Dockerfile** — Updated with:
   - HF_HOME, TRANSFORMERS_CACHE, TORCH_HOME environment variables
   - Torch installed separately
   - Additional system packages (libc6, git)

2. **MODEL_DEPLOYMENT_STRATEGY.md** — Complete guide including:
   - Step-by-step commands to upload each model to Hub
   - Environment variable configuration
   - Local testing instructions
   - Spaces deployment commands
   - Troubleshooting tips

---

## Quick Start Commands

### Upload t5-medical-new to Hub

```bash
pip install huggingface-hub

huggingface-cli login

cd /Users/ksidharthareddy/medicalreportsimplifier/models/t5-medical-new
git init
git lfs install
git lfs track "*.safetensors" "*.json" "*.txt" "spiece.model" "tokenizer.json"
git add .gitattributes
git commit -m "Setup Git LFS"
git remote add origin https://huggingface.co/<your-username>/t5-medical-new
git branch -M main
git push -u origin main
```

### Deploy to Hugging Face Spaces

```bash
cd /Users/ksidharthareddy/medicalreportsimplifier

git subtree split --prefix backend -b backend-spaces
git push https://huggingface.co/spaces/<your-username>/medical-report-simplifier backend-spaces:main

# Then set these env vars in Spaces UI:
# SIMPLIFIER_MODEL_NAME_OR_PATH = your-username/t5-medical-new
# MONGODB_URL, SECRET_KEY, CORS_ORIGINS, etc.
```

### Deploy to Vercel

```bash
cd frontend
npm install
vercel login
vercel link
vercel env add NEXT_PUBLIC_API_URL production # Value: /api
vercel env add BACKEND_ORIGIN production # Value: https://<spaces-url>.hf.space
vercel deploy --prod
```

---

## Timeline

- **Model upload:** 5–10 min per model
- **Spaces deployment:** 2–5 min
- **Vercel deployment:** 2–5 min
- **Total:** ~30 min for full deployment

---

## Files to Review

- [backend/Dockerfile](backend/Dockerfile) — Updated with optimizations
- [MODEL_DEPLOYMENT_STRATEGY.md](MODEL_DEPLOYMENT_STRATEGY.md) — Full deployment guide
- [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md) — Architecture overview
