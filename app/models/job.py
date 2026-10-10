from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True, nullable=False)
    
    # Certificate template metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    completion_date: Mapped[str] = mapped_column(String(50), nullable=False)
    signatory_name: Mapped[str] = mapped_column(String(255), nullable=False)
    signatory_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default="Program Director")
    
    total_recipients: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    send_emails: Mapped[Optional[bool]] = mapped_column(default=False, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    recipients: Mapped[List["CertificateRecord"]] = relationship(
        "CertificateRecord",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="CertificateRecord.id"
    )
