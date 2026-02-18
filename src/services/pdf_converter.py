"""PDF to PNG conversion service using ImageMagick."""

import subprocess
from pathlib import Path

from src.models.png_image import PNGImage
from src.utils.logging import get_logger

logger = get_logger()


class PDFConversionError(Exception):
    """Base exception for PDF conversion errors."""
    pass


class PDFCorruptedError(PDFConversionError):
    """Raised when PDF file is corrupted or malformed."""
    pass


class PDFPasswordProtectedError(PDFConversionError):
    """Raised when PDF file is password-protected or encrypted."""
    pass


class PDFConverterService:
    """Service for converting PDF files to PNG images using ImageMagick.

    Uses ImageMagick's 'magick' command to convert PDF pages to PNG images
    at 1920x1080 resolution with 300 DPI per FR-004, FR-005, FR-006, FR-007, FR-008.
    """

    def __init__(self) -> None:
        """Initialize PDF converter service."""
        self.target_resolution = (1920, 1080)
        self.target_dpi = 300
        self.quality = 95

    def convert_pdf_to_png(
        self,
        pdf_path: Path,
        output_prefix: str,
        temp_dir: Path
    ) -> list[PNGImage]:
        """Convert PDF file to PNG images (one per page).

        Args:
            pdf_path: Path to PDF file
            output_prefix: Prefix for output PNG filenames (sanitized)
            temp_dir: Directory to store PNG files

        Returns:
            List of PNGImage objects (one per PDF page)

        Raises:
            PDFCorruptedError: If PDF is malformed or cannot be read
            PDFPasswordProtectedError: If PDF is encrypted
            PDFConversionError: If conversion fails for other reasons
        """
        if not pdf_path.exists():
            raise PDFConversionError(f"PDF file not found: {pdf_path}")

        # Output pattern: prefix_pdf-001.png, prefix_pdf-002.png, etc.
        output_pattern = temp_dir / f"{output_prefix}_pdf-%03d.png"

        # Build ImageMagick command
        cmd = [
            "magick",
            "-density", str(self.target_dpi),  # Set DPI for PDF reading
            str(pdf_path),
            "-resize", f"{self.target_resolution[0]}x{self.target_resolution[1]}!",  # Force exact size
            "-quality", str(self.quality),
            str(output_pattern)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout per SC-001
                check=False  # Don't raise exception, we'll handle errors manually
            )

            # Check for specific error patterns
            if result.returncode != 0:
                stderr_lower = result.stderr.lower()

                # Check for password protection
                if "password" in stderr_lower or "encrypted" in stderr_lower:
                    raise PDFPasswordProtectedError(
                        f"PDF is password-protected or encrypted: {result.stderr}"
                    )

                # Check for corruption
                if "corrupt" in stderr_lower or "invalid" in stderr_lower or "error" in stderr_lower:
                    raise PDFCorruptedError(
                        f"PDF is corrupted or malformed: {result.stderr}"
                    )

                # Generic conversion error
                raise PDFConversionError(
                    f"ImageMagick conversion failed (exit code {result.returncode}): {result.stderr}"
                )

        except subprocess.TimeoutExpired as e:
            raise PDFConversionError(
                f"PDF conversion timed out after 120 seconds: {pdf_path}"
            ) from e
        except FileNotFoundError as e:
            raise PDFConversionError(
                "ImageMagick 'magick' command not found. Is ImageMagick installed?"
            ) from e

        # Find all generated PNG files
        png_files = sorted(temp_dir.glob(f"{output_prefix}_pdf-*.png"))

        if not png_files:
            raise PDFConversionError(
                f"No PNG files generated from PDF: {pdf_path}. "
                "PDF may be empty or have 0 pages."
            )

        # Create PNGImage objects for each generated file
        png_images = []
        for idx, png_path in enumerate(png_files, start=1):
            # Extract page number from filename (e.g., "prefix_pdf-002.png" → page 3)
            # The %03d format means: 000 → page 1, 001 → page 2, etc.
            page_number = idx  # Sequential numbering

            png_images.append(
                PNGImage(
                    path=png_path,
                    filename=png_path.name,
                    source_pdf=pdf_path.name,
                    page_number=page_number,
                    size_bytes=png_path.stat().st_size,
                    resolution=self.target_resolution,
                    density_dpi=self.target_dpi
                )
            )

        return png_images
