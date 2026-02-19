# PDF-to-PNG Email Processor

A containerized email monitoring service that automatically converts PDF attachments to PNG images and returns them via email. Built with Python 3.11, running as a Docker daemon with automatic restart and comprehensive error handling.

## Overview

This service monitors an IMAP inbox for incoming emails with PDF attachments from whitelisted senders, converts each PDF page to 1920x1080 PNG images at 300 DPI using ImageMagick, and sends the images back to the sender via email.

**Key Features:**
- ✅ Automatic PDF-to-PNG conversion (1920x1080, 300 DPI)
- ✅ Whitelist-based sender authentication
- ✅ CC recipients on response emails
- ✅ Detailed error notifications with stack traces
- ✅ Continuous daemon operation with automatic restart
- ✅ TLS/SSL support with plaintext fallback
- ✅ Sequential processing (one email at a time)
- ✅ Zero runtime dependencies (all Python stdlib!)

## Quick Start

See [specs/001-pdf-to-png-mailer/quickstart.md](specs/001-pdf-to-png-mailer/quickstart.md) for detailed setup instructions.

### Prerequisites

- Docker 20.10+ and Docker Compose 1.29+
- IMAP-enabled email account
- SMTP-enabled email account

### Installation

```bash
# Clone repository
git clone <repository-url>
cd png-from-pdf-extracter

# Copy environment template
cp .env.example .env

# Edit .env with your email credentials
nano .env

# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Basic Configuration

Required environment variables in `.env`:

```bash
# IMAP (incoming)
IMAP_HOST=imap.example.com
IMAP_PORT=993
IMAP_USERNAME=monitor@example.com
IMAP_PASSWORD=your_password

# SMTP (outgoing)
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_USERNAME=sender@example.com
SMTP_PASSWORD=your_password

# Whitelist (regex)
SENDER_WHITELIST_REGEX=.*@yourcompany\.com

# Optional: CC recipients
CC_ADDRESSES=supervisor@company.com;team@company.com
```

### Testing

Send an email with a PDF attachment to the monitored inbox from a whitelisted address. Within 60 seconds, you'll receive a reply with PNG images attached.

## Architecture

### Technology Stack

- **Language**: Python 3.11
- **Runtime Dependencies**: None (all stdlib!)
- **System Tools**: ImageMagick 7.x, GhostScript
- **Container**: Docker Alpine Linux
- **Testing**: pytest with coverage

### Project Structure

```
src/
├── main.py                 # Entry point
├── config.py               # Configuration management
├── models/                 # Data entities
│   ├── email_message.py
│   ├── pdf_attachment.py
│   ├── png_image.py
│   └── processing_job.py
├── services/               # Business logic
│   ├── imap_service.py     # Email monitoring
│   ├── smtp_service.py     # Email sending
│   ├── pdf_converter.py    # PDF-to-PNG conversion
│   ├── whitelist_service.py # Sender validation
│   └── job_processor.py    # Workflow orchestration
└── utils/                  # Utilities
    ├── logging.py          # Error-only logging
    └── file_utils.py       # File operations

tests/
├── unit/                   # Unit tests
├── integration/            # Integration tests
└── contract/               # Contract tests (ImageMagick, SMTP, etc.)
```

### Design Decisions

**All-stdlib approach**: No runtime Python dependencies for maximum security, compatibility, and minimal Docker footprint. ImageMagick/GhostScript are invoked via subprocess for precise control and memory efficiency (~300MB peak vs 800MB+ with Python bindings).

**Sequential processing**: One email at a time to prevent resource exhaustion and simplify error handling. Sufficient for typical use cases.

**Error-only logging**: Only ERROR and CRITICAL messages are logged to minimize log volume. Successful operations are silent.

**TLS fallback**: Tries SSL/TLS first, falls back to STARTTLS, then plaintext for maximum compatibility.

## Documentation

- **Quickstart Guide**: [specs/001-pdf-to-png-mailer/quickstart.md](specs/001-pdf-to-png-mailer/quickstart.md)
- **Feature Specification**: [specs/001-pdf-to-png-mailer/spec.md](specs/001-pdf-to-png-mailer/spec.md)
- **Implementation Plan**: [specs/001-pdf-to-png-mailer/plan.md](specs/001-pdf-to-png-mailer/plan.md)
- **Data Model**: [specs/001-pdf-to-png-mailer/data-model.md](specs/001-pdf-to-png-mailer/data-model.md)
- **Service Contracts**: [specs/001-pdf-to-png-mailer/contracts/](specs/001-pdf-to-png-mailer/contracts/)
- **Task Breakdown**: [specs/001-pdf-to-png-mailer/tasks.md](specs/001-pdf-to-png-mailer/tasks.md)

## Performance

- **Single-page PDF**: 2-5 seconds
- **10-page PDF**: 15-30 seconds
- **50-page PDF**: 60-120 seconds (within 2-minute budget)
- **Memory usage**: ~40MB idle, ~380MB peak (50-page PDF)
- **Docker image**: ~420MB (Python 3.11-alpine + ImageMagick + GhostScript)

## Development

### Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Lint code
ruff check src/ tests/

# Security audit
pip-audit
```

### Testing

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Security

- **Whitelist enforcement**: Only emails from regex-matched senders are processed
- **No credential storage**: All credentials in environment variables
- **TLS by default**: SSL/TLS attempted first, with plaintext as last fallback
- **Supply chain**: Zero runtime Python dependencies = zero attack surface
- **Error isolation**: Failed emails remain in inbox for manual inspection

## License

MIT License - see [LICENSE](LICENSE) file

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Support

For issues, questions, or contributions:
- **GitHub Issues**: https://github.com/Soneritics/png-from-pdf-extracter/issues
- **Documentation**: [specs/](specs/) directory
