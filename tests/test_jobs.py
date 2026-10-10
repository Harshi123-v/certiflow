import pytest

def test_create_and_retrieve_job(client):
    """Test job creation and metadata retrieval."""
    payload = {
        "certificate": {
            "title": "Certificate of Mastery",
            "course_name": "Full-Stack Web Systems",
            "organization_name": "Aero Engineering Lab",
            "completion_date": "2026-10-09",
            "signatory_name": "Sarah Connor",
            "signatory_title": "Lead Instructor"
        },
        "recipients": [
            {"name": "Ananya Sharma", "email": "ananya@example.com", "certificate_id": "CERT-FS-001"},
            {"name": "Rahul Verma", "email": "rahul@example.com", "certificate_id": "CERT-FS-002"}
        ]
    }
    # 1. Create Job
    post_res = client.post("/api/v1/jobs", json=payload)
    assert post_res.status_code == 201
    job_id = post_res.json()["job_id"]
    assert post_res.json()["total_recipients"] == 2
    assert post_res.json()["status"] in ["queued", "processing", "completed"]

    # 2. Get Job Detail
    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.status_code == 200
    job_detail = get_res.json()
    assert job_detail["id"] == job_id
    assert job_detail["course_name"] == "Full-Stack Web Systems"
    assert job_detail["total_recipients"] == 2
    assert "progress_percentage" in job_detail
    assert len(job_detail["recipients"]) == 2

def test_get_nonexistent_job(client):
    """Test 404 response when querying a non-existent job ID."""
    res = client.get("/api/v1/jobs/nonexistent-uuid-1234")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_get_nonexistent_certificate(client):
    """Test 404 response when querying a non-existent certificate ID."""
    res = client.get("/api/v1/certificates/NONEXISTENT-CERT-999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_list_jobs_and_filter(client):
    """Test listing jobs with search parameters."""
    # Create two different jobs
    for i in range(2):
        client.post("/api/v1/jobs", json={
            "certificate": {
                "title": f"Certificate {i}",
                "course_name": f"Course Special {i}",
                "organization_name": "Aero Academy",
                "completion_date": "2026-10-09",
                "signatory_name": "Instructor"
            },
            "recipients": [
                {"name": f"Student {i}", "email": f"st{i}@example.com", "certificate_id": f"CERT-LST-{i}"}
            ]
        })

    # Search by course name
    res = client.get("/api/v1/jobs?search=Special")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
