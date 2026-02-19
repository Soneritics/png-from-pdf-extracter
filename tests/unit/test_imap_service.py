"""Unit tests for IMAPService."""

import imaplib
import ssl
from unittest.mock import MagicMock, patch

import pytest

from src.services.imap_service import (
    IMAPAuthenticationError,
    IMAPConnectionError,
    IMAPError,
    IMAPService,
)


@pytest.fixture()
def imap_service(config):
    """IMAPService with test config."""
    return IMAPService(config)


class TestIMAPServiceInit:
    """Tests for IMAPService initialization."""

    def test_init(self, imap_service, config):
        """Service stores config and has no connection."""
        assert imap_service.config is config
        assert imap_service.connection is None


class TestIMAPServiceConnect:
    """Tests for IMAPService.connect()."""

    @patch("src.services.imap_service.imaplib")
    def test_connect_ssl_success(self, mock_imaplib, imap_service):
        """connect() succeeds with IMAP4_SSL."""
        mock_conn = MagicMock()
        mock_imaplib.IMAP4_SSL.return_value = mock_conn

        imap_service.connect()

        mock_imaplib.IMAP4_SSL.assert_called_once_with("imap.test.com", 993)
        mock_conn.login.assert_called_once_with("user@test.com", "secret")
        assert imap_service.connection is mock_conn

    @patch("src.services.imap_service.imaplib")
    def test_connect_ssl_fails_starttls_succeeds(self, mock_imaplib, imap_service):
        """connect() falls back to STARTTLS when SSL fails."""
        mock_imaplib.IMAP4_SSL.side_effect = ssl.SSLError("SSL failed")
        mock_conn = MagicMock()
        mock_imaplib.IMAP4.return_value = mock_conn

        imap_service.connect()

        mock_imaplib.IMAP4.assert_called_once_with("imap.test.com", 993)
        mock_conn.login.assert_called_once()

    @patch("src.services.imap_service.imaplib")
    def test_connect_auth_failure_ssl(self, mock_imaplib, imap_service):
        """connect() raises IMAPAuthenticationError on auth failure."""
        mock_imaplib.IMAP4_SSL.side_effect = Exception("other error")
        mock_imaplib.IMAP4.return_value = MagicMock()
        mock_imaplib.IMAP4.return_value.login.side_effect = Exception("login failed")

        with pytest.raises(IMAPConnectionError):
            imap_service.connect()

    @patch("src.services.imap_service.imaplib")
    def test_connect_imap4_auth_error(self, mock_imaplib, imap_service):
        """connect() raises IMAPAuthenticationError on IMAP4 auth failure."""
        mock_imaplib.IMAP4_SSL.side_effect = ssl.SSLError("SSL failed")
        mock_imaplib.IMAP4.return_value = MagicMock()
        mock_imaplib.IMAP4.return_value.login.side_effect = imaplib.IMAP4.error(
            "authentication failed"
        )
        mock_imaplib.IMAP4.error = imaplib.IMAP4.error

        with pytest.raises(IMAPAuthenticationError):
            imap_service.connect()


class TestIMAPServiceConnectWithBackoff:
    """Tests for IMAPService.connect_with_backoff()."""

    @patch("src.services.imap_service.time.sleep")
    def test_connect_with_backoff_success_first_try(self, mock_sleep, imap_service):
        """connect_with_backoff succeeds on first try without sleeping."""
        with patch.object(imap_service, "connect"):
            imap_service.connect_with_backoff(max_retries=3)

        mock_sleep.assert_not_called()

    @patch("src.services.imap_service.time.sleep")
    def test_connect_with_backoff_retries(self, mock_sleep, imap_service):
        """connect_with_backoff retries on connection failure."""
        with patch.object(
            imap_service,
            "connect",
            side_effect=[IMAPConnectionError("fail"), None],
        ):
            imap_service.connect_with_backoff(max_retries=3)

        assert mock_sleep.call_count == 1

    @patch("src.services.imap_service.time.sleep")
    def test_connect_with_backoff_max_retries_exceeded(self, _mock_sleep, imap_service):
        """connect_with_backoff raises after max retries."""
        with (
            patch.object(
                imap_service,
                "connect",
                side_effect=IMAPConnectionError("fail"),
            ),
            pytest.raises(IMAPConnectionError, match="after 2 attempts"),
        ):
            imap_service.connect_with_backoff(max_retries=2)

    @patch("src.services.imap_service.time.sleep")
    def test_connect_with_backoff_auth_error_not_retried(self, mock_sleep, imap_service):
        """connect_with_backoff does not retry auth errors."""
        with (
            patch.object(
                imap_service,
                "connect",
                side_effect=IMAPAuthenticationError("bad creds"),
            ),
            pytest.raises(IMAPAuthenticationError),
        ):
            imap_service.connect_with_backoff(max_retries=5)

        mock_sleep.assert_not_called()


class TestIMAPServiceFetchUnseen:
    """Tests for IMAPService.fetch_unseen_messages()."""

    def test_fetch_no_connection_raises(self, imap_service):
        """fetch_unseen_messages raises when not connected."""
        with pytest.raises(IMAPError, match="not established"):
            imap_service.fetch_unseen_messages()

    def test_fetch_no_unseen_messages(self, imap_service):
        """fetch_unseen_messages returns empty list when no unseen."""
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"1"])
        mock_conn.search.return_value = ("OK", [b""])
        imap_service.connection = mock_conn

        result = imap_service.fetch_unseen_messages()
        assert result == []

    def test_fetch_search_failure(self, imap_service):
        """fetch_unseen_messages raises on search failure."""
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"1"])
        mock_conn.search.return_value = ("BAD", [b""])
        imap_service.connection = mock_conn

        with pytest.raises(IMAPError):
            imap_service.fetch_unseen_messages()

    def test_fetch_parses_email(self, imap_service):
        """fetch_unseen_messages parses a simple email."""
        raw_email = (
            b"From: sender@test.com\r\nSubject: Test\r\nContent-Type: text/plain\r\n\r\nHello world"
        )

        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"1"])
        mock_conn.search.return_value = ("OK", [b"1"])
        mock_conn.fetch.return_value = ("OK", [(b"1", raw_email)])
        imap_service.connection = mock_conn

        messages = imap_service.fetch_unseen_messages()
        assert len(messages) == 1
        assert messages[0].sender == "sender@test.com"
        assert messages[0].subject == "Test"
        assert messages[0].body == "Hello world"

    def test_fetch_skips_failed_uid(self, imap_service):
        """fetch_unseen_messages skips UIDs that fail to fetch."""
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"1"])
        mock_conn.search.return_value = ("OK", [b"1 2"])
        mock_conn.fetch.side_effect = [
            ("BAD", None),
            ("OK", [(b"2", b"From: a@b.com\r\nSubject: S\r\n\r\nbody")]),
        ]
        imap_service.connection = mock_conn

        messages = imap_service.fetch_unseen_messages()
        assert len(messages) == 1


class TestIMAPServiceDeleteMessage:
    """Tests for IMAPService.delete_message()."""

    def test_delete_no_connection_raises(self, imap_service):
        """delete_message raises when not connected."""
        with pytest.raises(IMAPError, match="not established"):
            imap_service.delete_message(1)

    def test_delete_success(self, imap_service):
        """delete_message stores Deleted flag and expunges."""
        mock_conn = MagicMock()
        imap_service.connection = mock_conn

        imap_service.delete_message(42)

        mock_conn.store.assert_called_once_with("42", "+FLAGS", r"(\Deleted)")
        mock_conn.expunge.assert_called_once()

    def test_delete_failure_raises(self, imap_service):
        """delete_message raises IMAPError on failure."""
        mock_conn = MagicMock()
        mock_conn.store.side_effect = Exception("store failed")
        imap_service.connection = mock_conn

        with pytest.raises(IMAPError, match="Failed to delete"):
            imap_service.delete_message(1)


class TestIMAPServiceDisconnect:
    """Tests for IMAPService.disconnect()."""

    def test_disconnect_with_connection(self, imap_service):
        """disconnect closes and logs out."""
        mock_conn = MagicMock()
        imap_service.connection = mock_conn

        imap_service.disconnect()

        mock_conn.close.assert_called_once()
        mock_conn.logout.assert_called_once()
        assert imap_service.connection is None

    def test_disconnect_no_connection(self, imap_service):
        """disconnect with no connection is a no-op."""
        imap_service.disconnect()
        assert imap_service.connection is None

    def test_disconnect_error_ignored(self, imap_service):
        """disconnect swallows errors."""
        mock_conn = MagicMock()
        mock_conn.close.side_effect = Exception("close failed")
        imap_service.connection = mock_conn

        imap_service.disconnect()
        assert imap_service.connection is None
