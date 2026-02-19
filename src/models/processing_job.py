"""ProcessingJob entity for PDF-to-PNG email processor."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from src.models.email_message import EmailMessage
from src.models.pdf_attachment import PDFAttachment
from src.models.png_image import PNGImage


class JobStatus(Enum):
    """Status of a processing job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingJob:
    """Represents the complete processing lifecycle for one incoming email.

    Attributes:
        email_message: The email being processed
        pdf_attachments: Extracted PDF files
        png_images: All generated PNG images across all PDFs
        status: Current job state
        error: Captured exception if processing failed
        started_at: When processing began
        completed_at: When processing finished (success or failure)
        duration_seconds: Time taken to process
    """

    email_message: EmailMessage
    pdf_attachments: list[PDFAttachment] = field(default_factory=list)
    png_images: list[PNGImage] = field(default_factory=list)
    status: JobStatus = JobStatus.PENDING
    error: Exception | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    completed_at: datetime | None = None
    duration_seconds: float | None = None

    def __post_init__(self) -> None:
        """Validate ProcessingJob after initialization."""
        if self.email_message is None:
            raise ValueError("email_message must not be None")

        # Validate status transitions
        if self.status == JobStatus.COMPLETED and self.error is not None:
            raise ValueError("Completed jobs must not have errors")

        # Validate timestamps
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must be >= started_at")

    def mark_processing(self) -> None:
        """Mark job as processing."""
        self.status = JobStatus.PROCESSING

    def mark_completed(self) -> None:
        """Mark job as completed successfully."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(tz=UTC)
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def mark_failed(self, error: Exception) -> None:
        """Mark job as failed with error.

        Args:
            error: The exception that caused the failure
        """
        self.status = JobStatus.FAILED
        self.error = error
        self.completed_at = datetime.now(tz=UTC)
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
