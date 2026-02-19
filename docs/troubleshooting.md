# Troubleshooting

## Container Exits Immediately

**Check logs**:
```bash
docker-compose logs
```

**Common causes**:

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Required environment variable X is not set` | Missing `.env` variable | Check `.env` against `.env.example` |
| `Invalid SENDER_WHITELIST_REGEX` | Malformed regex | Test at [regex101.com](https://regex101.com/) (Python flavor) |
| `imap_port must be in range 1-65535` | Invalid port number | Use 993 (SSL) or 143 (plaintext) for IMAP |
| `IMAP authentication failed` | Wrong credentials | Verify username/password; use App Password for Gmail |
| `SMTP authentication failed` | Wrong credentials | Verify username/password; use App Password for Gmail |

## No Reply Email Received

1. **Verify the container is running**:
   ```bash
   docker-compose ps
   ```

2. **Verify the sender is whitelisted**:
   ```bash
   # Example: SENDER_WHITELIST_REGEX=.*@company\.com
   # ✅ user@company.com → matches
   # ❌ user@gmail.com   → ignored
   ```

3. **Verify the email has a PDF attachment**:
   - Emails without attachments are silently ignored.
   - Only `.pdf` files are processed (case-insensitive).

4. **Check Docker logs for errors**:
   ```bash
   docker-compose logs --tail=50
   ```

5. **Wait at least 60 seconds** — the polling interval is 60 seconds by default.

## IMAP Connection Failures

**Error**: `IMAPConnectionError: Failed to connect to imap.example.com:993`

**Steps**:

1. Verify IMAP host, port, username, and password in `.env`.
2. Test credentials with an email client (Thunderbird, Outlook).
3. Check network connectivity from the container:
   ```bash
   docker exec pdf-to-png-mailer ping imap.example.com
   ```
4. Check firewall rules: ports 993 (IMAP SSL) and 143 (IMAP plaintext) must be open.
5. The system automatically retries with exponential backoff:
   - 60s → 120s → 240s → 480s → 900s (capped at 15 min)
   - Every failure is logged.

## SMTP Connection Failures

**Error**: `SMTPConnectionError: SMTP connection failed for smtp.example.com:465`

**Steps**:

1. Verify SMTP host, port, username, and password in `.env`.
2. Common port configurations:
   - `465` — SSL/TLS
   - `587` — STARTTLS
   - `25` — Plaintext (not recommended)
3. Check firewall rules for the SMTP port.
4. The system tries SSL → STARTTLS → plaintext automatically.

## PDF Conversion Failures

When conversion fails, the **original sender receives an error email** with detailed information including the stack trace.

**Common causes**:

| Error Pattern | Cause | Fix |
|---------------|-------|-----|
| `PDF is password-protected or encrypted` | Encrypted PDF | Remove password protection before sending |
| `PDF is corrupted or malformed` | Damaged file | Re-create the PDF |
| `ImageMagick conversion failed` | Unsupported PDF features | Check ImageMagick version: `docker exec pdf-to-png-mailer magick --version` |
| `PDF conversion timed out` | Very large/complex PDF | Increase `PDF_CONVERSION_TIMEOUT_SECONDS` or reduce page count |
| `No PNG files generated from PDF` | Empty PDF (0 pages) | Verify the PDF has content |

**Verify ImageMagick is available**:
```bash
docker exec pdf-to-png-mailer magick --version
# Expected: ImageMagick 7.x.x
```

## Memory Issues

**Check current memory usage**:
```bash
docker stats pdf-to-png-mailer
```

| State | Expected |
|-------|----------|
| Idle | ~40 MB |
| Single-page PDF | ~120 MB |
| 50-page PDF | ~380 MB |
| Hard limit | 500 MB |

If the container is killed due to OOM (Out of Memory):
- Split large PDFs before sending (reduce page count).
- Increase Docker memory limit in `docker-compose.yml` if your host allows it.
- The container will auto-restart and pick up unprocessed emails.

## Duplicate Emails Received

If the container crashes **after** converting PDFs but **before** deleting the original email, the email will be reprocessed on restart, resulting in a duplicate reply. This is by design — the system prioritizes reliability (never losing a notification) over strict deduplication.

## Virtual Environment Issues

```bash
# Recreate from scratch
deactivate
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt
```

## Import Errors

Ensure `PYTHONPATH` includes the project root:

```bash
# Linux/macOS
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Windows
set PYTHONPATH=%PYTHONPATH%;%CD%
```

## Docker Build Failures

```bash
# Clear Docker cache and rebuild
docker-compose build --no-cache

# Check build logs
docker-compose build 2>&1 | tail -50
```

## Pre-Issue Checklist

Before opening a GitHub issue, verify:

- [ ] Docker and Docker Compose are installed and running
- [ ] `.env` file exists with all required variables
- [ ] IMAP/SMTP credentials are correct (tested with an email client)
- [ ] IMAP/SMTP ports are open (test with `telnet` or `nc`)
- [ ] `SENDER_WHITELIST_REGEX` is valid Python regex
- [ ] Test email sent from a whitelisted address
- [ ] Test email has a PDF attachment
- [ ] Container is running (`docker-compose ps`)
- [ ] Logs checked for errors (`docker-compose logs`)

## Support

- **GitHub Issues**: [Soneritics/png-from-pdf-extracter/issues](https://github.com/Soneritics/png-from-pdf-extracter/issues)
- Provide logs and your `.env` template (with credentials redacted) when reporting issues.
