# Development

## Prerequisites

- Python 3.11+
- Docker 20.10+ and Docker Compose 1.29+
- Git

## Setup

```bash
# Clone repository
git clone https://github.com/Soneritics/png-from-pdf-extracter.git
cd png-from-pdf-extracter

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate          # Windows

# Install development dependencies
pip install -r requirements-dev.txt
```

### Dev Dependencies

| Package | Purpose |
|---------|---------|
| `pytest` (≥7.4, <8.0) | Test framework |
| `pytest-cov` (≥4.1, <5.0) | Coverage reporting |
| `ruff` (≥0.1, <1.0) | Linting and code quality |
| `pip-audit` (≥2.6, <3.0) | Security vulnerability scanning |

There are **no runtime dependencies** — `requirements.txt` is intentionally empty (all stdlib).

## Running Tests

```bash
# Run all tests (with coverage enabled by default via pyproject.toml)
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/

# Run a single test file
pytest tests/unit/test_config.py

# Run a single test function
pytest tests/unit/test_config.py::test_config_validates_ports

# Run tests matching a pattern
pytest -k "test_whitelist"

# Coverage report (HTML)
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in your browser
```

### Coverage Requirements

| Scope | Minimum |
|-------|---------|
| Overall | ≥ 60% |
| Critical paths (PDF conversion, email processing, error handling) | ≥ 80% |

Coverage thresholds are enforced via `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = ["--cov=src", "--cov-fail-under=60"]
```

### Test Structure

- **Unit tests** (`tests/unit/`): Test individual functions and methods in isolation.
- **Integration tests** (`tests/integration/`): Test service interactions with mocking.
- **Contract tests** (`tests/contract/`): Verify external tool behavior (ImageMagick, SMTP).

## Linting

```bash
# Check code quality
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

Ruff is configured in `pyproject.toml` with a 100-character line length targeting Python 3.11.

## Security Audit

```bash
pip-audit
```

Expected result: zero vulnerabilities (no runtime dependencies).

## Code Style

- **Line length**: 100 characters
- **Import sorting**: stdlib → third-party → local (alphabetical)
- **Type hints**: Required on all function signatures
- **Docstrings**: Google style, required for all public classes and methods

### Example

```python
"""Module docstring."""

import os
from pathlib import Path

from src.models.email_message import EmailMessage


class MyService:
    """Service description.

    Attributes:
        config: Configuration instance
    """

    def __init__(self, config: Configuration) -> None:
        """Initialize service.

        Args:
            config: Configuration instance

        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config

    def process(self, data: bytes) -> str:
        """Process binary data.

        Args:
            data: Binary input data

        Returns:
            Processed string result

        Raises:
            ProcessingError: If processing fails
        """
        return "result"
```

## Test Naming

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

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
test: Add tests
refactor: Refactor code
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full pull request checklist and workflow.

### Quick Checklist

- [ ] All tests pass (`pytest`)
- [ ] Coverage meets thresholds (`pytest --cov=src`)
- [ ] Linting passes (`ruff check src/ tests/`)
- [ ] Security audit passes (`pip-audit`)
- [ ] Type hints on all new functions
- [ ] Docstrings on all public APIs
- [ ] Documentation updated if user-facing
