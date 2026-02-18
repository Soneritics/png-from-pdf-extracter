# Copilot Instructions

## Project Overview

**png-from-pdf-extracter** is a tool for extracting PNG images from PDF files. The project is in early stages — no source code exists yet.

## Development Workflow

This repository uses [Speckit](https://github.com/speckit) for spec-driven development. The workflow is:

1. `/speckit.specify` — Create a feature specification from a natural language description
2. `/speckit.clarify` — Identify underspecified areas and refine the spec
3. `/speckit.plan` — Generate a technical implementation plan
4. `/speckit.tasks` — Break the plan into dependency-ordered tasks
5. `/speckit.implement` — Execute all tasks from `tasks.md`

Supporting commands: `/speckit.constitution`, `/speckit.checklist`, `/speckit.analyze`, `/speckit.taskstoissues`.

Key files per feature live under a `specs/` directory with: `spec.md`, `plan.md`, `tasks.md`, and optional `checklists/`, `contracts/`, `research.md`.

## Speckit Conventions

- Specs describe **what** and **why**, never **how** (no tech stack, APIs, or code structure)
- The constitution (`.specify/memory/constitution.md`) defines project principles — check it before making architectural decisions (it may still be a template if not yet ratified)
- Scripts live in `.specify/scripts/powershell/` and are pre-approved for terminal execution
- Feature branches follow the pattern `{number}-{short-name}` (e.g., `1-pdf-extraction`)
