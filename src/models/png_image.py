"""PNGImage entity for PDF-to-PNG email processor."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PNGImage:
    """Represents a generated PNG image from a single PDF page.

    Attributes:
        path: Filesystem path to the PNG file (in temp directory)
        filename: Final filename for email attachment
        source_pdf: Original PDF filename this image came from
        page_number: PDF page number (1-indexed)
        size_bytes: File size of the PNG
        resolution: Always (1920, 1080) per FR-006
        density_dpi: Always 300 per FR-005
    """

    path: Path
    filename: str
    source_pdf: str
    page_number: int
    size_bytes: int
    resolution: tuple[int, int]
    density_dpi: int

    def __post_init__(self) -> None:
        """Validate PNGImage after initialization."""
        if not self.path.exists():
            raise ValueError("PNG file must exist on filesystem")
        if self.size_bytes <= 0:
            raise ValueError("PNG must not be empty")
        if self.resolution != (1920, 1080):
            raise ValueError("Resolution must be 1920x1080")
        if self.density_dpi != 300:
            raise ValueError("DPI must be 300")
        if self.page_number < 1:
            raise ValueError("Page number must be >= 1")
