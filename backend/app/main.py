from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import ensure_indexes
from app.routers.auth import router as auth_router
from app.routers.reports import router as reports_router

settings = get_settings()

app = FastAPI(title="Medical Report Simplifier API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Startup event
@app.on_event("startup")
def on_startup() -> None:
    ensure_indexes()

# Root route (Option 2 fix)
@app.get("/")
def root():
    return {"message": "Medical Report Simplifier API is running"}

# Health check route
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Routers
app.include_router(auth_router)
app.include_router(reports_router)