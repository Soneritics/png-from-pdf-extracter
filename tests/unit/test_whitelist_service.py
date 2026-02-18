"""Unit tests for WhitelistService."""

import pytest

from src.services.whitelist_service import WhitelistService


def test_whitelist_matches_valid_address():
    """T054 [US2] Unit test: WhitelistService matches valid address."""
    whitelist = WhitelistService(regex_pattern=".*@company\\.com")

    assert whitelist.is_whitelisted("alice@company.com") is True
    assert whitelist.is_whitelisted("bob@company.com") is True
    assert whitelist.is_whitelisted("user123@company.com") is True


def test_whitelist_rejects_invalid_address():
    """T055 [US2] Unit test: WhitelistService rejects invalid address."""
    whitelist = WhitelistService(regex_pattern=".*@company\\.com")

    assert whitelist.is_whitelisted("user@external.com") is False
    assert whitelist.is_whitelisted("user@other.org") is False
    assert whitelist.is_whitelisted("user@companyxcom") is False  # Missing dot


def test_whitelist_pattern_matches_domain():
    """T056 [US2] Unit test: WhitelistService pattern '.*@company\\.com' matches user@company.com."""
    whitelist = WhitelistService(regex_pattern=".*@company\\.com")

    assert whitelist.is_whitelisted("user@company.com") is True
    assert whitelist.is_whitelisted("any.user@company.com") is True
    assert whitelist.is_whitelisted("test123@company.com") is True


def test_whitelist_pattern_rejects_different_domain():
    """T057 [US2] Unit test: WhitelistService pattern '.*@company\\.com' rejects user@external.com."""
    whitelist = WhitelistService(regex_pattern=".*@company\\.com")

    assert whitelist.is_whitelisted("user@external.com") is False
    assert whitelist.is_whitelisted("user@company.org") is False
    assert whitelist.is_whitelisted("user@mycompany.com") is False


def test_whitelist_raises_on_invalid_regex():
    """T058 [US2] Unit test: WhitelistService raises ValueError on invalid regex."""
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        WhitelistService(regex_pattern="[invalid(regex")
