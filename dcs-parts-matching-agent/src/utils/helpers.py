"""
Helper utilities for common operations.

Provides utility functions for file handling, validation, and data processing.
"""

import hashlib
import mimetypes
import uuid
from pathlib import Path
from typing import Optional, Tuple
from ..core.models import DocumentType


def generate_request_id() -> str:
    """
    Generate a unique request ID.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def get_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        Hex digest of file hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def detect_document_type(file_path: Path) -> DocumentType:
    """
    Detect document type from file extension and MIME type.

    Args:
        file_path: Path to file

    Returns:
        Detected DocumentType
    """
    extension = file_path.suffix.lower()
    mime_type, _ = mimetypes.guess_type(str(file_path))

    if extension == ".pdf":
        return DocumentType.PDF
    elif extension in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"]:
        return DocumentType.IMAGE
    elif extension == ".dwg":
        return DocumentType.CAD_DWG
    elif extension == ".dxf":
        return DocumentType.CAD_DXF
    elif extension in [".txt", ".doc", ".docx"]:
        return DocumentType.TEXT
    else:
        return DocumentType.UNKNOWN


def validate_file_size(file_path: Path, max_size_mb: int) -> Tuple[bool, Optional[str]]:
    """
    Validate file size against maximum allowed.

    Args:
        file_path: Path to file
        max_size_mb: Maximum allowed size in MB

    Returns:
        Tuple of (is_valid, error_message)
    """
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed ({max_size_mb} MB)"
    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = Path(filename).name

    # Replace potentially dangerous characters
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')

    return filename


def parse_dimension_string(dim_str: str) -> Optional[float]:
    """
    Parse dimension string to float value.

    Handles various formats like "10.5mm", "2.5 inches", "100"

    Args:
        dim_str: Dimension string

    Returns:
        Parsed float value or None if parsing fails
    """
    import re

    # Remove whitespace
    dim_str = dim_str.strip()

    # Try to extract number
    match = re.search(r'(\d+\.?\d*)', dim_str)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def calculate_dimensional_similarity(dim1: dict, dim2: dict, tolerance_percent: float = 5.0) -> float:
    """
    Calculate similarity between two dimensional specifications.

    Args:
        dim1: First dimension dict
        dim2: Second dimension dict
        tolerance_percent: Allowed tolerance percentage

    Returns:
        Similarity score 0.0-1.0
    """
    if not dim1 or not dim2:
        return 0.0

    common_dims = set(dim1.keys()) & set(dim2.keys())
    if not common_dims:
        return 0.0

    matches = 0
    total = len(common_dims)

    for dim in common_dims:
        try:
            val1 = float(dim1[dim])
            val2 = float(dim2[dim])

            if val1 == 0 or val2 == 0:
                if val1 == val2:
                    matches += 1
                continue

            # Calculate percentage difference
            diff_percent = abs(val1 - val2) / max(val1, val2) * 100

            if diff_percent <= tolerance_percent:
                matches += 1
        except (ValueError, TypeError):
            # If can't convert to float, do string comparison
            if str(dim1[dim]).lower() == str(dim2[dim]).lower():
                matches += 1

    return matches / total if total > 0 else 0.0


def normalize_specification_value(value: str, spec_type: str) -> str:
    """
    Normalize specification value for comparison.

    Args:
        value: Raw specification value
        spec_type: Type of specification

    Returns:
        Normalized value
    """
    value = value.strip().lower()

    # Remove common prefixes/suffixes
    value = value.replace('approx.', '').replace('~', '').strip()

    return value
