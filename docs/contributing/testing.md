# Testing Guide

**Status:** Active
**Last Updated:** 2026-01-07

## Quick Reference

```bash
# Run unit + integration tests (default)
pytest

# Run E2E tests (requires: notebooklm login)
pytest tests/e2e -m e2e

# Run specific marker combinations
pytest tests/e2e -m "e2e and not slow"      # Quick E2E validation
pytest tests/e2e -m "e2e and golden"        # Read-only tests only
pytest tests/e2e -m "e2e and not exhaustive" # Skip variant tests
```

## Test Structure

```
tests/
├── conftest.py              # RPC response builders
├── unit/                    # No network, fast
│   ├── cli/                 # CLI command tests
│   ├── test_decoder.py
│   ├── test_encoder.py
│   └── ...
├── integration/             # Mocked HTTP
│   ├── conftest.py          # Mock auth tokens
│   └── test_*.py
└── e2e/                     # Real API
    ├── conftest.py          # Auth, fixtures, cleanup
    ├── test_generation.py   # All artifact generation tests
    ├── test_artifacts.py    # Artifact CRUD/list operations
    ├── test_downloads.py    # Download operations
    ├── test_sources.py      # Source operations
    └── ...
```

## E2E Fixtures

### Which Fixture Do I Need?

| I want to... | Use | Why |
|--------------|-----|-----|
| List/download existing artifacts | `test_notebook_id` | Golden notebook has pre-made content |
| Add/delete sources or notes | `temp_notebook` | Isolated, auto-cleanup |
| Generate audio/video/quiz | `generation_notebook` | Writable, has content, session-scoped |

### `test_notebook_id` (Golden Notebook)

Google's shared demo notebook: `19bde485-a9c1-4809-8884-e872b2b67b44`

Pre-populated with sources and artifacts. You don't own it, so you can only read.

```python
@pytest.mark.golden
async def test_list_artifacts(self, client, test_notebook_id):
    artifacts = await client.artifacts.list(test_notebook_id)
    assert isinstance(artifacts, list)
```

### `temp_notebook`

Fresh notebook per test. Automatically deleted after test completes (even on failure).

```python
async def test_add_source(self, client, temp_notebook):
    source = await client.sources.add_url(temp_notebook.id, "https://example.com")
    assert source.id is not None
```

### `generation_notebook`

Session-scoped notebook with content. Created once, shared across all generation tests.

```python
@pytest.mark.slow
async def test_generate_quiz(self, client, generation_notebook):
    result = await client.artifacts.generate_quiz(generation_notebook.id)
    assert result is not None
```

**Why not golden?** You can't generate on notebooks you don't own.
**Why not temp_notebook?** Creating fresh notebooks per test wastes quota.

## Test Markers

All markers defined in `pyproject.toml`:

| Marker | Purpose |
|--------|---------|
| `e2e` | Requires real API (excluded by default via `--ignore=tests/e2e`) |
| `slow` | Takes 30+ seconds (generation tests) |
| `exhaustive` | Parameter variant tests (exclude to save quota) |
| `golden` | Uses golden notebook (read-only, safe) |
| `stable` | Consistently passes |
| `unstable` | May fail due to rate limits or API changes |
| `mutation` | Modifies and reverts golden data |
| `exports` | Creates Google Docs/Sheets |
| `contract` | API contract validation |
| `smoke` | Critical path tests |

### Exhaustive Testing

Each artifact type has multiple options. We test one default per type, mark variants as `exhaustive`:

```python
# Runs by default
@pytest.mark.slow
async def test_generate_audio_default(self, client, generation_notebook):
    result = await client.artifacts.generate_audio(generation_notebook.id)

# Only when requested: pytest -m exhaustive
@pytest.mark.slow
@pytest.mark.exhaustive
async def test_generate_audio_brief(self, client, generation_notebook):
    result = await client.artifacts.generate_audio(
        generation_notebook.id,
        audio_format=AudioFormat.BRIEF,
    )
```

## E2E Fixtures Reference

From `tests/e2e/conftest.py`:

### Authentication

```python
@pytest.fixture(scope="session")
def auth_cookies() -> dict[str, str]:
    """Load cookies from ~/.notebooklm/storage.json"""

@pytest.fixture(scope="session")
def auth_tokens(auth_cookies) -> AuthTokens:
    """Fetch CSRF + session ID from NotebookLM homepage"""

@pytest.fixture
async def client(auth_tokens) -> NotebookLMClient:
    """Fresh client per test"""
```

### Notebooks

```python
@pytest.fixture(scope="session")
def golden_notebook_id() -> str:
    """Returns DEFAULT_GOLDEN_NOTEBOOK_ID or env override"""

@pytest.fixture
def test_notebook_id(golden_notebook_id) -> str:
    """Returns NOTEBOOKLM_TEST_NOTEBOOK_ID or golden"""

@pytest.fixture
async def temp_notebook(client) -> Notebook:
    """Create notebook, auto-delete after test"""

@pytest.fixture(scope="session")
async def generation_notebook(auth_tokens) -> Notebook:
    """Session notebook with content for generation tests"""
```

### Cleanup Helpers

```python
# Collector fixtures - append IDs to track for cleanup
created_notebooks: list[str]
created_sources: list[str]
created_artifacts: list[str]

# Cleanup fixtures - delete tracked items after test
cleanup_notebooks
cleanup_sources
cleanup_artifacts
```

### Decorators

```python
@requires_auth  # Skip test if no auth stored
```

## Environment Variables

```bash
# Override golden notebook ID
export NOTEBOOKLM_GOLDEN_NOTEBOOK_ID="your-id"

# Override test_notebook_id fixture
export NOTEBOOKLM_TEST_NOTEBOOK_ID="your-id"
```

## Constants

From `tests/e2e/conftest.py`:

```python
RATE_LIMIT_DELAY = 3.0        # Delay after tests
SOURCE_PROCESSING_DELAY = 2.0  # Wait for source indexing
POLL_INTERVAL = 2.0           # Status poll interval
POLL_TIMEOUT = 60.0           # Max poll wait time
DEFAULT_GOLDEN_NOTEBOOK_ID = "19bde485-a9c1-4809-8884-e872b2b67b44"
```

## Writing New Tests

### Decision Tree

```
Need network?
├── No → tests/unit/
├── Mocked → tests/integration/
└── Real API → tests/e2e/
    └── What notebook?
        ├── Read-only → test_notebook_id + @pytest.mark.golden
        ├── CRUD → temp_notebook
        └── Generation → generation_notebook + @pytest.mark.slow
            └── Variant? → add @pytest.mark.exhaustive
```

### Example: New Generation Test

Add generation tests to `tests/e2e/test_generation.py`:

```python
@requires_auth
@pytest.mark.e2e
class TestNewArtifact:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_new_artifact_default(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_new(generation_notebook.id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_new_artifact_with_options(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_new(
            generation_notebook.id,
            option=SomeOption.VALUE,
        )
        assert result is not None
```
