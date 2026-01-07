import pytest
from .conftest import requires_auth
from notebooklm import Source


@requires_auth
@pytest.mark.e2e
class TestSourceOperations:
    @pytest.mark.asyncio
    async def test_add_text_source(
        self, client, test_notebook_id, created_sources, cleanup_sources
    ):
        source = await client.sources.add_text(
            test_notebook_id,
            "E2E Test Text Source",
            "This is test content for E2E testing. It contains enough text for NotebookLM to process.",
        )
        assert isinstance(source, Source)
        assert source.id is not None
        assert source.title == "E2E Test Text Source"
        created_sources.append(source.id)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_add_url_source(
        self, client, test_notebook_id, created_sources, cleanup_sources
    ):
        source = await client.sources.add_url(
            test_notebook_id, "https://httpbin.org/html"
        )
        assert isinstance(source, Source)
        assert source.id is not None
        assert source.url == "https://httpbin.org/html"
        created_sources.append(source.id)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_add_youtube_source(
        self, client, test_notebook_id, created_sources, cleanup_sources
    ):
        source = await client.sources.add_url(
            test_notebook_id, "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        )
        assert isinstance(source, Source)
        assert source.id is not None
        assert source.title is not None  # API returns title
        # Note: API might not return URL in add response, only id/title
        created_sources.append(source.id)

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
