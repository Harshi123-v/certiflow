from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.models.job import GenerationJob
from app.models.certificate import CertificateRecord
from app.schemas.job import (
    JobCreateRequest,
    JobCreateResponse,
    JobDetailResponse,
    JobSummaryResponse,
    JobListResponse,
    RecipientListResponse,
)
from app.schemas.certificate import RecipientResponse
from app.services.generation_service import generation_service
from app.services.storage_service import storage_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])

def compute_job_stats(db: Session, job: GenerationJob):
    """Computes real-time progress and counts from persisted recipient records."""
    recipients = db.query(CertificateRecord.status).filter(
        CertificateRecord.job_id == job.id
    ).all()
    
    total = job.total_recipients
    completed = sum(1 for r in recipients if r[0] == "completed")
    failed = sum(1 for r in recipients if r[0] == "failed")
    processing = sum(1 for r in recipients if r[0] == "processing")
    pending = sum(1 for r in recipients if r[0] == "pending")
    
    progress = round(((completed + failed) / total * 100), 1) if total > 0 else 0.0

    return {
        "successful_certificates": completed,
        "failed_certificates": failed,
        "processing_recipients": processing,
        "pending_recipients": pending,
        "progress_percentage": progress,
        "download_all_url": f"/api/v1/jobs/{job.id}/download" if completed > 0 else None
    }

@router.post("", response_model=JobCreateResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Creates a new bulk generation job.
    Accepts job metadata and a list of recipients.
    Validates records, flags any individual failures, queues valid records,
    and dispatches background generation.
    """
    job, valid_count, invalid_count = generation_service.create_generation_job(db, request)

    # Dispatch background worker
    background_tasks.add_task(generation_service.process_job, job.id)

    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_recipients,
        valid_recipients=valid_count,
        invalid_recipients=invalid_count,
        created_at=job.created_at,
        message=f"Generation job created with {valid_count} valid recipient(s) queued."
    )

@router.get("", response_model=JobListResponse)
def list_jobs(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by job status"),
    search: Optional[str] = Query(None, description="Search by title, course name, or organization"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lists generation jobs sorted by creation date descending."""
    query = db.query(GenerationJob)
    
    if status_filter:
        query = query.filter(GenerationJob.status == status_filter)
        
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (GenerationJob.id.ilike(search_pattern)) |
            (GenerationJob.course_name.ilike(search_pattern)) |
            (GenerationJob.organization_name.ilike(search_pattern)) |
            (GenerationJob.title.ilike(search_pattern))
        )
        
    total = query.count()
    jobs = query.order_by(desc(GenerationJob.created_at)).offset(offset).limit(limit).all()

    items = []
    for job in jobs:
        stats = compute_job_stats(db, job)
        items.append(
            JobSummaryResponse(
                id=job.id,
                status=job.status,
                title=job.title,
                course_name=job.course_name,
                organization_name=job.organization_name,
                completion_date=job.completion_date,
                signatory_name=job.signatory_name,
                total_recipients=job.total_recipients,
                successful_certificates=stats["successful_certificates"],
                failed_certificates=stats["failed_certificates"],
                pending_recipients=stats["pending_recipients"],
                processing_recipients=stats["processing_recipients"],
                progress_percentage=stats["progress_percentage"],
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                download_all_url=stats["download_all_url"]
            )
        )

    return JobListResponse(total=total, items=items)

@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job_detail(job_id: str, db: Session = Depends(get_db)):
    """Retrieves full details of a specific generation job with recipient summaries."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found."
        )

    stats = compute_job_stats(db, job)

    # Fetch recipient records
    recipients = db.query(CertificateRecord).filter(
        CertificateRecord.job_id == job.id
    ).order_by(CertificateRecord.id).all()

    recipient_responses = []
    for r in recipients:
        download_url = f"/api/v1/certificates/{r.certificate_id}/download" if r.status == "completed" else None
        recipient_responses.append(
            RecipientResponse(
                id=r.id,
                job_id=r.job_id,
                recipient_name=r.recipient_name,
                recipient_email=r.recipient_email,
                certificate_id=r.certificate_id,
                status=r.status,
                file_path=r.file_path,
                error_message=r.error_message,
                created_at=r.created_at,
                completed_at=r.completed_at,
                download_url=download_url
            )
        )

    return JobDetailResponse(
        id=job.id,
        status=job.status,
        title=job.title,
        course_name=job.course_name,
        organization_name=job.organization_name,
        completion_date=job.completion_date,
        signatory_name=job.signatory_name,
        signatory_title=job.signatory_title,
        total_recipients=job.total_recipients,
        successful_certificates=stats["successful_certificates"],
        failed_certificates=stats["failed_certificates"],
        pending_recipients=stats["pending_recipients"],
        processing_recipients=stats["processing_recipients"],
        progress_percentage=stats["progress_percentage"],
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        download_all_url=stats["download_all_url"],
        recipients=recipient_responses
    )

@router.get("/{job_id}/recipients", response_model=RecipientListResponse)
def get_job_recipients(
    job_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Retrieves paginated recipient results for a specific job."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found."
        )

    query = db.query(CertificateRecord).filter(CertificateRecord.job_id == job_id)
    if status_filter:
        query = query.filter(CertificateRecord.status == status_filter)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (CertificateRecord.recipient_name.ilike(search_pattern)) |
            (CertificateRecord.recipient_email.ilike(search_pattern)) |
            (CertificateRecord.certificate_id.ilike(search_pattern))
        )

    total = query.count()
    recipients = query.order_by(CertificateRecord.id).offset(offset).limit(limit).all()

    items = []
    for r in recipients:
        download_url = f"/api/v1/certificates/{r.certificate_id}/download" if r.status == "completed" else None
        items.append(
            RecipientResponse(
                id=r.id,
                job_id=r.job_id,
                recipient_name=r.recipient_name,
                recipient_email=r.recipient_email,
                certificate_id=r.certificate_id,
                status=r.status,
                file_path=r.file_path,
                error_message=r.error_message,
                created_at=r.created_at,
                completed_at=r.completed_at,
                download_url=download_url
            )
        )

    return RecipientListResponse(job_id=job_id, total=total, items=items)

@router.get("/{job_id}/download")
def download_job_certificates_zip(job_id: str, db: Session = Depends(get_db)):
    """
    Generates and returns a ZIP archive containing all successfully generated certificates
    for the requested job.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found."
        )

    successful_records = db.query(CertificateRecord).filter(
        CertificateRecord.job_id == job_id,
        CertificateRecord.status == "completed"
    ).all()

    if not successful_records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No successful certificates available for download in this job."
        )

    cert_paths = []
    for r in successful_records:
        if r.file_path and Path(r.file_path).exists():
            cert_paths.append(Path(r.file_path))

    if not cert_paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate PDF files could not be located on storage."
        )

    zip_file = storage_service.create_job_zip(job_id, cert_paths)
    safe_download_name = f"Certificates_{job.course_name.replace(' ', '_')[:30]}_{job_id[:8]}.zip"

    return FileResponse(
        path=zip_file,
        media_type="application/zip",
        filename=safe_download_name
    )

@router.get("/{job_id}/export/csv")
def export_job_recipients_csv(job_id: str, db: Session = Depends(get_db)):
    """
    Exports all recipient records and statuses for this job into a CSV spreadsheet
    directly openable in Microsoft Excel.
    """
    import csv
    import io
    from fastapi import Response

    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found."
        )

    recipients = db.query(CertificateRecord).filter(
        CertificateRecord.job_id == job_id
    ).order_by(CertificateRecord.id).all()

    output = io.StringIO()
    # Write UTF-8 BOM so Microsoft Excel automatically recognizes character encoding
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        "Recipient Name",
        "Recipient Email",
        "Certificate ID",
        "Status",
        "Course Name",
        "Organization",
        "Completion Date",
        "Signatory Name",
        "Signatory Title",
        "Failure Reason",
        "Download URL"
    ])

    for r in recipients:
        download_url = f"/api/v1/certificates/{r.certificate_id}/download" if r.status == "completed" else "N/A"
        writer.writerow([
            r.recipient_name,
            r.recipient_email,
            r.certificate_id,
            r.status,
            job.course_name,
            job.organization_name,
            job.completion_date,
            job.signatory_name,
            job.signatory_title or "",
            r.error_message or "",
            download_url
        ])

    csv_data = output.getvalue()
    safe_filename = f"CertiFlow_Report_{job.course_name.replace(' ', '_')[:30]}_{job_id[:8]}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"'
        }
    )

