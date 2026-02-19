"""Contract tests for ImageMagick CLI tool."""

import subprocess
import tempfile
from pathlib import Path

import pytest


def test_imagemagick_availability():
    """T027 [US1] Contract test: ImageMagick CLI availability."""
    # Test that 'magick' command is available
    try:
        result = subprocess.run(
            ["magick", "--version"], capture_output=True, text=True, check=True, timeout=5
        )
        assert "ImageMagick" in result.stdout
        assert result.returncode == 0
    except FileNotFoundError:
        pytest.fail("ImageMagick CLI 'magick' command not found")
    except subprocess.CalledProcessError as e:
        pytest.fail(f"ImageMagick version check failed: {e}")


def test_imagemagick_single_page_conversion():
    """T028 [US1] Contract test: ImageMagick converts single-page PDF to PNG."""
    # Create a minimal single-page PDF for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        output_pattern = Path(tmpdir) / "test_pdf-%03d.png"

        # Create a minimal PDF using ImageMagick itself (convert from solid color)
        subprocess.run(
            [
                "magick",
                "-size",
                "1920x1080",
                "xc:white",  # Solid white canvas
                "-density",
                "300",
                str(pdf_path),
            ],
            check=True,
            capture_output=True,
            timeout=10,
        )

        assert pdf_path.exists(), "Test PDF creation failed"

        # Convert PDF to PNG
        result = subprocess.run(
            [
                "magick",
                "-density",
                "300",
                str(pdf_path),
                "-resize",
                "1920x1080!",
                "-quality",
                "95",
                str(output_pattern),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        # Should succeed
        assert result.returncode == 0, f"Conversion failed: {result.stderr}"

        # Check output file exists
        expected_file = Path(tmpdir) / "test_pdf-000.png"
        assert expected_file.exists(), "PNG output file not created"

        # Verify resolution using ImageMagick identify
        identify_result = subprocess.run(
            ["magick", "identify", "-format", "%wx%h", str(expected_file)],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        resolution = identify_result.stdout.strip()
        assert resolution == "1920x1080", f"Expected 1920x1080, got {resolution}"


def test_imagemagick_multipage_conversion():
    """T029 [US1] Contract test: ImageMagick converts multi-page PDF with sequential numbering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "multipage.pdf"
        output_pattern = Path(tmpdir) / "multipage_pdf-%03d.png"

        # Create a 3-page PDF using ImageMagick
        subprocess.run(
            [
                "magick",
                "-size",
                "1920x1080",
                "xc:white",
                "xc:gray",
                "xc:black",  # 3 pages with different colors
                "-density",
                "300",
                str(pdf_path),
            ],
            check=True,
            capture_output=True,
            timeout=10,
        )

        # Convert to PNG
        result = subprocess.run(
            [
                "magick",
                "-density",
                "300",
                str(pdf_path),
                "-resize",
                "1920x1080!",
                "-quality",
                "95",
                str(output_pattern),
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        assert result.returncode == 0, f"Conversion failed: {result.stderr}"

        # Verify all 3 pages were created with sequential numbering
        expected_files = [
            Path(tmpdir) / "multipage_pdf-000.png",
            Path(tmpdir) / "multipage_pdf-001.png",
            Path(tmpdir) / "multipage_pdf-002.png",
        ]

        for expected_file in expected_files:
            assert expected_file.exists(), f"PNG page {expected_file.name} not created"
            assert expected_file.stat().st_size > 0, f"PNG page {expected_file.name} is empty"
