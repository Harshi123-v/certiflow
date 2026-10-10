import pytest
from pathlib import Path
from app.services.generation_service import generation_service
from app.services.pdf_service import pdf_service
from app.models.job import GenerationJob
from app.models.certificate import CertificateRecord

def test_valid_pdf_generation_content(tmp_path):
    """Test that PDF generator outputs a real, readable PDF with correct binary headers."""
    output_pdf = tmp_path / "test_cert.pdf"
    cert_data = {
        "title": "Certificate of Completion",
        "course_name": "Python Systems Engineering",
        "organization_name": "Aero Academy",
        "completion_date": "2026-10-09",
        "signatory_name": "Chief Architect",
        "signatory_title": "Director"
    }
    rec_data = {
        "name": "Jane Alexander Doe",
        "email": "jane@example.com",
        "certificate_id": "CERT-PDF-VALID-01"
    }
    generated_path = pdf_service.generate_certificate(cert_data, rec_data, output_pdf)
    assert generated_path.exists()
    assert generated_path.stat().st_size > 1000

    # Verify standard PDF file header
    with open(generated_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"

def test_all_recipients_succeed(client, db_session):
    """Test job terminal status when all recipients succeed (status = completed)."""
    payload = {
        "certificate": {
            "title": "Certificate of Completion",
            "course_name": "Aerospace Software Engineering",
            "organization_name": "Aero Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Dean of Engineering"
        },
        "recipients": [
            {"name": "Student Alpha", "email": "alpha@example.com", "certificate_id": "CERT-SUCC-01"},
            {"name": "Student Beta", "email": "beta@example.com", "certificate_id": "CERT-SUCC-02"}
        ]
    }
    res = client.post("/api/v1/jobs", json=payload)
    job_id = res.json()["job_id"]

    # Explicitly run process_job to ensure background work runs synchronously in test session
    generation_service.process_job(job_id)

    job = db_session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    assert job.status == "completed"

    recipients = db_session.query(CertificateRecord).filter(CertificateRecord.job_id == job_id).all()
    for r in recipients:
        assert r.status == "completed"
        assert r.file_path is not None
        assert Path(r.file_path).exists()

def test_isolated_failure_allows_others_to_continue(client, db_session, monkeypatch):
    """
    Test per-recipient error isolation:
    Deliberately inject an exception when generating one specific certificate.
    Verify that other recipients still generate successfully and job transitions to 'completed_with_errors'.
    """
    original_gen = pdf_service.generate_certificate

    def simulated_failing_generator(cert_data, recipient_data, output_path):
        if recipient_data.get("certificate_id") == "CERT-FAIL-INJECT":
            raise RuntimeError("Injected render engine malfunction for testing")
        return original_gen(cert_data, recipient_data, output_path)

    monkeypatch.setattr(pdf_service, "generate_certificate", simulated_failing_generator)

    payload = {
        "certificate": {
            "title": "Certificate of Completion",
            "course_name": "Resilient Microservices",
            "organization_name": "Aero Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Security Officer"
        },
        "recipients": [
            {"name": "Good Recipient 1", "email": "good1@example.com", "certificate_id": "CERT-GOOD-01"},
            {"name": "Bad Recipient", "email": "bad@example.com", "certificate_id": "CERT-FAIL-INJECT"},
            {"name": "Good Recipient 2", "email": "good2@example.com", "certificate_id": "CERT-GOOD-02"}
        ]
    }
    res = client.post("/api/v1/jobs", json=payload)
    job_id = res.json()["job_id"]

    generation_service.process_job(job_id)

    job = db_session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    # Terminal status must be completed_with_errors
    assert job.status == "completed_with_errors"

    good1 = db_session.query(CertificateRecord).filter(CertificateRecord.certificate_id == "CERT-GOOD-01").first()
    good2 = db_session.query(CertificateRecord).filter(CertificateRecord.certificate_id == "CERT-GOOD-02").first()
    bad = db_session.query(CertificateRecord).filter(CertificateRecord.certificate_id == "CERT-FAIL-INJECT").first()

    assert good1.status == "completed"
    assert good1.file_path is not None
    assert Path(good1.file_path).exists()

    assert good2.status == "completed"
    assert good2.file_path is not None
    assert Path(good2.file_path).exists()

    assert bad.status == "failed"
    assert "Injected render engine malfunction" in bad.error_message

def test_all_recipients_fail(client, db_session, monkeypatch):
    """Test terminal status when all recipients fail (status = failed)."""
    def always_fail_generator(cert_data, recipient_data, output_path):
        raise RuntimeError("Total system failure")

    monkeypatch.setattr(pdf_service, "generate_certificate", always_fail_generator)

    payload = {
        "certificate": {
            "title": "Certificate of Completion",
            "course_name": "Failing Course",
            "organization_name": "Aero Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Lead"
        },
        "recipients": [
            {"name": "User 1", "email": "u1@example.com", "certificate_id": "CERT-ALLFAIL-01"},
            {"name": "User 2", "email": "u2@example.com", "certificate_id": "CERT-ALLFAIL-02"}
        ]
    }
    res = client.post("/api/v1/jobs", json=payload)
    job_id = res.json()["job_id"]

    generation_service.process_job(job_id)

    job = db_session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    assert job.status == "failed"
