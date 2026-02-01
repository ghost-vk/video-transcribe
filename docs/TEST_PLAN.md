# Test Plan — Video Transcribe

> **Status:** Draft
> **Last updated:** 2025-02-01
> **Target coverage:** 18 core tests for critical business logic

## Overview

This test plan focuses on high-ROI tests for a solo-developed CLI tool with active feature development. The goal is to prevent regressions in critical business logic without over-engineering.

**Testing philosophy:**

- 20-30% coverage is acceptable for this use case
- Focus on critical paths and edge cases
- Mock external dependencies (API calls, FFmpeg)
- No E2E tests requiring real API keys initially

---

## Module: `audio/chunker.py` — CRITICAL

**Why:** Complex overlap logic + file operations = high bug risk

### Test Suite: `test_chunker.py`

| #   | Test Name                             | What It Tests                                           | Edge Case / Scenario                                     |
| --- | ------------------------------------- | ------------------------------------------------------- | -------------------------------------------------------- |
| 1.1 | `test_no_chunking_needed_small_file`  | File <= limit returns single chunk with `is_temp=False` | Original file should NOT be deleted on cleanup           |
| 1.2 | `test_overlap_within_limit`           | Overlap is WITHIN limit, not added on top               | For 30s limit, 2s overlap: `[0-30s], [28-58s], [56-86s]` |
| 1.3 | `test_overlap_equals_duration_raises` | `overlap >= duration` raises `RuntimeError`             | Prevent infinite loop                                    |
| 1.4 | `test_chunk_boundaries_calculation`   | Correct boundary calculation                            | Last chunk doesn't exceed audio duration                 |
| 1.5 | `test_cleanup_temp_only`              | `cleanup_chunks()` only deletes `is_temp=True`          | Original file preserved                                  |

**Dependencies:** pytest, pytest-mock, pydub (for audio fixtures)

---

## Module: `transcribe/merger.py` — CRITICAL

**Why:** Speaker renumbering is a key feature with complex logic

### Test Suite: `test_merger.py`

| #   | Test Name                                   | What It Tests                                      | Edge Case / Scenario               |
| --- | ------------------------------------------- | -------------------------------------------------- | ---------------------------------- |
| 2.1 | `test_speaker_renumbering_two_chunks`       | Chunk 1: A,B → Chunk 2: A,B → Result: A,B,C,D      | Two chunks, different speakers     |
| 2.2 | `test_speaker_renumbering_many_chunks`      | Multiple chunks: A,B,A,B,A,B → A,B,C,D,E,F,G,H     | Several chunk boundaries           |
| 2.3 | `test_speaker_renumbering_beyond_z`         | Handles >26 speakers: A...Z,AA,AB,AC...            | Large meetings                     |
| 2.4 | `test_timestamp_adjustment_with_offset`     | `start_sec + chunk_offset` correct                 | Timestamps adjusted for each chunk |
| 2.5 | `test_merge_results_length_mismatch_raises` | `len(results) != len(offsets)` raises `ValueError` | Input validation                   |

**Dependencies:** pytest only (pure logic, no external deps)

---

## Module: `postprocess/filename.py` — MEDIUM PRIORITY

**Why:** File safety and cross-platform compatibility affect users directly

### Test Suite: `test_filename.py`

| #   | Test Name                                 | What It Tests                       | Edge Case / Scenario                |
| --- | ----------------------------------------- | ----------------------------------- | ----------------------------------- |
| 3.1 | `test_extract_filename_from_html_comment` | Parses `<!-- FILENAME: ... -->`     | Extracts filename from LLM response |
| 3.2 | `test_sanitize_windows_invalid_chars`     | `<>:"/\|?*` → `_`                   | Windows compatibility               |
| 3.3 | `test_sanitize_path_traversal`            | `../../etc/passwd` → `passwd.md`    | Path traversal attack prevention    |
| 3.4 | `test_sanitize_reserved_names`            | `CON`, `PRN`, `NUL` → `_CON`        | Windows reserved names              |
| 3.5 | `test_resolve_collision_adds_suffix`      | `test.md` → `test_1.md` (if exists) | Filename collision handling         |
| 3.6 | `test_generate_safe_filename_fallback`    | `None` → `transcript.md`            | Fallback to default                 |

**Dependencies:** pytest only (pure string logic)

---

## Module: `config.py` — BASE PROTECTION

**Why:** Prevent invalid configuration at startup

### Test Suite: `test_config.py`

| #   | Test Name                                       | What It Tests                                     | Edge Case / Scenario              |
| --- | ----------------------------------------------- | ------------------------------------------------- | --------------------------------- |
| 4.1 | `test_validate_chunk_overlap_negative_raises`   | `CHUNK_OVERLAP_SEC < 0` raises `ValueError`       | Negative overlap invalid          |
| 4.2 | `test_validate_chunk_duration_positive`         | `CHUNK_MAX_DURATION_SEC <= 0` raises `ValueError` | Non-positive duration invalid     |
| 4.3 | `test_validate_overlap_less_than_duration`      | `overlap >= duration` raises `ValueError`         | Overlap cannot equal/exceed limit |
| 4.4 | `test_validate_max_size_less_than_openai_limit` | `CHUNK_MAX_SIZE_MB >= 25` raises `ValueError`     | Must be under OpenAI API limit    |

**Dependencies:** pytest, pytest-mock (for env var mocking)

---

## Test Structure

**Approach:** Tests placed next to source code (co-location)

```
src/video_transcribe/
├── audio/
│   ├── chunker.py
│   └── test_chunker.py           # 5 tests
├── transcribe/
│   ├── merger.py
│   └── test_merger.py            # 5 tests
├── postprocess/
│   ├── filename.py
│   └── test_filename.py          # 6 tests
├── config.py
├── test_config.py                # 4 tests
└── __init__.py

tests/
├── __init__.py
├── conftest.py                    # Shared fixtures for all tests
└── fixtures/
    └── audio_sample.mp3          # 5-10 second file for chunker tests
```

**Rationale:** Co-location makes it easier to find tests when working on a module, and keeps implementation and tests in context during refactoring.

---

## Setup Requirements

### Add to `pyproject.toml`

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.12",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
markers = [
    "unit: Fast unit tests",
    "integration: Tests with external resources (FFmpeg, network)",
]
```

### Installation

```bash
pip install -e ".[dev]"
```

---

## Running Tests

```bash
# All unit tests
pytest tests/ -v

# Specific module
pytest tests/unit/test_chunker.py -v

# With coverage (optional)
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Not Included (Yet)

- ❌ E2E tests (require API keys, slow)
- ❌ CLI tests (Click testing is straightforward, low ROI)
- ❌ Adapter mock tests (thin wrappers over APIs)
- ❌ Pipeline orchestration (simple composition, low bug risk)

**When to add:**

- E2E: Before major releases, with CI secrets
- CLI: If complex CLI options are added
- Adapter: If custom adapter logic grows

---

## Time Estimate

| Task                               | Time          |
| ---------------------------------- | ------------- |
| Setup (pytest, conftest, fixtures) | 30-60 min     |
| test_chunker.py                    | 60-90 min     |
| test_merger.py                     | 45-60 min     |
| test_filename.py                   | 45-60 min     |
| test_config.py                     | 30-45 min     |
| **Total**                          | **3-4 hours** |

---

## Success Criteria

- All 18 tests pass
- Coverage of critical modules: >70%
- Tests run in <5 seconds
- No external dependencies required (API keys, network)

---

## Next Steps

1. Create `tests/` directory structure
2. Add pytest to dev dependencies
3. Create `conftest.py` with shared fixtures
4. Write tests in priority order: config → filename → merger → chunker
5. Add pre-commit hook (optional): `pytest tests/ -q`
