import zipfile
import io
import pytest
from app.services.generation_service import generation_service

def test_download_individual_certificate_pdf(client):
    """Test downloading a valid individual certificate PDF."""
    payload = {
        "certificate": {
            "title": "Certificate of Completion",
            "course_name": "API Security & Defense",
            "organization_name": "Aero Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Chief Information Security Officer"
        },
        "recipients": [
            {"name": "Marcus Aurelius", "email": "marcus@example.com", "certificate_id": "CERT-DL-001"}
        ]
    }
    res = client.post("/api/v1/jobs", json=payload)
    job_id = res.json()["job_id"]
    generation_service.process_job(job_id)

    # Download PDF
    dl_res = client.get("/api/v1/certificates/CERT-DL-001/download")
    assert dl_res.status_code == 200
    assert "application/pdf" in dl_res.headers.get("content-type", "")
    assert dl_res.content.startswith(b"%PDF-")

def test_download_bulk_zip_archive(client):
    """Test downloading a ZIP archive containing all generated certificates for a job."""
    payload = {
        "certificate": {
            "title": "Certificate of Excellence",
            "course_name": "Distributed Systems",
            "organization_name": "Aero Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Dean"
        },
        "recipients": [
            {"name": "Alice Cooper", "email": "alice.c@example.com", "certificate_id": "CERT-ZIP-01"},
            {"name": "Bob Dylan", "email": "bob.d@example.com", "certificate_id": "CERT-ZIP-02"}
        ]
    }
    res = client.post("/api/v1/jobs", json=payload)
    job_id = res.json()["job_id"]
    generation_service.process_job(job_id)

    # Download ZIP
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download")
    assert zip_res.status_code == 200
    assert "application/zip" in zip_res.headers.get("content-type", "")

    # Validate that it is a valid zip containing both PDFs
    with zipfile.ZipFile(io.BytesIO(zip_res.content)) as zf:
        namelist = zf.namelist()
        assert len(namelist) == 2
        for name in namelist:
            assert name.endswith(".pdf")

def test_download_zip_fails_when_no_successful_certificates(client):
    """Test that downloading a ZIP for a job with zero completed certificates returns HTTP 400."""
    payload = {
        "certificate": {
            "title": "Certificate",
            "course_name": "Math",
            "organization_name": "Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Dean"
        },
        "recipients": [
            # Invalid email will cause recipient to fail immediately upon job ingestion
            {"name": "Bad Recipient", "email": "invalid-email-syntax", "certificate_id": "CERT-FAIL-ZIP"}
        ]
    }
    res = client.post("/api/v1/jobs", json=payload)
    job_id = res.json()["job_id"]
    generation_service.process_job(job_id)

    zip_res = client.get(f"/api/v1/jobs/{job_id}/download")
    assert zip_res.status_code == 400
    assert "No successful certificates available" in zip_res.json()["detail"]

def test_export_job_recipients_csv(client):
    """Test exporting job recipients report to CSV spreadsheet."""
    payload = {
        "certificate": {
            "title": "Certificate of Completion",
            "course_name": "Data Engineering",
            "organization_name": "Aero Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Dean"
        },
        "recipients": [
            {"name": "Tara Smith", "email": "tara@example.com", "certificate_id": "CERT-CSV-01"}
        ]
    }
    res = client.post("/api/v1/jobs", json=payload)
    job_id = res.json()["job_id"]
    generation_service.process_job(job_id)

    csv_res = client.get(f"/api/v1/jobs/{job_id}/export/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    content = csv_res.content.decode("utf-8-sig")
    assert "Recipient Name,Recipient Email,Certificate ID" in content
    assert "Tara Smith,tara@example.com,CERT-CSV-01" in content

def test_export_master_vault_csv(client):
    """Test exporting master vault of all certificates to CSV spreadsheet."""
    csv_res = client.get("/api/v1/certificates/export/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    content = csv_res.content.decode("utf-8-sig")
    assert "Certificate ID,Recipient Name,Email,Course Name" in content

