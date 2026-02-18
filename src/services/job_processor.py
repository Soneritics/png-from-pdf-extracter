"""Job processor service that orchestrates the PDF-to-PNG email workflow."""

import email
import email.policy
import tempfile
import time
from pathlib import Path

from src.config import Configuration
from src.models.pdf_attachment import PDFAttachment
from src.models.processing_job import JobStatus, ProcessingJob
from src.services.imap_service import IMAPService
from src.services.pdf_converter import PDFConverterService
from src.services.smtp_service import SMTPService
from src.services.whitelist_service import WhitelistService
from src.utils.file_utils import sanitize_filename
from src.utils.logging import get_logger

logger = get_logger()


class JobProcessorService:
    """Service that orchestrates the complete email→PDF→PNG→reply workflow.

    Implements FR-003, FR-004, FR-009, FR-012, FR-013, FR-021, FR-022, FR-023, FR-024.
    """

    def __init__(
        self,
        config: Configuration,
        imap_service: IMAPService,
        smtp_service: SMTPService,
        pdf_converter: PDFConverterService,
        whitelist_service: WhitelistService
    ) -> None:
        """Initialize job processor with dependencies.

        Args:
            config: Configuration instance
            imap_service: IMAP service for email retrieval
            smtp_service: SMTP service for email sending
            pdf_converter: PDF converter service
            whitelist_service: Whitelist service for sender validation
        """
        self.config = config
        self.imap_service = imap_service
        self.smtp_service = smtp_service
        self.pdf_converter = pdf_converter
        self.whitelist_service = whitelist_service

    def process_next_email(self) -> None:
        """Process the next unseen email from INBOX.

        Workflow per FR-003, FR-004, FR-009, FR-021:
        1. Fetch unseen messages from IMAP
        2. For each message:
           a. Extract PDF attachments
           b. Convert PDFs to PNGs
           c. Send reply email with PNG attachments
           d. Delete original email from INBOX

        Sequential processing per FR-022 (one email at a time).

        Error handling per FR-012, FR-013:
        - Send error notification email to sender if processing fails
        - Original email NOT deleted if processing fails per NFR-007
        """
        try:
            # Fetch unseen messages
            messages = self.imap_service.fetch_unseen_messages()

            if not messages:
                return  # No messages to process

            # Process first message only (sequential processing per FR-022)
            message = messages[0]

            # Validate sender against whitelist per FR-002, FR-014
            if not self.whitelist_service.is_whitelisted(message.sender):
                # Non-whitelisted sender - ignore silently per FR-014
                # No processing, no response, no error notification
                logger.error(f"Ignored email from non-whitelisted sender: {message.sender}")
                # Delete the message to prevent reprocessing
                self.imap_service.delete_message(message.uid)
                return

            # Create processing job
            job = ProcessingJob(email_message=message)
            job.mark_processing()

            try:
                # Extract PDF attachments from email
                pdf_attachments = self._extract_pdf_attachments(message)

                if not pdf_attachments:
                    # No PDFs found - ignore this email (extension of FR-014)
                    logger.error(f"No PDF attachments found in email from {message.sender}")
                    # Delete email since there's nothing to process
                    self.imap_service.delete_message(message.uid)
                    return

                job.pdf_attachments = pdf_attachments

                # Convert all PDFs to PNGs
                with tempfile.TemporaryDirectory() as tmpdir:
                    temp_path = Path(tmpdir)

                    for pdf in pdf_attachments:
                        # Write PDF content to temp file
                        pdf_path = temp_path / pdf.filename
                        pdf_path.write_bytes(pdf.content)

                        # Convert to PNG
                        png_images = self.pdf_converter.convert_pdf_to_png(
                            pdf_path=pdf_path,
                            output_prefix=pdf.sanitized_name,
                            temp_dir=temp_path
                        )

                        # Update page count
                        pdf.page_count = len(png_images)

                        # Add to job
                        job.png_images.extend(png_images)

                    # Send reply email with PNG attachments
                    subject = f"Re: {message.subject}"
                    body = (
                        f"Your PDF(s) have been converted to PNG images.\n\n"
                        f"PDF files processed: {len(pdf_attachments)}\n"
                        f"Total pages/images: {len(job.png_images)}\n\n"
                        f"Please find the PNG images attached."
                    )

                    self.smtp_service.send_reply_with_attachments(
                        to_address=message.sender,
                        subject=subject,
                        body=body,
                        attachments=job.png_images,
                        cc_addresses=self.config.cc_addresses
                    )

                # Mark job as completed
                job.mark_completed()

                # Delete original email per FR-021
                self.imap_service.delete_message(message.uid)

            except Exception as e:
                # Mark job as failed
                job.mark_failed(e)

                # Send error notification per FR-012, FR-013
                context = {
                    "Email Subject": message.subject,
                    "PDF Filenames": ", ".join(
                        pdf.filename for pdf in job.pdf_attachments
                    ) if job.pdf_attachments else "None",
                    "Sender": message.sender,
                }

                try:
                    self.smtp_service.send_error_notification(
                        to_address=message.sender,
                        error=e,
                        context=context
                    )
                except Exception as smtp_error:
                    logger.error(f"Failed to send error notification: {smtp_error}")

                # Log the error per FR-023, FR-024
                logger.error(
                    f"Failed to process email from {message.sender}: {e}",
                    exc_info=True
                )

                # Do NOT delete original email per NFR-007
                # Email remains in INBOX for manual recovery

        except Exception as e:
            # Fatal error in email fetching
            logger.error(f"Failed to fetch or process emails: {e}", exc_info=True)
            raise

    def _extract_pdf_attachments(self, message) -> list[PDFAttachment]:
        """Extract PDF attachments from email message.

        Args:
            message: EmailMessage object

        Returns:
            List of PDFAttachment objects
        """
        parsed_msg = email.message_from_bytes(message.raw_bytes, policy=email.policy.default)

        pdf_attachments = []

        # Iterate through email parts
        for part in parsed_msg.walk():
            # Check if this is an attachment
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()

                # Check if PDF file
                if filename and filename.lower().endswith(".pdf"):
                    content = part.get_payload(decode=True)

                    if content:
                        sanitized_name = sanitize_filename(filename)

                        pdf_attachments.append(
                            PDFAttachment(
                                filename=filename,
                                sanitized_name=sanitized_name,
                                content=content,
                                size_bytes=len(content)
                            )
                        )

        return pdf_attachments

    def run_daemon(self) -> None:
        """Run continuous polling loop with IMAP connection recovery per FR-001, FR-016, FR-027.

        This method implements the daemon behavior:
        1. Continuous polling loop with configured interval
        2. Sequential email processing (one at a time per FR-022)
        3. IMAP connection recovery with exponential backoff per FR-027
        4. Runs indefinitely per NFR-011

        The daemon will continue running even if:
        - IMAP connection is lost (reconnects with backoff)
        - Individual email processing fails (logs error, continues)
        - SMTP errors occur (logs error, continues)
        """
        while True:
            try:
                # Process next email
                self.process_next_email()

            except IMAPConnectionError:
                # IMAP connection lost - reconnect with backoff per FR-027
                logger.error("IMAP connection lost. Attempting reconnection with backoff...")
                try:
                    self.imap_service.connect_with_backoff()
                    logger.error("IMAP connection restored successfully")
                except Exception as reconnect_error:
                    logger.error(f"Failed to reconnect to IMAP: {reconnect_error}")
                    # Continue trying in next iteration

            except KeyboardInterrupt:
                # Allow graceful shutdown
                raise

            except Exception as e:
                # Log error but keep running per NFR-011
                logger.error(f"Error in daemon loop: {e}", exc_info=True)

            # Sleep for polling interval per FR-001
            time.sleep(self.config.polling_interval_seconds)

