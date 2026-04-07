from datetime import datetime, timezone
from pathlib import Path
from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pymongo.database import Database
from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.auth import UserResponse
from app.schemas.report import ReportResponse, SimplifyTextRequest, UploadResponse
from app.services.ocr import OCRUnavailableError, extract_text_from_file
from app.services.simplify import extract_important_terms, simplify_text
from app.utils.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()


def _serialize_report(report: dict) -> dict:
    return {
        "id": str(report["_id"]),
        "user_id": report["user_id"],
        "file_name": report["file_name"],
        "extracted_text": report["extracted_text"],
        "simplified_text": report["simplified_text"],
        "important_terms": report.get("important_terms", []),
        "created_at": report["created_at"],
    }


@router.post("/simplify-text", response_model=UploadResponse)
def simplify_raw_text(
    payload: SimplifyTextRequest,
    save_result: bool = False,
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    extracted_text = payload.text.strip()
    simplified_text = simplify_text(extracted_text)
    terms = extract_important_terms(extracted_text)

    if save_result:
        report_doc = {
            "user_id": current_user.id,
            "file_name": "manual_text_entry.txt",
            "extracted_text": extracted_text,
            "simplified_text": simplified_text,
            "important_terms": terms,
            "created_at": datetime.now(timezone.utc),
        }
        inserted = db["reports"].insert_one(report_doc)
        report = db["reports"].find_one({"_id": inserted.inserted_id})
        created_at = report_doc["created_at"] if not report else report["created_at"]
    else:
        report = None
        created_at = datetime.now(timezone.utc)

    return UploadResponse(
        saved=save_result,
        report=_serialize_report(report) if report else None,
        file_name="manual_text_entry.txt",
        extracted_text=extracted_text,
        simplified_text=simplified_text,
        important_terms=terms,
        created_at=created_at
    )


@router.get("", response_model=list[ReportResponse])
def list_reports(current_user: UserResponse = Depends(get_current_user), db: Database = Depends(get_db)):
    reports = (
        db["reports"]
        .find({"user_id": current_user.id})
        .sort("created_at", -1)
    )
    return [_serialize_report(report) for report in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    if not ObjectId.is_valid(report_id):
        raise HTTPException(status_code=404, detail="Report not found")

    report = db["reports"].find_one({"_id": ObjectId(report_id), "user_id": current_user.id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _serialize_report(report)


@router.post("/upload", response_model=UploadResponse)
async def upload_report(
    file: UploadFile = File(...),
    save_result: bool = Form(True),
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".pdf"}:
        raise HTTPException(status_code=400, detail="Only PNG, JPG, JPEG, and PDF are supported")

    file_bytes = await file.read()
    try:
        extracted_text = extract_text_from_file(file.filename, file_bytes)
    except OCRUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    simplified_text = simplify_text(extracted_text)
    terms = extract_important_terms(extracted_text)

    if save_result:
        report_doc = {
            "user_id": current_user.id,
            "file_name": file.filename,
            "extracted_text": extracted_text or "",
            "simplified_text": simplified_text,
            "important_terms": terms,
            "created_at": datetime.now(timezone.utc),
        }
        inserted = db["reports"].insert_one(report_doc)
        report = db["reports"].find_one({"_id": inserted.inserted_id})
        created_at = report_doc["created_at"] if not report else report["created_at"]
    else:
        report = None
        created_at = datetime.now(timezone.utc)

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    (upload_dir / safe_name).write_bytes(file_bytes)

    return UploadResponse(
        saved=save_result,
        report=_serialize_report(report) if report else None,
        file_name=file.filename,
        extracted_text=extracted_text,
        simplified_text=simplified_text,
        important_terms=terms,
        created_at=created_at
    )
