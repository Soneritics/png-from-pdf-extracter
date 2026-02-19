# PDF-to-PNG Email Processor — Documentation

Welcome to the documentation for the **PDF-to-PNG Email Processor**, a containerized email monitoring service that automatically converts PDF attachments to PNG images and returns them via email.

## Documentation Overview

| Document | Description |
|----------|-------------|
| [Getting Started](getting-started.md) | Installation, prerequisites, and first run |
| [Configuration](configuration.md) | Environment variables and configuration reference |
| [Architecture](architecture.md) | System design, data model, and design decisions |
| [API Reference](api-reference.md) | Source code reference for all modules, services, and models |
| [Deployment](deployment.md) | Docker deployment, monitoring, and operations |
| [Development](development.md) | Development setup, testing, linting, and contributing |
| [Troubleshooting](troubleshooting.md) | Common issues, error handling, and debugging |

## Key Features

- **Automatic PDF-to-PNG conversion** — 1920×1080 pixels, 300 DPI, centered content
- **Whitelist-based sender authentication** — regex-based access control
- **CC recipients on response emails** — configurable via environment variable
- **Detailed error notifications** — stack traces sent to the original sender
- **Continuous daemon operation** — Docker container with automatic restart
- **TLS/SSL support** — encrypted connections with plaintext fallback
- **Zero runtime Python dependencies** — all stdlib for maximum security and compatibility

## Quick Links

- **GitHub Repository**: [Soneritics/png-from-pdf-extracter](https://github.com/Soneritics/png-from-pdf-extracter)
- **License**: [MIT](../LICENSE)
- **Feature Specification**: [specs/001-pdf-to-png-mailer/spec.md](../specs/001-pdf-to-png-mailer/spec.md)

## Version

**1.0.0** — Python 3.11 · Docker Alpine · ImageMagick 7.x · GhostScript
