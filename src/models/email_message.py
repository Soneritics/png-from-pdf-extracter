"""EmailMessage entity for PDF-to-PNG email processor."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmailMessage:
    """Represents an incoming email retrieved from IMAP INBOX.

    Attributes:
        uid: IMAP UID of the message (unique within mailbox)
        sender: Email address of the sender
        subject: Email subject line
        body: Plain text body (optional, used for error context)
        raw_bytes: Complete RFC 5322 message
        received_at: Timestamp when email was retrieved
    """

    uid: int
    sender: str
    subject: str
    body: str
    raw_bytes: bytes
    received_at: datetime

    def __post_init__(self) -> None:
        """Validate EmailMessage after initialization."""
        if self.uid <= 0:
            raise ValueError("UID must be positive")
        if "@" not in self.sender:
            raise ValueError("Sender must be a valid email address")
        if not self.raw_bytes:
            raise ValueError("Raw bytes must not be empty")
