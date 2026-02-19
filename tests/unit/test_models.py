"""Unit tests for all model dataclasses."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.models.pdf_attachment import PDFAttachment
from src.models.png_image import PNGImage
from src.models.processing_job import JobStatus, ProcessingJob

_UTC = timezone.utc

# --- EmailMessage tests ---


class TestEmailMessage:
    """Tests for EmailMessage dataclass."""

    def test_valid_email_message(self, make_email):
        """Valid EmailMessage is created without errors."""
        msg = make_email()
        assert msg.uid == 1
        assert msg.sender == "alice@test.com"
        assert msg.subject == "Test PDF"

    def test_invalid_uid_raises(self, make_email):
        """UID <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="UID must be positive"):
            make_email(uid=0)

    def test_negative_uid_raises(self, make_email):
        """Negative UID raises ValueError."""
        with pytest.raises(ValueError, match="UID must be positive"):
            make_email(uid=-5)

    def test_invalid_sender_raises(self, make_email):
        """Sender without @ raises ValueError."""
        with pytest.raises(ValueError, match="valid email"):
            make_email(sender="not-an-email")

    def test_empty_raw_bytes_raises(self, make_email):
        """Empty raw_bytes raises ValueError."""
        with pytest.raises(ValueError, match="Raw bytes must not be empty"):
            make_email(raw_bytes=b"")


# --- PDFAttachment tests ---


class TestPDFAttachment:
    """Tests for PDFAttachment dataclass."""

    def test_valid_pdf_attachment(self):
        """Valid PDFAttachment is created without errors."""
        pdf = PDFAttachment(
            filename="invoice.pdf",
            sanitized_name="invoice",
            content=b"%PDF-1.4 content",
            size_bytes=100,
        )
        assert pdf.filename == "invoice.pdf"
        assert pdf.page_count is None

    def test_non_pdf_extension_raises(self):
        """Non-.pdf filename raises ValueError."""
        with pytest.raises(ValueError, match="pdf extension"):
            PDFAttachment(
                filename="document.docx",
                sanitized_name="document",
                content=b"content",
                size_bytes=7,
            )

    def test_empty_pdf_raises(self):
        """Zero-size PDF raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            PDFAttachment(
                filename="empty.pdf",
                sanitized_name="empty",
                content=b"",
                size_bytes=0,
            )

    def test_oversized_pdf_raises(self):
        """PDF > 100MB raises ValueError."""
        with pytest.raises(ValueError, match="100MB"):
            PDFAttachment(
                filename="huge.pdf",
                sanitized_name="huge",
                content=b"x",
                size_bytes=200 * 1024 * 1024,
            )

    def test_invalid_sanitized_name_raises(self):
        """Sanitized name with special chars raises ValueError."""
        with pytest.raises(ValueError, match="alphanumeric"):
            PDFAttachment(
                filename="test.pdf",
                sanitized_name="test file!",
                content=b"pdf",
                size_bytes=3,
            )

    def test_page_count_optional(self):
        """page_count defaults to None and can be set."""
        pdf = PDFAttachment(
            filename="a.pdf",
            sanitized_name="a",
            content=b"data",
            size_bytes=4,
        )
        assert pdf.page_count is None
        pdf.page_count = 3
        assert pdf.page_count == 3


# --- PNGImage tests ---


class TestPNGImage:
    """Tests for PNGImage dataclass."""

    def test_valid_png_image(self):
        """Valid PNGImage is created when file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = Path(tmpdir) / "test.png"
            png_path.write_bytes(b"\x89PNG fake content")

            img = PNGImage(
                path=png_path,
                filename="test.png",
                source_pdf="doc.pdf",
                page_number=1,
                size_bytes=17,
                resolution=(1920, 1080),
                density_dpi=300,
            )
            assert img.page_number == 1
            assert img.resolution == (1920, 1080)

    def test_nonexistent_path_raises(self):
        """PNGImage with non-existent path raises ValueError."""
        with pytest.raises(ValueError, match="must exist"):
            PNGImage(
                path=Path("/nonexistent/test.png"),
                filename="test.png",
                source_pdf="doc.pdf",
                page_number=1,
                size_bytes=100,
                resolution=(1920, 1080),
                density_dpi=300,
            )

    def test_zero_size_raises(self):
        """PNGImage with zero size raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = Path(tmpdir) / "test.png"
            png_path.write_bytes(b"x")

            with pytest.raises(ValueError, match="must not be empty"):
                PNGImage(
                    path=png_path,
                    filename="test.png",
                    source_pdf="doc.pdf",
                    page_number=1,
                    size_bytes=0,
                    resolution=(1920, 1080),
                    density_dpi=300,
                )

    def test_invalid_resolution_raises(self):
        """PNGImage with zero resolution raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = Path(tmpdir) / "test.png"
            png_path.write_bytes(b"x")

            with pytest.raises(ValueError, match="Resolution"):
                PNGImage(
                    path=png_path,
                    filename="test.png",
                    source_pdf="doc.pdf",
                    page_number=1,
                    size_bytes=1,
                    resolution=(0, 1080),
                    density_dpi=300,
                )

    def test_invalid_dpi_raises(self):
        """PNGImage with zero DPI raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = Path(tmpdir) / "test.png"
            png_path.write_bytes(b"x")

            with pytest.raises(ValueError, match="DPI"):
                PNGImage(
                    path=png_path,
                    filename="test.png",
                    source_pdf="doc.pdf",
                    page_number=1,
                    size_bytes=1,
                    resolution=(1920, 1080),
                    density_dpi=0,
                )

    def test_invalid_page_number_raises(self):
        """PNGImage with page_number < 1 raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = Path(tmpdir) / "test.png"
            png_path.write_bytes(b"x")

            with pytest.raises(ValueError, match="Page number"):
                PNGImage(
                    path=png_path,
                    filename="test.png",
                    source_pdf="doc.pdf",
                    page_number=0,
                    size_bytes=1,
                    resolution=(1920, 1080),
                    density_dpi=300,
                )


# --- ProcessingJob tests ---


class TestProcessingJob:
    """Tests for ProcessingJob dataclass."""

    def test_valid_processing_job(self, email_msg):
        """Valid ProcessingJob is created with defaults."""
        job = ProcessingJob(email_message=email_msg)
        assert job.status == JobStatus.PENDING
        assert job.error is None
        assert job.completed_at is None
        assert job.pdf_attachments == []
        assert job.png_images == []

    def test_none_email_raises(self):
        """None email_message raises ValueError."""
        with pytest.raises(ValueError, match="must not be None"):
            ProcessingJob(email_message=None)

    def test_mark_processing(self, email_msg):
        """mark_processing transitions to PROCESSING."""
        job = ProcessingJob(email_message=email_msg)
        job.mark_processing()
        assert job.status == JobStatus.PROCESSING

    def test_mark_completed(self, email_msg):
        """mark_completed transitions to COMPLETED with timestamp."""
        job = ProcessingJob(email_message=email_msg)
        job.mark_completed()
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.duration_seconds is not None
        assert job.duration_seconds >= 0

    def test_mark_failed(self, email_msg):
        """mark_failed transitions to FAILED with error and timestamp."""
        job = ProcessingJob(email_message=email_msg)
        error = RuntimeError("conversion failed")
        job.mark_failed(error)
        assert job.status == JobStatus.FAILED
        assert job.error is error
        assert job.completed_at is not None
        assert job.duration_seconds >= 0

    def test_completed_with_error_raises(self, email_msg):
        """Completed status with error set raises ValueError."""
        with pytest.raises(ValueError, match="must not have errors"):
            ProcessingJob(
                email_message=email_msg,
                status=JobStatus.COMPLETED,
                error=RuntimeError("oops"),
            )

    def test_completed_at_before_started_raises(self, email_msg):
        """completed_at < started_at raises ValueError."""
        early = datetime(2020, 1, 1, tzinfo=_UTC)
        late = datetime(2025, 1, 1, tzinfo=_UTC)
        with pytest.raises(ValueError, match="completed_at must be >= started_at"):
            ProcessingJob(
                email_message=email_msg,
                started_at=late,
                completed_at=early,
            )

    def test_job_status_enum(self):
        """JobStatus enum has expected values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
