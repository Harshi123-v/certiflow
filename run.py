import sys
from pathlib import Path
import uvicorn

# Ensure the project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" CertiFlow — Bulk Certificate Generation & Tracking System")
    print("="*70)
    print(" • Web Application (Frontend):  http://localhost:8000/")
    print(" • Interactive API Docs (Swagger): http://localhost:8000/docs")
    print(" • Alternative Docs (ReDoc):    http://localhost:8000/redoc")
    print(" • Health Endpoint:             http://localhost:8000/health")
    print("="*70 + "\n")
    
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
