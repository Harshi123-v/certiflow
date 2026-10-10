# CertiFlow — Bulk Certificate Generation & Tracking System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![ReportLab](https://img.shields.io/badge/ReportLab-4.0+-2C5E8A)](https://www.reportlab.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**CertiFlow** is an enterprise-grade bulk certificate generation and verification platform built with Python, FastAPI, SQLAlchemy 2.0, ReportLab, and a vanilla JavaScript SaaS interface.

Designed for the **Aero Company Technical Shortlisting Assignment**, CertiFlow features high-volume document synthesis, per-recipient failure isolation, real-time telemetry, and automated ZIP packaging.

---

## Table of Contents
1. [Core Features](#1-core-features)
2. [Technology Stack & Rationale](#2-technology-stack--rationale)
3. [System Architecture](#3-system-architecture)
4. [Prerequisites](#4-prerequisites)
5. [Quickstart Guide (Windows & Linux/macOS)](#5-quickstart-guide)
6. [Database Setup (SQLite & PostgreSQL)](#6-database-setup)
7. [Running the Application](#7-running-the-application)
8. [API Endpoints & Usage Examples](#8-api-endpoints--usage-examples)
9. [Automated Testing Suite](#9-automated-testing-suite)
10. [Frontend Interface](#10-frontend-interface)
11. [Project Structure](#11-project-structure)
12. [Architectural Limitations & Trade-offs](#12-architectural-limitations--trade-offs)
13. [Troubleshooting Guide](#13-troubleshooting-guide)

---

## 1. Core Features

- **Bulk Asynchronous Ingestion**: Dispatches jobs containing up to 500 recipients per batch, returning an immediate job ticket without blocking the HTTP thread.
- **Per-Recipient Error Isolation**: Individual recipient failures (e.g., malformed email or duplicate certificate ID) are isolated and flagged without terminating other valid certificates in the batch.
- **Predefined Vector Certificate Template**: Generates high-resolution landscape PDFs using ReportLab with a navy, ivory, and gold aesthetic, multi-tier decorative borders, vector medallions, dynamic font auto-fitting, and digital signature flourishes.
- **Real-Time Live Telemetry**: Dynamic polling on the UI tracks generation states (`queued`, `processing`, `completed`, `completed_with_errors`, `failed`), automatically terminating polling upon reaching terminal status.
- **Bulk & Individual Retrieval**: Download individual signed PDFs or a single bundled `.zip` archive containing all successful certificates for a job.
- **Interactive CSV Import & Sample Export**: Seamlessly import recipient rosters from standard CSV files with client-side header validation.
- **Dual Database Support**: Out-of-the-box zero-setup SQLite engine, fully compatible with enterprise PostgreSQL via SQLAlchemy 2.0 connection pooling.

---

## 2. Technology Stack & Rationale

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend API** | FastAPI (ASGI) | High-performance asynchronous REST endpoints, automatic OpenAPI/Swagger generation, and native Pydantic v2 integration. |
| **Database ORM** | SQLAlchemy 2.x | Modern mapped columns, migration readiness, explicit transaction boundaries, and support for SQLite and PostgreSQL. |
| **PDF Engine** | ReportLab | Native Python vector rendering. Eliminates external headless browser dependencies (like Puppeteer or wkhtmltopdf), reducing memory and security risks. |
| **Data Validation**| Pydantic v2 | High-throughput data parsing and schema validation with structured error responses. |
| **Frontend** | Vanilla ES6 HTML/CSS | Zero build step, lightweight, instantly editable, and runs out-of-the-box without Node.js or npm toolchains. |
| **Test Engine** | Pytest & TestClient | Comprehensive test suite verifying validation edge cases, PDF generation, failure isolation, and downloads. |

---

## 3. System Architecture

CertiFlow follows a modular layered architecture:

```
[ Frontend SPA (Vanilla JS) / API Client ]
                   │
                   ▼ HTTP REST / JSON
┌────────────────────────────────────────────────────────┐
│                   FastAPI Application                  │
│       /api/v1/jobs  •  /api/v1/certificates  •  /health │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
                ▼                        ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│       GenerationService       │ │     StorageService / PDF      │
│  - Pre-validates recipients   │ │  - ReportLab vector rendering │
│  - Stages job in DB           │ │  - Path-traversal sanitizing  │
│  - Dispatches BackgroundTasks │ │  - Zip archive packaging      │
└───────────────┬───────────────┘ └───────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────┐
│             Relational Database (SQLAlchemy)           │
│         SQLite (Default)  /  PostgreSQL (Enterprise)   │
└────────────────────────────────────────────────────────┘
```
*For deep technical specifications, refer to [ARCHITECTURE.md](ARCHITECTURE.md).*

---

## 4. Prerequisites

- **Python 3.10+** (Tested on Python 3.10 and Python 3.11)
- **pip** package manager
- Modern Web Browser (Chrome, Edge, Firefox, Safari)

---

## 5. Quickstart Guide

### Windows (PowerShell)

```powershell
# 1. Clone or extract the project
cd certiflow

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment template
Copy-Item .env.example .env
```

### Linux / macOS (Bash)

```bash
# 1. Clone or extract the project
cd certiflow

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate the virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment template
cp .env.example .env
```

---

## 6. Database Setup

### Default: Zero-Configuration SQLite (Recommended for Testing)
By default, the `.env` file uses:
```env
DATABASE_URL="sqlite:///./certiflow.db"
```
No manual migrations or setup steps are necessary. The application automatically initializes all tables and indexes upon startup.

### Optional: PostgreSQL Setup
To connect CertiFlow to a PostgreSQL database:
1. Ensure a PostgreSQL instance is running and create a database:
   ```sql
   CREATE DATABASE certiflow_db;
   ```
2. Update `.env`:
   ```env
   DATABASE_URL="postgresql+psycopg2://postgres:your_password@localhost:5432/certiflow_db"
   ```
3. CertiFlow uses SQLAlchemy connection pooling with `pool_pre_ping=True` and auto-creates schema definitions on startup.

---

## 7. Running the Application

### Start the Server

```bash
python run.py
```
*(Alternatively: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`)*

Once started, access the application endpoints:
- **Web Application (UI)**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### Load Realistic Demo Data (Optional)
To pre-populate the database with sample completed batches and isolated error states:
```bash
python scripts/seed_demo.py
```

---

## 8. API Endpoints & Usage Examples

### A. Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "app": "CertiFlow",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2026-10-09T16:45:00.000000"
}
```

---

### B. Create Bulk Generation Job
```http
POST /api/v1/jobs
Content-Type: application/json
```
**Request Body:**
```json
{
  "certificate": {
    "title": "Certificate of Completion",
    "course_name": "Python Development Bootcamp",
    "organization_name": "Aero Learning Academy",
    "completion_date": "2026-10-09",
    "signatory_name": "Dr. Arvind Rao",
    "signatory_title": "Dean of Engineering"
  },
  "recipients": [
    {
      "name": "Ananya Sharma",
      "email": "ananya@example.com",
      "certificate_id": "CERT-2026-001"
    },
    {
      "name": "Rahul Verma",
      "email": "rahul@example.com",
      "certificate_id": "CERT-2026-002"
    }
  ]
}
```
**Success Response (HTTP 201 Created):**
```json
{
  "job_id": "33cac042-460c-45fb-8b30-60a68f2c1a90",
  "status": "queued",
  "total_recipients": 2,
  "valid_recipients": 2,
  "invalid_recipients": 0,
  "created_at": "2026-10-09T16:45:00.123456",
  "message": "Generation job created with 2 valid recipient(s) queued."
}
```

---

### C. Inspect Job Progress & Details
```http
GET /api/v1/jobs/{job_id}
```
**Response:**
```json
{
  "id": "33cac042-460c-45fb-8b30-60a68f2c1a90",
  "status": "completed",
  "title": "Certificate of Completion",
  "course_name": "Python Development Bootcamp",
  "organization_name": "Aero Learning Academy",
  "completion_date": "2026-10-09",
  "signatory_name": "Dr. Arvind Rao",
  "signatory_title": "Dean of Engineering",
  "total_recipients": 2,
  "successful_certificates": 2,
  "failed_certificates": 0,
  "pending_recipients": 0,
  "processing_recipients": 0,
  "progress_percentage": 100.0,
  "created_at": "2026-10-09T16:45:00.123456",
  "started_at": "2026-10-09T16:45:00.130000",
  "completed_at": "2026-10-09T16:45:00.450000",
  "download_all_url": "/api/v1/jobs/33cac042-460c-45fb-8b30-60a68f2c1a90/download",
  "recipients": [
    {
      "id": 1,
      "job_id": "33cac042-460c-45fb-8b30-60a68f2c1a90",
      "recipient_name": "Ananya Sharma",
      "recipient_email": "ananya@example.com",
      "certificate_id": "CERT-2026-001",
      "status": "completed",
      "download_url": "/api/v1/certificates/CERT-2026-001/download"
    }
  ]
}
```

---

### D. Download Individual Certificate PDF
```http
GET /api/v1/certificates/{certificate_id}/download
```
Returns binary stream with header `Content-Type: application/pdf` and filename `Ananya_Sharma_CERT-2026-001.pdf`.

---

### E. Download Bulk ZIP Archive
```http
GET /api/v1/jobs/{job_id}/download
```
Returns bundled ZIP archive with header `Content-Type: application/zip` containing all successfully rendered PDF certificates.

---

### F. Validation Error Responses

#### Empty Recipient List (HTTP 422):
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "recipients"],
      "msg": "Value error, Recipients list cannot be empty. At least one recipient is required."
    }
  ]
}
```

#### Excessive Batch Size (> 500 recipients) (HTTP 422):
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "recipients"],
      "msg": "Value error, Batch size exceeds maximum limit of 500 recipients."
    }
  ]
}
```

---

## 9. Automated Testing Suite

CertiFlow includes a complete automated test suite utilizing Pytest and the FastAPI TestClient with an isolated in-memory SQLite database and temporary file sandboxes.

### Execute All Tests:
```bash
python -m pytest -v
```

### Test Coverage Highlights:
- `test_jobs.py`: Tests job creation, metadata retrieval, pagination, search filters, and 404 handlers.
- `test_validation.py`: Tests missing fields, empty recipient lists, batch size limits (>500), duplicate certificate ID detection, whitespace names, and invalid email formats.
- `test_generation.py`: Tests PDF binary headers (`%PDF-`), successful runs, injected per-recipient failure isolation, and terminal state resolution (`completed`, `completed_with_errors`, `failed`).
- `test_downloads.py`: Tests single PDF downloads, bulk ZIP archive creation, and zero-success safeguards.

---

## 10. Frontend Interface

CertiFlow features a built-in Single Page Application (SPA) located under `frontend/`:
1. **Executive Dashboard**: Displays real-time KPIs (Total Jobs, Delivered Credentials, In-Progress Renderings, Isolated Failures) and recent activity logs.
2. **Job Creator**: Sectioned configuration for certificate attributes, interactive recipient table (with dynamic add/remove rows), sample CSV download, and automated CSV roster importer.
3. **Jobs Registry**: Filter, search, and view historical batch jobs with real-time status badges and progress meters.
4. **Job Detail Monitor**: Live auto-refreshing progress monitor that polls every 2.5s and terminates automatically upon job completion, complete with individual failure diagnostics and bulk ZIP download.
5. **Certificate Vault**: Master searchable repository for all issued credentials across all batches.
6. **Live Template Preview**: Visual inspection panel rendering the vector certificate layout.

---

## 11. Project Structure

```
certiflow/
├── app/
│   ├── main.py                     # FastAPI application setup & static mounting
│   ├── core/
│   │   └── config.py               # Pydantic Settings & environment variables
│   ├── db/
│   │   └── database.py             # SQLAlchemy 2.0 engine, sessions & get_db
│   ├── models/
│   │   ├── job.py                  # GenerationJob ORM model
│   │   └── certificate.py          # CertificateRecord ORM model
│   ├── schemas/
│   │   ├── job.py                  # Job request/response schemas (Pydantic v2)
│   │   └── certificate.py          # Certificate & recipient schemas
│   ├── api/
│   │   └── routes/
│   │       ├── health.py           # Health check endpoint
│   │       ├── jobs.py             # Jobs CRUD and ZIP download endpoints
│   │       └── certificates.py     # Certificate retrieval & PDF download
│   ├── services/
│   │   ├── generation_service.py   # Bulk orchestration & fault-isolated worker
│   │   ├── pdf_service.py          # ReportLab integration & safety cleanup
│   │   └── storage_service.py      # Path sanitizing & ZIP archiving
│   └── utils/
│       └── validation.py           # Email regex, safe filenames, and field checks
├── frontend/
│   ├── index.html                  # Responsive SPA interface
│   ├── css/
│   │   └── styles.css              # Custom styling (Ivory, Navy, Gold theme)
│   └── js/
│       ├── api.js                  # Frontend API abstraction
│       └── app.js                  # SPA routing, polling, CSV parsing
├── templates/
│   └── certificate_template.py     # ReportLab vector certificate engine
├── storage/
│   └── certificates/               # Safe storage directory for generated PDFs
├── tests/
│   ├── conftest.py                 # Pytest fixtures & isolated in-memory DB
│   ├── test_jobs.py                # Job lifecycle and 404 tests
│   ├── test_validation.py          # Schema & input validation tests
│   ├── test_generation.py          # ReportLab & error-isolation tests
│   └── test_downloads.py           # PDF and ZIP download verification
├── scripts/
│   └── seed_demo.py                # Demo data seeder script
├── .env.example                    # Sample environment variables
├── .gitignore                      # Git ignore specifications
├── requirements.txt                # Pinned production dependencies
├── ARCHITECTURE.md                 # System architecture documentation
├── README.md                       # Complete documentation
└── run.py                          # Local development runner
```

---

## 12. Architectural Limitations & Trade-offs

1. **In-Process BackgroundTasks vs. Distributed Queues**:
   - *Design Choice*: For local evaluation without requiring Redis, RabbitMQ, or Docker, FastAPI's `BackgroundTasks` executes in-process on the server's threadpool.
   - *Limitation*: If the server process is forcefully terminated midway through generation, in-flight jobs remain in the `processing` state without an automatic retry worker. In a distributed multi-node cloud environment, `GenerationService` would be bound to a durable queue (e.g., Celery, RQ, or AWS SQS).
2. **Local Disk Storage**:
   - *Design Choice*: Certificates are stored under `./storage/certificates/{job_id}/` using path-traversal-safe filenames.
   - *Production Adaptation*: For multi-server clusters, `StorageService` can be swapped for an S3-compatible object store (e.g. AWS S3 or MinIO) with signed URLs.

---

## 13. Troubleshooting Guide

- **Port 8000 already in use**:
  Run `uvicorn app.main:app --port 8080 --reload` or specify a custom port in `run.py`.
- **Database locked (SQLite)**:
  SQLite operates with `check_same_thread=False` and handles standard local concurrency. If running multiple external writer processes, switch to PostgreSQL via `DATABASE_URL` in `.env`.
- **Permission errors on storage directory**:
  Ensure the running user has read and write permissions to the `./storage/certificates/` directory.

---

## License
MIT License. Developed for the Aero Company Technical Shortlisting Assignment.
