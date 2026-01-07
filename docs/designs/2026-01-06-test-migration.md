# Plan: Migrate Tests to New Namespaced API Client

## Overview

Migrate all integration and e2e tests from the old `api_client.py` + `services/` layer to the new namespaced `NotebookLMClient`. Since there's no public release yet, we can break backward compatibility and remove the old code entirely.

## Files to Update

### E2E Tests (6 files)

| File | Lines | Changes |
|------|-------|---------|
| `tests/e2e/conftest.py` | 117 | Update client import, fixture uses new client |
| `tests/e2e/test_notebooks.py` | ~150 | Remove NotebookService, ConversationService usage |
| `tests/e2e/test_sources.py` | ~100 | Remove SourceService usage |
| `tests/e2e/test_artifacts.py` | 285 | Remove ArtifactService usage |
| `tests/e2e/test_downloads.py` | ~80 | Remove ArtifactService usage |
| `tests/e2e/test_full_workflow.py` | 179 | Remove all service imports |

### Integration Tests (2 files)

| File | Lines | Changes |
|------|-------|---------|
| `tests/integration/test_api_client.py` | 556 | Update to new client methods |
| `tests/integration/test_services.py` | 426 | Rewrite entirely or delete |

### Unit Tests (5 files)

| File | Lines | Changes |
|------|-------|---------|
| `tests/unit/test_services_new.py` | 310 | Delete (tests old services) |
| `tests/unit/test_conversation.py` | ~100 | Update imports from types |
| `tests/unit/test_research.py` | ~50 | Update client import |
| `tests/unit/test_api_coverage.py` | 317 | Update to test new client |
| `tests/unit/test_youtube_extraction.py` | ~50 | Update client import |

## Files to Delete

After migration is complete:

```
src/notebooklm/api_client.py          # Old monolithic client (~2800 lines)
src/notebooklm/services/              # Entire directory
  ├── __init__.py
  ├── notebooks.py
  ├── sources.py
  ├── artifacts.py
  ├── conversation.py
  └── research.py
tests/unit/test_services_new.py       # Tests old services layer
tests/integration/test_services.py    # Tests old services layer (optional: rewrite)
```

## Migration Patterns

### 1. Import Changes

```python
# OLD
from notebooklm.api_client import NotebookLMClient
from notebooklm.services import NotebookService, SourceService, ArtifactService
from notebooklm.services.notebooks import Notebook, NotebookDescription
from notebooklm.services.conversation import ChatMode, AskResult

# NEW
from notebooklm import NotebookLMClient
from notebooklm import (
    Notebook, NotebookDescription, Source, Artifact, Note,
    ChatMode, AskResult, GenerationStatus
)
# Or import from types directly:
from notebooklm.types import Notebook, Source, Artifact
```

### 2. Service Pattern → Direct Client

```python
# OLD
async with NotebookLMClient(auth) as client:
    service = NotebookService(client)
    notebooks = await service.list()
    nb = await service.create("Title")

# NEW
async with NotebookLMClient(auth) as client:
    notebooks = await client.notebooks.list()
    nb = await client.notebooks.create("Title")
```

### 3. Method Name Mappings

| Old (Service.method) | New (client.namespace.method) |
|---------------------|-------------------------------|
| `NotebookService.list()` | `client.notebooks.list()` |
| `NotebookService.create(title)` | `client.notebooks.create(title)` |
| `NotebookService.get(id)` | `client.notebooks.get(id)` |
| `NotebookService.delete(id)` | `client.notebooks.delete(id)` |
| `NotebookService.rename(id, title)` | `client.notebooks.rename(id, title)` |
| `NotebookService.get_description(id)` | `client.notebooks.get_description(id)` |
| `SourceService.list(nb_id)` | `client.sources.list(nb_id)` |
| `SourceService.add_url(nb_id, url)` | `client.sources.add_url(nb_id, url)` |
| `SourceService.add_text(nb_id, text)` | `client.sources.add_text(nb_id, text)` |
| `SourceService.delete(nb_id, src_id)` | `client.sources.delete(nb_id, src_id)` |
| `ArtifactService.list(nb_id)` | `client.artifacts.list(nb_id)` |
| `ArtifactService.generate_audio(...)` | `client.artifacts.generate_audio(...)` |
| `ArtifactService.download_audio(...)` | `client.artifacts.download_audio(...)` |
| `ArtifactService.wait_for_completion(...)` | `client.artifacts.wait_for_completion(...)` |
| `ConversationService.ask(...)` | `client.chat.ask(...)` |
| `ConversationService.configure(...)` | `client.chat.configure(...)` |
| `ConversationService.set_mode(...)` | `client.chat.set_mode(...)` |

### 4. conftest.py Fixture Update

```python
# OLD (tests/e2e/conftest.py)
from notebooklm.api_client import NotebookLMClient

@pytest.fixture
async def client():
    auth = await load_auth()
    async with NotebookLMClient(auth) as client:
        yield client

# NEW
from notebooklm import NotebookLMClient

@pytest.fixture
async def client():
    async with await NotebookLMClient.from_storage() as client:
        yield client
```

## Execution Order

### Phase 1: Update conftest and imports
1. Update `tests/e2e/conftest.py` - central fixture
2. Update `__init__.py` exports if needed

### Phase 2: Update E2E tests (parallel)
3. `test_notebooks.py`
4. `test_sources.py`
5. `test_artifacts.py`
6. `test_downloads.py`
7. `test_full_workflow.py`

### Phase 3: Update integration tests
8. `test_api_client.py` - update to new client
9. `test_services.py` - delete or rewrite

### Phase 4: Update unit tests
10. `test_conversation.py`
11. `test_research.py`
12. `test_api_coverage.py`
13. `test_youtube_extraction.py`
14. Delete `test_services_new.py`

### Phase 5: Cleanup
15. Remove `LegacyNotebookLMClient` from `__init__.py`
16. Delete `src/notebooklm/api_client.py`
17. Delete `src/notebooklm/services/` directory
18. Run full test suite to verify

## Estimated Scope

- **~12 test files** to update
- **~2000 lines** of test code affected
- **~3700 lines** of old code to delete
- **Net reduction**: ~1500+ lines

## Verification

After each phase, run:
```bash
pytest tests/unit -q          # After unit test updates
pytest tests/integration -q   # After integration updates
pytest tests/e2e -m e2e -q    # After e2e updates (requires auth)
pytest -q                     # Full suite
```
