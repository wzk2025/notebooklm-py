# Testing Guide

**Status:** Active
**Last Updated:** 2026-01-07

How to run tests, write new tests, and work with E2E fixtures.

## Running Tests

### Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests (excludes E2E by default)
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov
```

### By Category

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests (requires authentication)
pytest tests/e2e/ -m e2e

# E2E without slow tests (quick validation)
pytest tests/e2e/ -m "e2e and not slow"

# Golden notebook tests only (read-only, safe)
pytest tests/e2e/ -m golden
```

### By Marker

```bash
# Slow tests (generation, 15+ seconds each)
pytest -m slow

# Exhaustive tests (all parameter variants)
pytest -m exhaustive

# Skip slow tests for quick iteration
pytest -m "not slow"

# Stable tests only (consistently pass)
pytest -m stable
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures (RPC response builders)
├── unit/                    # Unit tests (no network, fast)
│   ├── cli/                 # CLI command tests
│   │   ├── test_artifact.py
│   │   ├── test_download.py
│   │   ├── test_generate.py
│   │   ├── test_notebook.py
│   │   ├── test_session.py
│   │   ├── test_source.py
│   │   └── ...
│   ├── test_decoder.py      # RPC response decoding
│   ├── test_encoder.py      # RPC request encoding
│   ├── test_auth.py         # Authentication logic
│   ├── test_types.py        # Dataclass parsing
│   └── ...
├── integration/             # Integration tests (mocked HTTP)
│   ├── conftest.py          # Mock auth, response builders
│   ├── test_notebooks.py
│   ├── test_sources.py
│   ├── test_artifacts.py
│   ├── test_chat.py
│   └── ...
└── e2e/                     # End-to-end tests (real API)
    ├── conftest.py          # Auth, fixtures, cleanup
    ├── test_notebooks.py    # CRUD operations
    ├── test_sources.py      # Source management
    ├── test_artifacts.py    # Artifact generation
    ├── test_audio_video.py  # Audio/video generation
    ├── test_downloads.py    # Download operations
    ├── test_research.py     # Research mode
    └── ...
```

## Test Categories

### Unit Tests

Fast tests with no network access. Test individual functions in isolation.

**What to test:**
- RPC encoding/decoding
- Dataclass parsing (`Notebook.from_api_response()`)
- Authentication token extraction
- CLI argument parsing
- Utility functions

```python
# tests/unit/test_decoder.py
def test_decode_notebook_response():
    raw = ''')}]'
123
["wrb.fr","abc123","[[\\"nb1\\",\\"Title\\"]]",null,null,null,"generic"]
'''
    result = decode_response(raw, "abc123")
    assert result == [["nb1", "Title"]]
```

### Integration Tests

Test full method flows with mocked HTTP responses.

**What to test:**
- Client method behavior
- Response parsing into dataclasses
- Error handling

```python
# tests/integration/test_notebooks.py
@pytest.mark.asyncio
async def test_list_notebooks(httpx_mock, auth_tokens, build_rpc_response):
    # Mock the API response
    httpx_mock.add_response(
        url__regex=r".*/batchexecute.*",
        text=build_rpc_response(
            RPCMethod.LIST_NOTEBOOKS,
            [[["Title", [], "nb_001", "📘", None, [None, None, None, None, None, [1704067200, 0]]]]]
        )
    )

    async with NotebookLMClient(auth_tokens) as client:
        notebooks = await client.notebooks.list()
        assert len(notebooks) == 1
        assert notebooks[0].id == "nb_001"
```

### E2E Tests

Test against the real NotebookLM API. Requires authentication.

**What to test:**
- Real API contract validation
- End-to-end workflows
- Download operations

```bash
# Setup: Authenticate first
notebooklm login

# Run E2E tests
pytest tests/e2e/ -m e2e -v
```

## E2E Fixture Strategy

E2E tests use a tiered fixture system to balance coverage, speed, and quota usage.

### The Problem

NotebookLM has constraints that make naive testing problematic:

1. **Generation is slow** - Audio takes 2-5 minutes, video even longer
2. **Rate limiting** - Too many operations trigger throttling
3. **Source processing** - URLs need time to be indexed
4. **Cleanup failures** - Failed tests can leave orphaned notebooks

### The Solution: Tiered Fixtures

| Fixture | Scope | Purpose | Creates Resources? |
|---------|-------|---------|-------------------|
| `test_notebook_id` | function | Read-only operations | No - uses golden notebook |
| `temp_notebook` | function | Isolated CRUD tests | Yes - auto-cleanup |
| `generation_notebook` | session | Generation tests | Yes - session cleanup |

### Golden Notebook (`test_notebook_id`)

Google's shared demo notebook with pre-seeded content and artifacts.

**ID:** `19bde485-a9c1-4809-8884-e872b2b67b44`

**Use for:**
- Download tests (audio, video, slides already exist)
- List operations (sources, artifacts)
- Read-only queries
- Tests marked `@pytest.mark.golden`

```python
@pytest.mark.golden
async def test_list_artifacts(self, client, test_notebook_id):
    """Read-only - uses golden notebook."""
    artifacts = await client.artifacts.list(test_notebook_id)
    assert isinstance(artifacts, list)
```

**Why:** Pre-existing artifacts mean no generation wait. Always available, no setup needed.

### Temporary Notebook (`temp_notebook`)

Fresh notebook per test, automatically deleted.

**Use for:**
- Source CRUD (add, rename, delete)
- Note CRUD
- Artifact deletion tests
- Tests needing isolated state

```python
async def test_add_and_delete_source(self, client, temp_notebook):
    """CRUD needs owned notebook."""
    source = await client.sources.add_url(temp_notebook.id, "https://example.com")
    deleted = await client.sources.delete(temp_notebook.id, source.id)
    assert deleted is True
```

**Why:** Isolation prevents test interference. Cleanup on failure prevents debris.

### Test Workspace (`generation_notebook`)

Session-scoped writable notebook with pre-seeded content.

**Use for:**
- Artifact generation tests
- Tests that trigger generation but don't need isolation

```python
@pytest.mark.slow
async def test_generate_quiz(self, client, generation_notebook):
    """Generation needs writable notebook."""
    result = await client.artifacts.generate_quiz(generation_notebook.id)
    assert result is not None
```

**Why golden doesn't work:** You can't generate artifacts on notebooks you don't own.

**Why not temp_notebook:** Creating fresh notebooks per generation test wastes time and quota.

## Test Markers

### Available Markers

| Marker | Purpose | Default |
|--------|---------|---------|
| `e2e` | Requires real API | Excluded by pytest |
| `slow` | Takes > 30 seconds | Included |
| `exhaustive` | Parameter variant tests | Included |
| `golden` | Uses golden notebook (read-only) | Included |
| `stable` | Consistently passes | Included |

### Exhaustive Testing

Each artifact type has multiple parameter combinations. Testing all would burn quota.

**Solution:** One default test per type, variants marked `@pytest.mark.exhaustive`.

```python
# DEFAULT: Always runs
@pytest.mark.slow
async def test_generate_audio_default(self, client, generation_notebook):
    result = await client.artifacts.generate_audio(generation_notebook.id)
    assert result is not None

# EXHAUSTIVE: Only when explicitly requested
@pytest.mark.slow
@pytest.mark.exhaustive
async def test_generate_audio_brief_short(self, client, generation_notebook):
    result = await client.artifacts.generate_audio(
        generation_notebook.id,
        audio_format=AudioFormat.BRIEF,
        audio_length=AudioLength.SHORT,
    )
    assert result is not None
```

**Running:**
```bash
# Default (one per type)
pytest tests/e2e -m "e2e and slow"

# All variants
pytest tests/e2e -m "e2e and exhaustive"

# Exclude variants
pytest tests/e2e -m "e2e and not exhaustive"
```

## Fixtures Reference

### Root `conftest.py`

```python
# tests/conftest.py

@pytest.fixture
def build_rpc_response():
    """Factory for building mock RPC responses."""
    def _build(rpc_id: Union[RPCMethod, str], data) -> str:
        rpc_id_str = rpc_id.value if isinstance(rpc_id, RPCMethod) else rpc_id
        inner = json.dumps(data)
        chunk = json.dumps(["wrb.fr", rpc_id_str, inner, None, None])
        return f")]}}'\n{len(chunk)}\n{chunk}\n"
    return _build
```

### Integration `conftest.py`

```python
# tests/integration/conftest.py

@pytest.fixture
def auth_tokens():
    """Mock authentication tokens for integration tests."""
    return AuthTokens(
        cookies={"SID": "test_sid", "HSID": "test_hsid", ...},
        csrf_token="test_csrf_token",
        session_id="test_session_id",
    )
```

### E2E `conftest.py`

```python
# tests/e2e/conftest.py

@pytest.fixture(scope="session")
def auth_tokens(auth_cookies) -> AuthTokens:
    """Fetch real auth tokens from stored cookies."""
    # Fetches CSRF and session ID from NotebookLM homepage
    ...

@pytest.fixture
async def client(auth_tokens) -> AsyncGenerator[NotebookLMClient, None]:
    """Authenticated client for each test."""
    async with NotebookLMClient(auth_tokens) as c:
        yield c

@pytest.fixture
def test_notebook_id(golden_notebook_id):
    """Notebook ID for read-only tests. Defaults to golden."""
    return os.environ.get("NOTEBOOKLM_TEST_NOTEBOOK_ID", golden_notebook_id)

@pytest.fixture
async def temp_notebook(client, created_notebooks, cleanup_notebooks):
    """Fresh notebook with auto-cleanup."""
    notebook = await client.notebooks.create(f"Test-{uuid4().hex[:8]}")
    created_notebooks.append(notebook.id)
    return notebook

@pytest.fixture(scope="session")
async def generation_notebook(auth_tokens) -> AsyncGenerator:
    """Session-scoped workspace with content for generation tests."""
    async with NotebookLMClient(auth_tokens) as client:
        notebook = await client.notebooks.create(f"E2E-Workspace-{uuid4().hex[:8]}")
        await client.sources.add_text(notebook.id, title="Test Content", content="...")
        await asyncio.sleep(2.0)  # Wait for source processing
        yield notebook
        await client.notebooks.delete(notebook.id)
```

## Environment Variables

Override fixture defaults for custom setups:

```bash
# Use your own golden notebook
export NOTEBOOKLM_GOLDEN_NOTEBOOK_ID="your-notebook-id"

# Use specific notebook for test_notebook_id
export NOTEBOOKLM_TEST_NOTEBOOK_ID="your-notebook-id"
```

## CLI Testing

CLI tests live in `tests/unit/cli/` and use Click's test runner.

```python
# tests/unit/cli/test_notebook.py
from click.testing import CliRunner
from notebooklm.cli import cli

def test_list_command(mocker):
    mock_notebooks = [Notebook(id="nb1", title="Test", sources_count=0)]

    # Mock the async client
    mock_client = AsyncMock()
    mock_client.notebooks.list = AsyncMock(return_value=mock_notebooks)
    mocker.patch('notebooklm.cli.helpers.get_client', return_value=mock_client)

    runner = CliRunner()
    result = runner.invoke(cli, ['list'])

    assert result.exit_code == 0
    assert "Test" in result.output
```

## Coverage

```bash
# Generate HTML report
pytest --cov=notebooklm --cov-report=html

# View report
open htmlcov/index.html
```

**Goals:**
- Unit tests: High coverage of encoding/decoding/parsing
- Integration: Cover all client methods
- E2E: Smoke tests for critical paths

## Writing New Tests

### Decision Tree

1. **Does it need the network?**
   - No → Unit test
   - Mocked → Integration test
   - Real API → E2E test

2. **E2E: What notebook do I need?**
   - Read-only → `test_notebook_id` (golden)
   - CRUD operations → `temp_notebook`
   - Generation → `generation_notebook`

3. **E2E: How long does it take?**
   - < 5 seconds → No special marker
   - 30+ seconds → `@pytest.mark.slow`
   - Variant of slow test → `@pytest.mark.exhaustive`

### Best Practices

1. **Clean up resources** - Use fixtures with cleanup
2. **Use unique names** - Include UUID in notebook titles
3. **Don't test destructive ops on golden** - It's read-only anyway
4. **Prefer golden for read tests** - No setup, always available
5. **One assertion focus** - Each test validates one thing
