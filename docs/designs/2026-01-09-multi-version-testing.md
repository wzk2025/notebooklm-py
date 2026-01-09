# Multi-Python-Version Docker Test Runner

**Date:** 2026-01-09
**Status:** Design Complete

## Overview

A local testing tool that runs the test suite across multiple Python versions using Docker containers, providing fast feedback before pushing to CI.

## Components

1. **Shell script:** `dev/test-versions.sh`
2. **Claude Code skill:** `/matrix`
3. **Project updates:** pyproject.toml and CI workflow

## Supported Python Versions

Changing from 3.9-3.12 to **3.10-3.14**:
- Drop 3.9 (EOL October 2025)
- Add 3.13 and 3.14

## Usage

### Shell Script

```bash
# Run all versions (default: 3.10, 3.11, 3.12, 3.13, 3.14)
./dev/test-versions.sh

# Run specific versions only
./dev/test-versions.sh 3.12 3.13

# Include readonly e2e tests (auto-mounts auth storage)
./dev/test-versions.sh -r
./dev/test-versions.sh --with-readonly

# Pass pytest arguments (after --)
./dev/test-versions.sh -- -k test_encoder
./dev/test-versions.sh -- -x --tb=short

# Combine all options
./dev/test-versions.sh -r 3.12 3.13 -- -k test_encoder -v
```

### Claude Code Skill

```
/matrix              # All versions, unit+integration
/matrix 3.12         # Single version
/matrix -r           # Include readonly e2e tests
/matrix -r 3.12 3.13 -- -k test_encoder
```

## Technical Design

### Docker Strategy

Each Python version runs in its own container with:
- **Read-only source mount:** `-v "$PWD:/src:ro"` prevents race conditions between parallel containers
- **Copy inside container:** `cp -r /src/. /test` gives each container isolated workspace
- **Named pip cache volume:** `-v pip-cache-3.12:/root/.cache/pip` for fast subsequent runs
- **Slim images:** `python:3.12-slim` for faster pulls

### Installation

Uses `uv` for 10-100x faster dependency resolution:
```bash
pip install -q uv && uv pip install --system -e '.[dev]'
```

### Parallelism

All containers launch simultaneously as bash background jobs (`&`), then `wait` for all to complete. Each container writes:
- `$TMPDIR/$version.log` - full stdout/stderr
- `$TMPDIR/$version.exit` - exit code

### Safety Features

- **Signal handling:** Ctrl+C kills all background containers and cleans up temp files
- **Docker check:** Fails fast with clear error if Docker daemon isn't running
- **Temp cleanup:** `trap cleanup EXIT` ensures no leftover files

### Test Scope

- **Default:** `pytest --ignore=tests/e2e` (unit + integration only)
- **With `-r`:** `pytest -m "readonly or not e2e"` (adds readonly e2e tests)

### Auth Mounting for E2E Tests

When `--with-readonly` is specified, auto-mount auth storage:
```bash
-v "$HOME/.notebooklm:/root/.notebooklm:ro"
```

## Output Format

```
Testing Python versions: 3.10 3.11 3.12 3.13 3.14
Pytest args: --ignore=tests/e2e

Starting Python 3.10...
Starting Python 3.11...
Starting Python 3.12...
Starting Python 3.13...
Starting Python 3.14...

════════ RESULTS ════════
Python 3.10:  PASS  42 passed in 8.23s
Python 3.11:  PASS  42 passed in 7.91s
Python 3.12:  FAIL  41 passed, 1 failed in 8.15s
--- Last 20 lines ---
[failure output here]
---
Python 3.13:  PASS  42 passed in 8.02s
Python 3.14:  PASS  42 passed in 7.88s
═════════════════════════
```

Exit code: 0 if all pass, 1 if any fail.

## Files to Create/Modify

### New Files

1. `dev/test-versions.sh` - Main test runner script
2. `.claude/skills/matrix.md` - Claude Code skill

### Modified Files

1. `pyproject.toml`:
   - Change `requires-python = ">=3.9"` to `">=3.10"`
   - Update classifiers: remove 3.9, add 3.13 and 3.14

2. `.github/workflows/test.yml`:
   - Change matrix: `["3.9", "3.10", "3.11", "3.12"]` to `["3.10", "3.11", "3.12", "3.13", "3.14"]`

## Script Implementation Notes

Key implementation details:
- Use `set -euo pipefail` for safety
- Parse arguments: versions before `--`, pytest args after
- Handle `-r`/`--with-readonly` flag
- Colored output (green PASS, red FAIL)
- Extract pytest summary line from logs
- Show last 20 lines of output on failure
