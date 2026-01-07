# Architecture Guide

Overview of the `notebooklm-client` codebase structure and design decisions.

## Package Structure

```
src/notebooklm/
├── __init__.py          # Public exports
├── client.py            # NotebookLMClient main class
├── auth.py              # Authentication handling
├── types.py             # Dataclasses and type definitions
├── _core.py             # Core HTTP/RPC infrastructure
├── _notebooks.py        # NotebooksAPI implementation
├── _sources.py          # SourcesAPI implementation
├── _artifacts.py        # ArtifactsAPI implementation
├── _chat.py             # ChatAPI implementation
├── _research.py         # ResearchAPI implementation
├── _notes.py            # NotesAPI implementation
├── rpc/                 # RPC protocol layer
│   ├── __init__.py
│   ├── types.py         # RPCMethod enum and constants
│   ├── encoder.py       # Request encoding
│   └── decoder.py       # Response parsing
└── cli/                 # CLI implementation
    ├── __init__.py      # CLI package exports
    ├── helpers.py       # Shared utilities
    ├── session.py       # login, use, status, clear
    ├── notebook.py      # list, create, delete, rename, etc.
    ├── source.py        # source add, list, delete, etc.
    ├── artifact.py      # artifact list, get, delete, etc.
    ├── generate.py      # generate audio, video, etc.
    ├── download.py      # download audio, video, etc.
    ├── chat.py          # ask, configure, history
    └── note.py          # note create, list, etc.
```

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│   cli/session.py, cli/notebook.py, cli/generate.py, etc.   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      Client Layer                           │
│  NotebookLMClient → NotebooksAPI, SourcesAPI, ArtifactsAPI │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                       Core Layer                            │
│              ClientCore → _rpc_call(), HTTP client          │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                        RPC Layer                            │
│        encoder.py, decoder.py, types.py (RPCMethod)         │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**CLI Layer (`cli/`)**
- User-facing commands
- Input validation and formatting
- Output rendering with Rich
- Context management (active notebook)

**Client Layer (`client.py`, `_*.py`)**
- High-level Python API
- Domain-specific methods (`notebooks.create()`, `sources.add_url()`)
- Returns typed dataclasses (`Notebook`, `Source`, `Artifact`)
- Wraps Core layer RPC calls

**Core Layer (`_core.py`)**
- HTTP client management (`httpx.AsyncClient`)
- Request counter (`_reqid_counter`)
- RPC call abstraction
- Authentication handling

**RPC Layer (`rpc/`)**
- Protocol constants and enums
- Request encoding (`encode_rpc_request()`)
- Response parsing (`decode_response()`)
- No HTTP/networking logic

## Key Files

### `client.py`

The main public interface. Users import `NotebookLMClient` from here.

```python
class NotebookLMClient:
    notebooks: NotebooksAPI
    sources: SourcesAPI
    artifacts: ArtifactsAPI
    chat: ChatAPI
    research: ResearchAPI
    notes: NotesAPI
```

Design decisions:
- Namespaced APIs for organization
- Async context manager pattern
- `from_storage()` factory for easy initialization

### `_core.py`

Infrastructure shared by all API classes:

```python
class ClientCore:
    auth: AuthTokens
    _client: httpx.AsyncClient
    _reqid_counter: int

    async def rpc_call(method, params, ...) -> Any
    async def open() / close()
```

All `_*.py` API classes receive a `ClientCore` instance.

### `_*.py` Files

Underscore prefix indicates internal modules (not for direct import by users).

Pattern:
```python
class SomeAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def some_method(self, ...):
        params = [...]  # Build RPC params
        result = await self._core.rpc_call(RPCMethod.SOME, params)
        return SomeType.from_api_response(result)
```

### `rpc/types.py`

**This is THE source of truth for RPC constants.**

```python
class RPCMethod(str, Enum):
    LIST_NOTEBOOKS = "wXbhsf"
    CREATE_NOTEBOOK = "CCqFvf"
    # ... all method IDs
```

When Google changes method IDs, only this file needs updating.

### `types.py`

Domain dataclasses:

```python
@dataclass
class Notebook:
    id: str
    title: str
    created_at: Optional[datetime]
    sources_count: int

    @classmethod
    def from_api_response(cls, data: list) -> "Notebook":
        # Parse nested list structure
```

## Design Decisions

### Why Underscore Prefixes?

Files like `_notebooks.py` use underscore prefixes to:
1. Signal they're internal implementation
2. Keep public API clean (`from notebooklm import NotebookLMClient`)
3. Allow refactoring without breaking imports

### Why Namespaced APIs?

Instead of `client.list_notebooks()`, we use `client.notebooks.list()`:
- Groups related methods
- Mirrors UI organization
- Scales better as API grows
- Tab completion friendly

### Why Async?

Google's API can be slow. Async allows:
- Concurrent operations
- Non-blocking downloads
- Integration with async frameworks (FastAPI, etc.)

### Why No Service Layer?

Originally had `NotebookService(client)` pattern. Removed because:
- Extra indirection without value
- Users had to instantiate both client and services
- Namespaced APIs (`client.notebooks`) achieve same organization

## Adding New Features

### New RPC Method

1. Capture network traffic (see `docs/contributing/debugging.md`)
2. Add to `rpc/types.py`:
   ```python
   NEW_METHOD = "AbCdEf"
   ```
3. Add to appropriate `_*.py` API class
4. Add dataclass to `types.py` if needed
5. Add CLI command if user-facing

### New API Class

1. Create `_newfeature.py`:
   ```python
   class NewFeatureAPI:
       def __init__(self, core: ClientCore):
           self._core = core
   ```
2. Add to `client.py`:
   ```python
   self.newfeature = NewFeatureAPI(self._core)
   ```
3. Export types from `__init__.py`

### New CLI Command

1. Add to appropriate `cli/*.py` file
2. Register in `cli/__init__.py` or `notebooklm_cli.py`
3. Follow existing patterns (Click decorators, async handling)

## Testing Patterns

See `docs/contributing/testing.md` for details.

- Unit tests: Mock `ClientCore.rpc_call()`
- Integration tests: Mock HTTP responses
- E2E tests: Real API calls (require auth)
