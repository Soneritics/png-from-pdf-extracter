"""Whitelist service for sender validation."""

import re


class WhitelistService:
    """Service for validating email senders against a whitelist regex per FR-002, FR-019."""

    def __init__(self, regex_pattern: str) -> None:
        """Initialize whitelist service with regex pattern.

        Args:
            regex_pattern: Python regex pattern for matching allowed sender addresses

        Raises:
            ValueError: If regex pattern is invalid
        """
        self.regex_pattern = regex_pattern

        # Compile and validate regex
        try:
            self.compiled_pattern = re.compile(regex_pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e

    def is_whitelisted(self, email_address: str) -> bool:
        """Check if email address matches whitelist pattern per FR-002.

        Args:
            email_address: Email address to validate

        Returns:
            True if address matches whitelist pattern, False otherwise
        """
        if not email_address:
            return False

        return self.compiled_pattern.match(email_address) is not None
