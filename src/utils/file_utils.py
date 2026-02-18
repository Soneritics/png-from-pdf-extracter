"""File utilities for PDF-to-PNG email processor."""

import re


def sanitize_filename(filename: str, max_length: int = 50) -> str:
    """Sanitize filename for filesystem safety per FR-008.

    Removes special characters and truncates to max_length.
    Only allows alphanumeric characters, underscores, and hyphens.

    Args:
        filename: Original filename (e.g., "invoice (copy).pdf")
        max_length: Maximum length of sanitized filename (default: 50)

    Returns:
        Sanitized filename (e.g., "invoice_copy")

    Examples:
        >>> sanitize_filename("invoice (copy).pdf")
        'invoice_copy'
        >>> sanitize_filename("my*file?name.pdf")
        'myfilename'
        >>> sanitize_filename("a" * 100)
        'aaaaa...' (truncated to 50 chars)
    """
    # Remove file extension if present
    if "." in filename:
        name_without_ext = filename.rsplit(".", 1)[0]
    else:
        name_without_ext = filename

    # Replace non-alphanumeric characters (except underscore and hyphen) with underscore
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name_without_ext)

    # Remove consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")

    # Truncate to max_length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    # Ensure we have at least some content
    if not sanitized:
        sanitized = "unnamed"

    return sanitized
