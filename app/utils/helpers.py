import re
import hashlib
from typing import Optional

def sanitize_filename(filename: str) -> str:
    """Sanitizes file name to prevent directory traversal and invalid characters."""
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

def compute_file_hash(file_bytes: bytes) -> str:
    """Computes SHA-256 hash of file content for deduplication."""
    return hashlib.sha256(file_bytes).hexdigest()

def is_allowed_file(filename: str, allowed_extensions: Optional[list] = None) -> bool:
    if allowed_extensions is None:
        allowed_extensions = [".pdf", ".txt", ".md", ".wav", ".mp3"]
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed_extensions
