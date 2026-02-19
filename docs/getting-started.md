# Getting Started

This guide gets the PDF-to-PNG Email Processor running in under 10 minutes.

## Prerequisites

- **Docker** 20.10+ and **Docker Compose** 1.29+
- An **IMAP-enabled** email account (Gmail, Outlook, custom mail server)
- An **SMTP-enabled** email account (can be the same as IMAP)

## Installation

```bash
# Clone repository
git clone https://github.com/Soneritics/png-from-pdf-extracter.git
cd png-from-pdf-extracter

# Copy environment template
cp .env.example .env

# Edit .env with your email credentials
nano .env   # or your preferred editor
```

See the [Configuration Reference](configuration.md) for details on all available environment variables.

## Build and Run

```bash
# Build Docker image
docker-compose build

# Start container in background
docker-compose up -d

# Follow logs (only errors are logged)
docker-compose logs -f
```

No output in the logs means everything is working correctly. Only errors are logged per the error-only logging policy.

## Test with an Email

1. **Send a test email** from a whitelisted address to the monitored inbox.
   - Attach any PDF file (start with a single-page PDF).
2. **Wait up to 60 seconds** for the polling cycle.
3. **Check your inbox** for a reply containing PNG images (1920×1080, one per PDF page).
4. The original email is **deleted** from the INBOX after successful processing.

## Provider-Specific Setup

### Gmail

- Enable IMAP: *Settings → Forwarding and POP/IMAP → Enable IMAP*
- Use an **App Password** (Google Account → Security → App passwords), not your regular password.
- If 2FA is enabled, App Password is required.
- IMAP: `imap.gmail.com:993` · SMTP: `smtp.gmail.com:465`

### Outlook / Office 365

- IMAP: `outlook.office365.com:993`
- SMTP: `smtp.office365.com:587`
- May need to enable "Less secure app access" or use OAuth2.

## What's Next

- [Configuration Reference](configuration.md) — all environment variables explained
- [Deployment Guide](deployment.md) — production operations and monitoring
- [Troubleshooting](troubleshooting.md) — solving common issues
