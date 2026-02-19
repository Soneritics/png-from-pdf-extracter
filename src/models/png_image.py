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
        resolution: Output resolution as (width, height), configurable via Configuration
        density_dpi: Rendering DPI, configurable via Configuration
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
        if self.resolution[0] < 1 or self.resolution[1] < 1:
            raise ValueError("Resolution dimensions must be >= 1")
        if self.density_dpi < 1:
            raise ValueError("DPI must be >= 1")
        if self.page_number < 1:
            raise ValueError("Page number must be >= 1")
