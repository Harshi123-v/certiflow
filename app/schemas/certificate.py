from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class CertificateInfo(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Certificate title (e.g. Certificate of Completion)")
    course_name: str = Field(..., min_length=1, max_length=255, description="Course or event name")
    organization_name: str = Field(..., min_length=1, max_length=255, description="Issuing organization name")
    completion_date: str = Field(..., min_length=1, max_length=50, description="Date of completion (YYYY-MM-DD or formatted)")
    signatory_name: str = Field(..., min_length=1, max_length=255, description="Name of the signatory")
    signatory_title: Optional[str] = Field("Program Director", max_length=255, description="Title of the signatory")

class RecipientInput(BaseModel):
    name: str = Field(..., description="Recipient full name")
    email: str = Field(..., description="Recipient email address")
    certificate_id: str = Field(..., description="Unique certificate ID")

class RecipientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: str
    recipient_name: str
    recipient_email: str
    certificate_id: str
    status: str
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None

class CertificateDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    certificate_id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    status: str
    title: str
    course_name: str
    organization_name: str
    completion_date: str
    signatory_name: str
    signatory_title: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None

