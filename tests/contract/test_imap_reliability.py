"""Contract tests for IMAP exponential backoff and daemon resilience."""

import pytest


def test_imap_exponential_backoff_schedule():
    """T080 [P] Contract test: IMAPService exponential backoff schedule per FR-027."""
    # This test will verify the exponential backoff schedule:
    # 60s → 120s → 240s → ... up to 900s (15 min max)
    pytest.skip("Contract test - requires mock IMAP server with controlled failures")


def test_imap_logs_connection_failures():
    """T081 [P] Contract test: IMAPService logs every connection failure per FR-028."""
    # This test will verify that every connection failure is logged
    pytest.skip("Contract test - requires log capture and mock IMAP failures")


def test_imap_retries_indefinitely():
    """T082 [P] Contract test: IMAPService retries indefinitely per NFR-011."""
    # This test will verify that connect_with_backoff() continues retrying
    # when max_retries=None (infinite retries)
    pytest.skip("Contract test - requires mock IMAP server")
