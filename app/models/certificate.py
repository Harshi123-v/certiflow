from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class CertificateRecord(Base):
    __tablename__ = "certificate_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    certificate_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Status: pending, processing, completed, failed
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_sent: Mapped[Optional[bool]] = mapped_column(default=False, nullable=True)
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    email_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    job: Mapped["GenerationJob"] = relationship("GenerationJob", back_populates="recipients")
