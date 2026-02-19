"""Main entry point for PDF-to-PNG email processor."""

import sys

from src.config import Configuration
from src.services.imap_service import IMAPService
from src.services.job_processor import JobProcessorService
from src.services.pdf_converter import PDFConverterService
from src.services.smtp_service import SMTPService
from src.services.whitelist_service import WhitelistService
from src.utils.logging import setup_logging

# Setup logging
logger = setup_logging()


def main() -> None:  # noqa: PLR0915
    """Main entry point for the PDF-to-PNG email processor daemon.

    Workflow:
    1. Load configuration from environment variables
    2. Initialize all services
    3. Connect to IMAP and SMTP
    4. Poll INBOX for unseen messages per FR-001
    5. Process emails sequentially per FR-022
    6. Repeat forever with polling interval per FR-016
    """
    try:
        # Load configuration
        print("Loading configuration from environment variables...")
        config = Configuration.from_env()
        print("✓ Configuration loaded successfully")
        print(f"  IMAP: {config.imap_host}:{config.imap_port}")
        print(f"  SMTP: {config.smtp_host}:{config.smtp_port}")
        print(f"  Whitelist: {config.sender_whitelist_regex}")
        print(f"  Polling interval: {config.polling_interval_seconds}s")

    except Exception as e:
        logger.exception("Failed to load configuration: %s", e)
        print(f"ERROR: Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize services
    print("\nInitializing services...")
    imap_service = IMAPService(config)
    smtp_service = SMTPService(config)
    pdf_converter = PDFConverterService(config)
    whitelist_service = WhitelistService(config.sender_whitelist_regex)
    job_processor = JobProcessorService(
        config=config,
        imap_service=imap_service,
        smtp_service=smtp_service,
        pdf_converter=pdf_converter,
        whitelist_service=whitelist_service,
    )
    print("✓ Services initialized")

    # Connect to IMAP with exponential backoff
    print("\nConnecting to IMAP server...")
    try:
        imap_service.connect_with_backoff()
        print(f"✓ Connected to IMAP: {config.imap_host}:{config.imap_port}")
    except Exception as e:
        logger.exception("Failed to connect to IMAP: %s", e)
        print(f"ERROR: Failed to connect to IMAP: {e}", file=sys.stderr)
        sys.exit(1)

    # Connect to SMTP
    print("Connecting to SMTP server...")
    try:
        smtp_service.connect()
        print(f"✓ Connected to SMTP: {config.smtp_host}:{config.smtp_port}")
    except Exception as e:
        logger.exception("Failed to connect to SMTP: %s", e)
        print(f"ERROR: Failed to connect to SMTP: {e}", file=sys.stderr)
        sys.exit(1)

    # Main processing loop
    print("\n" + "=" * 60)
    print("PDF-to-PNG Email Processor is now running!")
    print("=" * 60)
    print(f"Polling INBOX every {config.polling_interval_seconds} seconds...")
    print("Press Ctrl+C to stop.\n")

    try:
        # Run daemon with continuous polling and connection recovery
        job_processor.run_daemon()

    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")

    finally:
        # Cleanup connections
        print("Disconnecting from servers...")
        try:
            imap_service.disconnect()
            smtp_service.disconnect()
            print("✓ Disconnected successfully")
        except Exception as e:
            logger.error("Error during disconnect: %s", e)

        print("Shutdown complete.")


if __name__ == "__main__":
    main()
