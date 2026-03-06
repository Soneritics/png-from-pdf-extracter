"""Logging setup for PDF-to-PNG email processor."""

import logging
import os
import sys


def setup_logging() -> logging.Logger:
    """Configure logging per FR-023, FR-024, NFR-001, NFR-002.

    Log level is controlled by the LOG_LEVEL environment variable
    (default: INFO). Accepted values: DEBUG, INFO, WARNING, ERROR, CRITICAL.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("pdf_to_png_mailer")

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)

    # Create formatter with timestamp, level, and message
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
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
