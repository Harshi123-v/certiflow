# CertiFlow Architecture & Design Documentation

## 1. Architectural Philosophy

CertiFlow was designed from first principles to solve high-volume credential generation with maximum reliability, auditability, and operational simplicity.

In production bulk-processing systems, a common failure mode is **batch poisoning**—where a single malformed email or corrupt character causes an entire transaction of 500 records to roll back, failing all legitimate recipients. CertiFlow avoids this pitfall using **Per-Recipient Fault Isolation** and **Two-Phase Lifecycle Processing**.

---

## 2. System Architecture

```
                       ┌────────────────────────────────────────┐
                       │          Client (Browser / API)        │
                       └───────────────────┬────────────────────┘
                                           │
                                  HTTP REST / JSON
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │             FastAPI Gateway            │
                       │   - CORS, Request Validation (Pydantic)│
                       │   - Static Web Application Hosting     │
                       └───────────┬────────────────┬───────────┘
                                   │                │
            POST /api/v1/jobs      │                │ BackgroundTasks Dispatch
                                   ▼                ▼
┌──────────────────────────────────────┐  ┌─────────────────────────────────────┐
│          GenerationService           │  │       Async Background Worker       │
│  - Pre-validates each recipient      │  │  - Fresh Isolated DB Session        │
│  - Stages Job as 'queued'            │  │  - Independent Try/Catch per item   │
│  - Immediately returns Job ID (201)  │  │  - Transitions: pending->processing │
└──────────────────┬───────────────────┘  └──────────────────┬──────────────────┘
                   │                                         │
                   │                                         │ PDF Rendering
                   ▼                                         ▼
┌──────────────────────────────────────┐  ┌─────────────────────────────────────┐
│          Relational Database         │  │         ReportLab PDF Engine        │
│    (SQLite Default / PostgreSQL)     │  │  - Vector Borders, Crest, Seals     │
│  - generation_jobs                   │  │  - Dynamic Text Auto-Fitting        │
│  - certificate_records               │  │  - Atomic Safe Disk Writing         │
└──────────────────────────────────────┘  └──────────────────┬──────────────────┘
                                                             │
                                                             ▼
                                          ┌─────────────────────────────────────┐
                                          │      Safe File Storage Sandbox      │
                                          │     ./storage/certificates/{job}/   │
                                          └─────────────────────────────────────┘
```

---

## 3. Data Flow & Request-Processing Lifecycle

### Phase 1: Ingestion & Validation
1. Client issues `POST /api/v1/jobs` with certificate metadata and up to 500 recipients.
2. **Batch-Level Validation (Pydantic v2)**:
   - Validates required fields, type bounds, and enforces `MAX_BATCH_SIZE` (500).
   - Fundamentally malformed payloads return `422 Unprocessable Entity`.
3. **Record-Level Validation & Database Staging**:
   - Unique constraints within the batch and existing database records are inspected.
   - Individually invalid entries (e.g. malformed email, blank name, or duplicate cert ID) are marked as `failed` with precise error messages recorded.
   - Structurally valid entries are marked as `pending`.
   - The job is persisted with status `queued`.
   - Returns HTTP 201 Created immediately with the `job_id`.

### Phase 2: Asynchronous Execution & Failure Isolation
1. FastAPI's `BackgroundTasks` executes `generation_service.process_job(job_id)`.
2. The worker acquires a dedicated database session (`SessionLocal`).
3. For every `pending` recipient:
   - Status transitions to `processing`.
   - The ReportLab engine renders the certificate PDF directly to `./storage/certificates/{job_id}/{safe_cert_id}.pdf`.
   - If rendering succeeds: Status updates to `completed`, recording the storage file path and timestamp.
   - If an unexpected error occurs: Status updates to `failed`, safely recording the sanitized error message without exposing server internals or aborting remaining recipients. Any partially written file is safely removed.
4. Once all records reach a terminal state:
   - Terminal status is computed:
     - `completed`: 100% of recipients generated successfully.
     - `completed_with_errors`: At least one succeeded, but some failed.
     - `failed`: All recipients failed.
   - `completed_at` timestamp is written to the database.

---

## 4. Key Design Decisions

### A. ReportLab over HTML-to-PDF Converters
- **Why**: Many systems rely on headless Chrome, WeasyPrint, or wkhtmltopdf, which introduce heavy binary dependencies, font-rendering inconsistencies across OS platforms, high memory overhead, and severe vulnerability surfaces (SSRF / local file inclusion via CSS).
- **ReportLab Advantage**: Pure Python, zero external browser runtime, sub-millisecond vector rendering, predictable pixel-perfect alignment, and native cryptography/PDF compliance.

### B. SQLite Default with PostgreSQL Compatibility
- **Zero Friction Setup**: Works out of the box on Windows, macOS, and Linux without installing, provisioning, or configuring database servers.
- **Enterprise Ready**: Uses standard SQLAlchemy 2.0 ORM declarations and connection pooling (`pool_size`, `max_overflow`), allowing a seamless switch to PostgreSQL simply by changing `DATABASE_URL` in `.env`.

### C. In-Process Background Execution vs. Distributed Queue
- **Decision**: Uses FastAPI's `BackgroundTasks` for local standalone operation.
- **Rationale**: For technical shortlisting, zero-dependency local execution is paramount. Introducing Redis + Celery/RabbitMQ would require external services, multi-process management, and added installation complexity.
- **Honest Limitations**: In-process tasks run within the ASGI server lifecycle. If the server process terminates abruptly, in-flight jobs will remain in `processing` state. In high-scale multi-node deployments, transitioning this service boundary to Celery or Temporal is straightforward due to the clean separation of `GenerationService`.
