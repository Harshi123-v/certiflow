import io
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from templates.certificate_template import render_certificate_pdf
from app.services.storage_service import storage_service

class PDFService:
    def generate_certificate(
        self,
        cert_data: Dict[str, Any],
        recipient_data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """
        Generates a PDF certificate file at the specified output path.
        Cleans up partial files if generation encounters an error.
        """
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            render_certificate_pdf(output_path, cert_data, recipient_data)
            return output_path
        except Exception as e:
            # Clean up partially written file
            storage_service.delete_file_safely(output_path)
            raise RuntimeError(f"Certificate PDF generation failed: {str(e)}") from e

    def generate_preview_bytes(
        self,
        cert_data: Optional[Dict[str, Any]] = None,
        recipient_data: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generates a sample preview PDF and returns binary bytes.
        """
        effective_cert = {
            "title": "Certificate of Completion",
            "course_name": "Python Development Bootcamp",
            "organization_name": "Aero Learning Academy",
            "completion_date": "2026-10-09",
            "signatory_name": "Program Director",
            "signatory_title": "Authorized Signatory"
        }
        if cert_data:
            effective_cert.update(cert_data)

        effective_recipient = {
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "certificate_id": "PREVIEW-2026-SAMPLE"
        }
        if recipient_data:
            effective_recipient.update(recipient_data)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            self.generate_certificate(effective_cert, effective_recipient, tmp_path)
            pdf_bytes = tmp_path.read_bytes()
            return pdf_bytes
        finally:
            storage_service.delete_file_safely(tmp_path)

pdf_service = PDFService()
