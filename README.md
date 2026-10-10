# CertiFlow — Bulk Certificate Generation & Tracking System


CertiFlow is a web-based application that automates bulk certificate generation, tracking, and downloading. Built using FastAPI, Python, PostgreSQL, SQLAlchemy 2.x, and ReportLab, it generates personalized PDF certificates and tracks the processing status of every recipient.

The core idea behind CertiFlow is simple: **one invalid record should not stop an entire batch.** The system validates recipients individually, processes valid records in the background, and records failures with clear explanations.

## Key Features

- **Bulk Generation:** Generate personalized PDF certificates for up to 500 recipients per job.
- **Fault Isolation:** Handle individual validation or generation failures without interrupting the remaining recipients.
- **Job Tracking:** Monitor processing progress, successful generations, pending records, and failures through a web dashboard.
- **PDF Downloads:** Download individual certificates or a ZIP archive containing successfully generated PDFs.
- **CSV Import and Export:** Import recipient information from CSV files and export generation reports.
- **PostgreSQL Integration:** Persist job information, certificate records, and processing statuses using PostgreSQL and SQLAlchemy.
- **Automated Testing:** Test validation, PDF generation, failure handling, downloads, and job status transitions using pytest.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| FastAPI | REST API development |
| PostgreSQL | Persistent data storage |
| SQLAlchemy 2.x | Database models and queries |
| Pydantic | Request validation and data schemas |
| ReportLab | PDF certificate generation |
| HTML5, CSS3, JavaScript | Web dashboard |
| FastAPI BackgroundTasks | Background processing |
| pytest | Automated testing |

## How It Works

1. **Submit:** The user provides certificate details and recipient information through the web interface or API.
2. **Validate:** The backend checks request structure, required fields, email formats, and duplicate certificate IDs.
3. **Create a Job:** The application stores job information in PostgreSQL and returns a unique job ID.
4. **Generate Certificates:** A background task processes valid recipients and creates personalized PDF certificates.
5. **Track Progress:** The dashboard retrieves updated job information and displays processing progress and failures.
6. **Download Results:** Users can download individual PDFs, a ZIP archive, or a CSV report.

Invalid recipient records are tracked with their failure reasons, allowing the remaining valid records to continue processing.

## System Architecture

```text
             Web Dashboard
                   |
                   v
              FastAPI API
                   |
                   v
          Request Validation
                   |
                   v
          Generation Service
                   |
             +-----+-----+
             |           |
             v           v
        PostgreSQL   Background Task
                         |
                         v
                 Recipient Processing
                         |
                         v
                  ReportLab PDF
                         |
                         v
                  File Storage
                         |
                         v
               Status and Reports
```

## Project Structure

```text
certiflow/
├── app/
│   ├── main.py
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── api/
│   │   └── routes/
│   ├── services/
│   └── utils/
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
├── templates/
├── storage/
│   └── certificates/
├── tests/
├── scripts/
├── .env.example
├── .gitignore
├── requirements.txt
├── ARCHITECTURE.md
├── README.md
└── run.py
```

## Getting Started

### Prerequisites

- Python 3.10 or later
- PostgreSQL
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/certiflow.git
cd certiflow
```

Replace `YOUR_USERNAME` with the GitHub repository owner's username.

### 2. Create and Activate a Virtual Environment

For Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database named `certiflow_db`. Create a `.env` file in the project root and configure the database connection.

Example:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/certiflow_db
```

Replace `YOUR_PASSWORD` with your PostgreSQL password. Ensure the connection URL matches the PostgreSQL driver configured in `requirements.txt`.

Keep `.env` private and never commit database credentials to GitHub.

### 5. Start the Application

```bash
python run.py
```

Once the server is running, access the application at:

- **Web Dashboard:** http://localhost:8000/
- **Interactive API Documentation:** http://localhost:8000/docs
- **Alternative API Documentation:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check application health |
| POST | `/api/v1/jobs` | Create a bulk generation job |
| GET | `/api/v1/jobs/{job_id}` | Retrieve job progress and results |
| GET | `/api/v1/jobs/{job_id}/download` | Download certificates as a ZIP archive |
| GET | `/api/v1/jobs/{job_id}/export/csv` | Export a CSV report |
| GET | `/api/v1/certificates/{certificate_id}/download` | Download an individual PDF |

Detailed request and response schemas are available through the interactive API documentation at `/docs`.

## Running Tests

Run the automated test suite from the project root:

```bash
python -m pytest -v
```

The tests cover request validation, PDF generation, failure isolation, job status transitions, and downloads.

## Engineering Decisions

- **PostgreSQL:** Provides persistent storage for generation jobs, recipient records, and certificate metadata.
- **Background Processing:** Separates certificate generation from the initial API request. FastAPI BackgroundTasks keeps the implementation simple for this assignment.
- **ReportLab:** Generates PDFs directly in Python, providing precise control over layouts, borders, typography, and vector graphics.
- **Fault Isolation:** Records individual failures without unnecessarily interrupting valid recipients.
- **Modular Architecture:** Separates API routes, business logic, database access, PDF generation, and file storage for easier maintenance.

## Future Improvements

Potential improvements include durable background queues, authentication and role-based access control, cloud-based certificate storage, configurable templates, and automatic recovery of interrupted jobs.

## License

MIT License.

**Developed for the Aero Company Technical Shortlisting Assignment.**