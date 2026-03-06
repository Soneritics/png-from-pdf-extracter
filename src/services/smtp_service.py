"""SMTP service for sending emails with attachments."""

import contextlib
import smtplib
import ssl
import traceback
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import Configuration
from src.models.png_image import PNGImage
from src.utils.logging import get_logger

logger = get_logger()


class SMTPError(Exception):
    """Base exception for SMTP operations."""


class SMTPConnectionError(SMTPError):
    """Raised when SMTP connection fails."""


class SMTPAuthenticationError(SMTPError):
    """Raised when SMTP login credentials are rejected."""


class SMTPService:
    """Service for sending emails via SMTP with TLS fallback.

    Implements FR-009, FR-010, FR-011, FR-012, FR-013, FR-020, FR-025, FR-026.
    """

    MAX_SEND_RETRIES = 2

    def __init__(self, config: Configuration) -> None:
        """Initialize SMTP service with configuration.

        Args:
            config: Configuration instance with SMTP settings
        """
        self.config = config
        self.connection: smtplib.SMTP | None = None

    def connect(self) -> None:
        """Establish SMTP connection with TLS fallback per FR-025, FR-026.

        Connection Strategy:
        1. Attempt SMTP_SSL (TLS)
        2. If SSLError, attempt SMTP + starttls()
        3. If starttls() fails, fall back to plaintext SMTP

        Raises:
            SMTPConnectionError: If all connection methods fail
            SMTPAuthenticationError: If login fails
        """
        host = self.config.smtp_host
        port = self.config.smtp_port
        username = self.config.smtp_username
        password = self.config.smtp_password
        timeout = self.config.smtp_timeout_seconds

        # Try SMTP_SSL first (ports 465, 587)
        try:
            self.connection = smtplib.SMTP_SSL(host, port, timeout=timeout)
            self.connection.login(username, password)
            logger.info("SMTP connected via SSL to %s:%d", host, port)
            return
        except ssl.SSLError:
            # SSL failed, will try STARTTLS next
            pass
        except smtplib.SMTPAuthenticationError as e:
            raise SMTPAuthenticationError(f"SMTP authentication failed: {e}") from e
        except Exception:
            # Other errors - will try STARTTLS
            pass

        # Try SMTP + STARTTLS
        try:
            self.connection = smtplib.SMTP(host, port, timeout=timeout)
            with contextlib.suppress(Exception):
                self.connection.starttls()
            self.connection.login(username, password)
            logger.info("SMTP connected via STARTTLS to %s:%d", host, port)
            return
        except smtplib.SMTPAuthenticationError as e:
            raise SMTPAuthenticationError(f"SMTP authentication failed: {e}") from e
        except Exception as e:
            raise SMTPConnectionError(f"SMTP connection failed for {host}:{port}: {e}") from e

    def send_reply_with_attachments(
        self,
        to_address: str,
        subject: str,
        body: str,
        attachments: list[PNGImage],
        cc_addresses: list[str] | None = None,
    ) -> None:
        """Send reply email with PNG attachments per FR-009, FR-010, FR-011, FR-020.

        Args:
            to_address: Recipient email address
            subject: Email subject
            body: Email body text
            attachments: List of PNGImage objects to attach
            cc_addresses: Optional list of CC recipients

        Raises:
            SMTPError: If email sending fails
        """
        # Create multipart message
        msg = MIMEMultipart()
        msg["From"] = self.config.smtp_username
        msg["To"] = to_address
        msg["Subject"] = subject

        # Add CC recipients if provided
        if cc_addresses:
            msg["Cc"] = ", ".join(cc_addresses)

        # Attach body text
        msg.attach(MIMEText(body, "plain"))

        # Attach PNG files
        for png in attachments:
            with png.path.open("rb") as f:
                part = MIMEBase("image", "png")
                part.set_payload(f.read())

            # Encode in base64
            encoders.encode_base64(part)

            # Add header with filename
            part.add_header("Content-Disposition", f"attachment; filename= {png.filename}")

            msg.attach(part)

        # Build recipient list (To + CC)
        recipients = [to_address]
        if cc_addresses:
            recipients.extend(cc_addresses)

        # Send email with reconnection retry
        self._send_with_retry(
            lambda: self.connection.sendmail(
                self.config.smtp_username, recipients, msg.as_string()
            ),
            error_context=f"send reply email to {to_address}",
        )

    def send_error_notification(
        self, to_address: str, error: Exception, context: dict[str, str] | None = None
    ) -> None:
        """Send error notification email with detailed stack trace per FR-012, FR-013.

        Args:
            to_address: Recipient email address (original sender)
            error: The exception that occurred
            context: Optional context dict (email subject, PDF filenames, etc.)

        Raises:
            SMTPError: If email sending fails
        """

        # Build error email subject
        subject = f"Error processing your PDF: {type(error).__name__}"

        # Build detailed error body
        body_parts = [
            "An error occurred while processing your PDF attachment.",
            "",
            f"Error Type: {type(error).__name__}",
            f"Error Message: {error!s}",
            "",
            "Technical Details:",
            "-" * 60,
            traceback.format_exc(),
            "-" * 60,
        ]

        # Add context information if provided
        if context:
            body_parts.extend(["", "Email Context:", "-" * 60])
            for key, value in context.items():
                body_parts.append(f"{key}: {value}")
            body_parts.append("-" * 60)

        body_parts.extend(
            [
                "",
                "Please verify your PDF file is:",
                "- Not corrupted or malformed",
                "- Not password-protected or encrypted",
                "- A valid PDF document",
                "",
                "If the problem persists, please contact support.",
            ]
        )

        body = "\n".join(body_parts)

        # Create and send error email
        msg = MIMEMultipart()
        msg["From"] = self.config.smtp_username
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send error email with reconnection retry
        self._send_with_retry(
            lambda: self.connection.sendmail(
                self.config.smtp_username, [to_address], msg.as_string()
            ),
            error_context=f"send error notification to {to_address}",
        )

    def _send_with_retry(self, send_fn, *, error_context: str) -> None:
        """Execute a send operation with automatic reconnection on failure.

        On the first failure the connection is re-established and the
        send is retried up to MAX_SEND_RETRIES times.

        Args:
            send_fn: Callable that performs the actual SMTP send
            error_context: Human-readable description for log messages

        Raises:
            SMTPError: If sending fails after all retries
            SMTPAuthenticationError: Immediately on authentication failure
        """
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_SEND_RETRIES + 1):
            try:
                if not self.connection:
                    logger.info("SMTP connection not active, reconnecting...")
                    self.connect()
                send_fn()
                if attempt > 1:
                    logger.info("SMTP send succeeded on attempt %d", attempt)
                return
            except SMTPAuthenticationError:
                raise
            except Exception as e:
                last_error = e
                logger.warning(
                    "SMTP send attempt %d/%d failed (%s): %s",
                    attempt,
                    self.MAX_SEND_RETRIES,
                    error_context,
                    e,
                )
                self.disconnect()

        logger.error("Failed to %s after %d attempts", error_context, self.MAX_SEND_RETRIES)
        raise SMTPError(f"Failed to {error_context}: {last_error}") from last_error

    def disconnect(self) -> None:
        """Close SMTP connection gracefully."""
        if self.connection:
            try:
                self.connection.quit()
            except Exception:
                # Ignore errors during disconnect
                pass
            finally:
                self.connection = None
