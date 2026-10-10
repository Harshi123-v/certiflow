import os
import zipfile
from pathlib import Path
from typing import List, Optional
from app.core.config import settings
from app.utils.validation import sanitize_filename

class StorageService:
    def __init__(self, base_storage_dir: Optional[Path] = None):
        self.base_dir = (base_storage_dir or settings.STORAGE_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_job_dir(self, job_id: str) -> Path:
        """Returns the job directory path, ensuring it is within base storage."""
        safe_job_id = sanitize_filename(job_id).replace(".pdf", "")
        job_dir = (self.base_dir / safe_job_id).resolve()
        
        # Guard against path traversal
        if not str(job_dir).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected for job ID: {job_id}")
            
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    def get_certificate_path(self, job_id: str, certificate_id: str) -> Path:
        """Returns the safe certificate PDF path."""
        job_dir = self.get_job_dir(job_id)
        filename = sanitize_filename(certificate_id)
        pdf_path = (job_dir / filename).resolve()
        
        # Guard against path traversal
        if not str(pdf_path).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected for certificate ID: {certificate_id}")
            
        return pdf_path

    def delete_file_safely(self, file_path: Optional[Path]) -> None:
        """Safely removes a file if it exists."""
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass

    def create_job_zip(self, job_id: str, cert_file_paths: List[Path]) -> Path:
        """
        Creates a ZIP archive containing all valid certificates for a job.
        Returns the path to the generated ZIP archive.
        """
        job_dir = self.get_job_dir(job_id)
        zip_path = job_dir / f"certificates_job_{job_id}.zip"
        
        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for pdf_path in cert_file_paths:
                if pdf_path and pdf_path.exists():
                    zf.write(pdf_path, arcname=pdf_path.name)
                    
        return zip_path

storage_service = StorageService()
