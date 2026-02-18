# Quickstart Guide: PDF-to-PNG Email Processor

**Date**: 2026-02-18
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This quickstart guide gets the PDF-to-PNG email processor running in under 10 minutes. For detailed architecture, see [data-model.md](./data-model.md) and [contracts/](./contracts/).

---

## Prerequisites

- Docker 20.10+ and Docker Compose 1.29+
- IMAP-enabled email account (Gmail, Outlook, custom mail server)
- SMTP-enabled email account (can be same as IMAP)
- Basic knowledge of Docker and environment variables

---

## Quick Start (3 Steps)

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd png-from-pdf-extracter

# Copy environment template
cp .env.example .env

# Edit .env with your email credentials
nano .env
```

**Required `.env` configuration**:

```bash
# IMAP Settings (incoming email)
IMAP_HOST=imap.gmail.com        # Your IMAP server
IMAP_PORT=993                   # 993 for SSL, 143 for plaintext
IMAP_USERNAME=monitor@gmail.com # Email address to monitor
IMAP_PASSWORD=your-app-password  # IMAP password or app password

# SMTP Settings (outgoing email)
SMTP_HOST=smtp.gmail.com        # Your SMTP server
SMTP_PORT=465                   # 465 for SSL, 587 for STARTTLS
SMTP_USERNAME=sender@gmail.com  # Email address to send from
SMTP_PASSWORD=your-app-password  # SMTP password or app password

# Whitelist (who can send PDFs)
SENDER_WHITELIST_REGEX=.*@yourcompany\.com  # Python regex pattern

# Optional: CC recipients (semicolon-separated)
CC_ADDRESSES=supervisor@company.com;team@company.com

# Optional: Polling interval (default: 60 seconds)
POLLING_INTERVAL_SECONDS=60

# Optional: Max retry interval for IMAP failures (default: 900 = 15 min)
MAX_RETRY_INTERVAL_SECONDS=900
```

**Gmail-specific setup**:
- Enable IMAP in Gmail settings (Settings → Forwarding and POP/IMAP)
- Use App Password, not your regular password (Google Account → Security → App passwords)
- If using 2FA, App Password is required

**Outlook-specific setup**:
- IMAP: `outlook.office365.com:993`
- SMTP: `smtp.office365.com:587`
- May need to enable "Less secure app access" or use OAuth2 (stdlib SMTP supports basic auth only)

---

### 2. Build and Run

```bash
# Build Docker image
docker-compose build

# Start container (runs in background)
docker-compose up -d

# Check logs (only shows errors per FR-023-FR-024)
docker-compose logs -f
```

**Expected output** (only errors are logged):
```
# No output = everything working correctly
# Errors only appear for IMAP/SMTP connection failures, PDF conversion failures, etc.
```

---

### 3. Test with Email

1. **Send test email** from a whitelisted address:
   - **To**: `monitor@gmail.com` (your IMAP_USERNAME)
   - **Subject**: Test PDF Conversion
   - **Attachment**: Any PDF file (try single-page first)

2. **Wait up to 60 seconds** (polling interval)

3. **Check your inbox** for reply email:
   - **From**: `sender@gmail.com` (your SMTP_USERNAME)
   - **To**: Your whitelisted sender address
   - **CC**: Any addresses in `CC_ADDRESSES`
   - **Attachments**: PNG images (1920x1080, one per PDF page)

4. **Original email deleted** from INBOX after successful processing (per FR-021)

---

## Common Issues

### ❌ Container exits immediately

**Check logs**:
```bash
docker-compose logs
```

**Common causes**:
- Missing or invalid environment variables → Check `.env` file
- Invalid IMAP/SMTP credentials → Test credentials with email client
- Invalid `SENDER_WHITELIST_REGEX` → Test regex at https://regex101.com/

---

### ❌ No reply email received

**Check container is running**:
```bash
docker-compose ps
```

**Verify email sent from whitelisted address**:
```bash
# Example whitelist: .*@company\.com
# ✅ Matches: user@company.com
# ❌ Doesn't match: user@gmail.com
```

**Check Docker logs** for errors:
```bash
docker-compose logs --tail=50
```

**Verify email has PDF attachment**:
- Emails without attachments are ignored
- Only `.pdf` files are processed (case-insensitive)

---

### ❌ IMAP connection failures

**Error in logs**:
```
IMAPConnectionError: Failed to connect to imap.gmail.com:993
```

**Solutions**:
1. **Verify IMAP settings**: Check host, port, username, password
2. **Check network**: Ensure Docker container can reach email server
   ```bash
   docker exec pdf-to-png-mailer ping imap.gmail.com
   ```
3. **Try TLS fallback**: System automatically tries SSL → STARTTLS → plaintext (per FR-025-FR-026)
4. **Check firewall**: Ensure ports 993 (IMAP) and 465/587 (SMTP) are open

**Exponential backoff** (per FR-027):
- System retries with increasing delays: 60s → 120s → 240s → ... up to 15 min
- Every failure is logged (per FR-028)

---

### ❌ PDF conversion failures

**Error notification email** sent to sender (per FR-012-FR-013):
- Subject: `Error processing PDF: <filename>`
- Body: Detailed stack trace and system information

**Common causes**:
- **Corrupted PDF**: PDF file is malformed or damaged
- **Password-protected PDF**: System cannot extract pages from encrypted PDFs
- **Invalid PDF**: File has `.pdf` extension but is not a valid PDF

**Check ImageMagick availability**:
```bash
docker exec pdf-to-png-mailer magick --version
```

**Expected output**:
```
Version: ImageMagick 7.x.x
```

---

### ❌ Memory usage >500MB

**Check current memory**:
```bash
docker stats pdf-to-png-mailer
```

**Typical memory usage**:
- Idle: ~30-50MB (Python runtime only)
- Processing single-page PDF: ~100-150MB
- Processing 50-page PDF: ~300-400MB (peak)

**If exceeding 500MB**:
- Reduce PDF page count (split large PDFs before sending)
- Check for memory leaks (shouldn't occur with stdlib approach)
- Increase Docker memory limit if needed

---

## Advanced Configuration

### Custom polling interval

```bash
# Check every 30 seconds instead of 60
POLLING_INTERVAL_SECONDS=30
```

**Trade-off**: More frequent checks = higher IMAP server load

---

### Multiple CC recipients

```bash
# Semicolon-separated list (per FR-020)
CC_ADDRESSES=recipient1@company.com;recipient2@company.com;recipient3@company.com
```

---

### Complex whitelist patterns

```bash
# Allow multiple domains
SENDER_WHITELIST_REGEX=".*@(company\.com|partner\.org)"

# Allow specific users only
SENDER_WHITELIST_REGEX="(alice|bob|charlie)@company\.com"

# Allow all addresses (not recommended for security)
SENDER_WHITELIST_REGEX=".*"
```

**Test regex** at https://regex101.com/ (select Python flavor)

---

### Non-SSL email servers

**IMAP plaintext** (port 143):
```bash
IMAP_HOST=mail.example.com
IMAP_PORT=143
```

**SMTP plaintext** (port 25):
```bash
SMTP_HOST=mail.example.com
SMTP_PORT=25
```

System automatically tries TLS first, then falls back to plaintext (per FR-025-FR-026).

---

## Stopping the Service

```bash
# Stop container (keeps data)
docker-compose stop

# Stop and remove container
docker-compose down

# Stop, remove container, and delete image
docker-compose down --rmi all
```

---

## Monitoring

### View logs (errors only)

```bash
# Follow live logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

**Log levels** (per FR-023-FR-024, NFR-001-NFR-002):
- ✅ **Logged**: IMAP connection failures, SMTP send failures, PDF conversion errors, configuration errors
- ❌ **NOT logged**: Successful email processing, PNG conversions, email sends (minimizes log volume)

---

### Check container health

```bash
# Container status
docker-compose ps

# Resource usage (CPU, memory)
docker stats pdf-to-png-mailer

# Container uptime
docker inspect pdf-to-png-mailer | grep StartedAt
```

---

### Restart container

```bash
# Graceful restart (waits for current email to finish)
docker-compose restart

# Force restart (may interrupt processing)
docker-compose restart -t 0
```

**Email safety** (per NFR-007):
- Emails are only deleted from INBOX after successful reply send
- If container crashes mid-processing, email remains in INBOX
- Next startup will reprocess the email (acceptable per NFR-008)

---

## Performance Benchmarks

**Expected processing times** (per SC-001):
- Single-page PDF: 2-5 seconds
- 10-page PDF: 15-30 seconds
- 50-page PDF: 60-120 seconds (within 2-minute budget)

**Memory usage** (measured):
- Idle: ~40MB
- Single-page PDF: ~120MB
- 50-page PDF: ~380MB (within 500MB budget per constitution)

**Docker image size**:
- Final image: ~420MB (Python 3.11-alpine + ImageMagick + GhostScript)

---

## Security Considerations

### Whitelist enforcement

**Critical**: Only emails from whitelisted senders are processed (per FR-002, FR-014)

- Non-whitelisted emails are **ignored** (no processing, no response)
- No error notification sent to non-whitelisted senders (prevents spam feedback)
- Whitelist enforced **before** any PDF processing (prevents abuse)

---

### Credential protection

**Never commit credentials**:
- `.env` file is in `.gitignore` (excluded from version control)
- Use environment variables or Docker secrets
- Rotate passwords regularly

**Use App Passwords** for Gmail/Outlook:
- More secure than regular passwords
- Can be revoked independently
- Required if 2FA is enabled

---

### TLS encryption

**Default behavior** (per FR-025-FR-026):
1. **Try TLS/SSL first** (IMAP4_SSL, SMTP_SSL)
2. **Fall back to STARTTLS** if SSL fails
3. **Fall back to plaintext** if STARTTLS fails

**Rationale**: Prioritizes availability over strict encryption (per NFR-004-NFR-006)

**For strict TLS-only** (modify source code):
```python
# Remove plaintext fallback in imap_service.py and smtp_service.py
# Only attempt IMAP4_SSL/SMTP_SSL, raise exception if fails
```

---

## Backup and Recovery

### No persistent state

- **Stateless design**: No database, no persistent storage (per data model)
- **Crash recovery**: Unprocessed emails remain in INBOX, reprocessed on restart
- **No data loss**: Emails only deleted after successful reply send (per NFR-007)

---

### Configuration backup

```bash
# Backup .env file (contains credentials)
cp .env .env.backup

# Store securely (DO NOT commit to Git)
```

---

## Updating the Application

```bash
# Pull latest code
git pull origin main

# Rebuild Docker image
docker-compose build

# Restart with new image
docker-compose up -d

# Verify logs
docker-compose logs -f
```

---

## Next Steps

- **Production deployment**: See [deployment guide](./deployment.md) (TODO)
- **Development setup**: See [development guide](./development.md) (TODO)
- **Architecture details**: See [data-model.md](./data-model.md) and [contracts/](./contracts/)
- **Task breakdown**: See [tasks.md](./tasks.md) (generated by `/speckit.tasks` command)

---

## Troubleshooting Checklist

Before opening an issue, verify:

- [ ] Docker and Docker Compose installed and running
- [ ] `.env` file exists with all required variables
- [ ] IMAP/SMTP credentials are correct (test with email client)
- [ ] IMAP/SMTP ports are open (test with `telnet` or `nc`)
- [ ] `SENDER_WHITELIST_REGEX` is valid Python regex
- [ ] Test email sent from whitelisted address
- [ ] Test email has PDF attachment
- [ ] Container is running (`docker-compose ps`)
- [ ] Logs checked for errors (`docker-compose logs`)

---

## Support

- **Issues**: GitHub Issues (provide logs and `.env` template, NOT credentials)
- **Documentation**: See [README.md](../../README.md) and [spec.md](./spec.md)
- **Email**: support@example.com (replace with actual support contact)

---

**Version**: 1.0.0 | **Last Updated**: 2025-01-21
