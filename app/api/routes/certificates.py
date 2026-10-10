from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.models.certificate import CertificateRecord
from app.models.job import GenerationJob
from app.schemas.certificate import CertificateDetailResponse
from app.services.pdf_service import pdf_service
from app.utils.validation import sanitize_filename

router = APIRouter(prefix="/certificates", tags=["Certificates"])

@router.get("/preview/sample")
def preview_sample_certificate():
    """Generates and returns an instant sample PDF for visual preview."""
    try:
        pdf_bytes = pdf_service.generate_preview_bytes()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline; filename=CertiFlow_Sample_Preview.pdf"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not generate preview PDF: {str(e)}"
        )

@router.get("/export/csv")
def export_all_certificates_csv(db: Session = Depends(get_db)):
    """Exports all certificates across all jobs to a CSV spreadsheet compatible with Microsoft Excel."""
    import csv
    import io

    records = db.query(CertificateRecord, GenerationJob).join(
        GenerationJob, CertificateRecord.job_id == GenerationJob.id
    ).order_by(desc(CertificateRecord.created_at)).all()

    output = io.StringIO()
    output.write('\ufeff') # UTF-8 BOM for Excel
    writer = csv.writer(output)
    writer.writerow([
        "Certificate ID",
        "Recipient Name",
        "Email",
        "Course Name",
        "Organization",
        "Status",
        "Completion Date",
        "Signatory Name",
        "Failure Reason",
        "Download URL"
    ])

    for cert, job in records:
        download_url = f"/api/v1/certificates/{cert.certificate_id}/download" if cert.status == "completed" else "N/A"
        writer.writerow([
            cert.certificate_id,
            cert.recipient_name,
            cert.recipient_email,
            job.course_name,
            job.organization_name,
            cert.status,
            job.completion_date,
            job.signatory_name,
            cert.error_message or "",
            download_url
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="CertiFlow_Master_Vault_Report.csv"'
        }
    )


@router.get("", response_model=List[CertificateDetailResponse])
def list_certificates(
    search: Optional[str] = Query(None, description="Search by recipient name, email, or certificate ID"),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lists generated certificates across all jobs."""
    query = db.query(CertificateRecord, GenerationJob).join(
        GenerationJob, CertificateRecord.job_id == GenerationJob.id
    )

    if status_filter:
        query = query.filter(CertificateRecord.status == status_filter)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (CertificateRecord.recipient_name.ilike(pattern)) |
            (CertificateRecord.recipient_email.ilike(pattern)) |
            (CertificateRecord.certificate_id.ilike(pattern))
        )

    records = query.order_by(desc(CertificateRecord.created_at)).offset(offset).limit(limit).all()

    results = []
    for cert, job in records:
        download_url = f"/api/v1/certificates/{cert.certificate_id}/download" if cert.status == "completed" else None
        results.append(
            CertificateDetailResponse(
                certificate_id=cert.certificate_id,
                job_id=cert.job_id,
                recipient_name=cert.recipient_name,
                recipient_email=cert.recipient_email,
                status=cert.status,
                title=job.title,
                course_name=job.course_name,
                organization_name=job.organization_name,
                completion_date=job.completion_date,
                signatory_name=job.signatory_name,
                signatory_title=job.signatory_title,
                created_at=cert.created_at,
                completed_at=cert.completed_at,
                download_url=download_url
            )
        )

    return results

@router.get("/{certificate_id}", response_model=CertificateDetailResponse)
def get_certificate_detail(certificate_id: str, db: Session = Depends(get_db)):
    """Retrieves full metadata for a specific certificate."""
    record = db.query(CertificateRecord, GenerationJob).join(
        GenerationJob, CertificateRecord.job_id == GenerationJob.id
    ).filter(CertificateRecord.certificate_id == certificate_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found."
        )

    cert, job = record
    download_url = f"/api/v1/certificates/{cert.certificate_id}/download" if cert.status == "completed" else None

    return CertificateDetailResponse(
        certificate_id=cert.certificate_id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        status=cert.status,
        title=job.title,
        course_name=job.course_name,
        organization_name=job.organization_name,
        completion_date=job.completion_date,
        signatory_name=job.signatory_name,
        signatory_title=job.signatory_title,
        created_at=cert.created_at,
        completed_at=cert.completed_at,
        download_url=download_url
    )

@router.get("/{certificate_id}/download")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """Downloads the generated PDF file for a certificate."""
    cert = db.query(CertificateRecord).filter(
        CertificateRecord.certificate_id == certificate_id
    ).first()

    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found."
        )

    if cert.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate '{certificate_id}' cannot be downloaded because its status is '{cert.status}'."
        )

    if not cert.file_path or not Path(cert.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate PDF file is missing on storage for '{certificate_id}'."
        )

    safe_name = sanitize_filename(f"{cert.recipient_name}_{cert.certificate_id}")

    return FileResponse(
        path=Path(cert.file_path),
        media_type="application/pdf",
        filename=safe_name
    )
