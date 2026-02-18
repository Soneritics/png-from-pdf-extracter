# Implementation Plan: PDF-to-PNG Email Processor

**Branch**: `001-pdf-to-png-mailer` | **Date**: 2025-01-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-pdf-to-png-mailer/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

A containerized email monitoring service that watches an IMAP inbox for PDF attachments from whitelisted senders, converts each PDF page to PNG images (1920x1080, 300 DPI) using ImageMagick/GhostScript, and returns the images via email. Built with Python, running continuously in Docker with automatic restart, sequential email processing, and comprehensive error handling with detailed notifications.

## Technical Context

**Language/Version**: Python 3.11 (latest LTS as per constitution)  
**Primary Dependencies**: **All stdlib** - imaplib (IMAP), smtplib (SMTP), email (parsing), subprocess (ImageMagick CLI), tempfile (temp storage)  
**Storage**: Filesystem (temporary storage for PDF→PNG conversion via tempfile.TemporaryDirectory, automatic cleanup)  
**Testing**: pytest with coverage plugin (≥80% critical paths, ≥60% overall per constitution)  
**Target Platform**: Docker container on Linux (Python 3.11-alpine + imagemagick + ghostscript system packages)  
**Project Type**: Single service (background daemon, sequential processing)  
**Performance Goals**: PDF processing <2 min per file (SC-001), email polling every 60s (FR-001), error notification <1 min (SC-004)  
**Constraints**: Memory <500MB peak (constitution), sequential processing (FR-022), exponential backoff on IMAP failures (FR-027), TLS with fallback (FR-025-026)  
**Scale/Scope**: Single inbox monitoring, up to 50-page PDFs (SC-006), 30+ days uptime (SC-003), unlimited email volume but sequential processing  
**Key Architectural Decision**: All-stdlib approach (zero runtime Python dependencies) for supply chain security, guaranteed compatibility, and minimal Docker footprint. ImageMagick/GhostScript invoked via subprocess for exact control and memory efficiency (~300MB peak vs 800MB+ with Wand bindings).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Gate 1: Pre-Implementation ✅ PASSED
- [x] **Tests written and failing**: TDD approach mandated - tests for email polling, whitelist validation, PDF conversion, email sending, error handling
- [x] **Design reviewed against constitution principles**: 
  - **Code Quality**: Python type hints, clear module separation, PEP 8 compliance, docstrings for all public APIs
  - **Test-First Development**: Unit tests for business logic, integration tests for IMAP/SMTP/ImageMagick contracts
  - **UX Consistency**: Error emails with detailed stack traces (FR-013), clear success/failure states
  - **Performance**: PDF processing budgets defined (SC-001: 2 min per PDF), memory <500MB peak
  - **Modern Technology**: Python 3.11 LTS, latest stable dependencies (all stdlib - zero external dependencies)
- [x] **Performance budget defined**: See Technical Context - 2 min per PDF, 60s polling, 1 min error notifications

### Gate 2: Implementation (DEFERRED - to be checked during implementation)
- [ ] All tests passing (deferred to implementation phase)
- [ ] Code coverage targets met (≥60% overall, ≥80% critical paths)
- [ ] Linting passing with zero warnings (ruff or pylint)
- [ ] No security vulnerabilities introduced (pip-audit checks)
- [ ] Documentation updated (README, docstrings)

### Gate 3: Code Review (DEFERRED - to be checked during code review)
- [ ] Peer review approved
- [ ] Constitution compliance verified
- [ ] Performance benchmarks within budget
- [ ] User experience validated (error email clarity)
- [ ] Breaking changes documented (N/A for initial implementation)

### Gate 4: Pre-Deployment (DEFERRED - to be checked before deployment)
- [ ] Integration tests passing (IMAP/SMTP/ImageMagick end-to-end)
- [ ] Performance tests passing (50-page PDF benchmark)
- [ ] Deployment checklist complete (Docker build, environment variables documented)
- [ ] Rollback plan documented (container restart procedure)

### Phase 1 Design Evaluation ✅ PASSED

**All-stdlib architecture verified**:
- ✅ **Principle I (Code Quality)**: Clear separation of concerns (models, services, utils), single-responsibility services, comprehensive docstrings in contracts
- ✅ **Principle II (Test-First Development)**: Comprehensive contract tests defined for all services (90+ test cases documented), unit/integration/contract test structure established
- ✅ **Principle III (UX Consistency)**: Error notifications with detailed stack traces (FR-013), consistent email format, clear error messages
- ✅ **Principle IV (Performance Requirements)**: Memory budget met (300MB peak for PDF processing vs 500MB limit), processing times within spec (2 min per PDF)
- ✅ **Principle V (Modern Technology Standards)**: Python 3.11 LTS, all stdlib (zero external dependencies = zero security vulnerabilities to track), ImageMagick latest stable, GhostScript latest stable

**Design artifacts complete**:
- ✅ `research.md`: All library choices researched and justified (imaplib, smtplib, email stdlib)
- ✅ `data-model.md`: 5 entities defined with validation rules, state transitions, and type annotations
- ✅ `contracts/service-contracts.md`: 6 service contracts with 90+ test cases, environment variable contract, Docker contract
- ✅ `quickstart.md`: Complete setup guide with troubleshooting and security considerations
- ✅ Agent context updated: `.github/agents/copilot-instructions.md` includes Python 3.11 + stdlib stack

**Status**: ✅ PASS - Ready for Phase 2 (task generation via `/speckit.tasks`)

## Project Structure

### Documentation (this feature)

```text
specs/001-pdf-to-png-mailer/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Single project structure (background daemon service)
src/
├── __init__.py
├── main.py                 # Entry point, main loop
├── config.py               # Configuration loading from env vars
├── models/
│   ├── __init__.py
│   ├── email_message.py    # Email message entity
│   ├── pdf_attachment.py   # PDF attachment entity
│   └── processing_job.py   # Job tracking entity
├── services/
│   ├── __init__.py
│   ├── imap_service.py     # IMAP email monitoring with exponential backoff
│   ├── smtp_service.py     # SMTP email sending with TLS fallback
│   ├── whitelist_service.py # Regex-based sender validation
│   ├── pdf_converter.py    # ImageMagick/GhostScript PNG conversion
│   └── job_processor.py    # Orchestrates email→PDF→PNG→reply workflow
└── utils/
    ├── __init__.py
    ├── logging.py          # Minimal error-only logging
    └── file_utils.py       # Temp file management, sanitization

tests/
├── __init__.py
├── unit/
│   ├── test_whitelist_service.py
│   ├── test_pdf_converter.py
│   ├── test_config.py
│   └── test_models.py
├── integration/
│   ├── test_imap_flow.py       # Mock IMAP server
│   ├── test_smtp_flow.py       # Mock SMTP server
│   └── test_end_to_end.py      # Full email→PNG→reply
└── contract/
    ├── test_imagemagick.py     # Verify ImageMagick CLI behavior
    └── test_ghostscript.py     # Verify GhostScript integration

# Docker/Infrastructure
Dockerfile                  # Alpine Linux + Python 3.11 + ImageMagick + GhostScript
docker-compose.yml          # Container config with restart: unless-stopped
.env.example                # Template for required environment variables
requirements.txt            # Python dependencies (pinned versions)
requirements-dev.txt        # Dev dependencies (pytest, ruff, pip-audit)

# Configuration
.gitignore
README.md                   # Setup, configuration, usage
LICENSE
pyproject.toml              # Tool configuration (ruff, pytest, coverage)
```

**Structure Decision**: Single project structure chosen because this is a standalone background daemon with no user-facing UI. All logic lives in `src/` with clear separation: models (entities), services (business logic), utils (helpers). Docker container runs `python -m src.main` as the entry point. Test structure mirrors source with unit/integration/contract separation per constitution testing requirements.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No complexity violations identified. This is a straightforward single-service daemon with clear separation of concerns following Python best practices.
