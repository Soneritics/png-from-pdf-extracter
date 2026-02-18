# Data Model: PDF-to-PNG Email Processor

**Date**: 2025-01-21  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This document defines the key entities and their relationships for the PDF-to-PNG email processing daemon. The system is stateless (no persistent database) and operates on in-memory representations of emails, attachments, and conversion jobs during processing.

---

## Entities

### 1. EmailMessage

Represents an incoming email retrieved from the IMAP INBOX.

**Attributes**:
- `uid: int` — IMAP UID of the message (unique within the mailbox)
- `sender: str` — Email address of the sender (extracted via `email.utils.parseaddr()`)
- `subject: str` — Email subject line
- `body: str` — Plain text body (optional, used for error context logging)
- `raw_bytes: bytes` — Complete RFC 5322 message (for re-parsing if needed)
- `received_at: datetime` — Timestamp when email was retrieved from IMAP server

**Validation Rules**:
- `sender` MUST be a valid email address format (validated via regex)
- `uid` MUST be a positive integer
- `raw_bytes` MUST not be empty

**State Transitions**:
1. **Fetched** → Email retrieved from IMAP but not yet processed
2. **Whitelisted** → Sender matches whitelist regex (FR-002)
3. **Processing** → Attachments being extracted and converted
4. **Completed** → PNG images sent successfully (email deleted from INBOX per FR-021)
5. **Failed** → Processing error occurred (error email sent per FR-012)
6. **Ignored** → Sender not whitelisted (no action taken per FR-014)

**Relationships**:
- Has many **PDFAttachment** (0..n)

**Source**: Parsed from IMAP fetch response via `email.message_from_bytes()`

---

### 2. PDFAttachment

Represents a PDF file extracted from an email message.

**Attributes**:
- `filename: str` — Original attachment filename from email (e.g., `invoice.pdf`)
- `sanitized_name: str` — Filename sanitized for filesystem safety (removes special chars, truncates to 50 chars)
- `content: bytes` — Binary content of the PDF file
- `size_bytes: int` — Size of the PDF in bytes
- `page_count: int | None` — Number of pages (detected after ImageMagick conversion, may be None if conversion fails)

**Validation Rules**:
- `filename` MUST have `.pdf` extension (case-insensitive)
- `content` MUST not be empty
- `size_bytes` MUST be > 0 and < 100MB (reasonable limit to prevent memory exhaustion)
- `sanitized_name` MUST match pattern `^[a-zA-Z0-9_-]+$` (only alphanumeric, underscore, hyphen)

**State Transitions**:
1. **Extracted** → Pulled from email message via `iter_attachments()`
2. **Validated** → Content is non-empty and filename has `.pdf` extension
3. **Converted** → ImageMagick successfully generated PNG images
4. **Failed** → Conversion error (corrupted PDF, password-protected, etc.)

**Relationships**:
- Belongs to one **EmailMessage**
- Has many **PNGImage** (1..n after successful conversion)

**Source**: Extracted via `email.message.EmailMessage.iter_attachments()`

---

### 3. PNGImage

Represents a generated PNG image from a single PDF page.

**Attributes**:
- `path: Path` — Filesystem path to the PNG file (in temp directory)
- `filename: str` — Final filename for email attachment (e.g., `invoice_pdf-001.png`)
- `source_pdf: str` — Original PDF filename this image came from
- `page_number: int` — PDF page number this image represents (1-indexed)
- `size_bytes: int` — File size of the PNG
- `resolution: tuple[int, int]` — Always `(1920, 1080)` per FR-006
- `density_dpi: int` — Always `300` per FR-005

**Validation Rules**:
- `path` MUST exist on filesystem before email sending
- `size_bytes` MUST be > 0 (empty files indicate conversion failure)
- `resolution` MUST equal `(1920, 1080)` (enforced by ImageMagick command)
- `page_number` MUST be ≥ 1

**State Transitions**:
1. **Generated** → ImageMagick created the PNG file
2. **Validated** → File exists and is non-empty
3. **Attached** → Added to reply email as MIME attachment
4. **Cleaned** → Temporary file deleted after successful email send

**Relationships**:
- Belongs to one **PDFAttachment**
- Attached to one **ReplyEmail**

**Source**: Created by ImageMagick CLI via subprocess

---

### 4. ProcessingJob

Represents the complete processing lifecycle for one incoming email.

**Attributes**:
- `email_message: EmailMessage` — The email being processed
- `pdf_attachments: list[PDFAttachment]` — Extracted PDF files
- `png_images: list[PNGImage]` — All generated PNG images across all PDFs
- `status: JobStatus` — Current state (enum: PENDING, PROCESSING, COMPLETED, FAILED)
- `error: Exception | None` — Captured exception if processing failed
- `started_at: datetime` — When processing began
- `completed_at: datetime | None` — When processing finished (success or failure)
- `duration_seconds: float | None` — Time taken to process (for performance tracking)

**Validation Rules**:
- `email_message` MUST not be None
- `status` MUST transition in order: PENDING → PROCESSING → (COMPLETED | FAILED)
- `completed_at` MUST be ≥ `started_at` when set
- `error` MUST be None if `status` is COMPLETED

**State Transitions**:
1. **PENDING** → Email fetched, not yet processing
2. **PROCESSING** → PDF extraction and conversion in progress
3. **COMPLETED** → PNG images sent successfully, original email deleted
4. **FAILED** → Error occurred, error email sent

**Relationships**:
- Has one **EmailMessage**
- Has many **PDFAttachment** (0..n)
- Has many **PNGImage** (0..n)

**Business Logic**:
- Processing is sequential (FR-022) — only one job active at a time
- Job is atomic — email only deleted after successful reply send (NFR-007)
- Failed jobs send error notification with full stack trace (FR-013)

---

### 5. Configuration

Represents system configuration loaded from environment variables at startup.

**Attributes**:
- `imap_host: str` — IMAP server hostname (FR-017)
- `imap_port: int` — IMAP server port (default: 993 for SSL, 143 for plaintext)
- `imap_username: str` — IMAP login username
- `imap_password: str` — IMAP login password
- `smtp_host: str` — SMTP server hostname (FR-018)
- `smtp_port: int` — SMTP server port (default: 465 for SSL, 587 for STARTTLS, 25 for plaintext)
- `smtp_username: str` — SMTP login username
- `smtp_password: str` — SMTP login password
- `sender_whitelist_regex: str` — Regex pattern for sender validation (FR-019)
- `cc_addresses: list[str]` — Semicolon-separated list of CC recipients (FR-020)
- `polling_interval_seconds: int` — IMAP polling frequency (default: 60 per FR-001)
- `max_retry_interval_seconds: int` — Max exponential backoff for IMAP failures (default: 900 = 15 min per FR-027)

**Validation Rules**:
- All `_host` fields MUST not be empty strings
- All `_port` fields MUST be in range 1-65535
- All `_username` and `_password` fields MUST not be empty
- `sender_whitelist_regex` MUST be a valid Python regex (compiled on load)
- `cc_addresses` MAY be empty list (no CC recipients)
- `polling_interval_seconds` MUST be ≥ 10 (prevent excessive polling)
- `max_retry_interval_seconds` MUST be ≥ `polling_interval_seconds`

**State Transitions**:
- Immutable after loading (no runtime configuration changes)

**Relationships**:
- Used by all services (IMAPService, SMTPService, WhitelistService)

**Source**: Loaded from environment variables via `os.getenv()` at startup

---

## Entity Relationships Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Configuration                             │
│  (loaded once at startup, immutable)                             │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ used by
                           ▼
┌───────────────────┐    ┌───────────────────────────────────────┐
│  EmailMessage     │◄───│        ProcessingJob                  │
│                   │    │  - email_message                      │
│  - uid            │    │  - pdf_attachments: list              │
│  - sender         │    │  - png_images: list                   │
│  - subject        │    │  - status: JobStatus                  │
│  - body           │    │  - error: Exception | None            │
│  - raw_bytes      │    │  - started_at / completed_at          │
│  - received_at    │    └───────────────────────────────────────┘
└───────────────────┘           │                  │
         │ has many             │ has many         │ has many
         ▼                      ▼                  ▼
┌───────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  PDFAttachment    │    │  PDFAttachment  │    │   PNGImage      │
│                   │    │  - filename     │    │   - path        │
│  - filename       │    │  - sanitized    │    │   - filename    │
│  - sanitized_name │    │  - content      │    │   - source_pdf  │
│  - content: bytes │    │  - size_bytes   │    │   - page_number │
│  - size_bytes     │    │  - page_count   │    │   - size_bytes  │
│  - page_count     │    └─────────────────┘    │   - resolution  │
└───────────────────┘           │                │   - density_dpi │
         │ has many             │ has many       └─────────────────┘
         ▼                      ▼
┌───────────────────┐    ┌─────────────────┐
│   PNGImage        │    │   PNGImage      │
│   (1..50 per PDF) │    │   (attached to  │
└───────────────────┘    │   reply email)  │
                         └─────────────────┘
```

---

## Key Data Flow

1. **Email Fetched**: `EmailMessage` created from IMAP UID fetch → sender validated against `Configuration.sender_whitelist_regex`
2. **Attachments Extracted**: `PDFAttachment` objects created from `EmailMessage.raw_bytes` parsing
3. **Conversion**: Each `PDFAttachment` → subprocess call to ImageMagick → generates `PNGImage` list
4. **Reply Sent**: `PNGImage` list → MIME multipart email → sent via SMTP with `Configuration.cc_addresses`
5. **Cleanup**: Original `EmailMessage` deleted from IMAP, `PNGImage` temp files removed

---

## Persistence Strategy

**No persistent storage** — all entities are in-memory only:
- Email processing is atomic per-email
- No database required (stateless daemon)
- Crash recovery: unprocessed emails remain in INBOX (per FR-021, emails only deleted after successful reply)
- Temporary files cleaned via `tempfile.TemporaryDirectory` context manager (automatic OS cleanup on process exit)

**Trade-off**: If container crashes mid-processing, the email will be reprocessed on restart (acceptable per NFR-008: idempotent design desirable but not guaranteed).

---

## Type Annotations (Python 3.11)

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class EmailMessage:
    uid: int
    sender: str
    subject: str
    body: str
    raw_bytes: bytes
    received_at: datetime

@dataclass
class PDFAttachment:
    filename: str
    sanitized_name: str
    content: bytes
    size_bytes: int
    page_count: int | None = None

@dataclass
class PNGImage:
    path: Path
    filename: str
    source_pdf: str
    page_number: int
    size_bytes: int
    resolution: tuple[int, int]
    density_dpi: int

@dataclass
class ProcessingJob:
    email_message: EmailMessage
    pdf_attachments: list[PDFAttachment]
    png_images: list[PNGImage]
    status: JobStatus
    error: Exception | None
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: float | None

@dataclass
class Configuration:
    imap_host: str
    imap_port: int
    imap_username: str
    imap_password: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    sender_whitelist_regex: str
    cc_addresses: list[str]
    polling_interval_seconds: int = 60
    max_retry_interval_seconds: int = 900
```

---

## Validation Functions

Each entity includes validation logic enforced at construction:

```python
def validate_email_message(msg: EmailMessage) -> None:
    """Validate EmailMessage constraints."""
    assert msg.uid > 0, "UID must be positive"
    assert "@" in msg.sender, "Sender must be valid email"
    assert len(msg.raw_bytes) > 0, "Raw bytes must not be empty"

def validate_pdf_attachment(pdf: PDFAttachment) -> None:
    """Validate PDFAttachment constraints."""
    assert pdf.filename.lower().endswith(".pdf"), "Must be PDF file"
    assert pdf.size_bytes > 0, "PDF must not be empty"
    assert pdf.size_bytes < 100 * 1024 * 1024, "PDF must be < 100MB"
    assert all(c.isalnum() or c in "_-" for c in pdf.sanitized_name), \
        "Sanitized name must be alphanumeric"

def validate_png_image(png: PNGImage) -> None:
    """Validate PNGImage constraints."""
    assert png.path.exists(), "PNG file must exist"
    assert png.size_bytes > 0, "PNG must not be empty"
    assert png.resolution == (1920, 1080), "Resolution must be 1920x1080"
    assert png.density_dpi == 300, "DPI must be 300"
    assert png.page_number >= 1, "Page number must be >= 1"
```

---

## Edge Case Handling

| Edge Case | Data Model Impact |
|-----------|------------------|
| Email with no attachments | `PDFAttachment` list is empty → email ignored (FR-014 extension) |
| Email with non-PDF attachments | Only `application/pdf` MIME type extracted → others ignored |
| Multiple PDFs in one email | `PDFAttachment` list has multiple items → all processed, PNGs use `sanitized_name` prefix (FR-008) |
| PDF with 0 pages | ImageMagick returns 0 PNG files → `PNGImage` list empty → error email sent (FR-012) |
| Corrupted PDF | ImageMagick subprocess returns non-zero exit code → `ProcessingJob.status = FAILED` → error email with stderr output |
| Password-protected PDF | GhostScript/ImageMagick fail → `ProcessingJob.error` captures exception → error email with stack trace (FR-013) |
| 50+ page PDF | `PNGImage` list has 50+ items → all attached to reply email (SC-006, no size limit per assumption) |
| Duplicate email reprocessing | Same email processed twice (container restart) → duplicate PNG conversion work → duplicate reply email sent (acceptable per NFR-008) |

---

**Version**: 1.0.0 | **Last Updated**: 2025-01-21
