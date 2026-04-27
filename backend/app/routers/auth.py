from fastapi import APIRouter, Depends, HTTPException, status, Response
from datetime import datetime, timezone
from pymongo.database import Database
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest

router = APIRouter(prefix="/auth", tags=["auth"])


# Handle CORS preflight requests
@router.options("/signup")
@router.options("/login")
def handle_options():
    return Response(status_code=200)


def _serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "full_name": user["full_name"],
        "created_at": user["created_at"],
    }


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignupRequest, db: Database = Depends(get_db)):
    users = db["users"]
    existing = users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    user_doc = {
        "email": payload.email,
        "full_name": payload.full_name,
        "hashed_password": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc),
    }
    inserted = users.insert_one(user_doc)
    user = users.find_one({"_id": inserted.inserted_id})

    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

    return AuthResponse(access_token=create_access_token(str(user["_id"])), user=_serialize_user(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Database = Depends(get_db)):
    users = db["users"]
    user = users.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return AuthResponse(access_token=create_access_token(str(user["_id"])), user=_serialize_user(user))
