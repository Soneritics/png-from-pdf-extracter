# Service Contracts

**Date**: 2025-01-21  
**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

This document defines the public interfaces (contracts) for all services in the PDF-to-PNG email processor. These interfaces establish the boundaries between components and enable independent testing.

---

## 1. IMAPService

Handles IMAP connection, email retrieval, and mailbox operations.

### Interface

```python
class IMAPService:
    """Service for IMAP email operations with TLS fallback and exponential backoff."""
    
    def __init__(self, config: Configuration) -> None:
        """Initialize IMAP service with configuration."""
        ...
    
    def connect(self) -> None:
        """
        Establish IMAP connection with TLS fallback.
        
        Connection Strategy (per FR-025, FR-026):
        1. Attempt IMAP4_SSL (TLS)
        2. If SSLError, attempt IMAP4 + starttls()
        3. If starttls() fails, fall back to plaintext IMAP4
        
        Raises:
            IMAPConnectionError: If all connection methods fail
            IMAPAuthenticationError: If login fails
        """
        ...
    
    def connect_with_backoff(self, max_retries: int = None) -> None:
        """
        Connect with exponential backoff on failure (per FR-027).
        
        Backoff schedule: 60s → 120s → 240s → ... up to 900s (15 min)
        Logs every failure attempt (per FR-028).
        
        Args:
            max_retries: Maximum retry attempts (None = infinite per NFR-011)
        
        Raises:
            IMAPConnectionError: If max_retries exceeded
        """
        ...
    
    def fetch_unseen_messages(self) -> list[EmailMessage]:
        """
        Fetch all UNSEEN messages from INBOX (per FR-001).
        
        Returns:
            List of EmailMessage objects with sender, subject, body, raw_bytes
        
        Raises:
            IMAPError: If fetch operation fails
        """
        ...
    
    def delete_message(self, uid: int) -> None:
        """
        Delete message by UID (per FR-021).
        
        Args:
            uid: IMAP message UID
        
        Raises:
            IMAPError: If deletion fails
        """
        ...
    
    def disconnect(self) -> None:
        """Close IMAP connection gracefully."""
        ...
```

### Error Handling

```python
class IMAPError(Exception):
    """Base exception for IMAP operations."""
    pass

class IMAPConnectionError(IMAPError):
    """Raised when IMAP connection fails after all retry attempts."""
    pass

class IMAPAuthenticationError(IMAPError):
    """Raised when IMAP login credentials are rejected."""
    pass
```

### Contract Tests

```python
def test_imap_service_connect_tls_success():
    """Verify TLS connection succeeds when server supports SSL."""
    ...

def test_imap_service_connect_fallback_to_plaintext():
    """Verify fallback to plaintext when TLS fails (per FR-026)."""
    ...

def test_imap_service_exponential_backoff():
    """Verify backoff schedule: 60s, 120s, 240s up to 900s (per FR-027)."""
    ...

def test_imap_service_logs_every_connection_failure():
    """Verify every connection failure is logged (per FR-028)."""
    ...

def test_imap_service_fetch_unseen_returns_email_messages():
    """Verify fetch_unseen_messages returns parsed EmailMessage objects."""
    ...

def test_imap_service_delete_removes_message_from_inbox():
    """Verify delete_message removes email from INBOX (per FR-021)."""
    ...
```

---

## 2. SMTPService

Handles SMTP connection and email sending with attachments.

### Interface

```python
class SMTPService:
    """Service for SMTP email operations with TLS fallback."""
    
    def __init__(self, config: Configuration) -> None:
        """Initialize SMTP service with configuration."""
        ...
    
    def connect(self) -> None:
        """
        Establish SMTP connection with TLS fallback.
        
        Connection Strategy (per FR-025, FR-026):
        1. Attempt SMTP_SSL (TLS)
        2. If SSLError, attempt SMTP + starttls()
        3. If starttls() fails, fall back to plaintext SMTP
        
        Raises:
            SMTPConnectionError: If all connection methods fail
            SMTPAuthenticationError: If login fails
        """
        ...
    
    def send_reply_with_attachments(
        self,
        to: str,
        cc: list[str],
        subject: str,
        body: str,
        attachments: list[PNGImage]
    ) -> None:
        """
        Send email with PNG attachments (per FR-009, FR-010, FR-011).
        
        Args:
            to: Recipient email address (original sender)
            cc: List of CC recipients (per FR-020, may be empty)
            subject: Email subject line
            body: Plain text email body
            attachments: List of PNGImage objects to attach
        
        Raises:
            SMTPError: If sending fails
        """
        ...
    
    def send_error_notification(
        self,
        to: str,
        subject: str,
        error: Exception,
        context: dict[str, any]
    ) -> None:
        """
        Send error notification with detailed stack trace (per FR-012, FR-013).
        
        Args:
            to: Recipient email address (original sender)
            subject: Email subject line
            error: Exception that occurred
            context: Additional context (email subject, PDF filenames, system info)
        
        Raises:
            SMTPError: If sending fails
        """
        ...
    
    def disconnect(self) -> None:
        """Close SMTP connection gracefully."""
        ...
```

### Error Handling

```python
class SMTPError(Exception):
    """Base exception for SMTP operations."""
    pass

class SMTPConnectionError(SMTPError):
    """Raised when SMTP connection fails."""
    pass

class SMTPAuthenticationError(SMTPError):
    """Raised when SMTP login credentials are rejected."""
    pass
```

### Contract Tests

```python
def test_smtp_service_connect_tls_success():
    """Verify TLS connection succeeds when server supports SSL."""
    ...

def test_smtp_service_connect_fallback_to_plaintext():
    """Verify fallback to plaintext when TLS fails (per FR-026)."""
    ...

def test_smtp_service_send_reply_includes_all_attachments():
    """Verify all PNG images are attached to reply email (per FR-009)."""
    ...

def test_smtp_service_send_reply_includes_cc_recipients():
    """Verify CC addresses are included in reply (per FR-011, FR-020)."""
    ...

def test_smtp_service_send_error_includes_stack_trace():
    """Verify error emails include detailed stack trace (per FR-013)."""
    ...

def test_smtp_service_send_error_includes_system_context():
    """Verify error emails include system info for debugging (per FR-013)."""
    ...
```

---

## 3. WhitelistService

Validates email sender addresses against configured regex pattern.

### Interface

```python
class WhitelistService:
    """Service for sender email address validation."""
    
    def __init__(self, regex_pattern: str) -> None:
        """
        Initialize whitelist service with regex pattern (per FR-019).
        
        Args:
            regex_pattern: Python regex for sender validation
        
        Raises:
            ValueError: If regex pattern is invalid
        """
        ...
    
    def is_whitelisted(self, email_address: str) -> bool:
        """
        Check if email address matches whitelist pattern (per FR-002).
        
        Args:
            email_address: Email address to validate
        
        Returns:
            True if address matches pattern, False otherwise
        """
        ...
```

### Contract Tests

```python
def test_whitelist_service_matches_valid_address():
    """Verify is_whitelisted returns True for matching address."""
    ...

def test_whitelist_service_rejects_invalid_address():
    """Verify is_whitelisted returns False for non-matching address."""
    ...

def test_whitelist_service_pattern_company_domain():
    """Verify pattern '.*@company\\.com' matches user@company.com (per spec)."""
    ...

def test_whitelist_service_pattern_company_domain_rejects_external():
    """Verify pattern '.*@company\\.com' rejects user@external.com (per spec)."""
    ...

def test_whitelist_service_raises_on_invalid_regex():
    """Verify ValueError raised if regex pattern is malformed."""
    ...
```

---

## 4. PDFConverterService

Converts PDF files to PNG images using ImageMagick CLI.

### Interface

```python
class PDFConverterService:
    """Service for PDF to PNG conversion via ImageMagick."""
    
    def convert_pdf_to_png(
        self,
        pdf_attachment: PDFAttachment,
        output_dir: Path
    ) -> list[PNGImage]:
        """
        Convert PDF pages to PNG images (per FR-004, FR-005, FR-006, FR-007, FR-008).
        
        Executes: magick -density 300 "input.pdf" -resize 1920x1080 
                  -gravity center -extent 1920x1080 "output-%03d.png"
        
        Args:
            pdf_attachment: PDFAttachment object with content and filename
            output_dir: Directory to write PNG files (typically temp directory)
        
        Returns:
            List of PNGImage objects (one per page, sequentially numbered)
        
        Raises:
            PDFConversionError: If ImageMagick command fails
            PDFCorruptedError: If PDF is corrupted or unreadable
            PDFPasswordProtectedError: If PDF requires password
        """
        ...
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize PDF filename for use in PNG output names (per FR-008).
        
        Strategy:
        - Remove file extension
        - Replace non-alphanumeric chars with underscore
        - Truncate to 50 characters
        - Convert to lowercase
        
        Args:
            filename: Original PDF filename
        
        Returns:
            Sanitized filename safe for filesystem use
        
        Example:
            "My Invoice (2024).pdf" → "my_invoice_2024_"
        """
        ...
```

### Error Handling

```python
class PDFConversionError(Exception):
    """Base exception for PDF conversion failures."""
    pass

class PDFCorruptedError(PDFConversionError):
    """Raised when PDF file is corrupted or malformed."""
    pass

class PDFPasswordProtectedError(PDFConversionError):
    """Raised when PDF requires password."""
    pass

class ImageMagickNotFoundError(PDFConversionError):
    """Raised when ImageMagick CLI is not available."""
    pass
```

### Contract Tests

```python
def test_pdf_converter_single_page_pdf():
    """Verify single-page PDF produces one PNG at 1920x1080 (per FR-006)."""
    ...

def test_pdf_converter_multi_page_pdf():
    """Verify multi-page PDF produces multiple PNGs, sequentially numbered."""
    ...

def test_pdf_converter_png_resolution_1920x1080():
    """Verify all PNGs are exactly 1920x1080 pixels (per FR-006)."""
    ...

def test_pdf_converter_png_density_300dpi():
    """Verify PNGs are rendered at 300 DPI (per FR-005)."""
    ...

def test_pdf_converter_png_filename_uses_sanitized_prefix():
    """Verify PNG filenames use sanitized PDF name as prefix (per FR-008)."""
    ...

def test_pdf_converter_50_page_pdf():
    """Verify 50-page PDF is handled within memory budget (per SC-006)."""
    ...

def test_pdf_converter_raises_on_corrupted_pdf():
    """Verify PDFCorruptedError raised for malformed PDF."""
    ...

def test_pdf_converter_raises_on_password_protected_pdf():
    """Verify PDFPasswordProtectedError raised for encrypted PDF."""
    ...

def test_pdf_converter_sanitize_removes_special_chars():
    """Verify sanitize_filename replaces special characters."""
    ...

def test_pdf_converter_sanitize_truncates_long_names():
    """Verify sanitize_filename truncates to 50 chars."""
    ...
```

---

## 5. JobProcessorService

Orchestrates the complete email → PDF → PNG → reply workflow.

### Interface

```python
class JobProcessorService:
    """Orchestrates processing of incoming emails."""
    
    def __init__(
        self,
        imap: IMAPService,
        smtp: SMTPService,
        whitelist: WhitelistService,
        converter: PDFConverterService,
        config: Configuration
    ) -> None:
        """Initialize job processor with all required services."""
        ...
    
    def process_next_email(self) -> ProcessingJob | None:
        """
        Process the next UNSEEN email from INBOX (per FR-022: sequential).
        
        Workflow:
        1. Fetch UNSEEN messages from IMAP
        2. Take first message (sequential processing)
        3. Validate sender against whitelist (FR-002)
        4. Extract PDF attachments (FR-003)
        5. Convert PDFs to PNGs (FR-004-FR-008)
        6. Send reply email with PNGs (FR-009-FR-011)
        7. Delete original email (FR-021)
        
        If error occurs, send error notification (FR-012-FR-013).
        
        Returns:
            ProcessingJob with status COMPLETED or FAILED, or None if no emails
        
        Raises:
            JobProcessorError: If critical error prevents processing
        """
        ...
    
    def run_daemon(self) -> None:
        """
        Run continuous email monitoring loop (per FR-001, FR-016).
        
        Workflow:
        1. Connect to IMAP with exponential backoff (FR-027)
        2. Poll INBOX every 60 seconds (FR-001)
        3. Process emails sequentially (FR-022)
        4. Retry IMAP connection on failure with backoff (FR-027-FR-028)
        5. Continue indefinitely (NFR-011)
        
        This method blocks forever (only returns on unrecoverable error).
        """
        ...
```

### Error Handling

```python
class JobProcessorError(Exception):
    """Base exception for job processing failures."""
    pass
```

### Contract Tests

```python
def test_job_processor_whitelisted_sender_processes_email():
    """Verify email from whitelisted sender is processed (per FR-002)."""
    ...

def test_job_processor_non_whitelisted_sender_ignored():
    """Verify email from non-whitelisted sender is ignored (per FR-014)."""
    ...

def test_job_processor_extracts_all_pdf_attachments():
    """Verify all PDF attachments are extracted (per FR-003)."""
    ...

def test_job_processor_converts_all_pdfs_to_pngs():
    """Verify all PDFs are converted to PNGs (per FR-004)."""
    ...

def test_job_processor_sends_reply_with_all_pngs():
    """Verify reply email contains all generated PNGs (per FR-009)."""
    ...

def test_job_processor_sends_reply_to_original_sender():
    """Verify reply is sent to original sender (per FR-010)."""
    ...

def test_job_processor_includes_cc_recipients():
    """Verify CC recipients are included in reply (per FR-011)."""
    ...

def test_job_processor_deletes_email_after_success():
    """Verify original email is deleted after successful reply (per FR-021)."""
    ...

def test_job_processor_does_not_delete_email_on_failure():
    """Verify original email remains in INBOX if reply fails (per NFR-007)."""
    ...

def test_job_processor_sends_error_email_on_failure():
    """Verify error notification sent on processing failure (per FR-012)."""
    ...

def test_job_processor_error_email_includes_stack_trace():
    """Verify error notification includes detailed stack trace (per FR-013)."""
    ...

def test_job_processor_processes_emails_sequentially():
    """Verify emails are processed one at a time (per FR-022)."""
    ...

def test_job_processor_daemon_polls_every_60_seconds():
    """Verify run_daemon polls INBOX every 60 seconds (per FR-001)."""
    ...

def test_job_processor_daemon_retries_imap_with_backoff():
    """Verify run_daemon uses exponential backoff on IMAP failure (per FR-027)."""
    ...
```

---

## 6. ImageMagick CLI Contract

External command-line tool contract (not a Python service).

### Command

```bash
magick -density 300 "input.pdf" -resize 1920x1080 -gravity center -extent 1920x1080 "output-%03d.png"
```

### Expected Behavior

**Inputs**:
- `input.pdf`: Valid PDF file path
- `output-%03d.png`: Output filename pattern with zero-padded page numbers

**Outputs**:
- One PNG file per PDF page
- Filenames: `output-001.png`, `output-002.png`, ..., `output-050.png`
- Each PNG: exactly 1920x1080 pixels, 300 DPI, centered content

**Exit Codes**:
- `0`: Success
- Non-zero: Error (check stderr for details)

### Contract Tests

```python
def test_imagemagick_cli_available():
    """Verify ImageMagick 'magick' command is available in PATH."""
    ...

def test_imagemagick_cli_converts_single_page_pdf():
    """Verify magick command produces one PNG for single-page PDF."""
    ...

def test_imagemagick_cli_converts_multi_page_pdf():
    """Verify magick command produces multiple PNGs for multi-page PDF."""
    ...

def test_imagemagick_cli_png_resolution():
    """Verify PNG output is exactly 1920x1080 pixels."""
    ...

def test_imagemagick_cli_png_density():
    """Verify PNG is rendered at 300 DPI."""
    ...

def test_imagemagick_cli_fails_on_corrupted_pdf():
    """Verify magick returns non-zero exit code for corrupted PDF."""
    ...

def test_imagemagick_cli_fails_on_password_protected_pdf():
    """Verify magick returns non-zero exit code for encrypted PDF."""
    ...

def test_ghostscript_available():
    """Verify GhostScript is available for PDF pre-processing."""
    ...
```

---

## Environment Variable Contract

Configuration is loaded from environment variables at startup.

### Required Variables

```bash
# IMAP Configuration (FR-017)
IMAP_HOST="imap.example.com"
IMAP_PORT="993"  # 993 for SSL, 143 for plaintext
IMAP_USERNAME="monitor@example.com"
IMAP_PASSWORD="secret"

# SMTP Configuration (FR-018)
SMTP_HOST="smtp.example.com"
SMTP_PORT="465"  # 465 for SSL, 587 for STARTTLS, 25 for plaintext
SMTP_USERNAME="sender@example.com"
SMTP_PASSWORD="secret"

# Whitelist Configuration (FR-019)
SENDER_WHITELIST_REGEX=".*@company\\.com"  # Python regex pattern

# CC Configuration (FR-020)
CC_ADDRESSES="supervisor@company.com;team@company.com"  # Semicolon-separated

# Optional Configuration
POLLING_INTERVAL_SECONDS="60"  # Default: 60 (per FR-001)
MAX_RETRY_INTERVAL_SECONDS="900"  # Default: 900 = 15 min (per FR-027)
```

### Validation

All required variables must be non-empty strings. Application exits with error message if any are missing or invalid.

### Contract Tests

```python
def test_config_loads_all_required_env_vars():
    """Verify Configuration loads all required environment variables."""
    ...

def test_config_validates_imap_port_range():
    """Verify IMAP_PORT must be 1-65535."""
    ...

def test_config_validates_smtp_port_range():
    """Verify SMTP_PORT must be 1-65535."""
    ...

def test_config_validates_whitelist_regex():
    """Verify SENDER_WHITELIST_REGEX is compiled successfully."""
    ...

def test_config_parses_cc_addresses_semicolon_separated():
    """Verify CC_ADDRESSES is split by semicolon (per FR-020)."""
    ...

def test_config_defaults_polling_interval_60_seconds():
    """Verify POLLING_INTERVAL_SECONDS defaults to 60 (per FR-001)."""
    ...

def test_config_defaults_max_retry_interval_900_seconds():
    """Verify MAX_RETRY_INTERVAL_SECONDS defaults to 900 (per FR-027)."""
    ...

def test_config_exits_on_missing_required_var():
    """Verify application exits with error if required var missing."""
    ...
```

---

## Docker Container Contract

The application runs as a Docker container with specific runtime expectations.

### Dockerfile Contract

```dockerfile
FROM python:3.11-alpine

# Install ImageMagick and GhostScript system packages
RUN apk add --no-cache imagemagick ghostscript

# Copy application code
COPY src/ /app/src/
COPY requirements.txt /app/

# Install Python dependencies (only dev deps in requirements-dev.txt)
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set working directory
WORKDIR /app

# Run main daemon
CMD ["python", "-m", "src.main"]
```

### Docker Compose Contract

```yaml
version: '3.8'

services:
  pdf-to-png-mailer:
    build: .
    container_name: pdf-to-png-mailer
    restart: unless-stopped  # Per FR-016
    environment:
      IMAP_HOST: "imap.example.com"
      IMAP_PORT: "993"
      IMAP_USERNAME: "monitor@example.com"
      IMAP_PASSWORD: "${IMAP_PASSWORD}"
      SMTP_HOST: "smtp.example.com"
      SMTP_PORT: "465"
      SMTP_USERNAME: "sender@example.com"
      SMTP_PASSWORD: "${SMTP_PASSWORD}"
      SENDER_WHITELIST_REGEX: ".*@company\\.com"
      CC_ADDRESSES: "supervisor@company.com;team@company.com"
      POLLING_INTERVAL_SECONDS: "60"
      MAX_RETRY_INTERVAL_SECONDS: "900"
    volumes:
      - /etc/localtime:/etc/localtime:ro  # Sync container time with host
```

### Expected Behavior

- Container runs continuously (never exits under normal operation)
- Automatically restarts if crashed (per FR-016)
- Logs only critical errors to stdout/stderr (per FR-023-FR-024, NFR-001-NFR-002)
- Consumes <500MB memory peak (per constitution)
- Processes emails sequentially (per FR-022, NFR-009)

### Contract Tests

```bash
# Build test
test_docker_build_succeeds():
    docker build -t pdf-to-png-mailer .
    assert exit code == 0

# Runtime test
test_docker_container_runs_continuously():
    docker run -d pdf-to-png-mailer
    sleep 300  # 5 minutes
    assert container is still running

# Restart policy test
test_docker_container_restarts_on_crash():
    docker run -d --restart unless-stopped pdf-to-png-mailer
    docker exec <container> kill 1  # Kill main process
    sleep 10
    assert container restarted automatically
```

---

**Version**: 1.0.0 | **Last Updated**: 2025-01-21
