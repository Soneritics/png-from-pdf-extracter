"""SMTP service for sending emails with attachments."""

import smtplib
import ssl
import traceback
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.config import Configuration
from src.models.png_image import PNGImage
from src.utils.logging import get_logger

logger = get_logger()


class SMTPError(Exception):
    """Base exception for SMTP operations."""
    pass


class SMTPConnectionError(SMTPError):
    """Raised when SMTP connection fails."""
    pass


class SMTPAuthenticationError(SMTPError):
    """Raised when SMTP login credentials are rejected."""
    pass


class SMTPService:
    """Service for sending emails via SMTP with TLS fallback.

    Implements FR-009, FR-010, FR-011, FR-012, FR-013, FR-020, FR-025, FR-026.
    """

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

        # Try SMTP_SSL first (ports 465, 587)
        try:
            self.connection = smtplib.SMTP_SSL(host, port, timeout=30)
            self.connection.login(username, password)
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
            self.connection = smtplib.SMTP(host, port, timeout=30)
            try:
                self.connection.starttls()
            except Exception:
                # STARTTLS failed, connection remains in plaintext mode
                pass
            self.connection.login(username, password)
            return
        except smtplib.SMTPAuthenticationError as e:
            raise SMTPAuthenticationError(f"SMTP authentication failed: {e}") from e
        except Exception as e:
            raise SMTPConnectionError(
                f"SMTP connection failed for {host}:{port}: {e}"
            ) from e

    def send_reply_with_attachments(
        self,
        to_address: str,
        subject: str,
        body: str,
        attachments: list[PNGImage],
        cc_addresses: list[str] | None = None
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
        if not self.connection:
            raise SMTPError("SMTP connection not established. Call connect() first.")

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
            with open(png.path, "rb") as f:
                part = MIMEBase("image", "png")
                part.set_payload(f.read())

            # Encode in base64
            encoders.encode_base64(part)

            # Add header with filename
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {png.filename}"
            )

            msg.attach(part)

        # Build recipient list (To + CC)
        recipients = [to_address]
        if cc_addresses:
            recipients.extend(cc_addresses)

        # Send email
        try:
            self.connection.sendmail(
                self.config.smtp_username,
                recipients,
                msg.as_string()
            )
        except Exception as e:
            logger.error(f"Failed to send reply email to {to_address}: {e}")
            raise SMTPError(f"Failed to send email: {e}") from e

    def send_error_notification(
        self,
        to_address: str,
        error: Exception,
        context: dict[str, str] | None = None
    ) -> None:
        """Send error notification email with detailed stack trace per FR-012, FR-013.

        Args:
            to_address: Recipient email address (original sender)
            error: The exception that occurred
            context: Optional context dict (email subject, PDF filenames, etc.)

        Raises:
            SMTPError: If email sending fails
        """
        if not self.connection:
            raise SMTPError("SMTP connection not established. Call connect() first.")

        # Build error email subject
        subject = f"Error processing your PDF: {type(error).__name__}"

        # Build detailed error body
        body_parts = [
            "An error occurred while processing your PDF attachment.",
            "",
            f"Error Type: {type(error).__name__}",
            f"Error Message: {str(error)}",
            "",
            "Technical Details:",
            "-" * 60,
            traceback.format_exc(),
            "-" * 60,
        ]

        # Add context information if provided
        if context:
            body_parts.extend([
                "",
                "Email Context:",
                "-" * 60
            ])
            for key, value in context.items():
                body_parts.append(f"{key}: {value}")
            body_parts.append("-" * 60)

        body_parts.extend([
            "",
            "Please verify your PDF file is:",
            "- Not corrupted or malformed",
            "- Not password-protected or encrypted",
            "- A valid PDF document",
            "",
            "If the problem persists, please contact support.",
        ])

        body = "\n".join(body_parts)

        # Create and send error email
        msg = MIMEMultipart()
        msg["From"] = self.config.smtp_username
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            self.connection.sendmail(
                self.config.smtp_username,
                [to_address],
                msg.as_string()
            )
        except Exception as e:
            logger.error(f"Failed to send error notification to {to_address}: {e}")
            raise SMTPError(f"Failed to send error notification: {e}") from e

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
