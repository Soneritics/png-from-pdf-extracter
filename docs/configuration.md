# Configuration Reference

All configuration is managed through environment variables, defined in a `.env` file at the project root. Copy `.env.example` as a starting point.

## Required Variables

### IMAP (Incoming Email)

| Variable | Description | Example |
|----------|-------------|---------|
| `IMAP_HOST` | IMAP server hostname | `imap.gmail.com` |
| `IMAP_PORT` | IMAP server port (993 for SSL, 143 for plaintext) | `993` |
| `IMAP_USERNAME` | IMAP login username / email address | `monitor@gmail.com` |
| `IMAP_PASSWORD` | IMAP login password or app password | `your-app-password` |

### SMTP (Outgoing Email)

| Variable | Description | Example |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port (465 for SSL, 587 for STARTTLS, 25 for plaintext) | `465` |
| `SMTP_USERNAME` | SMTP login username / email address | `sender@gmail.com` |
| `SMTP_PASSWORD` | SMTP login password or app password | `your-app-password` |

### Whitelist

| Variable | Description | Example |
|----------|-------------|---------|
| `SENDER_WHITELIST_REGEX` | Python regex pattern for allowed senders | `.*@yourcompany\.com` |

**Whitelist examples**:

```bash
# All addresses from a domain
SENDER_WHITELIST_REGEX=.*@company\.com

# Multiple domains
SENDER_WHITELIST_REGEX=.*@(company\.com|partner\.org)

# Specific users only
SENDER_WHITELIST_REGEX=(alice|bob|charlie)@company\.com

# Allow all (NOT recommended)
SENDER_WHITELIST_REGEX=.*
```

Test your regex at [regex101.com](https://regex101.com/) using the Python flavor.

## Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CC_ADDRESSES` | Semicolon-separated CC recipients | *(empty)* |
| `POLLING_INTERVAL_SECONDS` | Seconds between INBOX checks (minimum: 10) | `60` |
| `MAX_RETRY_INTERVAL_SECONDS` | Maximum backoff delay for IMAP connection failures | `900` (15 min) |
| `PDF_RESOLUTION_WIDTH` | Output PNG width in pixels | `1920` |
| `PDF_RESOLUTION_HEIGHT` | Output PNG height in pixels | `1080` |
| `PDF_DENSITY_DPI` | DPI for PDF rendering (higher = better quality, slower) | `300` |
| `PDF_BACKGROUND` | Background color for transparent PDFs | `white` |
| `PDF_CONVERSION_TIMEOUT_SECONDS` | Timeout for a single PDF conversion | `120` |

### CC Recipients

```bash
# Single recipient
CC_ADDRESSES=supervisor@company.com

# Multiple recipients (semicolon-separated)
CC_ADDRESSES=supervisor@company.com;team@company.com;admin@company.com
```

When no CC addresses are configured, reply emails are sent only to the original sender.

## Validation Rules

The application validates all configuration at startup and exits with an error if validation fails:

- All host, username, and password fields must be non-empty strings.
- Port values must be in range 1–65535.
- `SENDER_WHITELIST_REGEX` must be a valid Python regex (compiled at startup).
- `POLLING_INTERVAL_SECONDS` must be ≥ 10 to prevent excessive polling.
- `MAX_RETRY_INTERVAL_SECONDS` must be ≥ `POLLING_INTERVAL_SECONDS`.
- `PDF_RESOLUTION_WIDTH` and `PDF_RESOLUTION_HEIGHT` must be ≥ 1.
- `PDF_DENSITY_DPI` must be ≥ 1.
- `PDF_CONVERSION_TIMEOUT_SECONDS` must be ≥ 1.

## Security Notes

- **Never commit `.env` to version control** — it is listed in `.gitignore`.
- Use app-specific passwords where possible (Gmail, Outlook).
- Rotate credentials regularly.
- Restrict the whitelist regex to only the addresses you trust.
