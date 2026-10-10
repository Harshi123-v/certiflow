import uuid
import logging
from datetime import datetime
from typing import Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import SessionLocal
from app.models.job import GenerationJob
from app.models.certificate import CertificateRecord
from app.schemas.job import JobCreateRequest
from app.services.storage_service import storage_service
from app.services.pdf_service import pdf_service
from app.utils.validation import validate_recipient_data

logger = logging.getLogger("certiflow.generation")

class GenerationService:
    def create_generation_job(
        self,
        db: Session,
        request: JobCreateRequest
    ) -> Tuple[GenerationJob, int, int]:
        """
        Creates a job and recipient records in the database.
        Implements partial failure handling:
        - Fundamentally valid request with individually invalid recipients creates
          the job, marks invalid recipients as 'failed', and stages valid ones as 'pending'.
        """
        job_id = str(uuid.uuid4())
        
        # Pre-fetch existing certificate IDs to check uniqueness against DB
        incoming_ids = [r.certificate_id.strip() for r in request.recipients if r.certificate_id]
        existing_ids_query = db.query(CertificateRecord.certificate_id).filter(
            CertificateRecord.certificate_id.in_(incoming_ids)
        ).all()
        existing_ids = {row[0] for row in existing_ids_query}
        
        seen_in_batch = set()
        valid_count = 0
        invalid_count = 0

        # Create Job record
        job = GenerationJob(
            id=job_id,
            status="queued",
            title=request.certificate.title.strip(),
            course_name=request.certificate.course_name.strip(),
            organization_name=request.certificate.organization_name.strip(),
            completion_date=request.certificate.completion_date.strip(),
            signatory_name=request.certificate.signatory_name.strip(),
            signatory_title=(request.certificate.signatory_title or "Program Director").strip(),
            total_recipients=len(request.recipients),
            send_emails=False,
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.flush()

        # Create Recipient records
        for r in request.recipients:
            is_valid, err_msg = validate_recipient_data(
                name=r.name,
                email=r.email,
                certificate_id=r.certificate_id,
                seen_in_batch=seen_in_batch,
                existing_in_db=existing_ids
            )
            
            clean_cert_id = r.certificate_id.strip() if r.certificate_id else f"INVALID-{uuid.uuid4().hex[:8]}"

            if is_valid:
                seen_in_batch.add(clean_cert_id)
                rec_record = CertificateRecord(
                    job_id=job_id,
                    recipient_name=r.name.strip(),
                    recipient_email=r.email.strip(),
                    certificate_id=clean_cert_id,
                    status="pending",
                    error_message=None,
                    email_sent=False,
                    email_status="not_configured",
                    created_at=datetime.utcnow()
                )
                valid_count += 1
            else:
                # If cert ID was duplicate in batch, assign unique dummy key in DB if collision occurs
                if clean_cert_id in seen_in_batch or clean_cert_id in existing_ids:
                    store_cert_id = f"{clean_cert_id}-dup-{uuid.uuid4().hex[:6]}"
                else:
                    store_cert_id = clean_cert_id
                    seen_in_batch.add(store_cert_id)

                rec_record = CertificateRecord(
                    job_id=job_id,
                    recipient_name=(r.name or "").strip(),
                    recipient_email=(r.email or "").strip(),
                    certificate_id=store_cert_id,
                    status="failed",
                    error_message=err_msg,
                    email_sent=False,
                    email_status="not_configured",
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                invalid_count += 1

            db.add(rec_record)

        db.commit()
        db.refresh(job)
        return job, valid_count, invalid_count

    def process_job(self, job_id: str) -> None:
        """
        Background worker entrypoint to process all pending recipients of a job.
        Uses its own fresh DB session for thread/worker safety.
        Performs per-recipient error isolation.
        """
        db = SessionLocal()
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                logger.error(f"Job not found for ID: {job_id}")
                return

            # Update job status to processing
            job.status = "processing"
            job.started_at = datetime.utcnow()
            db.commit()

            cert_metadata = {
                "title": job.title,
                "course_name": job.course_name,
                "organization_name": job.organization_name,
                "completion_date": job.completion_date,
                "signatory_name": job.signatory_name,
                "signatory_title": job.signatory_title
            }

            # Fetch pending recipients
            recipients = db.query(CertificateRecord).filter(
                CertificateRecord.job_id == job_id,
                CertificateRecord.status == "pending"
            ).all()

            for rec in recipients:
                rec.status = "processing"
                db.commit()

                try:
                    pdf_path = storage_service.get_certificate_path(job_id, rec.certificate_id)
                    recipient_data = {
                        "name": rec.recipient_name,
                        "email": rec.recipient_email,
                        "certificate_id": rec.certificate_id
                    }
                    pdf_service.generate_certificate(cert_metadata, recipient_data, pdf_path)

                    # Mark completed
                    rec.status = "completed"
                    rec.file_path = str(pdf_path)
                    rec.completed_at = datetime.utcnow()
                    rec.error_message = None
                    db.commit()

                except Exception as ex:
                    logger.warning(f"Failed to generate certificate for {rec.certificate_id}: {str(ex)}")
                    rec.status = "failed"
                    # Safe concise error message without stack trace
                    rec.error_message = f"Generation error: {str(ex)[:200]}"
                    rec.completed_at = datetime.utcnow()
                    db.commit()

            # Compute terminal status
            total = job.total_recipients
            completed_count = db.query(func.count(CertificateRecord.id)).filter(
                CertificateRecord.job_id == job_id,
                CertificateRecord.status == "completed"
            ).scalar() or 0
            
            failed_count = db.query(func.count(CertificateRecord.id)).filter(
                CertificateRecord.job_id == job_id,
                CertificateRecord.status == "failed"
            ).scalar() or 0

            if completed_count == total:
                job.status = "completed"
            elif completed_count > 0 and failed_count > 0:
                job.status = "completed_with_errors"
            elif failed_count == total:
                job.status = "failed"
            else:
                # If there were 0 recipients (should not happen) or partial state
                job.status = "completed"

            job.completed_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            logger.exception(f"Fatal error processing job {job_id}: {str(e)}")
            try:
                job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
                if job:
                    job.status = "failed"
                    job.error_message = f"Job processing failed: {str(e)[:200]}"
                    job.completed_at = datetime.utcnow()
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

generation_service = GenerationService()
