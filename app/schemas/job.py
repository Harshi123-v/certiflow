from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.certificate import CertificateInfo, RecipientInput, RecipientResponse
from app.core.config import settings

class JobCreateRequest(BaseModel):
    certificate: CertificateInfo
    recipients: List[RecipientInput] = Field(..., description="List of certificate recipients")

    @field_validator("recipients")
    def validate_recipients_list(cls, v):
        if not v:
            raise ValueError("Recipients list cannot be empty. At least one recipient is required.")
        if len(v) > settings.MAX_BATCH_SIZE:
            raise ValueError(f"Batch size exceeds maximum limit of {settings.MAX_BATCH_SIZE} recipients.")
        return v

class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    total_recipients: int
    valid_recipients: int
    invalid_recipients: int
    created_at: datetime
    message: str

class JobDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    title: str
    course_name: str
    organization_name: str
    completion_date: str
    signatory_name: str
    signatory_title: Optional[str] = None
    total_recipients: int
    successful_certificates: int
    failed_certificates: int
    pending_recipients: int
    processing_recipients: int
    progress_percentage: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    download_all_url: Optional[str] = None
    recipients: Optional[List[RecipientResponse]] = None

class JobSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    title: str
    course_name: str
    organization_name: str
    completion_date: str
    signatory_name: str
    total_recipients: int
    successful_certificates: int
    failed_certificates: int
    pending_recipients: int
    processing_recipients: int
    progress_percentage: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    download_all_url: Optional[str] = None


class JobListResponse(BaseModel):
    total: int
    items: List[JobSummaryResponse]

class RecipientListResponse(BaseModel):
    job_id: str
    total: int
    items: List[RecipientResponse]
