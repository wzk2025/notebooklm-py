import asyncio
import pytest
from .conftest import requires_auth
from notebooklm import Source


@requires_auth
@pytest.mark.e2e
class TestSourceOperations:
    """Tests for source creation operations.

    Note: Source creation requires an OWNED notebook. The golden notebook
    (shared demo) is read-only - use temp_notebook fixture instead.
    """

    @pytest.mark.asyncio
    @pytest.mark.stable
    async def test_add_text_source(self, client, temp_notebook):
        """Test adding a text source to an owned notebook."""
        source = await client.sources.add_text(
            temp_notebook.id,
            "E2E Test Text Source",
            "This is test content for E2E testing. It contains enough text for NotebookLM to process.",
        )
        assert isinstance(source, Source)
        assert source.id is not None
        assert source.title == "E2E Test Text Source"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.stable
    async def test_add_url_source(self, client, temp_notebook):
        """Test adding a URL source to an owned notebook."""
        source = await client.sources.add_url(
            temp_notebook.id, "https://httpbin.org/html"
        )
        assert isinstance(source, Source)
        assert source.id is not None
        # URL may or may not be returned in response
        # assert source.url == "https://httpbin.org/html"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.stable
    async def test_add_youtube_source(self, client, temp_notebook):
        """Test adding a YouTube source to an owned notebook."""
        source = await client.sources.add_url(
            temp_notebook.id, "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        )
        assert isinstance(source, Source)
        assert source.id is not None
        # Title is returned for YouTube videos
        assert source.title is not None

    @pytest.mark.asyncio
    async def test_list_and_rename_source(self, client, test_notebook_id):
        # List sources
        sources = await client.sources.list(test_notebook_id)
        assert isinstance(sources, list)

        if not sources:
            pytest.skip("No sources available to rename")

        # Get first source
        source = sources[0]
        assert isinstance(source, Source)
        original_title = source.title

        # Rename
        renamed = await client.sources.rename(
            test_notebook_id, source.id, "Renamed Test Source"
        )
        assert isinstance(renamed, Source)
        assert renamed.title == "Renamed Test Source"

        # Restore original title
        if original_title:
            await client.sources.rename(test_notebook_id, source.id, original_title)


@requires_auth
@pytest.mark.e2e
class TestSourceRetrieval:
    @pytest.mark.asyncio
    async def test_list_sources(self, client, test_notebook_id):
        sources = await client.sources.list(test_notebook_id)
        assert isinstance(sources, list)
        assert all(isinstance(src, Source) for src in sources)

    @pytest.mark.asyncio
    async def test_get_source(self, client, test_notebook_id):
        """Test getting a specific source by ID."""
        sources = await client.sources.list(test_notebook_id)
        if not sources:
            pytest.skip("No sources available to get")

        source = await client.sources.get(test_notebook_id, sources[0].id)
        assert source is not None
        assert isinstance(source, Source)
        assert source.id == sources[0].id

    @pytest.mark.asyncio
    async def test_get_source_not_found(self, client, test_notebook_id):
        """Test getting a non-existent source returns None."""
        source = await client.sources.get(test_notebook_id, "nonexistent_source_id")
        assert source is None

    @pytest.mark.asyncio
    async def test_get_guide(self, client, test_notebook_id):
        """Test getting source guide/summary."""
        sources = await client.sources.list(test_notebook_id)
        if not sources:
            pytest.skip("No sources available for guide")

        guide = await client.sources.get_guide(test_notebook_id, sources[0].id)
        # get_guide returns dict with summary and keywords
        assert isinstance(guide, dict)
        assert "summary" in guide
        assert "keywords" in guide


@requires_auth
@pytest.mark.e2e
class TestSourceMutations:
    """Tests that create/delete sources - use temp_notebook to avoid affecting golden notebook."""

    @pytest.mark.asyncio
    @pytest.mark.stable
    async def test_delete_source(self, client, temp_notebook):
        """Test deleting a source."""
        # Create a source to delete
        source = await client.sources.add_text(
            temp_notebook.id,
            "Source to Delete",
            "This source will be deleted as part of the E2E test.",
        )
        assert source.id is not None

        # Delete it
        deleted = await client.sources.delete(temp_notebook.id, source.id)
        assert deleted is True

        # Verify it's gone
        sources = await client.sources.list(temp_notebook.id)
        source_ids = [s.id for s in sources]
        assert source.id not in source_ids

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_refresh_source(self, client, temp_notebook):
        """Test refreshing a URL source."""
        # Add a URL source
        source = await client.sources.add_url(
            temp_notebook.id, "https://httpbin.org/html"
        )
        assert source.id is not None

        # Refresh it
        await asyncio.sleep(2)  # Wait for initial processing

        result = await client.sources.refresh(temp_notebook.id, source.id)
        # refresh() always returns True if successful
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_check_freshness(self, client, temp_notebook):
        """Test checking source freshness."""
        # Add a URL source
        source = await client.sources.add_url(
            temp_notebook.id, "https://httpbin.org/html"
        )
        assert source.id is not None

        await asyncio.sleep(2)  # Wait for processing

        # Check freshness
        freshness = await client.sources.check_freshness(temp_notebook.id, source.id)
        # check_freshness() returns bool: True if fresh, False if stale
        assert isinstance(freshness, bool)
