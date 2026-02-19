"""Unit tests for PDFConverterService."""

import tempfile
from pathlib import Path

import pytest

from src.services.pdf_converter import (
    PDFConverterService,
    PDFCorruptedError,
)
from src.utils.file_utils import sanitize_filename


def test_sanitize_filename_removes_special_chars():
    """T031 [US1] Unit test: PDFConverterService.sanitize_filename removes special chars."""
    # Test with various special characters
    assert sanitize_filename("invoice (copy).pdf") == "invoice_copy"
    assert sanitize_filename("my*file?name.pdf") == "my_file_name"
    assert sanitize_filename("report#2024!.pdf") == "report_2024"
    assert sanitize_filename("file:with:colons.pdf") == "file_with_colons"
    assert sanitize_filename("test@file$here%.pdf") == "test_file_here"


def test_sanitize_filename_truncates_to_50_chars():
    """T032 [US1] Unit test: PDFConverterService.sanitize_filename truncates to 50 chars."""
    long_name = "a" * 100 + ".pdf"
    result = sanitize_filename(long_name)
    assert len(result) == 50
    assert result == "a" * 50


def test_pdf_converter_raises_error_on_corrupted_pdf():
    """T033 [US1] Unit test: PDFConverterService raises PDFCorruptedError on malformed PDF."""
    converter = PDFConverterService()

    # Create a fake corrupted PDF (just random bytes)
    with tempfile.TemporaryDirectory() as tmpdir:
        corrupted_pdf = Path(tmpdir) / "corrupted.pdf"
        corrupted_pdf.write_bytes(b"This is not a valid PDF file")

        with pytest.raises(PDFCorruptedError):
            converter.convert_pdf_to_png(
                pdf_path=corrupted_pdf, output_prefix="test", temp_dir=Path(tmpdir)
            )


def test_pdf_converter_raises_error_on_encrypted_pdf():
    """T034 [US1] Unit test: PDFConverterService raises error on encrypted PDF."""
    PDFConverterService()

    # Note: Creating an actual encrypted PDF requires external tools
    # This test will be implemented when we have encrypted PDF test fixtures
    # For now, we'll skip it
    pytest.skip("Encrypted PDF test fixture not yet available")
