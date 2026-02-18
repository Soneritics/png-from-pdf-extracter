"""PDFAttachment entity for PDF-to-PNG email processor."""

from dataclasses import dataclass


@dataclass
class PDFAttachment:
    """Represents a PDF file extracted from an email message.

    Attributes:
        filename: Original attachment filename from email
        sanitized_name: Filename sanitized for filesystem safety
        content: Binary content of the PDF file
        size_bytes: Size of the PDF in bytes
        page_count: Number of pages (detected after conversion, may be None)
    """

    filename: str
    sanitized_name: str
    content: bytes
    size_bytes: int
    page_count: int | None = None

    def __post_init__(self) -> None:
        """Validate PDFAttachment after initialization."""
        if not self.filename.lower().endswith(".pdf"):
            raise ValueError("Filename must have .pdf extension")
        if self.size_bytes <= 0:
            raise ValueError("PDF must not be empty")
        if self.size_bytes > 100 * 1024 * 1024:  # 100MB limit
            raise ValueError("PDF must be < 100MB")
        if not all(c.isalnum() or c in "_-" for c in self.sanitized_name):
            raise ValueError("Sanitized name must contain only alphanumeric, underscore, hyphen")
