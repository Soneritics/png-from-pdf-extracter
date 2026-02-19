# Deployment

## Docker Setup

The application is packaged as a Docker container based on Python 3.11 Alpine Linux with ImageMagick and GhostScript pre-installed.

### Build

```bash
docker-compose build
```

### Start

```bash
# Start in background
docker-compose up -d
```

The container is configured with `restart: unless-stopped`, meaning it will automatically restart after crashes or host reboots unless you explicitly stop it.

### Stop

```bash
# Stop (keeps container)
docker-compose stop

# Stop and remove container
docker-compose down

# Stop, remove container, and delete image
docker-compose down --rmi all
```

## Docker Compose Configuration

```yaml
services:
  pdf-to-png-mailer:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: pdf-to-png-mailer
    restart: unless-stopped
    env_file:
      - .env
    mem_limit: 500m
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Key settings:

- **`restart: unless-stopped`** — automatic restart on crash or host reboot.
- **`mem_limit: 500m`** — hard memory limit of 500 MB.
- **Log rotation** — max 3 files of 10 MB each (30 MB total).

## Dockerfile

```dockerfile
FROM python:3.11-alpine
RUN apk add --no-cache imagemagick ghostscript imagemagick-pdf
WORKDIR /app
COPY src/ ./src/
ENV PYTHONPATH=/app
CMD ["python", "-m", "src.main"]
```

The image has zero runtime Python dependencies — only system packages (ImageMagick, GhostScript) and the Python standard library.

## Monitoring

### Logs

Only errors are logged. No output means the service is operating normally.

```bash
# Follow live logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

**What gets logged** (ERROR/CRITICAL only):
- IMAP connection failures
- SMTP send failures
- PDF conversion errors
- Configuration errors
- Authentication failures

**What is NOT logged**:
- Successful email processing
- Successful PNG conversions
- Successful email sends
- Polling cycles

### Container Health

```bash
# Container status
docker-compose ps

# Resource usage (CPU, memory)
docker stats pdf-to-png-mailer

# Container uptime
docker inspect pdf-to-png-mailer | grep StartedAt
```

### Memory Usage

| State | Expected Memory |
|-------|----------------|
| Idle | ~40 MB |
| Single-page PDF | ~120 MB |
| 10-page PDF | ~200 MB |
| 50-page PDF | ~380 MB |
| Hard limit | 500 MB |

If memory exceeds 500 MB, Docker will kill the container. It will auto-restart and pick up any unprocessed emails.

## Restart

```bash
# Graceful restart (waits for current processing to finish)
docker-compose restart

# Force restart
docker-compose restart -t 0
```

**Email safety**: Emails are only deleted from the INBOX after the reply is successfully sent. If the container crashes mid-processing, the email remains in the INBOX and will be reprocessed on the next startup.

## Updating

```bash
# Pull latest code
git pull origin main

# Rebuild image
docker-compose build

# Restart with new image
docker-compose up -d

# Verify logs
docker-compose logs -f
```

## Backup and Recovery

### No Persistent State

The service is fully stateless — there is no database or persistent storage to back up. Configuration is stored in the `.env` file.

```bash
# Back up configuration (do NOT commit to Git)
cp .env .env.backup
```

### Crash Recovery

1. Container restarts automatically (`restart: unless-stopped`).
2. Unprocessed emails remain in the INBOX.
3. The daemon reconnects to IMAP with exponential backoff (60s → 120s → ... → 900s).
4. Processing resumes once connectivity is restored.

## Security Considerations

- **Credentials**: Stored in `.env`, excluded from Git via `.gitignore`.
- **Whitelist**: Only emails matching `SENDER_WHITELIST_REGEX` are processed.
- **TLS**: Encrypted connections attempted first; plaintext is a last resort fallback.
- **Supply chain**: Zero runtime Python dependencies — no third-party packages in production.
- **Memory isolation**: Docker `mem_limit` prevents resource exhaustion on the host.
