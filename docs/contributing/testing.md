# Testing Guide

How to run tests, write new tests, and handle E2E authentication.

## Running Tests

### Quick Start

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all tests (excludes E2E by default)
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov

# Run specific file
pytest tests/unit/test_decoder.py

# Run specific test
pytest tests/unit/test_decoder.py::test_decode_simple_response
```

### Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests (requires authentication)
pytest tests/e2e/ -m e2e

# Slow tests (audio/video generation)
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests (no network)
│   ├── test_decoder.py
│   ├── test_encoder.py
│   ├── test_auth.py
│   └── test_cli_*.py
├── integration/         # Integration tests (mocked HTTP)
│   ├── test_notebooks.py
│   ├── test_sources.py
│   └── test_artifacts.py
└── e2e/                 # End-to-end tests (real API)
    ├── conftest.py      # E2E fixtures
    ├── test_notebooks_e2e.py
    ├── test_sources_e2e.py
    └── test_artifacts_e2e.py
```

## Writing Unit Tests

Unit tests should be fast and not require network access.

### Testing RPC Encoding

```python
import pytest
from notebooklm.rpc import encode_rpc_request, RPCMethod

def test_encode_list_notebooks():
    params = [None, 1, None, [2]]
    result = encode_rpc_request(RPCMethod.LIST_NOTEBOOKS, params)

    assert RPCMethod.LIST_NOTEBOOKS in result
    assert "[null,1,null,[2]]" in result
```

### Testing RPC Decoding

```python
import pytest
from notebooklm.rpc import decode_response

def test_decode_simple_response():
    raw = ''')]}\'

123
["wrb.fr","wXbhsf","[[\\"id\\",\\"title\\"]]",null,null,null,"generic"]
'''
    result = decode_response(raw, "wXbhsf")
    assert result == [["id", "title"]]
```

### Testing Dataclass Parsing

```python
import pytest
from notebooklm.types import Notebook

def test_notebook_from_api_response():
    raw_data = ["nb123", "My Notebook", None, [[1704067200]], 5]

    nb = Notebook.from_api_response(raw_data)

    assert nb.id == "nb123"
    assert nb.title == "My Notebook"
    assert nb.sources_count == 5
```

## Writing Integration Tests

Integration tests mock HTTP responses but test full method flow.

### Mocking RPC Calls

```python
import pytest
from unittest.mock import AsyncMock, patch
from notebooklm import NotebookLMClient, AuthTokens

@pytest.fixture
def mock_auth():
    return AuthTokens(
        cookies={"SID": "test"},
        csrf_token="test_csrf",
        session_id="test_sid"
    )

@pytest.mark.asyncio
async def test_list_notebooks(mock_auth):
    # Expected API response structure
    mock_response = [[
        ["nb1", "Notebook 1", None, [[1234567890]], 3],
        ["nb2", "Notebook 2", None, [[1234567891]], 0],
    ]]

    with patch('notebooklm._core.ClientCore.rpc_call', new_callable=AsyncMock) as mock:
        mock.return_value = mock_response

        client = NotebookLMClient(mock_auth)
        client._core._is_open = True  # Skip actual connection

        notebooks = await client.notebooks.list()

        assert len(notebooks) == 2
        assert notebooks[0].title == "Notebook 1"
        mock.assert_called_once()
```

### Mocking HTTP Responses

```python
import pytest
import httpx
from pytest_httpx import HTTPXMock

@pytest.mark.asyncio
async def test_full_request_flow(httpx_mock: HTTPXMock, mock_auth):
    # Mock the batchexecute response
    httpx_mock.add_response(
        url__regex=r".*/batchexecute.*",
        text=''')]}\'

100
["wrb.fr","wXbhsf","[[\\"nb1\\",\\"Test\\"]]",null,null,null,"generic"]
'''
    )

    async with NotebookLMClient(mock_auth) as client:
        notebooks = await client.notebooks.list()
        assert len(notebooks) == 1
```

## Writing E2E Tests

E2E tests run against the real API. They require authentication.

### E2E Test Setup

```bash
# First, authenticate
notebooklm login

# Then run E2E tests
pytest tests/e2e/ -m e2e -v
```

### E2E Test Structure

```python
import pytest
from notebooklm import NotebookLMClient

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio,
]

@pytest.fixture
async def client():
    """Create authenticated client."""
    async with await NotebookLMClient.from_storage() as c:
        yield c

@pytest.fixture
async def test_notebook(client):
    """Create a test notebook, cleanup after."""
    nb = await client.notebooks.create("E2E Test")
    yield nb
    await client.notebooks.delete(nb.id)

async def test_create_and_list_notebook(client, test_notebook):
    notebooks = await client.notebooks.list()
    ids = [n.id for n in notebooks]
    assert test_notebook.id in ids
```

### Marking Tests

```python
import pytest

# Basic E2E marker
@pytest.mark.e2e
async def test_basic():
    ...

# Slow test (audio/video generation)
@pytest.mark.e2e
@pytest.mark.slow
async def test_generate_audio():
    ...

# Expected to fail (known issue)
@pytest.mark.e2e
@pytest.mark.xfail(reason="Rate limiting")
async def test_bulk_operations():
    ...
```

### E2E Best Practices

1. **Clean up resources**: Use fixtures that delete test notebooks
2. **Use unique names**: Include timestamp in notebook titles
3. **Handle rate limits**: Add delays between tests
4. **Mark flaky tests**: Use `xfail` for known unreliable tests
5. **Don't test destructive operations**: Avoid testing delete on real data

## Fixtures Reference

### `conftest.py` Fixtures

```python
# tests/conftest.py

@pytest.fixture
def mock_auth():
    """Mock authentication tokens."""
    return AuthTokens(
        cookies={"SID": "test", "HSID": "test"},
        csrf_token="test_csrf",
        session_id="test_sid"
    )

@pytest.fixture
def mock_client(mock_auth):
    """Create client with mocked auth."""
    return NotebookLMClient(mock_auth)

@pytest.fixture
def sample_notebook_response():
    """Sample API response for notebook list."""
    return [[
        ["nb123", "Test Notebook", None, [[1704067200]], 3, None, True],
    ]]
```

### E2E Fixtures

```python
# tests/e2e/conftest.py

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session-scoped fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def auth_client():
    """Session-scoped authenticated client."""
    async with await NotebookLMClient.from_storage() as client:
        yield client
```

## CLI Testing

### Testing CLI Commands

```python
from click.testing import CliRunner
from notebooklm.notebooklm_cli import cli

def test_list_command(mocker):
    # Mock the async client
    mock_notebooks = [
        Notebook(id="nb1", title="Test", sources_count=0)
    ]
    mocker.patch(
        'notebooklm.cli.notebook.get_client',
        return_value=AsyncMock(notebooks=AsyncMock(list=AsyncMock(return_value=mock_notebooks)))
    )

    runner = CliRunner()
    result = runner.invoke(cli, ['list'])

    assert result.exit_code == 0
    assert "Test" in result.output
```

## Coverage

### Running with Coverage

```bash
# Generate coverage report
pytest --cov=notebooklm --cov-report=html

# View report
open htmlcov/index.html
```

### Coverage Goals

- Unit tests: High coverage of encoding/decoding/parsing
- Integration tests: Cover all API methods
- E2E tests: Smoke tests for critical paths

## Continuous Integration

Tests run automatically on PR. E2E tests require secrets:

```yaml
# GitHub Actions example
- name: Run tests
  run: pytest --ignore=tests/e2e

- name: Run E2E tests
  if: github.event_name == 'push'
  env:
    NOTEBOOKLM_STORAGE: ${{ secrets.NOTEBOOKLM_STORAGE }}
  run: pytest tests/e2e -m e2e
```
