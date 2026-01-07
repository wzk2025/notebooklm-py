"""Integration tests for NotebooksAPI."""

import pytest
from pytest_httpx import HTTPXMock

from notebooklm import NotebookLMClient, Notebook


class TestListNotebooks:
    @pytest.mark.asyncio
    async def test_list_notebooks_returns_notebooks(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        mock_list_notebooks_response,
    ):
        httpx_mock.add_response(content=mock_list_notebooks_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notebooks = await client.notebooks.list()

        assert len(notebooks) == 2
        assert all(isinstance(nb, Notebook) for nb in notebooks)
        assert notebooks[0].title == "My First Notebook"
        assert notebooks[0].id == "nb_001"

    @pytest.mark.asyncio
    async def test_list_notebooks_request_format(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        mock_list_notebooks_response,
    ):
        httpx_mock.add_response(content=mock_list_notebooks_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.list()

        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert "wXbhsf" in str(request.url)
        assert b"f.req=" in request.content

    @pytest.mark.asyncio
    async def test_request_includes_cookies(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        mock_list_notebooks_response,
    ):
        httpx_mock.add_response(content=mock_list_notebooks_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.list()

        request = httpx_mock.get_request()
        cookie_header = request.headers.get("cookie", "")
        assert "SID=test_sid" in cookie_header
        assert "HSID=test_hsid" in cookie_header

    @pytest.mark.asyncio
    async def test_request_includes_csrf(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        mock_list_notebooks_response,
    ):
        httpx_mock.add_response(content=mock_list_notebooks_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.list()

        request = httpx_mock.get_request()
        body = request.content.decode()
        assert "at=test_csrf_token" in body


class TestCreateNotebook:
    @pytest.mark.asyncio
    async def test_create_notebook(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "CCqFvf",
            [
                "My Notebook",
                [],
                "new_nb_id",
                "📓",
                None,
                [None, None, None, None, None, [1704067200, 0]],
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notebook = await client.notebooks.create("My Notebook")

        assert isinstance(notebook, Notebook)
        assert notebook.id == "new_nb_id"
        assert notebook.title == "My Notebook"

    @pytest.mark.asyncio
    async def test_create_notebook_request_contains_title(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "CCqFvf",
            ["Test Title", [], "id", "📓", None, [None, None, None, None, None, [1704067200, 0]]],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.create("Test Title")

        request = httpx_mock.get_request()
        assert "CCqFvf" in str(request.url)


class TestGetNotebook:
    @pytest.mark.asyncio
    async def test_get_notebook(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [["source1"], ["source2"]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notebook = await client.notebooks.get("nb_123")

        assert isinstance(notebook, Notebook)
        assert notebook.id == "nb_123"
        assert notebook.title == "Test Notebook"

    @pytest.mark.asyncio
    async def test_get_notebook_uses_source_path(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "rLM1Ne",
            [["Name", [], "nb_123", "📘", None, [None, None, None, None, None, [1704067200, 0]]]],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.get("nb_123")

        request = httpx_mock.get_request()
        assert "source-path=%2Fnotebook%2Fnb_123" in str(request.url)


class TestDeleteNotebook:
    @pytest.mark.asyncio
    async def test_delete_notebook(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response("WWINqb", [True])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notebooks.delete("nb_123")

        assert result is True


class TestSummary:
    @pytest.mark.asyncio
    async def test_get_summary(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "VfAZjd", ["Summary of the notebook content..."]
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notebooks.get_summary("nb_123")

        assert "Summary" in result


class TestRenameNotebook:
    @pytest.mark.asyncio
    async def test_rename_notebook(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        # First response for rename (returns null)
        rename_response = build_rpc_response("s0tc2d", None)
        httpx_mock.add_response(content=rename_response.encode())
        # Second response for get_notebook call after rename
        get_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "New Title",
                    [],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        httpx_mock.add_response(content=get_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notebook = await client.notebooks.rename("nb_123", "New Title")

        assert isinstance(notebook, Notebook)
        assert notebook.id == "nb_123"
        assert notebook.title == "New Title"

    @pytest.mark.asyncio
    async def test_rename_notebook_request_format(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        # Rename response (returns null)
        rename_response = build_rpc_response("s0tc2d", None)
        httpx_mock.add_response(content=rename_response.encode())
        # Get notebook response after rename
        get_response = build_rpc_response(
            "rLM1Ne",
            [["Renamed", [], "nb_123", "📘", None, [None, None, None, None, None, [1704067200, 0]]]],
        )
        httpx_mock.add_response(content=get_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.rename("nb_123", "Renamed")

        request = httpx_mock.get_requests()[0]
        assert "s0tc2d" in str(request.url)
        assert "source-path=%2F" in str(request.url)


class TestNotebooksAPIAdditional:
    """Additional integration tests for NotebooksAPI."""

    @pytest.mark.asyncio
    async def test_share_notebook(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test sharing a notebook with settings."""
        response = build_rpc_response(
            "QDyure",
            ["https://notebooklm.google.com/notebook/abc123?share=true"],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            # share() takes settings dict, not public=True
            result = await client.notebooks.share("nb_123", settings={"public": True})

        assert result is not None
        request = httpx_mock.get_request()
        assert "QDyure" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_summary_additional(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting notebook summary."""
        response = build_rpc_response(
            "VfAZjd",
            ["This is a comprehensive summary of the notebook content..."],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notebooks.get_summary("nb_123")

        assert "summary" in result.lower()

    @pytest.mark.asyncio
    async def test_get_analytics(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting analytics for notebook."""
        response = build_rpc_response(
            "AUrzMb",
            [10, 5, 3],  # views, edits, shares
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notebooks.get_analytics("nb_123")

        assert result is not None
        request = httpx_mock.get_request()
        assert "AUrzMb" in str(request.url)

    @pytest.mark.asyncio
    async def test_list_featured_basic(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing featured notebooks with default params."""
        response = build_rpc_response(
            "nS9Qlc",  # LIST_FEATURED_PROJECTS
            [[["featured_nb_1", "Featured Title", "icon"], ["featured_nb_2", "Another Featured", "icon"]]],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notebooks.list_featured()

        assert result is not None
        request = httpx_mock.get_request()
        assert "nS9Qlc" in str(request.url)

    @pytest.mark.asyncio
    async def test_list_featured_with_pagination(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing featured notebooks with pagination."""
        response = build_rpc_response(
            "nS9Qlc",  # LIST_FEATURED_PROJECTS
            [[["featured_nb_1", "Featured", "icon"]], "next_page_token"],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notebooks.list_featured(page_size=5, page_token="token123")

        assert result is not None

    @pytest.mark.asyncio
    async def test_remove_from_recent(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test removing notebook from recent list."""
        response = build_rpc_response("fejl7e", None)  # REMOVE_RECENTLY_VIEWED
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.remove_from_recent("nb_123")

        request = httpx_mock.get_request()
        assert "fejl7e" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_raw(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting raw notebook data."""
        raw_data = [
            ["Test Notebook", [["src1"], ["src2"]], "nb_123", "📘"],
            ["extra", "metadata"],
        ]
        response = build_rpc_response("rLM1Ne", raw_data)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notebooks.get_raw("nb_123")

        assert result == raw_data
        request = httpx_mock.get_request()
        assert "source-path=%2Fnotebook%2Fnb_123" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_description(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting notebook description with summary and topics."""
        response = build_rpc_response(
            "VfAZjd",
            [
                ["This notebook covers AI research."],
                [[
                    ["What are the main findings?", "Explain the key findings"],
                    ["How was the study conducted?", "Describe methodology"],
                ]],
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            description = await client.notebooks.get_description("nb_123")

        assert description.summary == "This notebook covers AI research."
        assert len(description.suggested_topics) == 2
        assert description.suggested_topics[0].question == "What are the main findings?"
        assert description.suggested_topics[0].prompt == "Explain the key findings"


class TestNotebookEdgeCases:
    """Test edge cases for NotebooksAPI."""

    @pytest.mark.asyncio
    async def test_list_notebooks_empty(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing notebooks when none exist."""
        response = build_rpc_response("wXbhsf", [])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notebooks = await client.notebooks.list()

        assert notebooks == []

    @pytest.mark.asyncio
    async def test_list_notebooks_nested_empty(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing notebooks with nested empty array."""
        response = build_rpc_response("wXbhsf", [[]])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notebooks = await client.notebooks.list()

        assert notebooks == []

    @pytest.mark.asyncio
    async def test_get_summary_empty(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting summary when empty."""
        response = build_rpc_response("VfAZjd", [])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notebooks.get_summary("nb_123")

        assert result == ""

    @pytest.mark.asyncio
    async def test_get_description_empty_topics(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting description with no suggested topics."""
        response = build_rpc_response(
            "VfAZjd",
            [["Summary text"], []],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            description = await client.notebooks.get_description("nb_123")

        assert description.summary == "Summary text"
        assert description.suggested_topics == []

    @pytest.mark.asyncio
    async def test_get_description_malformed_topics(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting description with malformed topic data."""
        response = build_rpc_response(
            "VfAZjd",
            [
                ["Summary"],
                [[
                    ["Valid question", "Valid prompt"],
                    ["Only question"],  # Missing prompt
                    "not a list",  # Not a list
                ]],
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            description = await client.notebooks.get_description("nb_123")

        assert description.summary == "Summary"
        # Should only include valid topics
        assert len(description.suggested_topics) == 1
        assert description.suggested_topics[0].question == "Valid question"
