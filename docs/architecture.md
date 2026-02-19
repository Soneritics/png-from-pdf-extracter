# Architecture

## Overview

The PDF-to-PNG Email Processor is a single-service background daemon that:

1. Monitors an IMAP inbox for new emails with PDF attachments.
2. Validates the sender against a whitelist regex.
3. Converts each PDF page to a 1920×1080 PNG image using ImageMagick/GhostScript.
4. Sends the PNG images back to the sender via SMTP.
5. Deletes the original email after successful processing.

## Technology Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Language | Python 3.11 | LTS version |
| Runtime Dependencies | None (all stdlib) | Zero supply chain risk |
| IMAP | `imaplib` (stdlib) | Email monitoring |
| SMTP | `smtplib` (stdlib) | Email sending |
| Email Parsing | `email` (stdlib) | MIME parsing & construction |
| PDF Conversion | ImageMagick 7.x (CLI) | Via `subprocess.run()` |
| PDF Pre-processing | GhostScript | Ensures PDF readability |
| Container | Docker (Python 3.11-alpine) | ~420MB image |
| Testing | pytest + coverage | Dev dependency only |
| Linting | ruff | Dev dependency only |

## Project Structure

```
src/
├── main.py                 # Entry point, daemon startup
├── config.py               # Configuration from environment variables
├── models/
│   ├── email_message.py    # EmailMessage dataclass
│   ├── pdf_attachment.py   # PDFAttachment dataclass
│   ├── png_image.py        # PNGImage dataclass
│   └── processing_job.py   # ProcessingJob dataclass + JobStatus enum
├── services/
│   ├── imap_service.py     # IMAP monitoring with TLS fallback & backoff
│   ├── smtp_service.py     # SMTP sending with TLS fallback
│   ├── pdf_converter.py    # ImageMagick PDF-to-PNG conversion
│   ├── whitelist_service.py # Regex-based sender validation
│   └── job_processor.py    # Workflow orchestration & daemon loop
└── utils/
    ├── logging.py          # Error-only logging setup
    └── file_utils.py       # Filename sanitization

tests/
├── unit/                   # Unit tests (isolated logic)
├── integration/            # Integration tests (service interactions)
└── contract/               # Contract tests (ImageMagick, SMTP behavior)
```

## Data Flow

```
┌──────────┐    ┌────────────────┐    ┌──────────────────┐    ┌────────────┐
│  IMAP    │───▸│ WhitelistService│───▸│ PDFConverterService│───▸│ SMTPService│
│ INBOX    │    │  (validate)    │    │   (ImageMagick)   │    │  (reply)   │
└──────────┘    └────────────────┘    └──────────────────┘    └────────────┘
     │                                                              │
     └──────────── delete after successful reply ◂─────────────────┘
```

1. **Email Fetched** — `IMAPService.fetch_unseen_messages()` retrieves UNSEEN emails from INBOX.
2. **Sender Validated** — `WhitelistService.is_whitelisted()` checks the sender against the regex. Non-matching emails are ignored.
3. **Attachments Extracted** — PDF attachments are extracted from the raw email bytes.
4. **PDFs Converted** — Each PDF is written to a temp directory and converted to PNG images via the `magick` CLI.
5. **Reply Sent** — `SMTPService.send_reply_with_attachments()` sends all PNGs back to the sender (with optional CC).
6. **Cleanup** — Original email is deleted from INBOX. Temp files are cleaned up automatically via `tempfile.TemporaryDirectory`.

## Data Model

### Entities

| Entity | Description |
|--------|-------------|
| `EmailMessage` | Incoming email: UID, sender, subject, body, raw bytes, timestamp |
| `PDFAttachment` | Extracted PDF: filename, sanitized name, binary content, size, page count |
| `PNGImage` | Generated PNG: path, filename, source PDF, page number, size, resolution, DPI |
| `ProcessingJob` | Lifecycle tracker: email, attachments, images, status, error, timing |
| `Configuration` | Immutable settings loaded from environment variables at startup |

### Entity Relationships

```
Configuration (immutable, used by all services)
       │
       ▼
ProcessingJob ──▸ EmailMessage
       │              │
       ├── PDFAttachment[] (extracted from email)
       │       │
       │       └── PNGImage[] (generated per PDF page)
       │
       └── PNGImage[] (all images across all PDFs)
```

### State Transitions

**ProcessingJob**: `PENDING → PROCESSING → COMPLETED | FAILED`

- `COMPLETED`: PNG images sent, original email deleted.
- `FAILED`: Error notification sent, original email remains in INBOX for reprocessing.

## Design Decisions

### All-Stdlib Approach

No runtime Python dependencies. All email operations use `imaplib`, `smtplib`, and `email` from the standard library. ImageMagick and GhostScript are invoked via `subprocess`.

**Rationale**:
- Zero supply chain attack surface.
- Guaranteed compatibility with Python 3.11+.
- Minimal Docker image footprint.
- No dependency updates to track for a long-running daemon.
- Memory efficiency: ~300MB peak vs 800MB+ with Python PDF bindings.

### Sequential Processing

Emails are processed one at a time in arrival order.

**Rationale**:
- Prevents resource exhaustion (memory, CPU) during PDF conversion.
- Simplifies error handling and state management.
- Sufficient for typical use cases (polling every 60 seconds).

### Error-Only Logging

Only `ERROR` and `CRITICAL` messages are logged. Successful operations are silent.

**Rationale**:
- Minimizes log volume for long-running daemons.
- Reduces storage requirements.
- Errors are actionable; success events are not.

### TLS Fallback Strategy

Connection attempts follow this order: TLS/SSL → STARTTLS → Plaintext.

**Rationale**: Prioritizes availability over strict encryption. If a mail server doesn't support TLS, the service still operates rather than failing completely.

### IMAP Exponential Backoff

On connection failure, retry delays follow: 60s → 120s → 240s → 480s → 900s (capped at 15 minutes). Retries continue indefinitely.

**Rationale**: Prevents overwhelming a failing server while ensuring automatic recovery once connectivity is restored.

### Stateless Design

No database or persistent storage. All state is in-memory during processing. Crash recovery relies on emails remaining in the INBOX until explicitly deleted after successful reply.

**Rationale**: Simplicity. A stateless daemon needs no backup/restore, no migration, and no schema management.

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Single-page PDF | 2–5 seconds |
| 10-page PDF | 15–30 seconds |
| 50-page PDF | 60–120 seconds |
| Idle memory | ~40 MB |
| Peak memory (50-page PDF) | ~380 MB |
| Docker image size | ~420 MB |
| Memory limit | 500 MB (Docker constraint) |
