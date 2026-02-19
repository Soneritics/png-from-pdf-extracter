# API Reference

This document covers all public modules, classes, and methods in the `src/` package.

---

## Configuration

**Module**: `src.config`

### `Configuration`

System configuration loaded from environment variables. Immutable after creation.

```python
@dataclass
class Configuration:
    # IMAP settings
    imap_host: str
    imap_port: int
    imap_username: str
    imap_password: str

    # SMTP settings
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str

    # Whitelist
    sender_whitelist_regex: str

    # CC recipients
    cc_addresses: list[str] = []

    # Polling
    polling_interval_seconds: int = 60
    max_retry_interval_seconds: int = 900

    # PDF conversion
    pdf_resolution_width: int = 1920
    pdf_resolution_height: int = 1080
    pdf_density_dpi: int = 300
    pdf_background: str = "white"
    pdf_conversion_timeout_seconds: int = 120
```

**Class Methods**:

| Method | Description |
|--------|-------------|
| `Configuration.from_env() → Configuration` | Load configuration from environment variables. Raises `ValueError` if required variables are missing or invalid. |

**Properties**:

| Property | Description |
|----------|-------------|
| `compiled_whitelist → re.Pattern` | Pre-compiled regex pattern for whitelist matching. |

---

## Models

### `EmailMessage`

**Module**: `src.models.email_message`

Represents an incoming email retrieved from the IMAP INBOX.

| Attribute | Type | Description |
|-----------|------|-------------|
| `uid` | `int` | IMAP UID (must be positive) |
| `sender` | `str` | Sender email address (must contain `@`) |
| `subject` | `str` | Email subject line |
| `body` | `str` | Plain text body |
| `raw_bytes` | `bytes` | Complete RFC 5322 message (must not be empty) |
| `received_at` | `datetime` | Timestamp when retrieved |

### `PDFAttachment`

**Module**: `src.models.pdf_attachment`

Represents a PDF file extracted from an email.

| Attribute | Type | Description |
|-----------|------|-------------|
| `filename` | `str` | Original filename (must end with `.pdf`) |
| `sanitized_name` | `str` | Filesystem-safe name (alphanumeric, `_`, `-` only) |
| `content` | `bytes` | Binary PDF content |
| `size_bytes` | `int` | File size (must be > 0 and < 100 MB) |
| `page_count` | `int \| None` | Number of pages (set after conversion) |

### `PNGImage`

**Module**: `src.models.png_image`

Represents a generated PNG image from a single PDF page.

| Attribute | Type | Description |
|-----------|------|-------------|
| `path` | `Path` | Filesystem path (must exist) |
| `filename` | `str` | Output filename (e.g., `invoice_pdf-001.png`) |
| `source_pdf` | `str` | Original PDF filename |
| `page_number` | `int` | 1-indexed page number |
| `size_bytes` | `int` | File size (must be > 0) |
| `resolution` | `tuple[int, int]` | Output resolution (width, height) |
| `density_dpi` | `int` | Rendering DPI |

### `ProcessingJob`

**Module**: `src.models.processing_job`

Tracks the lifecycle of processing a single email.

| Attribute | Type | Description |
|-----------|------|-------------|
| `email_message` | `EmailMessage` | The email being processed |
| `pdf_attachments` | `list[PDFAttachment]` | Extracted PDFs |
| `png_images` | `list[PNGImage]` | All generated PNGs |
| `status` | `JobStatus` | `PENDING`, `PROCESSING`, `COMPLETED`, or `FAILED` |
| `error` | `Exception \| None` | Captured exception on failure |
| `started_at` | `datetime` | Processing start time |
| `completed_at` | `datetime \| None` | Processing end time |
| `duration_seconds` | `float \| None` | Total processing duration |

**Methods**:

| Method | Description |
|--------|-------------|
| `mark_processing()` | Set status to `PROCESSING`. |
| `mark_completed()` | Set status to `COMPLETED`, record end time. |
| `mark_failed(error)` | Set status to `FAILED`, capture exception, record end time. |

### `JobStatus`

**Module**: `src.models.processing_job`

```python
class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

---

## Services

### `IMAPService`

**Module**: `src.services.imap_service`

Handles IMAP connection, email retrieval, and message deletion with TLS fallback and exponential backoff.

| Method | Description |
|--------|-------------|
| `__init__(config: Configuration)` | Initialize with IMAP settings from config. |
| `connect()` | Establish connection: tries SSL → STARTTLS → plaintext. Raises `IMAPConnectionError` or `IMAPAuthenticationError`. |
| `connect_with_backoff(max_retries=None)` | Connect with exponential backoff (60s → 120s → ... → 900s cap). `None` retries = infinite. |
| `fetch_unseen_messages() → list[EmailMessage]` | Fetch all UNSEEN messages from INBOX. Returns empty list if none. |
| `delete_message(uid: int)` | Mark message as deleted and expunge. |
| `disconnect()` | Close connection gracefully (errors silenced). |

**Exceptions**:

| Exception | Description |
|-----------|-------------|
| `IMAPError` | Base exception for IMAP operations. |
| `IMAPConnectionError` | All connection methods failed. |
| `IMAPAuthenticationError` | Login credentials rejected. |

### `SMTPService`

**Module**: `src.services.smtp_service`

Handles SMTP connection and email sending with TLS fallback.

| Method | Description |
|--------|-------------|
| `__init__(config: Configuration)` | Initialize with SMTP settings from config. |
| `connect()` | Establish connection: tries SSL → STARTTLS → plaintext. Raises `SMTPConnectionError` or `SMTPAuthenticationError`. |
| `send_reply_with_attachments(to_address, subject, body, attachments, cc_addresses=None)` | Send reply email with PNG attachments. |
| `send_error_notification(to_address, error, context=None)` | Send error notification with stack trace and context. |
| `disconnect()` | Close connection gracefully (errors silenced). |

**Exceptions**:

| Exception | Description |
|-----------|-------------|
| `SMTPError` | Base exception for SMTP operations. |
| `SMTPConnectionError` | All connection methods failed. |
| `SMTPAuthenticationError` | Login credentials rejected. |

### `PDFConverterService`

**Module**: `src.services.pdf_converter`

Converts PDF files to PNG images using ImageMagick CLI.

| Method | Description |
|--------|-------------|
| `__init__(config=None)` | Initialize with optional config (defaults: 1920×1080, 300 DPI, white bg, 120s timeout). |
| `convert_pdf_to_png(pdf_path, output_prefix, temp_dir) → list[PNGImage]` | Convert all PDF pages to PNG images. Returns one `PNGImage` per page. |

**ImageMagick command executed**:

```bash
magick -density 300 "input.pdf" -resize 1920x1080! -extent 1920x1080! -gravity center -background white "output_pdf-%03d.png"
```

**Exceptions**:

| Exception | Description |
|-----------|-------------|
| `PDFConversionError` | Base exception for conversion failures. |
| `PDFCorruptedError` | PDF is corrupted or malformed. |
| `PDFPasswordProtectedError` | PDF is password-protected. |

### `WhitelistService`

**Module**: `src.services.whitelist_service`

Validates email sender addresses against a compiled regex pattern.

| Method | Description |
|--------|-------------|
| `__init__(regex_pattern: str)` | Initialize with regex. Raises `ValueError` if invalid. |
| `is_whitelisted(email_address: str) → bool` | Returns `True` if the address matches the pattern. |

### `JobProcessorService`

**Module**: `src.services.job_processor`

Orchestrates the complete email → PDF → PNG → reply workflow.

| Method | Description |
|--------|-------------|
| `__init__(config, imap_service, smtp_service, pdf_converter, whitelist_service)` | Initialize with all service dependencies. |
| `process_next_email()` | Process the next unseen email: validate sender, extract PDFs, convert, reply, delete. Sends error notification on failure. |
| `run_daemon()` | Run continuous polling loop with IMAP connection recovery. Blocks forever. |

---

## Utilities

### `logging`

**Module**: `src.utils.logging`

| Function | Description |
|----------|-------------|
| `setup_logging() → Logger` | Configure error-only logging (ERROR + CRITICAL to stderr). |
| `get_logger() → Logger` | Get the configured logger instance. |

### `file_utils`

**Module**: `src.utils.file_utils`

| Function | Description |
|----------|-------------|
| `sanitize_filename(filename, max_length=50) → str` | Remove extension, replace special chars with `_`, collapse consecutive underscores, truncate. Returns `"unnamed"` for empty results. |

**Examples**:

```python
sanitize_filename("invoice (copy).pdf")  # → "invoice_copy"
sanitize_filename("my*file?name.pdf")    # → "myfilename"
sanitize_filename("a" * 100)             # → "aaa..." (truncated to 50)
```

---

## Entry Point

**Module**: `src.main`

The `main()` function:

1. Loads configuration from environment variables.
2. Initializes all services (IMAP, SMTP, PDF converter, whitelist, job processor).
3. Connects to IMAP with exponential backoff.
4. Connects to SMTP.
5. Runs the daemon loop (`job_processor.run_daemon()`).
6. On `KeyboardInterrupt`, disconnects gracefully.

```bash
# Run directly
python -m src.main

# Run in Docker
docker-compose up -d
```
