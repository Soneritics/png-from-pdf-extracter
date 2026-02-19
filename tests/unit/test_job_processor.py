"""Unit tests for JobProcessorService."""

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock, patch

import pytest

from src.models.pdf_attachment import PDFAttachment
from src.services.imap_service import IMAPConnectionError
from src.services.job_processor import JobProcessorService


def _build_email_with_pdf(sender="alice@test.com", subject="Invoice", pdf_name="doc.pdf"):
    """Build raw email bytes with a PDF attachment."""
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["Subject"] = subject
    msg.attach(MIMEText("Please convert", "plain"))

    part = MIMEBase("application", "pdf")
    part.set_payload(b"%PDF-1.4 fake content")
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={pdf_name}")
    msg.attach(part)
    return msg.as_bytes()


@pytest.fixture()
def mock_services(config):
    """Create JobProcessorService with all mocked dependencies."""
    imap = MagicMock()
    smtp = MagicMock()
    converter = MagicMock()
    whitelist = MagicMock()
    whitelist.is_whitelisted.return_value = True

    processor = JobProcessorService(
        config=config,
        imap_service=imap,
        smtp_service=smtp,
        pdf_converter=converter,
        whitelist_service=whitelist,
    )
    return processor, imap, smtp, converter, whitelist


class TestJobProcessorInit:
    """Tests for JobProcessorService initialization."""

    def test_init(self, mock_services):
        """Service stores all dependencies."""
        processor, imap, smtp, converter, whitelist = mock_services
        assert processor.imap_service is imap
        assert processor.smtp_service is smtp
        assert processor.pdf_converter is converter
        assert processor.whitelist_service is whitelist


class TestProcessNextEmail:
    """Tests for JobProcessorService.process_next_email()."""

    def test_no_messages(self, mock_services):
        """process_next_email returns when no unseen messages."""
        processor, imap, _, _, _ = mock_services
        imap.fetch_unseen_messages.return_value = []

        processor.process_next_email()

        imap.delete_message.assert_not_called()

    def test_non_whitelisted_sender_ignored(self, mock_services, make_email):
        """Non-whitelisted sender is deleted without processing."""
        processor, imap, smtp, _, whitelist = mock_services
        whitelist.is_whitelisted.return_value = False
        imap.fetch_unseen_messages.return_value = [make_email(sender="spam@evil.com")]

        processor.process_next_email()

        imap.delete_message.assert_called_once()
        smtp.send_reply_with_attachments.assert_not_called()

    def test_no_pdf_attachments(self, mock_services, make_email):
        """Email without PDF attachments is deleted."""
        processor, imap, smtp, _, _ = mock_services
        msg = make_email(raw_bytes=b"From: alice@test.com\r\nSubject: Hello\r\n\r\nNo PDFs here")
        imap.fetch_unseen_messages.return_value = [msg]

        processor.process_next_email()

        imap.delete_message.assert_called_once()
        smtp.send_reply_with_attachments.assert_not_called()

    def test_successful_processing(self, mock_services, make_email):
        """Full flow: extract PDF, convert, send reply, delete."""
        processor, imap, smtp, converter, _ = mock_services

        raw_email = _build_email_with_pdf()
        msg = make_email(raw_bytes=raw_email)
        imap.fetch_unseen_messages.return_value = [msg]

        # Converter returns empty list (no actual PNGs since we can't create real files)
        converter.convert_pdf_to_png.return_value = []

        processor.process_next_email()

        converter.convert_pdf_to_png.assert_called_once()
        smtp.send_reply_with_attachments.assert_called_once()
        imap.delete_message.assert_called_once()

    def test_conversion_error_sends_notification(self, mock_services, make_email):
        """Conversion error triggers error notification email."""
        processor, imap, smtp, converter, _ = mock_services

        raw_email = _build_email_with_pdf()
        msg = make_email(raw_bytes=raw_email)
        imap.fetch_unseen_messages.return_value = [msg]

        converter.convert_pdf_to_png.side_effect = RuntimeError("conversion failed")

        processor.process_next_email()

        smtp.send_error_notification.assert_called_once()
        # Original email NOT deleted on failure
        imap.delete_message.assert_not_called()

    def test_error_notification_failure_logged(self, mock_services, make_email):
        """If error notification itself fails, error is logged but not raised."""
        processor, imap, smtp, converter, _ = mock_services

        raw_email = _build_email_with_pdf()
        msg = make_email(raw_bytes=raw_email)
        imap.fetch_unseen_messages.return_value = [msg]

        converter.convert_pdf_to_png.side_effect = RuntimeError("conversion failed")
        smtp.send_error_notification.side_effect = Exception("SMTP down")

        # Should not raise despite double failure
        processor.process_next_email()

    def test_fetch_error_propagates(self, mock_services):
        """Fatal fetch error is re-raised."""
        processor, imap, _, _, _ = mock_services
        imap.fetch_unseen_messages.side_effect = RuntimeError("IMAP broken")

        with pytest.raises(RuntimeError, match="IMAP broken"):
            processor.process_next_email()


class TestExtractPdfAttachments:
    """Tests for _extract_pdf_attachments."""

    def test_extract_pdf(self, mock_services, make_email):
        """Extracts PDF attachments from email."""
        processor, _, _, _, _ = mock_services
        raw_email = _build_email_with_pdf(pdf_name="invoice.pdf")
        msg = make_email(raw_bytes=raw_email)

        attachments = processor._extract_pdf_attachments(msg)

        assert len(attachments) == 1
        assert attachments[0].filename == "invoice.pdf"
        assert isinstance(attachments[0], PDFAttachment)

    def test_extract_no_pdf(self, mock_services, make_email):
        """Returns empty list when no PDF attachments."""
        processor, _, _, _, _ = mock_services
        msg = make_email(raw_bytes=b"From: a@b.com\r\nSubject: Hi\r\n\r\nNo attachments")

        attachments = processor._extract_pdf_attachments(msg)
        assert attachments == []


class TestRunDaemon:
    """Tests for JobProcessorService.run_daemon()."""

    @patch("src.services.job_processor.time.sleep")
    def test_daemon_keyboard_interrupt(self, _mock_sleep, mock_services):
        """Daemon exits on KeyboardInterrupt."""
        processor, _, _, _, _ = mock_services

        with (
            patch.object(processor, "process_next_email", side_effect=KeyboardInterrupt),
            pytest.raises(KeyboardInterrupt),
        ):
            processor.run_daemon()

    @patch("src.services.job_processor.time.sleep")
    def test_daemon_imap_reconnect(self, _mock_sleep, mock_services):
        """Daemon reconnects on IMAPConnectionError."""
        processor, imap, _, _, _ = mock_services

        call_count = 0

        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise IMAPConnectionError("lost connection")
            raise KeyboardInterrupt

        with (
            patch.object(processor, "process_next_email", side_effect=side_effect),
            pytest.raises(KeyboardInterrupt),
        ):
            processor.run_daemon()

        imap.connect_with_backoff.assert_called_once()

    @patch("src.services.job_processor.time.sleep")
    def test_daemon_general_error_continues(self, mock_sleep, mock_services):
        """Daemon continues after general errors."""
        processor, _, _, _, _ = mock_services

        call_count = 0

        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("transient error")
            raise KeyboardInterrupt

        with (
            patch.object(processor, "process_next_email", side_effect=side_effect),
            pytest.raises(KeyboardInterrupt),
        ):
            processor.run_daemon()

        # Should have slept (polling interval) before retrying
        assert mock_sleep.call_count >= 1

    @patch("src.services.job_processor.time.sleep")
    def test_daemon_reconnect_failure_continues(self, _mock_sleep, mock_services):
        """Daemon continues even when reconnection fails."""
        processor, imap, _, _, _ = mock_services
        imap.connect_with_backoff.side_effect = Exception("reconnect failed")

        call_count = 0

        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise IMAPConnectionError("lost")
            raise KeyboardInterrupt

        with (
            patch.object(processor, "process_next_email", side_effect=side_effect),
            pytest.raises(KeyboardInterrupt),
        ):
            processor.run_daemon()
