"""Shared test fixtures for unit tests."""

from datetime import datetime, timezone

import pytest

from src.config import Configuration
from src.models.email_message import EmailMessage

# Use datetime.UTC on Python 3.11+, timezone.utc on 3.10
_UTC = timezone.utc


@pytest.fixture()
def make_config():
    """Factory fixture for creating Configuration instances."""

    def _make(**overrides):
        defaults = {
            "imap_host": "imap.test.com",
            "imap_port": 993,
            "imap_username": "user@test.com",
            "imap_password": "secret",
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "smtp_username": "user@test.com",
            "smtp_password": "secret",
            "sender_whitelist_regex": ".*@test\\.com",
        }
        defaults.update(overrides)
        return Configuration(**defaults)

    return _make


@pytest.fixture()
def config(make_config):
    """Default valid Configuration."""
    return make_config()


@pytest.fixture()
def make_email():
    """Factory fixture for creating EmailMessage instances."""

    def _make(**overrides):
        defaults = {
            "uid": 1,
            "sender": "alice@test.com",
            "subject": "Test PDF",
            "body": "Please convert",
            "raw_bytes": b"From: alice@test.com\r\nSubject: Test PDF\r\n\r\nPlease convert",
            "received_at": datetime.now(tz=_UTC),
        }
        defaults.update(overrides)
        return EmailMessage(**defaults)

    return _make


@pytest.fixture()
def email_msg(make_email):
    """Default valid EmailMessage."""
    return make_email()
