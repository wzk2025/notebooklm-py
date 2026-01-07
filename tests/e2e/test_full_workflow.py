"""End-to-end tests for full NotebookLM workflow.

These tests require real authentication and interact with the live API.
Run with: pytest tests/e2e/ -v -m e2e
"""

import pytest
import httpx

from notebooklm.auth import (
    AuthTokens,
    extract_csrf_from_html,
    extract_session_id_from_html,
    load_auth_from_storage,
    DEFAULT_STORAGE_PATH,
)
from notebooklm import NotebookLMClient


def _has_auth() -> bool:
    try:
        load_auth_from_storage()
        return True
    except (FileNotFoundError, ValueError):
        return False


requires_auth = pytest.mark.skipif(
    not _has_auth(),
    reason=f"Requires authentication at {DEFAULT_STORAGE_PATH}",
)


async def get_auth(cookies: dict) -> AuthTokens:
    """Fetch tokens and create AuthTokens."""
    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())

    async with httpx.AsyncClient() as http:
        resp = await http.get(
            "https://notebooklm.google.com/",
            headers={"Cookie": cookie_header},
            follow_redirects=True,
        )
        resp.raise_for_status()
        csrf = extract_csrf_from_html(resp.text)
        session_id = extract_session_id_from_html(resp.text)

    return AuthTokens(cookies=cookies, csrf_token=csrf, session_id=session_id)


@requires_auth
@pytest.mark.e2e
class TestNotebookWorkflow:
    """Test complete notebook workflow: create -> add source -> delete."""

    @pytest.mark.asyncio
    async def test_list_notebooks(self, auth_cookies):
        """Test listing existing notebooks."""
        auth = await get_auth(auth_cookies)

        async with NotebookLMClient(auth) as client:
            notebooks = await client.notebooks.list()

        assert isinstance(notebooks, list)

    @pytest.mark.asyncio
    async def test_create_and_delete_notebook(
        self, auth_cookies, created_notebooks, cleanup_notebooks
    ):
        """Test creating and deleting a notebook."""
        auth = await get_auth(auth_cookies)

        async with NotebookLMClient(auth) as client:
            notebook = await client.notebooks.create("E2E Test Notebook")
            created_notebooks.append(notebook.id)

            assert notebook.id is not None
            assert notebook.title == "E2E Test Notebook"

            deleted = await client.notebooks.delete(notebook.id)
            assert deleted is True
            created_notebooks.remove(notebook.id)

    @pytest.mark.asyncio
    async def test_add_url_source(
        self, auth_cookies, created_notebooks, cleanup_notebooks
    ):
        """Test adding a URL source to a notebook."""
        auth = await get_auth(auth_cookies)

        async with NotebookLMClient(auth) as client:
            notebook = await client.notebooks.create("E2E URL Source Test")
            created_notebooks.append(notebook.id)

            source = await client.sources.add_url(
                notebook.id,
                "https://en.wikipedia.org/wiki/Python_(programming_language)",
            )

            assert source.id is not None

    @pytest.mark.asyncio
    async def test_add_text_source(
        self, auth_cookies, created_notebooks, cleanup_notebooks
    ):
        """Test adding a text source to a notebook."""
        auth = await get_auth(auth_cookies)

        async with NotebookLMClient(auth) as client:
            notebook = await client.notebooks.create("E2E Text Source Test")
            created_notebooks.append(notebook.id)

            source = await client.sources.add_text(
                notebook.id,
                "Test Document",
                "This is a test document with some content for NotebookLM to analyze.",
            )

            assert source.id is not None
            assert source.title == "Test Document"


@requires_auth
@pytest.mark.e2e
@pytest.mark.slow
class TestArtifactGeneration:
    """Test artifact generation (audio, slide deck). These are slow tests.

    Note: These tests may fail due to API rate limiting or quota restrictions.
    """

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Audio API may be rate-limited or quota-restricted")
    async def test_generate_audio_starts(
        self, auth_cookies, created_notebooks, cleanup_notebooks
    ):
        """Test that audio generation starts (doesn't wait for completion)."""
        auth = await get_auth(auth_cookies)

        async with NotebookLMClient(auth) as client:
            notebook = await client.notebooks.create("E2E Audio Test")
            created_notebooks.append(notebook.id)

            await client.sources.add_text(
                notebook.id,
                "Audio Test Content",
                """
                This is a comprehensive document about artificial intelligence.
                AI has transformed many industries including healthcare, finance, and transportation.
                Machine learning algorithms can now recognize patterns in data that humans cannot.
                Deep learning has enabled breakthroughs in computer vision and natural language processing.
                The future of AI holds both promise and challenges for society.
                """,
            )

            status = await client.artifacts.generate_audio(
                notebook.id, instructions="Keep it brief and casual"
            )

            assert status.task_id is not None
            assert status.status in ("pending", "processing")
