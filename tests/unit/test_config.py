"""Unit tests for Configuration."""

import os
from unittest.mock import patch

import pytest

from src.config import Configuration


class TestConfigValidation:
    """Tests for Configuration validation logic."""

    def test_valid_config(self, make_config):
        """Valid config is created without errors."""
        config = make_config()
        assert config.imap_host == "imap.test.com"
        assert config.polling_interval_seconds == 60

    def test_empty_imap_host_raises(self, make_config):
        """Empty imap_host raises ValueError."""
        with pytest.raises(ValueError, match="imap_host"):
            make_config(imap_host="")

    def test_empty_smtp_host_raises(self, make_config):
        """Empty smtp_host raises ValueError."""
        with pytest.raises(ValueError, match="smtp_host"):
            make_config(smtp_host="")

    def test_empty_password_raises(self, make_config):
        """Empty password raises ValueError."""
        with pytest.raises(ValueError, match="imap_password"):
            make_config(imap_password="")

    def test_invalid_imap_port_raises(self, make_config):
        """imap_port out of range raises ValueError."""
        with pytest.raises(ValueError, match="imap_port"):
            make_config(imap_port=0)

    def test_imap_port_too_high_raises(self, make_config):
        """imap_port > 65535 raises ValueError."""
        with pytest.raises(ValueError, match="imap_port"):
            make_config(imap_port=70000)

    def test_invalid_smtp_port_raises(self, make_config):
        """smtp_port out of range raises ValueError."""
        with pytest.raises(ValueError, match="smtp_port"):
            make_config(smtp_port=-1)

    def test_polling_too_low_raises(self, make_config):
        """Polling interval < 10 raises ValueError."""
        with pytest.raises(ValueError, match="polling_interval"):
            make_config(polling_interval_seconds=5)

    def test_max_retry_less_than_polling_raises(self, make_config):
        """max_retry < polling raises ValueError."""
        with pytest.raises(ValueError, match="max_retry"):
            make_config(polling_interval_seconds=60, max_retry_interval_seconds=30)

    def test_invalid_resolution_width_raises(self, make_config):
        """pdf_resolution_width < 1 raises ValueError."""
        with pytest.raises(ValueError, match="pdf_resolution_width"):
            make_config(pdf_resolution_width=0)

    def test_invalid_resolution_height_raises(self, make_config):
        """pdf_resolution_height < 1 raises ValueError."""
        with pytest.raises(ValueError, match="pdf_resolution_height"):
            make_config(pdf_resolution_height=0)

    def test_invalid_density_raises(self, make_config):
        """pdf_density_dpi < 1 raises ValueError."""
        with pytest.raises(ValueError, match="pdf_density_dpi"):
            make_config(pdf_density_dpi=0)

    def test_empty_background_raises(self, make_config):
        """Empty pdf_background raises ValueError."""
        with pytest.raises(ValueError, match="pdf_background"):
            make_config(pdf_background="")

    def test_invalid_timeout_raises(self, make_config):
        """pdf_conversion_timeout_seconds < 1 raises ValueError."""
        with pytest.raises(ValueError, match="pdf_conversion_timeout_seconds"):
            make_config(pdf_conversion_timeout_seconds=0)

    def test_invalid_whitelist_regex_raises(self, make_config):
        """Invalid regex pattern raises ValueError."""
        with pytest.raises(ValueError, match="Invalid SENDER_WHITELIST_REGEX"):
            make_config(sender_whitelist_regex="[invalid(regex")

    def test_compiled_whitelist_property(self, make_config):
        """compiled_whitelist returns compiled re.Pattern."""
        config = make_config(sender_whitelist_regex=".*@test\\.com")
        assert config.compiled_whitelist.match("user@test.com")
        assert config.compiled_whitelist.match("user@other.com") is None

    def test_custom_values(self, make_config):
        """Config accepts custom PDF settings."""
        config = make_config(
            pdf_resolution_width=3840,
            pdf_resolution_height=2160,
            pdf_density_dpi=600,
            pdf_background="black",
            pdf_conversion_timeout_seconds=300,
        )
        assert config.pdf_resolution_width == 3840
        assert config.pdf_resolution_height == 2160
        assert config.pdf_density_dpi == 600
        assert config.pdf_background == "black"
        assert config.pdf_conversion_timeout_seconds == 300

    def test_cc_addresses_default_empty(self, make_config):
        """cc_addresses defaults to empty list."""
        config = make_config()
        assert config.cc_addresses == []

    def test_cc_addresses_custom(self, make_config):
        """cc_addresses can be set."""
        config = make_config(cc_addresses=["admin@test.com", "boss@test.com"])
        assert len(config.cc_addresses) == 2


class TestConfigFromEnv:
    """Tests for Configuration.from_env()."""

    def _required_env(self, **overrides):
        """Return minimal required env vars."""
        env = {
            "IMAP_HOST": "imap.example.com",
            "IMAP_PORT": "993",
            "IMAP_USERNAME": "user@example.com",
            "IMAP_PASSWORD": "pass123",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "user@example.com",
            "SMTP_PASSWORD": "pass123",
            "SENDER_WHITELIST_REGEX": ".*@example\\.com",
        }
        env.update(overrides)
        return env

    def test_from_env_with_required_vars(self):
        """from_env loads required env vars correctly."""
        env = self._required_env()
        with patch.dict(os.environ, env, clear=True):
            config = Configuration.from_env()

        assert config.imap_host == "imap.example.com"
        assert config.imap_port == 993
        assert config.smtp_host == "smtp.example.com"
        assert config.smtp_port == 587
        assert config.polling_interval_seconds == 60  # default

    def test_from_env_with_optional_vars(self):
        """from_env loads optional env vars with overrides."""
        env = self._required_env(
            POLLING_INTERVAL_SECONDS="120",
            MAX_RETRY_INTERVAL_SECONDS="1800",
            PDF_RESOLUTION_WIDTH="3840",
            PDF_RESOLUTION_HEIGHT="2160",
            PDF_DENSITY_DPI="600",
            PDF_BACKGROUND="black",
            PDF_CONVERSION_TIMEOUT_SECONDS="300",
        )
        with patch.dict(os.environ, env, clear=True):
            config = Configuration.from_env()

        assert config.polling_interval_seconds == 120
        assert config.max_retry_interval_seconds == 1800
        assert config.pdf_resolution_width == 3840
        assert config.pdf_density_dpi == 600

    def test_from_env_cc_addresses(self):
        """from_env parses semicolon-separated CC_ADDRESSES."""
        env = self._required_env(CC_ADDRESSES="a@test.com;b@test.com")
        with patch.dict(os.environ, env, clear=True):
            config = Configuration.from_env()

        assert config.cc_addresses == ["a@test.com", "b@test.com"]

    def test_from_env_empty_cc(self):
        """from_env with empty CC_ADDRESSES gives empty list."""
        env = self._required_env()
        with patch.dict(os.environ, env, clear=True):
            config = Configuration.from_env()

        assert config.cc_addresses == []

    def test_from_env_missing_required_raises(self):
        """from_env raises ValueError when required var is missing."""
        with patch.dict(os.environ, {}, clear=True), pytest.raises(ValueError, match="IMAP_HOST"):
            Configuration.from_env()
