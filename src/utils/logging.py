"""Minimal error-only logging setup for PDF-to-PNG email processor."""

import logging
import sys


def setup_logging() -> logging.Logger:
    """Configure error-only logging per FR-023, FR-024, NFR-001, NFR-002.

    Only ERROR and CRITICAL level messages are logged to minimize log volume.
    Successful operations (email processing, PNG conversions) are NOT logged.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("pdf_to_png_mailer")

    # Set to ERROR level - only log errors and critical issues
    logger.setLevel(logging.ERROR)

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.ERROR)

    # Create formatter with timestamp, level, and message
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger() -> logging.Logger:
    """Get the configured logger instance.

    Returns:
        Logger instance (creates one if not already configured)
    """
    logger = logging.getLogger("pdf_to_png_mailer")
    if not logger.handlers:
        return setup_logging()
    return logger
