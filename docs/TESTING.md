# Testing Guide

## Tech Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **pytest** | 8.0+ | Test framework |
| **pytest-mock** | 3.12+ | Mocking utilities |
| **importlib.reload** | - | For modules with env vars at import time |

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest -v

# Run specific module
pytest src/video_transcribe/test_config.py -v

# Run specific test
pytest src/video_transcribe/test_config.py::TestValidateConfig::test_validate_chunk_overlap_negative_raises -v

# Run with markers (when implemented)
pytest -m unit -v
pytest -m integration -v

# Run with coverage (optional)
pytest --cov=src --cov-report=term-missing
```

## Test Structure

```
src/video_transcribe/
├── config.py
├── test_config.py          # Co-located tests
├── audio/
│   ├── converter.py
│   ├── chunker.py
│   └── test_chunker.py     # Future
├── transcribe/
│   ├── merger.py
│   └── test_merger.py      # Future
└── postprocess/
    ├── filename.py
    └── test_filename.py    # Future

tests/
├── __init__.py             # Package marker
└── conftest.py             # Shared fixtures
```

**Co-location rationale:** Tests next to source code are easier to find during refactoring and keep implementation in context.

## Key Pattern: Testing Modules with Env Vars

### The Problem

`config.py` calls `load_dotenv()` at module import time (line 6). Environment variables are read once when the module loads, not on each access:

```python
# config.py
from dotenv import load_dotenv
load_dotenv()  # Reads .env file at import time

CHUNK_MAX_SIZE_MB: int = int(os.getenv("CHUNK_MAX_SIZE_MB", "20"))
```

This means setting `os.environ["CHUNK_MAX_SIZE_MB"]` has no effect after the module is already imported.

### The Solution

Use `importlib.reload()` after setting environment variables:

```python
def test_config_validation(monkeypatch):
    # 1. Set env var via monkeypatch (auto-restored after test)
    monkeypatch.setenv("CHUNK_MAX_SIZE_MB", "30")

    # 2. Reload module to pick up new value
    import video_transcribe.config
    config = importlib.reload(video_transcribe.config)

    # 3. Test with new config
    assert config.CHUNK_MAX_SIZE_MB == 30
```

### Why This Works

1. `monkeypatch.setenv()` sets the environment variable
2. `importlib.reload()` re-executes the entire module from scratch
3. The module reads the new env var values during reload
4. `monkeypatch` automatically restores original env after test
5. Each test starts with a clean state

## Fixtures (tests/conftest.py)

### `clean_config` Fixture

Resets all environment variables to get default config values:

```python
def test_with_defaults(clean_config):
    # Config has default values, no env vars set
    assert clean_config.CHUNK_MAX_SIZE_MB == 20  # Default
    assert clean_config.CHUNK_OVERLAP_SEC == 2.0
```

### `mock_env` Fixture

Fluent API for setting environment variables:

```python
def test_with_custom(mock_env):
    mock_env.setenv("CHUNK_OVERLAP_SEC", "1.5")
    config = mock_env.reload_config()
    assert config.CHUNK_OVERLAP_SEC == 1.5
```

### `mock_dotenv` Fixture

Prevents loading the actual `.env` file during tests:

```python
def test_without_dotenv(mock_dotenv):
    # load_dotenv is mocked, won't read real .env file
    from video_transcribe import config
    # Config uses defaults, not values from .env
```

## Writing New Tests

### Test File Template

```python
"""Tests for video_transcribe.<module> module."""

import pytest


class Test<FeatureName>:
    """Test suite for <feature>."""

    def test_<what>_<expected>(self) -> None:
        """Test that <condition> leads to <expected result>.

        Given: <preconditions>
        When: <action>
        Then: <expected outcome>
        """
        # Arrange
        # Act
        # Assert
```

### Best Practices

1. **Naming:** Use descriptive test names: `test_<what>_<expected>`
2. **Classes:** Group related tests in `Test*` classes
3. **Docstrings:** Include Given/When/Then for complex tests
4. **Isolation:** Each test should be independent (use fixtures, not shared state)
5. **Exceptions:** Use `pytest.raises(ValueError, match="...")` for exception tests

### Example: Exception Test

```python
def test_validate_chunk_overlap_negative_raises(self, monkeypatch):
    """Test that CHUNK_OVERLAP_SEC < 0 raises ValueError."""
    monkeypatch.setenv("CHUNK_OVERLAP_SEC", "-1.0")

    import video_transcribe.config
    config = importlib.reload(video_transcribe.config)

    with pytest.raises(ValueError, match="CHUNK_OVERLAP_SEC must be non-negative"):
        config.validate_config()
```

### Example: Positive Test

```python
def test_validate_config_passes_with_valid_defaults(self, monkeypatch):
    """Test that validate_config() passes with default valid values."""
    # Clear env vars to use defaults
    monkeypatch.delenv("CHUNK_OVERLAP_SEC", raising=False)
    monkeypatch.delenv("CHUNK_MAX_DURATION_SEC", raising=False)

    import video_transcribe.config
    config = importlib.reload(video_transcribe.config)

    # Should not raise
    config.validate_config()
```

## Current Coverage

| Module | Tests | Status |
|--------|-------|--------|
| config.py | 9 | ✅ Implemented |
| audio/chunker.py | 5 | 🚧 Planned (TEST_PLAN.md §1) |
| transcribe/merger.py | 5 | 🚧 Planned (TEST_PLAN.md §2) |
| postprocess/filename.py | 6 | 🚧 Planned (TEST_PLAN.md §3) |

**Total:** 9 tests implemented, 16 planned

## Test Markers (Future)

When tests grow, use markers for categorization:

```python
@pytest.mark.unit
def test_fast_logic():
    """Fast unit test, no external deps."""
    pass

@pytest.mark.integration
def test_with_ffmpeg():
    """Integration test with FFmpeg."""
    pass
```

Run specific markers:
```bash
pytest -m unit -v      # Fast tests only
pytest -m integration -v  # Integration tests only
```

## See Also

- [docs/TEST_PLAN.md](TEST_PLAN.md) — Full test plan with all test cases
- [pyproject.toml](../pyproject.toml) — Pytest configuration
- [tests/conftest.py](../tests/conftest.py) — Shared fixtures
