# Phase 0 Research: Python Library Selection for PDF-to-PNG Email Processor

**Date**: 2025-07-17  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Research Summary

Library selections for three categories: IMAP monitoring, SMTP sending, and email parsing. Each evaluated against project requirements: Python 3.11+, long-running daemon suitability, memory efficiency (<500MB peak), sequential processing, TLS with plaintext fallback, and active maintenance.

---

## 1. IMAP Monitoring

### Candidates

| Library | Version | Last Release | Python Support | Dependencies | License |
|---------|---------|-------------|----------------|--------------|---------|
| **imaplib** (stdlib) | Built-in | Ships with Python | 3.11+ ✅ | None | PSF |
| **IMAPClient** | 3.1.0 | 2025 (recent) | 3.8–3.13 ✅ | None (runtime) | BSD-3 |
| **aioimaplib** | 2.0.1 | 2024 | 3.9–3.12 ⚠️ | None (runtime) | GPL-3 |

### Analysis

**imaplib (stdlib)** — ⭐ Recommended
- **Pros**: Zero dependencies, guaranteed Python 3.11+ compatibility, maintained by CPython core team, no supply chain risk, well-documented, battle-tested in production for decades, supports both `IMAP4` (plaintext) and `IMAP4_SSL` (TLS) classes making TLS-with-fallback straightforward.
- **Cons**: Low-level API — responses are raw bytes/tuples requiring manual parsing. No built-in connection retry/backoff (must implement manually). UID handling requires explicit `uid()` calls.
- **Daemon suitability**: Excellent. No connection pooling complexity, easy to implement reconnect logic. A simple `while True` loop with `select()`/`search()` is the standard pattern.
- **TLS fallback**: Native support — try `IMAP4_SSL` first, catch `ssl.SSLError`, fall back to `IMAP4` + `starttls()`, and finally fall back to plain `IMAP4`.
- **Memory**: Minimal overhead — stdlib module with no additional allocations.

**IMAPClient**
- **Pros**: Pythonic API wrapping imaplib, automatic UID handling, parsed responses as Python types, timezone handling, well-tested (comprehensive unit + functional tests against live servers), Python 3.13 compatible, active maintenance (v3.1.0 released 2025 with Python 3.14 compatibility fix).
- **Cons**: Adds a dependency (though lightweight, no transitive deps). Wraps imaplib internally, so any imaplib bugs still apply. TLS fallback requires the same manual logic as imaplib. Slightly larger API surface to learn.
- **Daemon suitability**: Good. Same reconnection patterns as imaplib but with cleaner API. The `folder_status()` and `search()` methods return parsed Python objects.
- **TLS fallback**: Supports `ssl_context` parameter and `starttls()`. Fallback logic must still be implemented manually.
- **Memory**: Negligible overhead above imaplib.

**aioimaplib**
- **Pros**: Native asyncio support, built-in IDLE command (RFC 2177) support for push-based notifications instead of polling, zero runtime dependencies.
- **Cons**: **GPL-3 license** (viral, may restrict distribution). Python 3.12 listed as latest tested — 3.11 supported but 3.13+ untested. No formal releases on GitHub (only PyPI). Uses deprecated `asyncio.get_event_loop()` pattern in examples. Smaller community. **For a sequential single-email processor that polls every 60s, async provides zero benefit and adds complexity** (event loop management, async context managers, coroutine debugging).
- **Daemon suitability**: Adequate for async daemons but overkill for this use case.
- **TLS fallback**: Supports `IMAP4_SSL` and `IMAP4` but fallback logic is manual.
- **Memory**: Slightly higher due to asyncio event loop overhead.

### Recommendation: **imaplib (stdlib)**

**Rationale**: For a single-threaded sequential email processor polling every 60s:

1. **Zero dependencies** — critical for a long-running Docker daemon (no supply chain updates, no version conflicts, no security advisories to track).
2. **Guaranteed compatibility** — ships with Python 3.11, will never break on Python upgrades.
3. **TLS fallback is straightforward** — `IMAP4_SSL` → `IMAP4` + `starttls()` → `IMAP4` plain, all native classes.
4. **Exponential backoff** is trivial to implement (~10 lines wrapping the connection in a retry loop).
5. **The low-level API is acceptable** because email operations are limited to: connect → login → select INBOX → search UNSEEN → fetch → delete → logout. IMAPClient's API sugar doesn't justify the dependency for this narrow use case.
6. **30+ day uptime requirement** favors stdlib — no risk of a third-party library update breaking the daemon.

IMAPClient would be a reasonable alternative if the project later needs complex IMAP operations (folder management, flag manipulation, complex search queries). For the current requirements, it's unnecessary abstraction.

aioimaplib is **not recommended** — async is overhead for sequential processing, GPL-3 license is restrictive, and the library has lower community adoption.

---

## 2. SMTP Sending

### Candidates

| Library | Version | Last Release | Python Support | Dependencies | License |
|---------|---------|-------------|----------------|--------------|---------|
| **smtplib** (stdlib) | Built-in | Ships with Python | 3.11+ ✅ | None | PSF |
| **aiosmtplib** | 5.1.0 | 2025 (recent) | 3.10+ ✅ | None | MIT |
| **yagmail** | 0.15.293 | Sep 2022 ❌ | 3.6–3.10 ⚠️ | premailer (+ keyring, dkimpy optional) | MIT |

### Analysis

**smtplib (stdlib)** — ⭐ Recommended
- **Pros**: Zero dependencies, guaranteed compatibility, supports `SMTP`, `SMTP_SSL`, and `starttls()` for TLS-with-fallback. Well-documented for building MIME messages with `email.mime` module. Handles large attachments via streaming. Direct control over connection lifecycle.
- **Cons**: Verbose API for building multipart messages with attachments — requires manual `MIMEMultipart`/`MIMEBase` construction. No automatic retry logic.
- **Large attachments**: Handles multiple PNG attachments well. Memory usage is proportional to attachment sizes (loaded into memory for MIME encoding), but this is unavoidable for any SMTP library.
- **CC support**: Native — set `Cc` header and include CC addresses in `sendmail()` recipient list.
- **TLS fallback**: Try `SMTP_SSL` first, fall back to `SMTP` + `starttls()`, then plain `SMTP`.

**aiosmtplib**
- **Pros**: Modern async SMTP client, zero dependencies, actively maintained (v5.1.0 in 2025), clean API, XOAUTH2 support, production-stable (Development Status: 5 - Production/Stable). Uses `email.message.EmailMessage` from stdlib.
- **Cons**: **Async adds no value for sequential email sending** — each email is sent one at a time after PDF conversion completes. Requires asyncio event loop management. Slightly more complex error handling (async exceptions).
- **Large attachments**: Same memory characteristics as smtplib (inherits from stdlib email module).
- **CC support**: Uses stdlib `EmailMessage` which supports CC natively.
- **TLS fallback**: Supports `use_tls`, `start_tls` parameters. Clean API for TLS configuration.

**yagmail**
- **Pros**: Extremely simple API for sending emails with attachments (one-liner). Automatic MIME type detection. Built-in attachment support.
- **Cons**: **Last commit September 2022 — nearly 3 years without updates** ❌. **Does not meet the "active maintenance within 12 months" requirement.** Python 3.10 is the latest listed supported version — 3.11+ untested. Has `premailer` as a required dependency (HTML email processing — unnecessary for this project). Gmail-centric design (keyring integration, Gmail-specific OAuth). Not designed for generic SMTP servers. No explicit TLS fallback support — assumes Gmail's security model.
- **Risk**: Abandoned project. Any Python 3.12+ breaking changes will not be fixed upstream.

### Recommendation: **smtplib (stdlib)**

**Rationale**:

1. **Zero dependencies** — same supply chain argument as imaplib.
2. **TLS fallback is native** — `SMTP_SSL` → `SMTP` + `starttls()` → `SMTP` plain.
3. **CC recipients are trivial** — add `Cc` header + include in recipient list.
4. **Large PNG attachments** work identically across all libraries (all use stdlib `email` module internally).
5. **The verbose MIME construction is a one-time cost** — write a `build_reply_email()` function once and it handles all cases. The ~20 extra lines vs yagmail's one-liner are negligible for a daemon that sends emails infrequently.
6. **Sequential sending** makes async pointless — `smtplib.sendmail()` blocks for the few seconds needed and that's fine.

yagmail is **eliminated** due to abandonment (last update Sep 2022) and Gmail-centric design. aiosmtplib is excellent but async provides zero benefit here.

---

## 3. Email Parsing

### Candidates

| Library | Version | Last Release | Python Support | Dependencies | License |
|---------|---------|-------------|----------------|--------------|---------|
| **email** (stdlib) | Built-in | Ships with Python | 3.11+ ✅ | None | PSF |
| **mail-parser** | 4.1.4 | 2024 | 3.8–3.10 ⚠️ | None (core) | Apache-2.0 |

### Analysis

**email (stdlib)** — ⭐ Recommended
- **Pros**: Zero dependencies, guaranteed compatibility, comprehensive MIME parsing, `email.message.EmailMessage` is the modern API (Python 3.6+), handles multipart messages, extracts attachments via `iter_attachments()`, parses sender/recipient/subject headers. Well-documented with many examples.
- **Cons**: Requires understanding MIME structure (multipart/mixed, multipart/alternative, etc.). Header parsing quirks with encoded headers (though `email.header.decode_header()` handles this).
- **Attachment extraction**: `message.iter_attachments()` yields each attachment part. `get_filename()` returns the attachment filename. `get_payload(decode=True)` returns binary content.
- **Sender extraction**: `message['From']` returns the sender. `email.utils.parseaddr()` extracts just the email address for whitelist matching.

**mail-parser**
- **Pros**: Convenient wrapper around stdlib `email` — parsed attributes match RFC header names (`from_`, `to`, `cc`, `attachments`). Convenient `.attachments` property returning list of dicts with `filename`, `payload`, `content_type`. Can parse Outlook .msg format (requires system package).
- **Cons**: Listed Python support only up to 3.10 — **3.11+ not officially tested** ⚠️. Last significant feature release was v3.15.0 (Feb 2021). Recent releases (4.x) appear to be CI/packaging fixes only. Wraps stdlib `email` internally — adds a dependency for convenience methods that are ~15 lines of code. The Outlook .msg parsing requires `libemail-outlook-message-perl` system package (irrelevant for this project — we only parse IMAP-retrieved RFC 5322 messages).
- **Risk**: Marginal maintenance. The convenience it provides doesn't justify the dependency.

### Recommendation: **email (stdlib)**

**Rationale**:

1. **Zero dependencies** — consistent with imaplib/smtplib choices.
2. **The parsing needed is minimal**: extract `From` header, iterate attachments, get filename + binary content. This is ~10 lines of stdlib code.
3. **mail-parser adds no meaningful value** for this use case — its convenience methods (`.from_`, `.attachments`) save maybe 5 lines of code while adding a dependency with uncertain 3.11+ support.
4. **The `email.message.EmailMessage` API is modern and clean** — `iter_attachments()`, `get_filename()`, `get_payload(decode=True)` are readable and well-documented.

---

## Final Recommendations

| Category | Library | Type | Rationale |
|----------|---------|------|-----------|
| **IMAP** | `imaplib` | stdlib | Zero deps, guaranteed compat, TLS fallback native, sufficient for poll-based monitoring |
| **SMTP** | `smtplib` | stdlib | Zero deps, TLS fallback native, CC support native, handles large attachments |
| **Email Parsing** | `email` | stdlib | Zero deps, modern `EmailMessage` API, minimal parsing needed |
| **PDF Conversion** | ImageMagick CLI (`magick`) | System tool | Per spec — called via `subprocess.run()`, not a Python library |
| **PDF Pre-processing** | GhostScript CLI (`gs`) | System tool | Per spec — ensures PDF readability before ImageMagick conversion |

### Architecture Implication: All-stdlib Approach

The all-stdlib recommendation means:
- **`requirements.txt` has zero runtime dependencies** — only dev dependencies (pytest, ruff, coverage, pip-audit)
- **Docker image is smaller** — no pip install step for runtime deps
- **No dependency updates to track** — stdlib evolves with Python itself
- **No supply chain attacks** — only CPython code runs in production
- **Simpler debugging** — all code paths are documented in Python official docs

### Key Implementation Patterns

```python
# IMAP with TLS fallback (imaplib)
def connect_imap(host: str, port: int, user: str, password: str) -> imaplib.IMAP4:
    try:
        conn = imaplib.IMAP4_SSL(host, port)
    except ssl.SSLError:
        conn = imaplib.IMAP4(host, port)
        try:
            conn.starttls()
        except Exception:
            pass  # Fall back to plaintext
    conn.login(user, password)
    return conn

# SMTP with TLS fallback (smtplib)
def connect_smtp(host: str, port: int, user: str, password: str) -> smtplib.SMTP:
    try:
        conn = smtplib.SMTP_SSL(host, port)
    except ssl.SSLError:
        conn = smtplib.SMTP(host, port)
        try:
            conn.starttls()
        except Exception:
            pass  # Fall back to plaintext
    conn.login(user, password)
    return conn

# Email parsing (email stdlib)
def extract_sender_and_pdfs(raw_bytes: bytes) -> tuple[str, list[tuple[str, bytes]]]:
    msg = email.message_from_bytes(raw_bytes, policy=email.policy.default)
    sender = email.utils.parseaddr(msg['From'])[1]
    pdfs = [
        (att.get_filename(), att.get_payload(decode=True))
        for att in msg.iter_attachments()
        if att.get_content_type() == 'application/pdf'
    ]
    return sender, pdfs
```

### When to Reconsider

- **If IDLE/push notifications are needed** instead of polling → consider IMAPClient (has cleaner IDLE support than raw imaplib)
- **If concurrent email processing is added** → consider aiosmtplib + aioimaplib for non-blocking I/O
- **If Outlook .msg files need parsing** → add mail-parser for its .msg support
- **If sending via Gmail specifically** → yagmail's OAuth integration would be useful (if it resumes maintenance)
