# Medical Report Simplifier

A clean, startup-style MVP that helps users upload medical reports/prescriptions and receive simple, patient-friendly explanations.

## 1) Chosen stack

- Frontend: Next.js (App Router) + TypeScript + Tailwind CSS
- Backend: FastAPI + PyMongo
- Database: MongoDB
- Authentication: JWT (login/signup/logout)
- OCR: Tesseract OCR (`pytesseract`) + PDF rendering (`PyMuPDF`)
- AI Simplification: lightweight transformer pipeline (`flan-t5-small`) with medical-term replacement fallback

## 2) Folder structure

- frontend/: Next.js UI app
- backend/: FastAPI API app
- database/: legacy SQL schema (not used after MongoDB migration)

Key paths:
- frontend/app/: landing, auth, dashboard, report detail pages
- frontend/components/: reusable UI sections
- frontend/lib/: API client, auth store, types
- backend/app/routers/: auth + report APIs
- backend/app/services/: OCR + simplification logic
- backend/app/models/: legacy SQLAlchemy models (not used after MongoDB migration)
- backend/app/core/: config, DB, security

## 3) Database schema

Collections:
- users (`_id`, `email`, `full_name`, `hashed_password`, `created_at`)
- reports (`_id`, `user_id`, `file_name`, `extracted_text`, `simplified_text`, `important_terms`, `created_at`)

Legacy SQL file: [database/schema.sql](database/schema.sql)

## 4) Backend API plan

Auth:
- `POST /auth/signup`
- `POST /auth/login`

Reports:
- `POST /reports/upload` (file upload → OCR → simplify → optional save)
- `GET /reports` (user history)
- `GET /reports/{id}` (single report detail)

Utility:
- `GET /health`

## 5) UI plan

Landing:
- Premium hero + gradient style
- Feature cards
- How it works
- Benefits + CTA + footer

Auth:
- Clean login/signup cards
- Input validation
- Clear loading/error states

Dashboard:
- Welcome + quick stats cards
- Polished upload card
- Result card (original text + simplified + key terms)
- History list with detail pages

---

## Setup instructions

## Prerequisites

- Node.js 18+
- Python 3.11+
- MongoDB (local or Atlas)
- Tesseract installed
  - macOS: `brew install tesseract`

## Backend setup

1. Go to backend folder.
2. Create and activate virtual environment.
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Copy env:
   - `cp .env.example .env`
5. Update `MONGODB_URL`, `MONGODB_DB_NAME`, `SECRET_KEY`, and `TESSERACT_CMD` in `.env`.
6. Run API:
   - `uvicorn app.main:app --reload`

API will run on `http://localhost:8000`.

## Frontend setup

1. Go to frontend folder.
2. Install dependencies:
   - `npm install`
3. Copy env:
   - `cp .env.local.example .env.local`
4. Run app:
   - `npm run dev`

Frontend will run on `http://localhost:3000`.

Set `BACKEND_ORIGIN` in `frontend/.env.local` if your API runs on a different host/port. All frontend calls go through `/api` and are proxied to this backend, avoiding CORS issues.

---

## Notes

- The simplification pipeline uses `flan-t5-small`; if loading fails, the app falls back to a rule-based simplifier.
- Uploaded files are stored in `backend/uploads`.
- This is an MVP for demo/final-year project use.
