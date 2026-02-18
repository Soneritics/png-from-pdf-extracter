"""Configuration management for PDF-to-PNG email processor."""

import os
import re
from dataclasses import dataclass, field


@dataclass
class Configuration:
    """System configuration loaded from environment variables."""

    # IMAP settings
    imap_host: str
    imap_port: int
    imap_username: str
    imap_password: str

    # SMTP settings
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str

    # Whitelist settings
    sender_whitelist_regex: str
    _compiled_whitelist: re.Pattern = field(init=False, repr=False)

    # CC recipients
    cc_addresses: list[str] = field(default_factory=list)

    # Polling configuration
    polling_interval_seconds: int = 60
    max_retry_interval_seconds: int = 900

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()
        # Compile regex for whitelist
        try:
            self._compiled_whitelist = re.compile(self.sender_whitelist_regex)
        except re.error as e:
            raise ValueError(f"Invalid SENDER_WHITELIST_REGEX: {e}") from e

    def _validate(self) -> None:
        """Validate configuration values."""
        # Validate required string fields
        required_fields = [
            ("imap_host", self.imap_host),
            ("imap_username", self.imap_username),
            ("imap_password", self.imap_password),
            ("smtp_host", self.smtp_host),
            ("smtp_username", self.smtp_username),
            ("smtp_password", self.smtp_password),
            ("sender_whitelist_regex", self.sender_whitelist_regex),
        ]

        for field_name, field_value in required_fields:
            if not field_value or not isinstance(field_value, str):
                raise ValueError(f"{field_name} must be a non-empty string")

        # Validate port ranges
        if not (1 <= self.imap_port <= 65535):
            raise ValueError(f"imap_port must be in range 1-65535, got {self.imap_port}")

        if not (1 <= self.smtp_port <= 65535):
            raise ValueError(f"smtp_port must be in range 1-65535, got {self.smtp_port}")

        # Validate polling intervals
        if self.polling_interval_seconds < 10:
            raise ValueError(
                f"polling_interval_seconds must be ≥10 to prevent excessive polling, "
                f"got {self.polling_interval_seconds}"
            )

        if self.max_retry_interval_seconds < self.polling_interval_seconds:
            raise ValueError(
                f"max_retry_interval_seconds ({self.max_retry_interval_seconds}) must be "
                f"≥ polling_interval_seconds ({self.polling_interval_seconds})"
            )

    @property
    def compiled_whitelist(self) -> re.Pattern:
        """Get compiled whitelist regex pattern."""
        return self._compiled_whitelist

    @classmethod
    def from_env(cls) -> "Configuration":
        """Load configuration from environment variables.

        Returns:
            Configuration instance

        Raises:
            ValueError: If required environment variables are missing or invalid
        """
        # Helper to get required env var
        def get_required(key: str) -> str:
            value = os.getenv(key)
            if not value:
                raise ValueError(f"Required environment variable {key} is not set")
            return value

        # Helper to get optional env var with default
        def get_optional(key: str, default: str) -> str:
            return os.getenv(key, default)

        # Parse CC addresses (semicolon-separated)
        cc_addresses_str = get_optional("CC_ADDRESSES", "")
        cc_addresses = [
            addr.strip() for addr in cc_addresses_str.split(";") if addr.strip()
        ]

        return cls(
            imap_host=get_required("IMAP_HOST"),
            imap_port=int(get_required("IMAP_PORT")),
            imap_username=get_required("IMAP_USERNAME"),
            imap_password=get_required("IMAP_PASSWORD"),
            smtp_host=get_required("SMTP_HOST"),
            smtp_port=int(get_required("SMTP_PORT")),
            smtp_username=get_required("SMTP_USERNAME"),
            smtp_password=get_required("SMTP_PASSWORD"),
            sender_whitelist_regex=get_required("SENDER_WHITELIST_REGEX"),
            cc_addresses=cc_addresses,
            polling_interval_seconds=int(get_optional("POLLING_INTERVAL_SECONDS", "60")),
            max_retry_interval_seconds=int(get_optional("MAX_RETRY_INTERVAL_SECONDS", "900")),
        )
