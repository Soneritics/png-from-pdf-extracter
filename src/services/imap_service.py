"""IMAP service for email monitoring and retrieval."""

import contextlib
import email
import email.policy
import email.utils
import imaplib
import ssl
import time
from datetime import UTC, datetime

from src.config import Configuration
from src.models.email_message import EmailMessage
from src.utils.logging import get_logger

logger = get_logger()


class IMAPError(Exception):
    """Base exception for IMAP operations."""


class IMAPConnectionError(IMAPError):
    """Raised when IMAP connection fails after all retry attempts."""


class IMAPAuthenticationError(IMAPError):
    """Raised when IMAP login credentials are rejected."""


class IMAPService:
    """Service for IMAP email operations with TLS fallback and exponential backoff.

    Implements FR-001, FR-021, FR-025, FR-026, FR-027, FR-028.
    """

    def __init__(self, config: Configuration) -> None:
        """Initialize IMAP service with configuration.

        Args:
            config: Configuration instance with IMAP settings
        """
        self.config = config
        self.connection: imaplib.IMAP4 | None = None

    def connect(self) -> None:
        """Establish IMAP connection with TLS fallback per FR-025, FR-026.

        Connection Strategy:
        1. Attempt IMAP4_SSL (TLS)
        2. If SSLError, attempt IMAP4 + starttls()
        3. If starttls() fails, fall back to plaintext IMAP4

        Raises:
            IMAPConnectionError: If all connection methods fail
            IMAPAuthenticationError: If login fails
        """
        host = self.config.imap_host
        port = self.config.imap_port
        username = self.config.imap_username
        password = self.config.imap_password

        # Try IMAP4_SSL first
        try:
            self.connection = imaplib.IMAP4_SSL(host, port)
            self.connection.login(username, password)
            return
        except ssl.SSLError:
            # SSL failed, will try STARTTLS next
            pass
        except imaplib.IMAP4.error as e:
            if "authentication" in str(e).lower() or "login" in str(e).lower():
                raise IMAPAuthenticationError(f"IMAP authentication failed: {e}") from e
            # Other errors - will try STARTTLS
        except Exception:
            # Other errors - will try STARTTLS
            pass

        # Try IMAP4 + STARTTLS
        try:
            self.connection = imaplib.IMAP4(host, port)
            with contextlib.suppress(Exception):
                self.connection.starttls()
            self.connection.login(username, password)
            return
        except imaplib.IMAP4.error as e:
            if "authentication" in str(e).lower() or "login" in str(e).lower():
                raise IMAPAuthenticationError(f"IMAP authentication failed: {e}") from e
            raise IMAPConnectionError(f"IMAP connection failed for {host}:{port}: {e}") from e
        except Exception as e:
            raise IMAPConnectionError(f"IMAP connection failed for {host}:{port}: {e}") from e

    def connect_with_backoff(self, max_retries: int | None = None) -> None:
        """Connect with exponential backoff on failure per FR-027.

        Backoff schedule: 60s → 120s → 240s → ... up to 900s (15 min)
        Logs every failure attempt per FR-028.

        Args:
            max_retries: Maximum retry attempts (None = infinite per NFR-011)

        Raises:
            IMAPConnectionError: If max_retries exceeded
        """
        attempt = 0
        base_delay = 60  # Start with 60 seconds
        max_delay = self.config.max_retry_interval_seconds

        while max_retries is None or attempt < max_retries:
            try:
                self.connect()
                return  # Success!
            except IMAPAuthenticationError:
                # Authentication errors should not be retried
                raise
            except IMAPConnectionError as e:
                attempt += 1

                # Calculate exponential backoff delay
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)

                # Log the failure per FR-028
                logger.error(
                    "IMAP connection failed (attempt %d): %s. Retrying in %d seconds...",
                    attempt,
                    e,
                    delay,
                )

                # Wait before retry
                time.sleep(delay)

        # Max retries exceeded
        raise IMAPConnectionError(f"IMAP connection failed after {max_retries} attempts")

    def fetch_unseen_messages(self) -> list[EmailMessage]:
        """Fetch all UNSEEN messages from INBOX per FR-001.

        Returns:
            List of EmailMessage objects

        Raises:
            IMAPError: If fetch operation fails
        """
        if not self.connection:
            raise IMAPError("IMAP connection not established. Call connect() first.")

        try:
            # Select INBOX
            self.connection.select("INBOX")

            # Search for UNSEEN messages
            status, message_ids = self.connection.search(None, "UNSEEN")

            if status != "OK":
                raise IMAPError(f"IMAP search failed: {status}")

            # Parse message IDs (space-separated list)
            if not message_ids[0]:
                return []  # No unseen messages

            uid_list = message_ids[0].split()

            # Fetch each message
            messages = []
            for uid in uid_list:
                status, msg_data = self.connection.fetch(uid, "(RFC822)")

                if status != "OK":
                    logger.error("Failed to fetch message UID %s: %s", uid, status)
                    continue

                # Parse email
                raw_bytes = msg_data[0][1]
                parsed_msg = email.message_from_bytes(raw_bytes, policy=email.policy.default)

                # Extract sender
                sender = email.utils.parseaddr(parsed_msg["From"])[1]

                # Extract subject
                subject = parsed_msg.get("Subject", "(no subject)")

                # Extract plain text body
                body = ""
                if parsed_msg.is_multipart():
                    for part in parsed_msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            break
                else:
                    body = parsed_msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                messages.append(
                    EmailMessage(
                        uid=int(uid),
                        sender=sender,
                        subject=subject,
                        body=body,
                        raw_bytes=raw_bytes,
                        received_at=datetime.now(tz=UTC),
                    )
                )

            return messages

        except Exception as e:
            raise IMAPError(f"Failed to fetch unseen messages: {e}") from e

    def delete_message(self, uid: int) -> None:
        """Delete message by UID per FR-021.

        Args:
            uid: IMAP message UID

        Raises:
            IMAPError: If deletion fails
        """
        if not self.connection:
            raise IMAPError("IMAP connection not established. Call connect() first.")

        try:
            # Mark message as deleted
            self.connection.store(str(uid), "+FLAGS", r"(\Deleted)")

            # Expunge to permanently delete
            self.connection.expunge()

        except Exception as e:
            raise IMAPError(f"Failed to delete message UID {uid}: {e}") from e

    def disconnect(self) -> None:
        """Close IMAP connection gracefully."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except Exception:
                # Ignore errors during disconnect
                pass
            finally:
                self.connection = None
