import sys
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.db.database import SessionLocal, init_db
from app.models.job import GenerationJob
from app.models.certificate import CertificateRecord
from app.core.config import settings

def reset_database():
    print("Resetting database records...")
    db = SessionLocal()
    try:
        db.query(CertificateRecord).delete()
        db.query(GenerationJob).delete()
        db.commit()
        print(" -> [OK] All job and certificate records removed from database.")
    finally:
        db.close()

    # Clean storage certificates directory
    if settings.STORAGE_DIR.exists():
        for item in settings.STORAGE_DIR.iterdir():
            if item.name == ".gitkeep":
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)
        print(" -> [OK] All generated certificate files cleaned from storage.")

    print("\nDatabase is now completely fresh and empty!")

if __name__ == "__main__":
    reset_database()
