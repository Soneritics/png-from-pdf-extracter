"""Unit tests for SMTPService."""

import smtplib
import ssl
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.png_image import PNGImage
from src.services.smtp_service import (
    SMTPAuthenticationError,
    SMTPConnectionError,
    SMTPError,
    SMTPService,
)


@pytest.fixture()
def smtp_service(config):
    """SMTPService with test config."""
    return SMTPService(config)


def _make_png_image(tmpdir: Path, name: str = "test.png") -> PNGImage:
    """Create a real PNGImage with a temp file."""
    png_path = tmpdir / name
    png_path.write_bytes(b"\x89PNG fake content here!")
    return PNGImage(
        path=png_path,
        filename=name,
        source_pdf="doc.pdf",
        page_number=1,
        size_bytes=png_path.stat().st_size,
        resolution=(1920, 1080),
        density_dpi=300,
    )


class TestSMTPServiceInit:
    """Tests for SMTPService initialization."""

    def test_init(self, smtp_service, config):
        """Service stores config and has no connection."""
        assert smtp_service.config is config
        assert smtp_service.connection is None


class TestSMTPServiceConnect:
    """Tests for SMTPService.connect()."""

    @patch("src.services.smtp_service.smtplib")
    def test_connect_ssl_success(self, mock_smtplib, smtp_service):
        """connect() succeeds with SMTP_SSL."""
        mock_conn = MagicMock()
        mock_smtplib.SMTP_SSL.return_value = mock_conn

        smtp_service.connect()

        mock_smtplib.SMTP_SSL.assert_called_once_with("smtp.test.com", 587, timeout=30)
        mock_conn.login.assert_called_once_with("user@test.com", "secret")

    @patch("src.services.smtp_service.smtplib")
    def test_connect_ssl_fails_starttls_succeeds(self, mock_smtplib, smtp_service):
        """connect() falls back to STARTTLS when SSL fails."""
        mock_smtplib.SMTP_SSL.side_effect = ssl.SSLError("SSL failed")
        mock_conn = MagicMock()
        mock_smtplib.SMTP.return_value = mock_conn

        smtp_service.connect()

        mock_smtplib.SMTP.assert_called_once()
        mock_conn.login.assert_called_once()

    @patch("src.services.smtp_service.smtplib")
    def test_connect_auth_failure(self, mock_smtplib, smtp_service):
        """connect() raises SMTPAuthenticationError on auth failure."""
        mock_smtplib.SMTP_SSL.side_effect = ssl.SSLError("SSL failed")
        mock_smtplib.SMTP.return_value = MagicMock()
        mock_smtplib.SMTP.return_value.login.side_effect = smtplib.SMTPAuthenticationError(
            535, b"bad creds"
        )
        mock_smtplib.SMTPAuthenticationError = smtplib.SMTPAuthenticationError

        with pytest.raises(SMTPAuthenticationError):
            smtp_service.connect()

    @patch("src.services.smtp_service.smtplib")
    def test_connect_all_fail(self, mock_smtplib, smtp_service):
        """connect() raises SMTPConnectionError when everything fails."""
        mock_smtplib.SMTP_SSL.side_effect = Exception("ssl fail")
        mock_smtplib.SMTP.return_value = MagicMock()
        mock_smtplib.SMTP.return_value.login.side_effect = Exception("login fail")
        mock_smtplib.SMTPAuthenticationError = type("SMTPAuthError", (Exception,), {})

        with pytest.raises(SMTPConnectionError):
            smtp_service.connect()

    @patch("src.services.smtp_service.smtplib")
    def test_connect_ssl_auth_failure(self, mock_smtplib, smtp_service):
        """connect() raises SMTPAuthenticationError on SSL auth failure."""
        mock_smtplib.SMTP_SSL.return_value = MagicMock()
        mock_smtplib.SMTP_SSL.return_value.login.side_effect = smtplib.SMTPAuthenticationError(
            535, b"bad creds"
        )
        mock_smtplib.SMTPAuthenticationError = smtplib.SMTPAuthenticationError

        with pytest.raises(SMTPAuthenticationError):
            smtp_service.connect()


class TestSMTPServiceSendReply:
    """Tests for SMTPService.send_reply_with_attachments()."""

    def test_send_no_connection_raises(self, smtp_service):
        """send raises when not connected."""
        with pytest.raises(SMTPError, match="not established"):
            smtp_service.send_reply_with_attachments(
                to_address="a@b.com", subject="Re: Test", body="Done", attachments=[]
            )

    def test_send_with_attachments(self, smtp_service):
        """send constructs email with PNG attachments."""
        mock_conn = MagicMock()
        smtp_service.connection = mock_conn

        with tempfile.TemporaryDirectory() as tmpdir:
            png = _make_png_image(Path(tmpdir))

            smtp_service.send_reply_with_attachments(
                to_address="alice@test.com",
                subject="Re: PDF",
                body="Here are your PNGs",
                attachments=[png],
            )

        mock_conn.sendmail.assert_called_once()
        args = mock_conn.sendmail.call_args
        assert args[0][0] == "user@test.com"
        assert args[0][1] == ["alice@test.com"]

    def test_send_with_cc(self, smtp_service):
        """send includes CC recipients."""
        mock_conn = MagicMock()
        smtp_service.connection = mock_conn

        with tempfile.TemporaryDirectory() as tmpdir:
            png = _make_png_image(Path(tmpdir))

            smtp_service.send_reply_with_attachments(
                to_address="alice@test.com",
                subject="Re: PDF",
                body="Done",
                attachments=[png],
                cc_addresses=["boss@test.com"],
            )

        args = mock_conn.sendmail.call_args
        assert "boss@test.com" in args[0][1]

    def test_send_failure_raises(self, smtp_service):
        """send raises SMTPError on sendmail failure."""
        mock_conn = MagicMock()
        mock_conn.sendmail.side_effect = Exception("network error")
        smtp_service.connection = mock_conn

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            pytest.raises(SMTPError, match="Failed to send email"),
        ):
            png = _make_png_image(Path(tmpdir))
            smtp_service.send_reply_with_attachments(
                to_address="a@b.com", subject="S", body="B", attachments=[png]
            )


class TestSMTPServiceSendError:
    """Tests for SMTPService.send_error_notification()."""

    def test_send_error_no_connection_raises(self, smtp_service):
        """send_error raises when not connected."""
        with pytest.raises(SMTPError, match="not established"):
            smtp_service.send_error_notification(to_address="a@b.com", error=RuntimeError("fail"))

    def test_send_error_notification(self, smtp_service):
        """send_error constructs error email."""
        mock_conn = MagicMock()
        smtp_service.connection = mock_conn

        smtp_service.send_error_notification(
            to_address="alice@test.com",
            error=RuntimeError("conversion failed"),
        )

        mock_conn.sendmail.assert_called_once()

    def test_send_error_with_context(self, smtp_service):
        """send_error includes context dict in body."""
        mock_conn = MagicMock()
        smtp_service.connection = mock_conn

        smtp_service.send_error_notification(
            to_address="alice@test.com",
            error=ValueError("bad pdf"),
            context={"Email Subject": "Invoice", "Sender": "alice@test.com"},
        )

        call_args = mock_conn.sendmail.call_args
        email_body = call_args[0][2]
        assert "Invoice" in email_body
        assert "ValueError" in email_body

    def test_send_error_failure_raises(self, smtp_service):
        """send_error raises SMTPError on failure."""
        mock_conn = MagicMock()
        mock_conn.sendmail.side_effect = Exception("network error")
        smtp_service.connection = mock_conn

        with pytest.raises(SMTPError, match="Failed to send error notification"):
            smtp_service.send_error_notification(to_address="a@b.com", error=RuntimeError("fail"))


class TestSMTPServiceDisconnect:
    """Tests for SMTPService.disconnect()."""

    def test_disconnect_with_connection(self, smtp_service):
        """disconnect quits and nullifies connection."""
        mock_conn = MagicMock()
        smtp_service.connection = mock_conn

        smtp_service.disconnect()

        mock_conn.quit.assert_called_once()
        assert smtp_service.connection is None

    def test_disconnect_no_connection(self, smtp_service):
        """disconnect with no connection is a no-op."""
        smtp_service.disconnect()
        assert smtp_service.connection is None

    def test_disconnect_error_ignored(self, smtp_service):
        """disconnect swallows errors."""
        mock_conn = MagicMock()
        mock_conn.quit.side_effect = Exception("quit failed")
        smtp_service.connection = mock_conn

        smtp_service.disconnect()
        assert smtp_service.connection is None
