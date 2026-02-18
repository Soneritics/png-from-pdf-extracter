# Contributing to PDF-to-PNG Email Processor

Thank you for your interest in contributing! This document provides guidelines for development and testing.

## Development Setup

### Prerequisites

- Python 3.11+
- Docker 20.10+ and Docker Compose 1.29+
- Git

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd png-from-pdf-extracter

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (if available)
# pre-commit install
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow these principles:
- **Test-first (TDD)**: Write tests before implementation
- **Type hints**: Use Python 3.11 type annotations
- **Docstrings**: Document all public classes and methods
- **PEP 8**: Follow Python style guide (enforced by ruff)

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage (must be ≥60% overall, ≥80% critical paths)
pytest --cov=src --cov-report=term-missing

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

### 4. Lint Code

```bash
# Check code quality
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

### 5. Security Audit

```bash
# Check for vulnerabilities (should be zero with all-stdlib approach)
pip-audit
```

### 6. Commit Changes

```bash
git add .
git commit -m "Brief description of changes"

# Follow conventional commits format:
# feat: Add new feature
# fix: Fix bug
# docs: Update documentation
# test: Add tests
# refactor: Refactor code
```

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Style

### Python Guidelines

- **Line length**: 100 characters (enforced by ruff)
- **Import sorting**: Alphabetical, stdlib → third-party → local
- **Type hints**: Required for all function signatures
- **Docstrings**: Google style, required for public APIs

### Example

```python
"""Module docstring."""

import os
from pathlib import Path

from src.models.email_message import EmailMessage


class MyService:
    """Service for doing something.

    Attributes:
        config: Configuration instance
    """

    def __init__(self, config: Configuration) -> None:
        """Initialize service with configuration.

        Args:
            config: Configuration instance

        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config

    def process_data(self, data: bytes) -> str:
        """Process binary data and return string result.

        Args:
            data: Binary input data

        Returns:
            Processed string result

        Raises:
            ProcessingError: If data processing fails
        """
        # Implementation
        return "result"
```

## Testing Guidelines

### Test Structure

- **Unit tests**: Test individual functions/methods in isolation
- **Integration tests**: Test service interactions (with mocking)
- **Contract tests**: Test external dependencies (ImageMagick, SMTP)

### Test Naming

```python
def test_function_does_something_under_condition():
    """Brief description of what is tested."""
    # Arrange
    service = MyService(config)

    # Act
    result = service.do_something()

    # Assert
    assert result == expected_value
```

### Coverage Requirements

- **Overall**: ≥60% coverage
- **Critical paths**: ≥80% coverage (PDF conversion, email processing, error handling)

### Running Specific Tests

```bash
# Run single test file
pytest tests/unit/test_config.py

# Run single test function
pytest tests/unit/test_config.py::test_config_validates_ports

# Run tests matching pattern
pytest -k "test_whitelist"
```

## Documentation

### Code Documentation

- All public classes and methods must have docstrings
- Use Google-style docstrings
- Include Args, Returns, Raises sections

### Architecture Documentation

When adding new features:
1. Update [specs/001-pdf-to-png-mailer/spec.md](specs/001-pdf-to-png-mailer/spec.md) if requirements change
2. Update [specs/001-pdf-to-png-mailer/plan.md](specs/001-pdf-to-png-mailer/plan.md) if architecture changes
3. Update [specs/001-pdf-to-png-mailer/data-model.md](specs/001-pdf-to-png-mailer/data-model.md) if entities change
4. Update [README.md](README.md) if user-facing features change

## Pull Request Checklist

Before submitting a PR, ensure:

- [ ] All tests pass (`pytest`)
- [ ] Code coverage meets requirements (`pytest --cov=src`)
- [ ] Linting passes (`ruff check src/ tests/`)
- [ ] Security audit passes (`pip-audit`)
- [ ] Documentation updated (README, docstrings, specs)
- [ ] Type hints added to all new functions
- [ ] Commit messages follow conventional commits format
- [ ] Branch is up to date with main

## Constitution Compliance

This project follows constitution principles:

### Principle I: Code Quality
- Clear separation of concerns (models, services, utils)
- Single-responsibility services
- Comprehensive documentation

### Principle II: Test-First Development
- All features must have tests written FIRST
- Tests must FAIL before implementation
- Unit, integration, and contract tests required

### Principle III: UX Consistency
- Error messages must be clear and actionable
- Error emails must include detailed stack traces
- Consistent email format

### Principle IV: Performance Requirements
- PDF processing < 2 min per file
- Memory usage < 500MB peak
- Email polling every 60s

### Principle V: Modern Technology Standards
- Python 3.11 LTS
- All stdlib (zero runtime dependencies)
- Latest stable system tools (ImageMagick, GhostScript)

## Common Issues

### Virtual Environment Issues

```bash
# Deactivate and recreate venv
deactivate
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Import Errors

Ensure PYTHONPATH includes project root:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Docker Build Failures

```bash
# Clear Docker cache
docker-compose build --no-cache

# Check Docker logs
docker-compose logs
```

## Questions?

- Open a GitHub issue with the "question" label
- Check existing issues and documentation first
- Provide minimal reproducible example if reporting a bug

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing!** 🎉
