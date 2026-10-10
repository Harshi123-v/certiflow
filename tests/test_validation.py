import pytest

def test_reject_missing_certificate_fields(client):
    """Test rejecting requests missing essential certificate metadata."""
    payload = {
        "certificate": {
            # missing title, course_name, organization_name, completion_date, signatory_name
            "signatory_title": "Director"
        },
        "recipients": [
            {"name": "Ananya Sharma", "email": "ananya@example.com", "certificate_id": "CERT-V-001"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()

def test_reject_empty_recipients_list(client):
    """Test rejecting requests with empty recipients list."""
    payload = {
        "certificate": {
            "title": "Certificate of Completion",
            "course_name": "Python Bootcamp",
            "organization_name": "Aero Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Program Director"
        },
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "Recipients list cannot be empty" in str(data)

def test_reject_excessive_batch_size(client):
    """Test rejecting requests that exceed the maximum batch size limit (500)."""
    # Create 501 recipients
    huge_batch = [
        {"name": f"Recipient {i}", "email": f"user{i}@example.com", "certificate_id": f"CERT-EX-{i}"}
        for i in range(501)
    ]
    payload = {
        "certificate": {
            "title": "Certificate of Completion",
            "course_name": "Python Bootcamp",
            "organization_name": "Aero Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Program Director"
        },
        "recipients": huge_batch
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "Batch size exceeds maximum limit" in str(data)

def test_detect_duplicate_certificate_ids_within_batch(client):
    """Test that duplicate certificate IDs within the same batch are safely flagged."""
    payload = {
        "certificate": {
            "title": "Certificate of Completion",
            "course_name": "Python Bootcamp",
            "organization_name": "Aero Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Program Director"
        },
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com", "certificate_id": "CERT-DUP-01"},
            {"name": "Bob Jones", "email": "bob@example.com", "certificate_id": "CERT-DUP-01"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 201
    job_data = response.json()
    assert job_data["total_recipients"] == 2
    assert job_data["valid_recipients"] == 1
    assert job_data["invalid_recipients"] == 1

    job_id = job_data["job_id"]
    recipients_res = client.get(f"/api/v1/jobs/{job_id}/recipients")
    recipients = recipients_res.json()["items"]
    
    # One is valid, one has failure message
    failed_rec = [r for r in recipients if r["status"] == "failed"]
    assert len(failed_rec) == 1
    assert "Duplicate certificate ID" in failed_rec[0]["error_message"]

def test_invalid_email_and_whitespace_name(client):
    """Test that invalid email and whitespace recipient names are flagged without killing the batch."""
    payload = {
        "certificate": {
            "title": "Certificate of Completion",
            "course_name": "Python Bootcamp",
            "organization_name": "Aero Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Program Director"
        },
        "recipients": [
            {"name": "Valid Student", "email": "valid@example.com", "certificate_id": "CERT-VAL-01"},
            {"name": "   ", "email": "whitespace@example.com", "certificate_id": "CERT-VAL-02"},
            {"name": "Bad Email Student", "email": "not-an-email", "certificate_id": "CERT-VAL-03"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["valid_recipients"] == 1
    assert data["invalid_recipients"] == 2
