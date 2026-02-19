"""Unit tests for PDFConverterService."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.pdf_converter import (
    PDFConversionError,
    PDFConverterService,
    PDFCorruptedError,
    PDFPasswordProtectedError,
)
from src.utils.file_utils import sanitize_filename


def test_sanitize_filename_removes_special_chars():
    """T031 [US1] Unit test: PDFConverterService.sanitize_filename removes special chars."""
    assert sanitize_filename("invoice (copy).pdf") == "invoice_copy"
    assert sanitize_filename("my*file?name.pdf") == "my_file_name"
    assert sanitize_filename("report#2024!.pdf") == "report_2024"
    assert sanitize_filename("file:with:colons.pdf") == "file_with_colons"
    assert sanitize_filename("test@file$here%.pdf") == "test_file_here"


def test_sanitize_filename_truncates_to_50_chars():
    """T032 [US1] Unit test: sanitize_filename truncates to 50 chars."""
    long_name = "a" * 100 + ".pdf"
    result = sanitize_filename(long_name)
    assert len(result) == 50
    assert result == "a" * 50


def test_sanitize_filename_no_extension():
    """sanitize_filename handles filenames without extension."""
    assert sanitize_filename("readme") == "readme"


def test_sanitize_filename_empty_becomes_unnamed():
    """sanitize_filename returns 'unnamed' for empty/special-only names."""
    assert sanitize_filename("!!!.pdf") == "unnamed"


def test_pdf_converter_default_config():
    """PDFConverterService uses defaults when no config given."""
    converter = PDFConverterService()
    assert converter.target_resolution == (1920, 1080)
    assert converter.target_dpi == 300
    assert converter.background == "white"
    assert converter.timeout == 120


def test_pdf_converter_with_config(config):
    """PDFConverterService uses config values."""
    converter = PDFConverterService(config)
    assert converter.target_resolution == (
        config.pdf_resolution_width,
        config.pdf_resolution_height,
    )
    assert converter.target_dpi == config.pdf_density_dpi


def test_pdf_converter_raises_error_on_corrupted_pdf():
    """PDFConverterService raises PDFCorruptedError on malformed PDF."""
    converter = PDFConverterService()
    mock_result = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="Error: corrupted PDF file"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        corrupted_pdf = Path(tmpdir) / "corrupted.pdf"
        corrupted_pdf.write_bytes(b"This is not a valid PDF file")

        with (
            patch("subprocess.run", return_value=mock_result),
            pytest.raises(PDFCorruptedError),
        ):
            converter.convert_pdf_to_png(
                pdf_path=corrupted_pdf, output_prefix="test", temp_dir=Path(tmpdir)
            )


def test_pdf_converter_raises_error_on_encrypted_pdf():
    """PDFConverterService raises PDFPasswordProtectedError on encrypted PDF."""
    converter = PDFConverterService()
    mock_result = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="This PDF is password protected"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "encrypted.pdf"
        pdf_path.write_bytes(b"fake encrypted pdf")

        with (
            patch("subprocess.run", return_value=mock_result),
            pytest.raises(PDFPasswordProtectedError),
        ):
            converter.convert_pdf_to_png(
                pdf_path=pdf_path, output_prefix="test", temp_dir=Path(tmpdir)
            )


def test_pdf_converter_generic_error():
    """PDFConverterService raises PDFConversionError on generic failure."""
    converter = PDFConverterService()
    mock_result = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="some unknown failure"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        with (
            patch("subprocess.run", return_value=mock_result),
            pytest.raises(PDFConversionError, match="ImageMagick conversion failed"),
        ):
            converter.convert_pdf_to_png(
                pdf_path=pdf_path, output_prefix="test", temp_dir=Path(tmpdir)
            )


def test_pdf_converter_file_not_found():
    """PDFConverterService raises on non-existent PDF."""
    converter = PDFConverterService()

    with (
        tempfile.TemporaryDirectory() as tmpdir,
        pytest.raises(PDFConversionError, match="not found"),
    ):
        converter.convert_pdf_to_png(
            pdf_path=Path(tmpdir) / "nonexistent.pdf",
            output_prefix="test",
            temp_dir=Path(tmpdir),
        )


def test_pdf_converter_timeout():
    """PDFConverterService raises on timeout."""
    converter = PDFConverterService()

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        with (
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired("magick", 120)),
            pytest.raises(PDFConversionError, match="timed out"),
        ):
            converter.convert_pdf_to_png(
                pdf_path=pdf_path, output_prefix="test", temp_dir=Path(tmpdir)
            )


def test_pdf_converter_magick_not_found():
    """PDFConverterService raises when magick command not found."""
    converter = PDFConverterService()

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        with (
            patch("subprocess.run", side_effect=FileNotFoundError("magick")),
            pytest.raises(PDFConversionError, match="not found"),
        ):
            converter.convert_pdf_to_png(
                pdf_path=pdf_path, output_prefix="test", temp_dir=Path(tmpdir)
            )


def test_pdf_converter_no_pngs_generated():
    """PDFConverterService raises when conversion produces no PNGs."""
    converter = PDFConverterService()
    mock_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "empty.pdf"
        pdf_path.write_bytes(b"fake pdf")

        with (
            patch("subprocess.run", return_value=mock_result),
            pytest.raises(PDFConversionError, match="No PNG files generated"),
        ):
            converter.convert_pdf_to_png(
                pdf_path=pdf_path, output_prefix="test", temp_dir=Path(tmpdir)
            )


def test_pdf_converter_success():
    """PDFConverterService returns PNGImage list on success."""
    converter = PDFConverterService()
    mock_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pdf_path = tmpdir_path / "doc.pdf"
        pdf_path.write_bytes(b"fake pdf")

        # Create fake output PNGs
        png1 = tmpdir_path / "doc_pdf-000.png"
        png2 = tmpdir_path / "doc_pdf-001.png"
        png1.write_bytes(b"\x89PNG page1")
        png2.write_bytes(b"\x89PNG page2")

        with patch("subprocess.run", return_value=mock_result):
            images = converter.convert_pdf_to_png(
                pdf_path=pdf_path, output_prefix="doc", temp_dir=tmpdir_path
            )

        assert len(images) == 2
        assert images[0].page_number == 1
        assert images[1].page_number == 2
        assert images[0].source_pdf == "doc.pdf"
        assert images[0].resolution == (1920, 1080)
