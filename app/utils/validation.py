import re
from typing import Tuple, Optional

# Standard RFC 5322 simplified email regex
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Safe filename regex: only letters, numbers, hyphens, underscores
SAFE_FILENAME_REGEX = re.compile(r"[^a-zA-Z0-9\-_]")

def validate_recipient_data(
    name: str,
    email: str,
    certificate_id: str,
    seen_in_batch: set,
    existing_in_db: set
) -> Tuple[bool, Optional[str]]:
    """
    Validates recipient details individually.
    Returns: (is_valid, error_message)
    """
    # 1. Name validation
    if not name or not name.strip():
        return False, "Recipient name cannot be empty or whitespace-only."
    if len(name.strip()) > 255:
        return False, "Recipient name exceeds maximum length of 255 characters."

    # 2. Email validation
    clean_email = email.strip() if email else ""
    if not clean_email:
        return False, "Recipient email is required."
    if not EMAIL_REGEX.match(clean_email):
        return False, f"Invalid email format: '{clean_email}'."
    if len(clean_email) > 255:
        return False, "Recipient email exceeds maximum length of 255 characters."

    # 3. Certificate ID validation
    clean_cert_id = certificate_id.strip() if certificate_id else ""
    if not clean_cert_id:
        return False, "Certificate ID cannot be empty or whitespace-only."
    if len(clean_cert_id) > 100:
        return False, "Certificate ID exceeds maximum length of 100 characters."

    # 4. Duplicate within current batch
    if clean_cert_id in seen_in_batch:
        return False, f"Duplicate certificate ID '{clean_cert_id}' within current batch."

    # 5. Duplicate in database
    if clean_cert_id in existing_in_db:
        return False, f"Certificate ID '{clean_cert_id}' already exists in database."

    return True, None

def sanitize_filename(identifier: str) -> str:
    """
    Sanitizes an identifier to prevent path traversal and filesystem issues.
    """
    # Remove directory separators and null bytes
    cleaned = identifier.replace("/", "_").replace("\\", "_").replace("\0", "")
    # Keep only safe characters
    cleaned = SAFE_FILENAME_REGEX.sub("_", cleaned)
    # Strip leading/trailing dots and underscores
    cleaned = cleaned.strip("._")
    if not cleaned:
        cleaned = "certificate"
    return f"{cleaned}.pdf"
