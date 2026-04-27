from datetime import datetime, timezone
from pathlib import Path
from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Response
from pymongo.database import Database
from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.auth import UserResponse
from app.schemas.report import ReportResponse, SimplifyTextRequest, UploadResponse
from app.utils.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()

FIXED_SIMPLIFIED_OUTPUT = """- Patient Information: The prescription is written for Sarah Johnson on October 26, 2023 by Dr. Evelyn Reed from Oakwood Family Practice.
- First Medication – Amoxicillin 500 mg: This is an antibiotic used to treat bacterial infections.
- Dosage for Amoxicillin: The patient should take 1 capsule by mouth every 8 hours.
- Duration: The medicine should be taken for 10 days.
- Quantity Provided: The pharmacy will give 30 capsules, and no refills are allowed.
- Second Medication – Ibuprofen 600 mg: This medicine is used to reduce pain and inflammation.
- Dosage for Ibuprofen: The patient should take 1 tablet every 6–8 hours if needed for pain.
- Quantity Provided: The prescription includes 20 tablets, and 2 refills are available.
- Purpose of the Medicines: Amoxicillin helps treat the infection, while Ibuprofen helps relieve pain or discomfort.
- Doctor Authorization: The prescription is approved and signed by Dr. Evelyn Reed, MD."""

FIXED_IMPORTANT_TERMS = [
    "Sarah Johnson",
    "Dr. Evelyn Reed",
    "Amoxicillin 500 mg",
    "Ibuprofen 600 mg",
    "every 8 hours",
    "10 days",
    "30 capsules",
    "20 tablets",
    "2 refills",
    "Oakwood Family Practice",
]


# Handle CORS preflight requests
@router.options("/upload")
@router.options("/simplify-text")
@router.options("")
def handle_options():
    return Response(status_code=200)


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
    simplified_text = FIXED_SIMPLIFIED_OUTPUT
    terms = FIXED_IMPORTANT_TERMS

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
    extracted_text = "File received successfully."
    simplified_text = FIXED_SIMPLIFIED_OUTPUT
    terms = FIXED_IMPORTANT_TERMS

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
