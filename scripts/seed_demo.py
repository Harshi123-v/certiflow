import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.db.database import SessionLocal, init_db
from app.models.job import GenerationJob
from app.models.certificate import CertificateRecord
from app.services.generation_service import generation_service
from app.schemas.job import JobCreateRequest
from app.schemas.certificate import CertificateInfo, RecipientInput

def seed_demo_data():
    print("Initializing database...")
    init_db()
    db = SessionLocal()

    try:
        # Check if already seeded
        existing = db.query(GenerationJob).count()
        if existing > 0:
            print(f"Database already contains {existing} job(s). Skipping seed.")
            return

        print("Seeding demo jobs...")

        # Batch 1: Completed All Success (Python Bootcamp)
        req1 = JobCreateRequest(
            certificate=CertificateInfo(
                title="Certificate of Completion",
                course_name="Python Development Bootcamp",
                organization_name="Aero Learning Academy",
                completion_date="2026-10-09",
                signatory_name="Dr. Arvind Rao",
                signatory_title="Director of Engineering Education"
            ),
            recipients=[
                RecipientInput(name="Ananya Sharma", email="ananya.sharma@example.com", certificate_id="AERO-PY-2026-001"),
                RecipientInput(name="Rahul Verma", email="rahul.verma@example.com", certificate_id="AERO-PY-2026-002"),
                RecipientInput(name="Priya Nair", email="priya.nair@example.com", certificate_id="AERO-PY-2026-003"),
                RecipientInput(name="Rohan Kulkarni", email="rohan.kulkarni@example.com", certificate_id="AERO-PY-2026-004")
            ]
        )
        job1, _, _ = generation_service.create_generation_job(db, req1)
        print(f"Created Job 1: {job1.id}. Processing PDFs...")
        generation_service.process_job(job1.id)

        # Batch 2: Partial failure (Completed with errors)
        req2 = JobCreateRequest(
            certificate=CertificateInfo(
                title="Certificate of Professional Achievement",
                course_name="Cloud & Systems Architecture",
                organization_name="Aero Tech Institute",
                completion_date="2026-09-15",
                signatory_name="Elena Rostova",
                signatory_title="Principal Solutions Architect"
            ),
            recipients=[
                RecipientInput(name="Vikramaditya Singhania", email="vikram@example.com", certificate_id="AERO-CSA-2026-101"),
                RecipientInput(name="Sneha Kapoor", email="invalid-email-address", certificate_id="AERO-CSA-2026-102"),
                RecipientInput(name="Tanvi Deshmukh", email="tanvi@example.com", certificate_id="AERO-CSA-2026-103")
            ]
        )
        job2, _, _ = generation_service.create_generation_job(db, req2)
        print(f"Created Job 2: {job2.id}. Processing PDFs...")
        generation_service.process_job(job2.id)

        print("Demo seed completed successfully!")
        db.expire_all()
        print(f"Job 1 Status: {db.query(GenerationJob).filter(GenerationJob.id == job1.id).first().status}")
        print(f"Job 2 Status: {db.query(GenerationJob).filter(GenerationJob.id == job2.id).first().status}")

    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
