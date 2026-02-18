# Feature Specification: PDF-to-PNG Email Processor

**Feature Branch**: `001-pdf-to-png-mailer`  
**Created**: 2025-01-21  
**Status**: Draft  
**Input**: User description: "A mail watcher application for an IMAP mail account, running in a Docker container. A whitelisted user sends an email with one or more PDF files to this email address. This script will then start extrating PNG images out of the PDF. Use ImageMick for extracting PNG images out of a PDF file, every page its own PNG file, using a density of 300 and a resolution of 1920x1080. The ImageMick command I currently use for this: magick -density 300 "pdffilename.pdf" -resize 1920x1080 -gravity center -extent 1920x1080 "$name-%03d.png" Next to ImageMick I also use GhostScript to make sure PDF files can be read. When the images are created, send them back to the email address that sent the PDF. Also optionally add CC addresses, which will be configured in the container's configuration. When processing is not possible due to errors, send this as body in the email. The Docker container must always run, so restart: unless-stopped Docker configuration: - Incoming mail server host name, port, username, password. - Outgoing mail server host name, port, username, password. - Regex for whitelisting the email address of the sender - List of cc-addresses, separated by a semicolon"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Convert PDF to PNG Images via Email (Priority: P1)

A user sends an email with one or more PDF attachments to the monitored email address. The system automatically converts each page of every PDF into a separate PNG image at 1920x1080 resolution and emails the images back to the sender.

**Why this priority**: This is the core functionality - without this, there is no product. It represents the complete end-to-end workflow that delivers immediate value to users.

**Independent Test**: Can be fully tested by sending an email with a PDF attachment to the monitored inbox and verifying that PNG images are received back via email, delivering the complete user value proposition.

**Acceptance Scenarios**:

1. **Given** a whitelisted user, **When** they send an email with a single-page PDF attachment, **Then** they receive an email back with one PNG image (1920x1080) of that PDF page
2. **Given** a whitelisted user, **When** they send an email with a multi-page PDF attachment, **Then** they receive an email back with multiple PNG images, one for each page, numbered sequentially
3. **Given** a whitelisted user, **When** they send an email with multiple PDF attachments, **Then** they receive an email back with PNG images for all pages from all PDFs
4. **Given** a PDF with mixed page sizes, **When** converted to PNG, **Then** all images are normalized to 1920x1080 with centered content and proper aspect ratio preservation

---

### User Story 2 - Access Control via Whitelist (Priority: P2)

Only emails from authorized senders (matching a configured whitelist pattern) are processed. Emails from non-whitelisted addresses are ignored to prevent abuse and unauthorized usage.

**Why this priority**: Essential for security and resource protection, but the core conversion functionality (P1) must work first before access control matters.

**Independent Test**: Can be tested by configuring a whitelist pattern, sending emails from both matching and non-matching addresses, and verifying only whitelisted emails are processed.

**Acceptance Scenarios**:

1. **Given** a sender address matches the whitelist regex, **When** they send an email with PDF, **Then** the PDF is processed and images are returned
2. **Given** a sender address does not match the whitelist regex, **When** they send an email with PDF, **Then** the email is ignored and no processing occurs
3. **Given** a whitelist pattern of `.*@company\.com`, **When** user@company.com sends a PDF, **Then** it is processed
4. **Given** a whitelist pattern of `.*@company\.com`, **When** user@external.com sends a PDF, **Then** it is ignored

---

### User Story 3 - CC Recipients on Response Emails (Priority: P3)

When sending converted PNG images back to the original sender, the system can also CC additional email addresses configured in the system settings, allowing teams or supervisors to receive copies.

**Why this priority**: This is a convenience feature that adds value but isn't critical for core functionality. Users can work effectively without CC functionality.

**Independent Test**: Can be tested by configuring CC addresses, processing a PDF, and verifying the response email includes the configured CC recipients.

**Acceptance Scenarios**:

1. **Given** CC addresses are configured, **When** a PDF is successfully processed, **Then** the response email is sent to the original sender with configured addresses in CC
2. **Given** multiple CC addresses separated by semicolons, **When** a PDF is processed, **Then** all CC addresses receive the response email
3. **Given** no CC addresses are configured, **When** a PDF is processed, **Then** only the original sender receives the response email

---

### User Story 4 - Error Notification (Priority: P2)

When PDF processing fails for any reason (corrupted PDF, processing errors, system issues), the system notifies the sender via email with a clear description of what went wrong.

**Why this priority**: Critical for user experience and debugging, but less important than getting the happy path working first. Users need to know when something fails.

**Independent Test**: Can be tested by sending intentionally problematic PDFs (corrupted, encrypted, invalid format) and verifying error emails are sent with descriptive messages.

**Acceptance Scenarios**:

1. **Given** a corrupted or unreadable PDF, **When** processing fails, **Then** the sender receives an email with detailed error information including stack trace and system details
2. **Given** a password-protected PDF, **When** processing cannot access content, **Then** the sender receives an email with detailed technical error explaining the PDF is protected
3. **Given** system errors during conversion, **When** processing fails, **Then** the sender receives an email with detailed technical error information including stack trace and system context
4. **Given** a PDF with no pages, **When** processing completes but produces no images, **Then** the sender receives an email with detailed information explaining no content was found

---

### Edge Cases

- What happens when an email contains both PDF and non-PDF attachments? (The system processes only the PDF files and ignores other attachments)
- What happens when a PDF is extremely large or has hundreds of pages? (System attempts processing; may fail due to memory/time limits and send error email. All images are sent in a single reply email regardless of total size)
- What happens if the outgoing email server is unreachable? (Processing completes but reply cannot be sent; incoming email remains in inbox and will be reprocessed on next polling cycle)
- What happens when multiple emails arrive simultaneously? (System processes them sequentially one at a time in arrival order to prevent resource exhaustion and race conditions)
- What happens if an email has no attachments? (Email is ignored; no processing occurs, no response sent, email remains in inbox)
- What happens when the Docker container restarts mid-processing? (Unprocessed emails remain in inbox and will be picked up again; emails in progress will be reprocessed since they are only deleted after successful reply)
- What happens if reply email sending fails after PDF processing completes? (Incoming email is NOT deleted and will be reprocessed on next check, resulting in duplicate conversion work but ensuring no lost notifications)
- What happens with PNG filenames when multiple PDFs are attached? (PNG filenames use sanitized PDF filename as prefix with sequential numbering, e.g., invoice_pdf-001.png, report_pdf-001.png, ensuring each PDF's pages are distinguishable)
- What happens when TLS/SSL connection to email servers fails? (System attempts encrypted connection first, falls back to unencrypted connection if TLS negotiation fails, ensuring availability over strict security)
- What happens if emails are delivered to folders other than INBOX (e.g., Sent, Drafts, custom folders)? (System monitors only the INBOX folder; emails in other folders are completely ignored and never processed)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST continuously monitor the INBOX folder of an IMAP email account for new incoming messages with a polling interval of 60 seconds
- **FR-027**: System MUST implement exponential backoff for IMAP connection failures with the following sequence: 60s → 120s → 240s → 480s → 900s (capped at 15 minutes) between retry attempts, retrying indefinitely until connection is restored
- **FR-028**: System MUST log every IMAP connection failure attempt with timestamp and error details
- **FR-002**: System MUST validate incoming email sender addresses against a configured regex whitelist pattern
- **FR-003**: System MUST extract all PDF file attachments from emails sent by whitelisted senders
- **FR-004**: System MUST convert each page of each PDF into a separate PNG image file
- **FR-005**: System MUST render PNG images at 300 DPI density during conversion
- **FR-006**: System MUST resize and fit PNG images to exactly 1920x1080 pixels with centered content
- **FR-007**: System MUST preserve aspect ratios when converting PDF pages to PNG format
- **FR-008**: System MUST generate PNG filenames using sanitized PDF filename as prefix followed by sequential numbering (e.g., invoice_pdf-001.png, invoice_pdf-002.png for invoice.pdf)
- **FR-009**: System MUST compose a reply email containing all generated PNG images as attachments in a single email
- **FR-010**: System MUST send reply emails to the original sender's email address
- **FR-011**: System MUST include configured CC recipients on reply emails when CC addresses are configured
- **FR-012**: System MUST send an error notification email to the sender when processing fails
- **FR-013**: System MUST include detailed technical error information in the body of error notification emails, including stack traces and system information
- **FR-014**: System MUST ignore emails from non-whitelisted sender addresses without sending any response
- **FR-015**: System MUST run as a continuously-operating Docker container
- **FR-016**: System MUST automatically restart when the container stops (unless explicitly stopped by administrator)
- **FR-017**: System MUST accept configuration for incoming IMAP server hostname, port, username, and password
- **FR-018**: System MUST accept configuration for outgoing SMTP server hostname, port, username, and password
- **FR-019**: System MUST accept configuration for sender whitelist as a regex pattern
- **FR-020**: System MUST accept configuration for semicolon-separated list of CC email addresses
- **FR-021**: System MUST delete incoming email messages immediately after successfully sending reply email
- **FR-022**: System MUST process incoming emails sequentially in arrival order (one at a time)
- **FR-023**: System MUST log only critical errors (e.g., connection failures, processing failures, configuration errors)
- **FR-024**: System MUST NOT log routine operational events such as successful email processing, image conversions, or email sends
- **FR-025**: System MUST attempt encrypted (TLS/SSL) connections to IMAP and SMTP servers by default
- **FR-026**: System MUST fall back to unencrypted connections when TLS/SSL negotiation fails with email servers
- **FR-029**: System MUST use only Python standard library modules for runtime dependencies; external packages are limited to development and testing tools only

### Non-Functional Requirements

**Observability**:
- **NFR-001**: System MUST log critical errors including: IMAP/SMTP connection failures, authentication failures, PDF processing failures, email send failures, configuration errors
- **NFR-001a**: System MUST log every IMAP connection failure with exponential backoff timing (60s, 120s, 240s, 480s, 900s capped) between retries
- **NFR-002**: System MUST NOT log successful operations (email retrieved, PDF converted, images sent) to minimize log volume and storage requirements
- **NFR-003**: Error log entries MUST include timestamp and sufficient context for debugging (e.g., email subject, sender, error type)

**Security & Connection Management**:
- **NFR-004**: System MUST attempt TLS/SSL encrypted connections to IMAP and SMTP servers as the first connection method
- **NFR-005**: System MUST automatically fall back to unencrypted (plaintext) connections when TLS/SSL negotiation fails
- **NFR-006**: Connection security approach prioritizes service availability over strict encryption enforcement

**Reliability & State Management**:
- **NFR-007**: System MUST delete processed emails only after successful reply email transmission to ensure no lost notifications
- **NFR-008**: System MUST tolerate duplicate processing of the same email (idempotent design desirable but not guaranteed)
- **NFR-009**: System MUST process emails sequentially to prevent resource exhaustion and ensure predictable behavior under load
- **NFR-010**: System MUST retry IMAP connections using exponential backoff (60s → 120s → 240s → 480s → 900s capped) when connection attempts fail
- **NFR-011**: System MUST continue retry attempts indefinitely until IMAP connection is restored (no permanent failure state)

### Key Entities

- **Email Message**: Represents an incoming email with sender address, subject, body, and attachments
- **PDF Attachment**: A PDF file attached to an email, with filename and binary content
- **PNG Image**: Generated image file at 1920x1080 resolution, represents one page from a PDF
- **Processing Job**: Represents the conversion task for one email, tracking status (pending, processing, completed, failed)
- **Configuration**: System settings including IMAP credentials, SMTP credentials, whitelist pattern, and CC addresses

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully processes and returns PNG images for 95% of valid PDF emails from whitelisted senders within 2 minutes per PDF (excluding email polling delay of up to 60 seconds)
- **SC-002**: All PNG images are exactly 1920x1080 pixels with content properly centered and aspect ratios preserved
- **SC-003**: System runs continuously for 30+ days without manual intervention or restarts
- **SC-004**: 100% of processing errors result in error notification emails sent to the original sender within 1 minute
- **SC-005**: System correctly rejects 100% of emails from non-whitelisted senders without processing or responding
- **SC-006**: System handles PDFs with up to 50 pages without failure
- **SC-007**: Container automatically recovers and resumes operation within 10 seconds after unexpected crashes or restarts

## Clarifications

### Session 2025-01-21

- Q: How should the system manage processed email state to prevent reprocessing? → A: Delete processed emails immediately after successful reply
- Q: Should there be size limits on reply emails with multiple images? → A: Send all images in a single email regardless of size
- Q: How should the system handle concurrent incoming emails? → A: Sequential processing - one at a time in arrival order
- Q: What level of logging and observability should the system provide? → A: Minimal logging, only critical errors
- Q: What email connection security should be used for IMAP/SMTP? → A: Default to encrypted but allow fallback to unencrypted if TLS negotiation fails
- Q: What polling frequency should the system use to check for new emails? → A: Every 60 seconds
- Q: How should the system handle IMAP connection failures during polling attempts? → A: Exponential backoff (60s→120s→240s up to 15 min) and log every failure attempt
- Q: How should PNG filenames be generated when multiple PDFs are attached to prevent conflicts? → A: Sanitized PDF filename as prefix (e.g., invoice_pdf-001.png)

### Session 2

- Q: What polling interval should the system use to check the IMAP server for new emails? → A: Poll IMAP server every 60 seconds
- Q: How should the system handle IMAP connection failures during polling? → A: Exponential backoff on connection failure (60s, 120s, 240s up to 15 min) with every failure logged
- Q: How should PNG filenames be generated to distinguish between multiple PDF attachments? → A: Sanitized PDF filename as prefix for PNG files (e.g. invoice_pdf-001.png)
- Q: What level of detail should error notification emails include? → A: Error notification emails include detailed technical error with stack traces and system information
- Q: Which IMAP folder(s) should the system monitor for incoming emails? → A: Monitor INBOX folder only

## Assumptions

- Email accounts support standard IMAP and SMTP protocols
- System monitors only the INBOX folder of the IMAP account; emails in other folders (Sent, Drafts, custom folders) are ignored
- ImageMagick and GhostScript are available and properly configured within the Docker container
- PDF files are not password-protected unless specified in edge cases
- Network connectivity to email servers is generally reliable but may experience intermittent TLS negotiation failures
- Sufficient disk space and memory are available for temporary file storage during conversion
- SMTP server and email infrastructure can handle large emails with multiple high-resolution PNG attachments (application sends all images in a single email with no size limits)
- System processes emails sequentially (one at a time) in arrival order rather than in parallel to avoid resource exhaustion and race conditions
- Original PDF filenames are sanitized and included as prefix in generated PNG filenames with sequential numbering (e.g., invoice_pdf-001.png) to avoid collisions when multiple PDFs are processed
- Processed emails are deleted from the IMAP inbox immediately after successful reply, preventing reprocessing
- Logging output is minimal and focused only on critical errors; successful operations are not logged for performance and storage efficiency
- Email server connections prioritize availability over strict security: TLS/SSL is attempted first but unencrypted fallback is acceptable when encryption negotiation fails
- IMAP polling occurs at 60-second intervals with exponential backoff (60s → 120s → 240s → 480s → 900s capped) applied when connection failures occur
- Error notification emails include detailed technical information with stack traces and system context to facilitate debugging
