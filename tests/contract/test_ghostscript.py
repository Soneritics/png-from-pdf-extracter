"""Contract tests for GhostScript CLI tool."""

import subprocess

import pytest


def test_ghostscript_availability():
    """T030 [US1] Contract test: GhostScript availability for PDF pre-processing."""
    # Test that 'gs' command is available
    try:
        result = subprocess.run(
            ["gs", "--version"], capture_output=True, text=True, check=True, timeout=5
        )
        assert result.returncode == 0
        # Version should be a number (e.g., "10.02.1")
        assert len(result.stdout.strip()) > 0
    except FileNotFoundError:
        pytest.fail("GhostScript CLI 'gs' command not found")
    except subprocess.CalledProcessError as e:
        pytest.fail(f"GhostScript version check failed: {e}")
