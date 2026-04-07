from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    id: str
    user_id: str
    file_name: str
    extracted_text: str
    simplified_text: str
    important_terms: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadResponse(BaseModel):
    saved: bool
    report: ReportResponse | None
    file_name: str
    extracted_text: str
    simplified_text: str
    important_terms: list[str]
    created_at: datetime


class SimplifyTextRequest(BaseModel):
    text: str
