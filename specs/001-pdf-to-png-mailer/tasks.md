# Tasks: PDF-to-PNG Email Processor

**Feature Branch**: `001-pdf-to-png-mailer`  
**Input**: Design documents from `/specs/001-pdf-to-png-mailer/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Test-Driven Development (TDD) approach mandated per constitution. All tests MUST be written first and FAIL before implementation.

**Organization**: Tasks organized by user story to enable independent implementation and testing of each story.

---

## Format: `- [ ] [TaskID] [P?] [Story?] Description`

- **- [ ]**: Markdown checkbox (REQUIRED at start of every task)
- **[TaskID]**: Sequential task number (T001, T002, T003...)
- **[P]**: Parallelizable (different files, no dependencies) - OPTIONAL marker
- **[Story]**: User story label (US1, US2, US3, US4) - REQUIRED for user story phase tasks
- **Description**: Clear action with exact file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

**Tasks**:

- [X] T001 Create project structure with src/, tests/, and docs/ directories at repository root
- [X] T002 Initialize Python 3.11 project with pyproject.toml for tool configuration
- [X] T003 [P] Create requirements.txt (empty - all stdlib runtime dependencies per research.md)
- [X] T004 [P] Create requirements-dev.txt with pytest, pytest-cov, ruff, and pip-audit
- [X] T005 [P] Create .gitignore for Python (__pycache__, .pytest_cache, .env, *.pyc)
- [X] T006 [P] Create .env.example template with all required environment variables per contracts/service-contracts.md
- [X] T007 [P] Configure pyproject.toml with ruff linting rules (PEP 8, line length 100)
- [X] T008 [P] Configure pyproject.toml with pytest settings (test discovery, coverage thresholds ≥60% overall, ≥80% critical paths)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Tasks**:

- [X] T009 Create Dockerfile with Python 3.11-alpine, ImageMagick, and GhostScript per contracts/service-contracts.md
- [X] T010 [P] Create docker-compose.yml with restart: unless-stopped and environment variable passthrough per FR-016
- [X] T011 [P] Create src/__init__.py (empty module marker)
- [X] T012 [P] Create src/models/__init__.py (empty module marker)
- [X] T013 [P] Create src/services/__init__.py (empty module marker)
- [X] T014 [P] Create src/utils/__init__.py (empty module marker)
- [X] T015 [P] Create tests/__init__.py (empty module marker)
- [X] T016 [P] Create tests/unit/__init__.py (empty module marker)
- [X] T017 [P] Create tests/integration/__init__.py (empty module marker)
- [X] T018 [P] Create tests/contract/__init__.py (empty module marker)
- [X] T019 Create src/config.py with Configuration dataclass and environment variable loading per data-model.md and contracts/service-contracts.md
- [X] T020 Implement configuration validation (port ranges, regex compilation, required vars) in src/config.py
- [X] T021 Create src/utils/logging.py with error-only logging setup per FR-023, FR-024, NFR-001, NFR-002
- [X] T022 [P] Create src/utils/file_utils.py with sanitize_filename function per FR-008 and data-model.md
- [X] T023 [P] Create src/models/email_message.py with EmailMessage dataclass per data-model.md
- [X] T024 [P] Create src/models/pdf_attachment.py with PDFAttachment dataclass per data-model.md
- [X] T025 [P] Create src/models/png_image.py with PNGImage dataclass per data-model.md
- [X] T026 [P] Create src/models/processing_job.py with ProcessingJob dataclass and JobStatus enum per data-model.md

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Convert PDF to PNG Images via Email (Priority: P1) 🎯 MVP

**Goal**: End-to-end workflow - user sends PDF, receives PNG images via email (core functionality)

**Independent Test**: Send email with PDF attachment to monitored inbox, verify PNG images received back via email

### Tests for User Story 1 (TDD - Write FIRST, Ensure FAIL)

- [X] T027 [P] [US1] Contract test: ImageMagick CLI availability in tests/contract/test_imagemagick.py
- [X] T028 [P] [US1] Contract test: ImageMagick converts single-page PDF to 1920x1080 PNG at 300 DPI in tests/contract/test_imagemagick.py
- [X] T029 [P] [US1] Contract test: ImageMagick converts multi-page PDF with sequential numbering in tests/contract/test_imagemagick.py
- [X] T030 [P] [US1] Contract test: GhostScript availability for PDF pre-processing in tests/contract/test_ghostscript.py
- [X] T031 [P] [US1] Unit test: PDFConverterService.sanitize_filename removes special chars in tests/unit/test_pdf_converter.py
- [X] T032 [P] [US1] Unit test: PDFConverterService.sanitize_filename truncates to 50 chars in tests/unit/test_pdf_converter.py
- [X] T033 [P] [US1] Unit test: PDFConverterService raises PDFCorruptedError on malformed PDF in tests/unit/test_pdf_converter.py
- [X] T034 [P] [US1] Unit test: PDFConverterService raises PDFPasswordProtectedError on encrypted PDF in tests/unit/test_pdf_converter.py
- [X] T035 [P] [US1] Contract test: SMTPService sends reply with all PNG attachments in tests/contract/test_smtp_service.py
- [X] T036 [P] [US1] Contract test: SMTPService sends error notification with stack trace in tests/contract/test_smtp_service.py
- [X] T037 [P] [US1] Integration test: End-to-end email→PDF→PNG→reply flow in tests/integration/test_end_to_end.py
- [X] T038 [P] [US1] Integration test: Multiple PDFs in one email processed correctly in tests/integration/test_end_to_end.py

### Implementation for User Story 1

- [X] T039 [US1] Implement PDFConverterService.__init__ and convert_pdf_to_png in src/services/pdf_converter.py with ImageMagick subprocess calls per FR-004, FR-005, FR-006, FR-007, FR-008
- [X] T040 [US1] Implement PDFConverterService exception handling (PDFConversionError, PDFCorruptedError, PDFPasswordProtectedError) in src/services/pdf_converter.py
- [X] T041 [P] [US1] Implement SMTPService.__init__ and connect with TLS fallback per FR-025, FR-026 in src/services/smtp_service.py
- [X] T042 [US1] Implement SMTPService.send_reply_with_attachments with MIME multipart construction per FR-009, FR-010 in src/services/smtp_service.py
- [X] T043 [US1] Implement SMTPService.send_error_notification with detailed stack trace per FR-012, FR-013 in src/services/smtp_service.py
- [X] T044 [US1] Implement SMTPService.disconnect in src/services/smtp_service.py
- [X] T045 [P] [US1] Implement IMAPService.__init__ and connect with TLS fallback per FR-025, FR-026 in src/services/imap_service.py
- [X] T046 [US1] Implement IMAPService.fetch_unseen_messages parsing EmailMessage from IMAP per FR-001 in src/services/imap_service.py
- [X] T047 [US1] Implement IMAPService.delete_message using IMAP store +FLAGS \\Deleted per FR-021 in src/services/imap_service.py
- [X] T048 [US1] Implement IMAPService.disconnect in src/services/imap_service.py
- [X] T049 [US1] Implement JobProcessorService.__init__ with dependency injection of all services in src/services/job_processor.py
- [X] T050 [US1] Implement JobProcessorService.process_next_email orchestrating full workflow per FR-003, FR-004, FR-009, FR-021 in src/services/job_processor.py
- [X] T051 [US1] Add error handling and error email sending to JobProcessorService.process_next_email per FR-012, FR-013 in src/services/job_processor.py
- [X] T052 [US1] Create src/main.py entry point that loads config, initializes services, and calls JobProcessorService.process_next_email in loop per FR-001
- [X] T053 [US1] Add minimal error-only logging to JobProcessorService per FR-023, FR-024, NFR-001, NFR-002 in src/services/job_processor.py

**Checkpoint**: User Story 1 complete - Core PDF→PNG email workflow functional and independently testable

---

## Phase 4: User Story 2 - Access Control via Whitelist (Priority: P2)

**Goal**: Security - only whitelisted senders can trigger PDF processing

**Independent Test**: Send emails from both whitelisted and non-whitelisted addresses, verify only whitelisted emails processed

### Tests for User Story 2 (TDD - Write FIRST, Ensure FAIL)

- [X] T054 [P] [US2] Unit test: WhitelistService matches valid address in tests/unit/test_whitelist_service.py
- [X] T055 [P] [US2] Unit test: WhitelistService rejects invalid address in tests/unit/test_whitelist_service.py
- [X] T056 [P] [US2] Unit test: WhitelistService pattern '.*@company\\.com' matches user@company.com in tests/unit/test_whitelist_service.py
- [X] T057 [P] [US2] Unit test: WhitelistService pattern '.*@company\\.com' rejects user@external.com in tests/unit/test_whitelist_service.py
- [X] T058 [P] [US2] Unit test: WhitelistService raises ValueError on invalid regex in tests/unit/test_whitelist_service.py
- [X] T059 [P] [US2] Integration test: Whitelisted sender processed, non-whitelisted ignored in tests/integration/test_whitelist_flow.py

### Implementation for User Story 2

- [X] T060 [US2] Implement WhitelistService.__init__ with regex compilation and validation per FR-019 in src/services/whitelist_service.py
- [X] T061 [US2] Implement WhitelistService.is_whitelisted with regex matching per FR-002 in src/services/whitelist_service.py
- [X] T062 [US2] Integrate WhitelistService into JobProcessorService.process_next_email per FR-002, FR-014 in src/services/job_processor.py
- [X] T063 [US2] Add sender validation before PDF extraction in JobProcessorService.process_next_email in src/services/job_processor.py
- [X] T064 [US2] Ensure non-whitelisted emails are ignored (no processing, no response) per FR-014 in src/services/job_processor.py

**Checkpoint**: User Story 2 complete - Whitelist security functional and independently testable

---

## Phase 5: User Story 3 - CC Recipients on Response Emails (Priority: P3)

**Goal**: Convenience - additional recipients can be CC'd on reply emails

**Independent Test**: Configure CC addresses, process PDF, verify CC recipients included in reply email

### Tests for User Story 3 (TDD - Write FIRST, Ensure FAIL)

- [X] T065 [P] [US3] Contract test: SMTPService includes CC recipients in reply email headers in tests/contract/test_smtp_service.py
- [X] T066 [P] [US3] Contract test: SMTPService handles multiple semicolon-separated CC addresses in tests/contract/test_smtp_service.py
- [X] T067 [P] [US3] Contract test: SMTPService handles empty CC list gracefully in tests/contract/test_smtp_service.py
- [X] T068 [P] [US3] Integration test: CC recipients receive reply email copies in tests/integration/test_cc_flow.py

### Implementation for User Story 3

- [X] T069 [US3] Update SMTPService.send_reply_with_attachments to include CC addresses in MIME headers and recipient list per FR-011, FR-020 in src/services/smtp_service.py
- [X] T070 [US3] Update JobProcessorService.process_next_email to pass CC addresses from config to SMTPService in src/services/job_processor.py
- [X] T071 [US3] Add validation for CC addresses in Configuration (semicolon-separated parsing) per FR-020 in src/config.py

**Checkpoint**: User Story 3 complete - CC functionality working and independently testable

---

## Phase 6: User Story 4 - Error Notification (Priority: P2)

**Goal**: User experience - users notified when processing fails with detailed error information

**Independent Test**: Send corrupted/invalid PDFs, verify error emails sent with descriptive messages and stack traces

### Tests for User Story 4 (TDD - Write FIRST, Ensure FAIL)

- [X] T072 [P] [US4] Integration test: Corrupted PDF triggers error email with stack trace in tests/integration/test_error_notification.py
- [X] T073 [P] [US4] Integration test: Password-protected PDF triggers error email with technical details in tests/integration/test_error_notification.py
- [X] T074 [P] [US4] Integration test: Zero-page PDF triggers error email with descriptive message in tests/integration/test_error_notification.py
- [X] T075 [P] [US4] Integration test: Error email includes system context (email subject, PDF filenames) per FR-013 in tests/integration/test_error_notification.py

### Implementation for User Story 4

- [X] T076 [US4] Enhance SMTPService.send_error_notification to include system context dict per FR-013 in src/services/smtp_service.py
- [X] T077 [US4] Update JobProcessorService error handling to capture full exception traceback and context in src/services/job_processor.py
- [X] T078 [US4] Ensure error emails sent for all processing failures (PDF conversion, SMTP send failures) per FR-012 in src/services/job_processor.py
- [X] T079 [US4] Verify original email NOT deleted when processing fails per NFR-007 in src/services/job_processor.py

**Checkpoint**: User Story 4 complete - Error notification functional and independently testable

---

## Phase 7: Reliability & Connection Management

**Goal**: Production-ready daemon with exponential backoff and continuous operation

**Independent Test**: Simulate IMAP connection failures, verify exponential backoff and retry behavior

### Tests (TDD - Write FIRST, Ensure FAIL)

- [X] T080 [P] Contract test: IMAPService exponential backoff schedule (60s, 120s, 240s up to 900s) per FR-027 in tests/contract/test_imap_service.py
- [X] T081 [P] Contract test: IMAPService logs every connection failure per FR-028 in tests/contract/test_imap_service.py
- [X] T082 [P] Contract test: IMAPService retries indefinitely until connection restored per NFR-011 in tests/contract/test_imap_service.py
- [X] T083 [P] Integration test: Daemon continues running after IMAP connection restored in tests/integration/test_daemon_resilience.py

### Implementation

- [X] T084 Implement IMAPService.connect_with_backoff with exponential backoff per FR-027 in src/services/imap_service.py
- [X] T085 Add connection failure logging to IMAPService.connect_with_backoff per FR-028, NFR-001a in src/services/imap_service.py
- [X] T086 Implement JobProcessorService.run_daemon with continuous polling loop per FR-001, FR-016 in src/services/job_processor.py
- [X] T087 Integrate IMAPService.connect_with_backoff into JobProcessorService.run_daemon per FR-027 in src/services/job_processor.py
- [X] T088 Ensure sequential email processing (one at a time) in JobProcessorService.run_daemon per FR-022, NFR-009 in src/services/job_processor.py
- [X] T089 Update src/main.py to call JobProcessorService.run_daemon instead of manual loop

**Checkpoint**: Daemon reliability complete - Continuous operation with connection recovery

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Production readiness - documentation, validation, and final quality checks

**Tasks**:

- [ ] T090 [P] Create README.md with project overview, quick start, and links to quickstart.md
- [ ] T091 [P] Add docstrings to all public classes and methods in src/models/, src/services/, src/utils/
- [ ] T092 [P] Run ruff linting and fix all warnings across src/ and tests/
- [ ] T093 [P] Run pytest with coverage report, verify ≥60% overall, ≥80% critical paths per constitution
- [ ] T094 [P] Run pip-audit to check for security vulnerabilities (should be zero with all-stdlib approach)
- [ ] T095 [P] Validate docker build succeeds: `docker build -t pdf-to-png-mailer .`
- [ ] T096 [P] Validate docker-compose up succeeds with .env.example template
- [ ] T097 Test quickstart.md guide end-to-end: setup, build, run, send test email, verify PNG reply
- [ ] T098 [P] Add inline comments for complex logic (exponential backoff, MIME construction, ImageMagick subprocess)
- [ ] T099 [P] Create CONTRIBUTING.md with development setup and testing guidelines
- [ ] T100 Final constitution gate check: tests passing, coverage met, linting clean, documentation complete

**Checkpoint**: Feature complete and production-ready

---

## Dependencies & Execution Order

### Phase Dependencies

1. **Setup (Phase 1)**: No dependencies - can start immediately
2. **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
3. **User Story 1 (Phase 3)**: Depends on Foundational completion - Core MVP functionality
4. **User Story 2 (Phase 4)**: Depends on Foundational completion - Can run parallel to US1 with different developer
5. **User Story 3 (Phase 5)**: Depends on US1 (uses SMTPService) - Extends email sending
6. **User Story 4 (Phase 6)**: Depends on US1 (uses error handling) - Enhances error reporting
7. **Reliability (Phase 7)**: Depends on US1, US2 - Adds daemon resilience
8. **Polish (Phase 8)**: Depends on all previous phases - Final quality pass

### User Story Dependencies

```
Setup → Foundational → [US1, US2] → [US3, US4] → Reliability → Polish
                          ↓     ↓        ↓     ↓
                          │     │        │     └─ Error emails depend on US1 email sending
                          │     │        └─ CC depends on US1 email sending
                          │     └─ Independent security layer
                          └─ Core functionality (MVP)
```

**Key Insights**:
- **US1 (P1)** is the foundation - must complete first for MVP
- **US2 (P2)** can be developed in parallel with US1 by different developer (touches different files)
- **US3 (P3)** and **US4 (P2)** both extend US1, but are independent of each other
- **Reliability (Phase 7)** builds on US1 + US2 integration

### Critical Path (MVP - Minimum Viable Product)

**Fastest path to working prototype**:
```
T001-T008 (Setup) → T009-T026 (Foundational) → T027-T053 (US1) → T097 (Quickstart validation)
```

**Result**: Basic PDF→PNG email processor working end-to-end without security/CC/advanced error handling

### Within Each User Story

**User Story 1 (US1)**:
- Tests T027-T038 can run in parallel (all marked [P])
- Implementation: T039-T040 (PDF) ∥ T041-T044 (SMTP) ∥ T045-T048 (IMAP) → T049-T051 (Orchestration) → T052-T053 (Main)

**User Story 2 (US2)**:
- Tests T054-T059 can run in parallel (all marked [P])
- Implementation: T060-T061 (WhitelistService) → T062-T064 (Integration)

**User Story 3 (US3)**:
- Tests T065-T068 can run in parallel (all marked [P])
- Implementation: T069-T071 (linear, sequential modifications)

**User Story 4 (US4)**:
- Tests T072-T075 can run in parallel (all marked [P])
- Implementation: T076-T079 (linear, sequential modifications)

**Reliability (Phase 7)**:
- Tests T080-T083 can run in parallel (all marked [P])
- Implementation: T084-T089 (linear, builds on each other)

### Parallel Opportunities

**Maximum parallelization** (with 4+ developers):

1. **After Foundational phase completes**:
   - Developer A: US1 implementation (T039-T053)
   - Developer B: US2 implementation (T060-T064)
   - Developer C: US1 tests (T027-T038)
   - Developer D: US2 tests (T054-T059)

2. **Within a phase**:
   - All tasks marked [P] can execute simultaneously
   - Example US1: T027, T028, T029, T030 (4 contract tests in parallel)
   - Example Setup: T003, T004, T005, T006, T007, T008 (6 config tasks in parallel)

3. **Polish phase**:
   - All T090-T096 and T098-T099 can run in parallel (different files/concerns)

---

## Parallel Execution Examples

### Example 1: User Story 1 Tests (All Parallel)

```bash
# Launch all US1 tests together:
copilot task "Contract test: ImageMagick CLI availability in tests/contract/test_imagemagick.py"
copilot task "Contract test: ImageMagick converts single-page PDF to 1920x1080 PNG at 300 DPI in tests/contract/test_imagemagick.py"
copilot task "Contract test: ImageMagick converts multi-page PDF with sequential numbering in tests/contract/test_imagemagick.py"
copilot task "Contract test: GhostScript availability for PDF pre-processing in tests/contract/test_ghostscript.py"
copilot task "Unit test: PDFConverterService.sanitize_filename removes special chars in tests/unit/test_pdf_converter.py"
# ... (continue with remaining US1 tests)
```

### Example 2: User Story 1 Services (Parallel Implementation)

```bash
# Launch all US1 service implementations together (different files):
copilot task "Implement PDFConverterService in src/services/pdf_converter.py with ImageMagick subprocess calls per FR-004, FR-005, FR-006, FR-007, FR-008"
copilot task "Implement SMTPService in src/services/smtp_service.py with TLS fallback and reply email sending per FR-025, FR-026, FR-009, FR-010"
copilot task "Implement IMAPService in src/services/imap_service.py with TLS fallback and email fetching per FR-025, FR-026, FR-001"
```

### Example 3: Setup Phase (Maximum Parallelization)

```bash
# After T001-T002 complete, launch all config tasks:
copilot task "Create requirements.txt (empty - all stdlib runtime dependencies)"
copilot task "Create requirements-dev.txt with pytest, pytest-cov, ruff, and pip-audit"
copilot task "Create .gitignore for Python (__pycache__, .pytest_cache, .env, *.pyc)"
copilot task "Create .env.example template with all required environment variables"
copilot task "Configure pyproject.toml with ruff linting rules (PEP 8, line length 100)"
copilot task "Configure pyproject.toml with pytest settings (test discovery, coverage thresholds)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**Goal**: Get to working demo as fast as possible

1. ✅ Complete Phase 1: Setup (T001-T008)
2. ✅ Complete Phase 2: Foundational (T009-T026)
3. ✅ Complete Phase 3: User Story 1 (T027-T053)
4. **STOP and VALIDATE**: Run quickstart.md, send test PDF, verify PNG reply
5. ✅ Deploy/demo if ready (US1 is the complete core workflow)

**Deliverable**: Working PDF→PNG email processor without security/CC/advanced features

---

### Incremental Delivery (Add Stories One by One)

**Goal**: Deliver value progressively, each story adds functionality

1. ✅ Complete Setup + Foundational → Foundation ready
2. ✅ Add User Story 1 → Test independently → **Deploy/Demo (MVP!)**
3. ✅ Add User Story 2 → Test independently → **Deploy/Demo (MVP + Security)**
4. ✅ Add User Story 3 → Test independently → **Deploy/Demo (MVP + Security + CC)**
5. ✅ Add User Story 4 → Test independently → **Deploy/Demo (Full Error Handling)**
6. ✅ Add Reliability → Test independently → **Deploy/Demo (Production-Ready)**
7. ✅ Polish → Final validation → **Deploy/Demo (Release Candidate)**

**Benefit**: Each phase delivers a shippable increment

---

### Parallel Team Strategy (4 Developers)

**Goal**: Maximum velocity with multiple developers

**Phase 1-2**: Team works together on Setup + Foundational (prerequisite for all stories)

**Phase 3-4** (once Foundational complete):
- **Developer A**: User Story 1 tests (T027-T038)
- **Developer B**: User Story 1 implementation (T039-T053)
- **Developer C**: User Story 2 tests (T054-T059)
- **Developer D**: User Story 2 implementation (T060-T064)

**Phase 5-6** (once US1 complete):
- **Developer A**: User Story 3 (T065-T071)
- **Developer B**: User Story 4 (T072-T079)
- **Developer C**: Reliability tests (T080-T083)
- **Developer D**: Reliability implementation (T084-T089)

**Phase 8**: All developers work on Polish tasks in parallel (T090-T100)

---

## Validation Checkpoints

### Checkpoint 1: Foundation Ready
**After T026**: Verify project structure, models, config loading, Docker build succeeds

### Checkpoint 2: User Story 1 Complete (MVP)
**After T053**: 
- Send test email with PDF from ANY address
- Verify PNG images received back
- This is the MINIMUM VIABLE PRODUCT

### Checkpoint 3: Security Enabled
**After T064**:
- Configure whitelist pattern
- Send from whitelisted + non-whitelisted addresses
- Verify only whitelisted processed

### Checkpoint 4: CC Functionality
**After T071**:
- Configure CC addresses
- Send test PDF
- Verify CC recipients receive copies

### Checkpoint 5: Error Handling Complete
**After T079**:
- Send corrupted PDF
- Verify error email with stack trace received

### Checkpoint 6: Production Ready
**After T089**:
- Run daemon continuously for 5+ minutes
- Simulate IMAP connection failure (disable network)
- Verify exponential backoff and recovery

### Checkpoint 7: Release Candidate
**After T100**:
- All tests passing (100%)
- Coverage ≥60% overall, ≥80% critical paths
- Linting clean (zero warnings)
- Documentation complete
- Quickstart guide validated

---

## Notes

- **[P] marker**: Tasks with [P] operate on different files with no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability and independent testing
- **TDD mandate**: All test tasks MUST be written FIRST and FAIL before implementation tasks
- **Commit strategy**: Commit after each task or logical group (e.g., all tests for a service, then the service implementation)
- **Independent stories**: Each user story should be completable and testable independently after Foundational phase
- **Stop at any checkpoint**: Validate story independently before proceeding to next priority

---

## Task Summary

- **Total tasks**: 100 tasks
- **Setup phase**: 8 tasks
- **Foundational phase**: 18 tasks
- **User Story 1 (P1)**: 27 tasks (12 tests + 15 implementation)
- **User Story 2 (P2)**: 11 tasks (6 tests + 5 implementation)
- **User Story 3 (P3)**: 7 tasks (4 tests + 3 implementation)
- **User Story 4 (P2)**: 8 tasks (4 tests + 4 implementation)
- **Reliability**: 10 tasks (4 tests + 6 implementation)
- **Polish**: 11 tasks

**Test coverage**: 38 test tasks total (38% of all tasks - TDD approach)

**Parallel opportunities**: 63 tasks marked [P] can execute in parallel with other [P] tasks in same phase

**MVP scope**: Tasks T001-T053 (53 tasks) deliver working PDF→PNG email processor

**Critical path duration** (sequential execution): ~100 task-hours → ~2.5 weeks for solo developer
**Optimized duration** (4 developers, parallel execution): ~35 task-hours → ~1 week

---

**Version**: 1.0.0  
**Generated**: 2025-01-21  
**Ready for execution**: ✅ All design artifacts validated, tasks are actionable and dependency-ordered
