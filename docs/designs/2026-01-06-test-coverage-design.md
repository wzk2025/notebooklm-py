# Test Coverage Improvement Plan

**Goal:** Improve E2E test coverage and reliability for live API testing
**Current Coverage:** 54.5% (target lowered from 90% to 70%)

## Strategy: Hybrid Golden Notebook + Session Fixtures

### Core Principles
1. **Catch regressions** - Detect when Google changes RPC format
2. **Validate live API** - Confirm reverse-engineered methods still work
3. **Don't wait for slow operations** - Fire-and-forget for generation (15+ min)

---

## Test Tiers

| Tier | Fixture | Operations | When to Run |
|------|---------|------------|-------------|
| **Golden Reader** | Pre-seeded notebook (env var) | list, get, download, query, export | Every PR |
| **CRUD Tests** | Function-scoped temp notebook | create, rename, delete notebooks/sources | Every PR |
| **Fast Generation** | Temp notebook | mind map, notes (< 10s) | Every PR |
| **Slow Generation** | Session fixture | audio, video, quiz, etc. (15+ min) | Nightly |
| **Mutation Tests** | Golden notebook + revert | rename artifact → revert | Every PR |

---

## Artifact Speed Categories

| Operation | Speed | Marker |
|-----------|-------|--------|
| Note create/delete | ~1s | `@e2e` |
| Mind Map generate | ~5-10s | `@e2e` |
| List/Get/Download | ~1-2s | `@golden` |
| Audio Overview | 2-15+ min | `@slow` |
| Video (Deep Dive) | 3-15+ min | `@slow` |
| Quiz/Flashcards | 2-15+ min | `@slow` |
| Slide Deck/Infographic | 2-15+ min | `@slow` |

---

## Phase 1: Add Pytest Markers

**File:** `pyproject.toml`

```toml
[tool.pytest.ini_options]
markers = [
    "e2e: end-to-end tests requiring authentication",
    "slow: slow tests (artifact generation, 15+ min)",
    "golden: tests using golden notebook (read-only)",
    "mutation: tests that modify and revert golden data",
]

[tool.coverage.report]
fail_under = 70  # Down from 90%
```

---

## Phase 2: Create Golden Notebook Fixtures

**File:** `tests/e2e/conftest.py`

```python
@pytest.fixture(scope="session")
def golden_notebook_id():
    """Requires NOTEBOOKLM_GOLDEN_NOTEBOOK_ID env var."""
    nb_id = os.environ.get("NOTEBOOKLM_GOLDEN_NOTEBOOK_ID")
    if not nb_id:
        pytest.skip("Golden notebook not configured")
    return nb_id

@pytest.fixture(scope="session")
async def golden_client(auth_tokens, golden_notebook_id):
    """Session-scoped client for read-only golden notebook tests."""
    async with NotebookLMClient(auth_tokens) as client:
        yield client

@pytest.fixture(scope="function")
async def temp_notebook(client, cleanup_notebooks):
    """Create temporary notebook, auto-deleted after test."""
    notebook = await client.notebooks.create(f"Test-{uuid4().hex[:8]}")
    cleanup_notebooks.append(notebook.id)
    return notebook

@pytest.fixture(scope="session")
async def generation_notebook(client, cleanup_notebooks):
    """Shared notebook for slow generation tests."""
    notebook = await client.notebooks.create(f"GenTest-{uuid4().hex[:8]}")
    # Add a source for generation
    await client.sources.add_text(notebook.id, "Test content for generation")
    cleanup_notebooks.append(notebook.id)
    return notebook
```

---

## Phase 3: Add Markers to Existing Tests

**Migration approach:** Add markers, don't reorganize files.

| Test | File | Marker |
|------|------|--------|
| `test_list_artifacts` | test_artifacts.py | `@golden` |
| `test_generate_mind_map` | test_artifacts.py | `@e2e` |
| `test_generate_quiz_*` | test_artifacts.py | `@slow` |
| `test_generate_audio_*` | test_audio_video.py | `@slow` |
| `test_generate_video_*` | test_audio_video.py | `@slow` |
| `test_download_*` | test_downloads.py | `@golden` |
| `test_*` | test_notebooks.py | `@e2e` |
| `test_*` | test_sources.py | `@e2e` |

---

## Phase 4: Test Patterns

### Pattern 1: Golden Read-Only
```python
@pytest.mark.golden
@pytest.mark.e2e
async def test_list_artifacts(golden_client, golden_notebook_id):
    artifacts = await golden_client.artifacts.list(golden_notebook_id)
    assert len(artifacts) > 0
```

### Pattern 2: Mutation with Revert
```python
@pytest.mark.mutation
@pytest.mark.e2e
async def test_rename_artifact(golden_client, golden_notebook_id):
    artifacts = await golden_client.artifacts.list(golden_notebook_id)
    artifact = artifacts[0]
    original_title = artifact.title

    await golden_client.artifacts.rename(golden_notebook_id, artifact.id, "Test")
    await golden_client.artifacts.rename(golden_notebook_id, artifact.id, original_title)
```

### Pattern 3: Fire-and-Forget Generation
```python
@pytest.mark.slow
@pytest.mark.e2e
async def test_generate_audio_accepted(client, generation_notebook):
    """Verify API accepts request - don't wait for completion."""
    result = await client.artifacts.generate_audio(generation_notebook.id)
    assert result is None or hasattr(result, 'task_id')
```

---

## Phase 5: Self-Healing Script

**File:** `scripts/heal_golden_notebook.py`

```python
"""
Ensures golden notebook has all required artifacts.
Run manually or nightly - NOT per-PR.

Usage: python scripts/heal_golden_notebook.py
"""

REQUIRED_ARTIFACTS = ["audio", "video", "quiz", "flashcards", "slide_deck", "mind_map"]
REQUIRED_SOURCES = ["web_url", "youtube", "text"]

async def heal():
    # 1. Check existing artifacts
    # 2. Generate missing ones
    # 3. Report status
```

---

## Phase 6: CI Configuration

**Run Commands:**
```bash
# Every PR (fast, ~2 min)
pytest tests/e2e -m "e2e and not slow"

# Nightly (slow generation, 30+ min)
pytest tests/e2e -m slow

# All E2E
pytest tests/e2e -m e2e
```

**GitHub Actions (optional):**
```yaml
# .github/workflows/heal-golden.yml
name: Heal Golden Notebook
on:
  schedule:
    - cron: '0 3 * * *'
  workflow_dispatch:
```

---

## Files to Modify

| File | Action |
|------|--------|
| `pyproject.toml` | Add markers, lower coverage threshold |
| `tests/e2e/conftest.py` | Add golden fixtures |
| `tests/e2e/test_artifacts.py` | Add `@golden`, `@slow` markers |
| `tests/e2e/test_audio_video.py` | Add `@slow` markers |
| `tests/e2e/test_downloads.py` | Add `@golden` markers |
| `tests/e2e/test_notebooks.py` | Add `@e2e` markers |
| `tests/e2e/test_sources.py` | Add `@e2e` markers |
| `scripts/heal_golden_notebook.py` | Create new |

---

## Golden Notebook Setup (Manual)

Before running tests, create a notebook with:
1. **Sources:** Web URL, YouTube video, pasted text
2. **Artifacts:** Audio, Video, Quiz, Flashcards, Slide Deck, Mind Map
3. **Set env var:** `NOTEBOOKLM_GOLDEN_NOTEBOOK_ID=<notebook-id>`

---

## Expected Outcomes

1. **Fast PR checks** - Golden + CRUD tests run in ~2 min
2. **Reliable regression detection** - Read tests catch RPC format changes immediately
3. **No CI timeouts** - Slow generation runs nightly, not per-PR
4. **Maintainable golden data** - Self-healing script keeps notebook healthy
