from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint confirming API and database status."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)[:100]}"

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "app": "CertiFlow",
        "version": settings.VERSION,
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }
