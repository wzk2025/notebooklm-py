"""Integration tests for NotebookLM API client."""

import pytest
from pytest_httpx import HTTPXMock

from notebooklm import NotebookLMClient, Notebook, Source, Artifact
from notebooklm import AudioFormat, AudioLength, VideoFormat, VideoStyle
from notebooklm.auth import AuthTokens


@pytest.fixture
def auth_tokens():
    return AuthTokens(
        cookies={
            "SID": "test_sid",
            "HSID": "test_hsid",
            "SSID": "test_ssid",
            "APISID": "test_apisid",
            "SAPISID": "test_sapisid",
        },
        csrf_token="test_csrf_token",
        session_id="test_session_id",
    )


class TestClientInitialization:
    @pytest.mark.asyncio
    async def test_client_initialization(self, auth_tokens):
        async with NotebookLMClient(auth_tokens) as client:
            assert client._core.auth == auth_tokens
            assert client._core._http_client is not None

    @pytest.mark.asyncio
    async def test_client_context_manager_closes(self, auth_tokens):
        async with NotebookLMClient(auth_tokens) as client:
            http = client._core._http_client
        assert client._core._http_client is None

    @pytest.mark.asyncio
    async def test_client_raises_if_not_initialized(self, auth_tokens):
        client = NotebookLMClient(auth_tokens)
        with pytest.raises(RuntimeError, match="not initialized"):
            await client.notebooks.list()


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


class TestAddSource:
    @pytest.mark.asyncio
    async def test_add_source_url(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "izAoDd",
            [
                [
                    [
                        ["source_id"],
                        "Example Site",
                        [None, 11, None, None, 5, None, 1, ["https://example.com"]],
                        [None, 2],
                    ]
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            source = await client.sources.add_url("nb_123", "https://example.com")

        assert isinstance(source, Source)
        assert source.id == "source_id"
        assert source.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_add_source_text(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "izAoDd", [[[["source_id"], "My Document", [None, 11], [None, 2]]]]
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            source = await client.sources.add_text(
                "nb_123", "My Document", "This is the content"
            )

        assert isinstance(source, Source)
        assert source.id == "source_id"
        assert source.title == "My Document"


class TestStudioContent:
    @pytest.mark.asyncio
    async def test_generate_audio(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["src_001"], "Source 1", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        httpx_mock.add_response(content=notebook_response.encode())

        audio_response = build_rpc_response(
            "R7cb6c", [["artifact_123", "Audio Overview", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=audio_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_audio(notebook_id="nb_123")

        assert result is not None
        assert result.task_id == "artifact_123"
        assert result.status in ("pending", "in_progress", "processing")

        request = httpx_mock.get_requests()[-1]
        assert "R7cb6c" in str(request.url)

    @pytest.mark.asyncio
    async def test_generate_audio_with_format_and_length(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["src_001"], "Source 1", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        httpx_mock.add_response(content=notebook_response.encode())

        response = build_rpc_response(
            "R7cb6c", [["artifact_123", "Audio Overview", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_audio(
                notebook_id="nb_123",
                audio_format=AudioFormat.DEBATE,
                audio_length=AudioLength.LONG,
            )

        assert result is not None
        assert result.task_id == "artifact_123"

    @pytest.mark.asyncio
    async def test_generate_video_with_format_and_style(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        video_response = build_rpc_response(
            "R7cb6c", [["artifact_456", "Video Overview", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=video_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_video(
                notebook_id="nb_123",
                video_format=VideoFormat.BRIEF,
                video_style=VideoStyle.ANIME,
            )

        assert result is not None
        assert result.task_id == "artifact_456"

    @pytest.mark.asyncio
    async def test_generate_slide_deck(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        slide_deck_response = build_rpc_response(
            "R7cb6c", [["artifact_456", "Slide Deck", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=slide_deck_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_slide_deck(notebook_id="nb_123")

        assert result is not None
        assert result.task_id == "artifact_456"

    @pytest.mark.asyncio
    async def test_poll_studio_status(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "gArtLc", ["task_id_123", "completed", "https://audio.url"]
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.poll_status(
                notebook_id="nb_123",
                task_id="task_id_123",
            )

        assert result is not None
        assert result.status == "completed"
        assert result.url == "https://audio.url"


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


class TestDeleteSource:
    @pytest.mark.asyncio
    async def test_delete_source(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response("tGMBJ", [True])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.sources.delete("nb_123", "source_456")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_source_request_format(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response("tGMBJ", [True])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.sources.delete("nb_123", "source_456")

        request = httpx_mock.get_request()
        assert "tGMBJ" in str(request.url)
        assert "source-path=%2Fnotebook%2Fnb_123" in str(request.url)


class TestGetSource:
    @pytest.mark.asyncio
    async def test_get_source(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        # get_source filters from get_notebook, so mock GET_NOTEBOOK response
        response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [
                        [["source_456"], "Source Title", [None, 0, [1704067200, 0]], [None, 2]],
                        [["source_789"], "Other Source", [None, 0, [1704153600, 0]], [None, 2]],
                    ],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            source = await client.sources.get("nb_123", "source_456")

        assert isinstance(source, Source)
        assert source.id == "source_456"
        assert source.title == "Source Title"


class TestGenerateQuiz:
    @pytest.mark.asyncio
    async def test_generate_quiz(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        quiz_response = build_rpc_response(
            "R7cb6c", [["quiz_123", "Quiz", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=quiz_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_quiz("nb_123")

        assert result is not None
        assert result.task_id == "quiz_123"


class TestDeleteStudioContent:
    @pytest.mark.asyncio
    async def test_delete_studio_content(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response("V5N4be", [True])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.delete("nb_123", "task_id_123")

        assert result is True


class TestMindMap:
    @pytest.mark.asyncio
    async def test_generate_mind_map(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        mindmap_response = build_rpc_response("yyryJe", None)
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=mindmap_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_mind_map("nb_123")

        # Mind map returns dict or None
        assert result is None or isinstance(result, dict)


# =============================================================================
# Notes API Tests
# =============================================================================


class TestNotesAPI:
    """Integration tests for the NotesAPI."""

    @pytest.mark.asyncio
    async def test_list_notes(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing notes in a notebook."""
        response = build_rpc_response(
            "cFji9",
            [
                [
                    ["note_001", ["note_001", "Note content 1", None, None, "My First Note"]],
                    ["note_002", ["note_002", "Note content 2", None, None, "My Second Note"]],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notes = await client.notes.list("nb_123")

        assert len(notes) == 2
        assert notes[0].id == "note_001"
        assert notes[0].title == "My First Note"
        assert notes[0].content == "Note content 1"
        assert notes[1].id == "note_002"
        assert notes[1].title == "My Second Note"

    @pytest.mark.asyncio
    async def test_list_notes_empty(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing notes when notebook is empty."""
        response = build_rpc_response("cFji9", [[]])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notes = await client.notes.list("nb_123")

        assert notes == []

    @pytest.mark.asyncio
    async def test_list_notes_excludes_mind_maps(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test that list() filters out mind maps."""
        response = build_rpc_response(
            "cFji9",
            [
                [
                    ["note_001", ["note_001", "Regular note content", None, None, "Regular Note"]],
                    # Mind map has JSON with 'children' key
                    ["mm_001", ["mm_001", '{"title":"Mind Map","children":[]}', None, None, "Mind Map"]],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notes = await client.notes.list("nb_123")

        assert len(notes) == 1
        assert notes[0].id == "note_001"

    @pytest.mark.asyncio
    async def test_get_note(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting a specific note by ID."""
        response = build_rpc_response(
            "cFji9",
            [
                [
                    ["note_001", ["note_001", "Content 1", None, None, "Note 1"]],
                    ["note_002", ["note_002", "Content 2", None, None, "Note 2"]],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            note = await client.notes.get("nb_123", "note_002")

        assert note is not None
        assert note.id == "note_002"
        assert note.title == "Note 2"
        assert note.content == "Content 2"

    @pytest.mark.asyncio
    async def test_get_note_not_found(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting a note that doesn't exist."""
        response = build_rpc_response(
            "cFji9",
            [
                [
                    ["note_001", ["note_001", "Content", None, None, "Title"]],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            note = await client.notes.get("nb_123", "nonexistent")

        assert note is None

    @pytest.mark.asyncio
    async def test_create_note(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test creating a new note."""
        # First response for CREATE_NOTE
        create_response = build_rpc_response("CYK0Xb", [["new_note_id"]])
        httpx_mock.add_response(content=create_response.encode())

        # Second response for UPDATE_NOTE (sets title/content)
        update_response = build_rpc_response("cYAfTb", None)
        httpx_mock.add_response(content=update_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            note = await client.notes.create("nb_123", "My Title", "My Content")

        assert note.id == "new_note_id"
        assert note.title == "My Title"
        assert note.content == "My Content"

        # Verify CREATE_NOTE was called
        requests = httpx_mock.get_requests()
        assert "CYK0Xb" in str(requests[0].url)
        # Verify UPDATE_NOTE was called after creation
        assert "cYAfTb" in str(requests[1].url)

    @pytest.mark.asyncio
    async def test_update_note(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test updating an existing note."""
        response = build_rpc_response("cYAfTb", None)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notes.update("nb_123", "note_001", "Updated content", "Updated title")

        request = httpx_mock.get_request()
        assert "cYAfTb" in str(request.url)
        assert "source-path=%2Fnotebook%2Fnb_123" in str(request.url)

    @pytest.mark.asyncio
    async def test_delete_note(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test deleting a note."""
        response = build_rpc_response("AH0mwd", None)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notes.delete("nb_123", "note_001")

        assert result is True
        request = httpx_mock.get_request()
        assert "AH0mwd" in str(request.url)

    @pytest.mark.asyncio
    async def test_list_mind_maps(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing mind maps in a notebook."""
        response = build_rpc_response(
            "cFji9",
            [
                [
                    ["note_001", ["note_001", "Regular note", None, None, "Note"]],
                    ["mm_001", ["mm_001", '{"title":"Mind Map 1","children":[]}', None, None, "MM1"]],
                    ["mm_002", ["mm_002", '{"nodes":[{"id":"1"}]}', None, None, "MM2"]],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            mind_maps = await client.notes.list_mind_maps("nb_123")

        assert len(mind_maps) == 2

    @pytest.mark.asyncio
    async def test_delete_mind_map(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test deleting a mind map."""
        response = build_rpc_response("AH0mwd", None)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notes.delete_mind_map("nb_123", "mm_001")

        assert result is True
        request = httpx_mock.get_request()
        assert "AH0mwd" in str(request.url)


# =============================================================================
# Chat API Tests
# =============================================================================


class TestChatAPI:
    """Integration tests for the ChatAPI."""

    @pytest.mark.asyncio
    async def test_get_history(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting conversation history."""
        response = build_rpc_response(
            "hPTbtc",
            [
                ["conv_001", "What is ML?", "Machine learning is...", 1704067200],
                ["conv_002", "Explain AI", "Artificial intelligence...", 1704153600],
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.chat.get_history("nb_123")

        assert result is not None
        request = httpx_mock.get_request()
        assert "hPTbtc" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_history_empty(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting empty conversation history."""
        response = build_rpc_response("hPTbtc", [])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.chat.get_history("nb_123")

        assert result == []

    @pytest.mark.asyncio
    async def test_configure_default_mode(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test configuring chat with default settings."""
        response = build_rpc_response("s0tc2d", None)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.chat.configure("nb_123")

        request = httpx_mock.get_request()
        assert "s0tc2d" in str(request.url)

    @pytest.mark.asyncio
    async def test_configure_learning_guide_mode(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test configuring chat as learning guide."""
        from notebooklm.rpc import ChatGoal, ChatResponseLength

        response = build_rpc_response("s0tc2d", None)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.chat.configure(
                "nb_123",
                goal=ChatGoal.LEARNING_GUIDE,
                response_length=ChatResponseLength.LONGER,
            )

        request = httpx_mock.get_request()
        assert "s0tc2d" in str(request.url)

    @pytest.mark.asyncio
    async def test_configure_custom_mode_without_prompt_raises(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
    ):
        """Test that CUSTOM mode without prompt raises ValueError."""
        from notebooklm.rpc import ChatGoal

        async with NotebookLMClient(auth_tokens) as client:
            with pytest.raises(ValueError, match="custom_prompt is required"):
                await client.chat.configure("nb_123", goal=ChatGoal.CUSTOM)

    @pytest.mark.asyncio
    async def test_configure_custom_mode_with_prompt(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test configuring chat with custom prompt."""
        from notebooklm.rpc import ChatGoal

        response = build_rpc_response("s0tc2d", None)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.chat.configure(
                "nb_123",
                goal=ChatGoal.CUSTOM,
                custom_prompt="You are a helpful tutor.",
            )

        request = httpx_mock.get_request()
        assert "s0tc2d" in str(request.url)

    @pytest.mark.asyncio
    async def test_set_mode(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test setting chat mode with predefined config."""
        from notebooklm.types import ChatMode

        response = build_rpc_response("s0tc2d", None)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.chat.set_mode("nb_123", ChatMode.CONCISE)

        request = httpx_mock.get_request()
        assert "s0tc2d" in str(request.url)

    def test_get_cached_turns_empty(self, auth_tokens):
        """Test getting cached turns for new conversation."""
        from notebooklm import NotebookLMClient

        client = NotebookLMClient(auth_tokens)
        # Note: can't use async context manager without initialization
        # but cached turns don't require HTTP
        turns = client.chat.get_cached_turns("nonexistent_conv")
        assert turns == []

    def test_clear_cache(self, auth_tokens):
        """Test clearing conversation cache."""
        from notebooklm import NotebookLMClient

        client = NotebookLMClient(auth_tokens)
        # Clearing non-existent conversation returns False, clearing all returns True
        result = client.chat.clear_cache("some_conv")
        # Non-existent conversation returns False
        assert result is False

    def test_clear_all_cache(self, auth_tokens):
        """Test clearing all conversation caches."""
        from notebooklm import NotebookLMClient

        client = NotebookLMClient(auth_tokens)
        result = client.chat.clear_cache()
        assert result is True


# =============================================================================
# Research API Tests
# =============================================================================


class TestResearchAPI:
    """Integration tests for the ResearchAPI."""

    @pytest.mark.asyncio
    async def test_start_fast_web_research(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test starting fast web research."""
        response = build_rpc_response(
            "Ljjv0c", ["task_123", "report_456"]
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.research.start(
                "nb_123", "quantum computing", source="web", mode="fast"
            )

        assert result is not None
        assert result["task_id"] == "task_123"
        assert result["report_id"] == "report_456"
        assert result["mode"] == "fast"

        request = httpx_mock.get_request()
        assert "Ljjv0c" in str(request.url)

    @pytest.mark.asyncio
    async def test_start_fast_drive_research(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test starting fast drive research."""
        response = build_rpc_response(
            "Ljjv0c", ["task_789", None]
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.research.start(
                "nb_123", "project docs", source="drive", mode="fast"
            )

        assert result is not None
        assert result["task_id"] == "task_789"
        assert result["mode"] == "fast"

    @pytest.mark.asyncio
    async def test_start_deep_web_research(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test starting deep web research."""
        response = build_rpc_response(
            "QA9ei", ["task_deep", "report_deep"]
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.research.start(
                "nb_123", "AI ethics", source="web", mode="deep"
            )

        assert result is not None
        assert result["mode"] == "deep"

        request = httpx_mock.get_request()
        assert "QA9ei" in str(request.url)

    @pytest.mark.asyncio
    async def test_start_deep_drive_research_raises(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
    ):
        """Test that deep research on drive raises ValueError."""
        async with NotebookLMClient(auth_tokens) as client:
            with pytest.raises(ValueError, match="Deep Research only supports Web"):
                await client.research.start(
                    "nb_123", "query", source="drive", mode="deep"
                )

    @pytest.mark.asyncio
    async def test_start_invalid_source_raises(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
    ):
        """Test that invalid source raises ValueError."""
        async with NotebookLMClient(auth_tokens) as client:
            with pytest.raises(ValueError, match="Invalid source"):
                await client.research.start("nb_123", "query", source="invalid")

    @pytest.mark.asyncio
    async def test_start_invalid_mode_raises(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
    ):
        """Test that invalid mode raises ValueError."""
        async with NotebookLMClient(auth_tokens) as client:
            with pytest.raises(ValueError, match="Invalid mode"):
                await client.research.start("nb_123", "query", mode="invalid")

    @pytest.mark.asyncio
    async def test_poll_completed(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test polling completed research."""
        response = build_rpc_response(
            "e3bVqc",
            [
                [
                    "task_123",
                    [
                        None,
                        ["quantum computing"],
                        None,
                        [
                            [
                                ["https://example.com", "Quantum Guide", "Description"],
                                ["https://another.com", "More Info", "Desc 2"],
                            ],
                            "Summary of quantum computing research...",
                        ],
                        2,  # status code 2 = completed
                    ],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.research.poll("nb_123")

        assert result["status"] == "completed"
        assert result["task_id"] == "task_123"
        assert len(result["sources"]) == 2
        assert result["sources"][0]["url"] == "https://example.com"
        assert result["sources"][0]["title"] == "Quantum Guide"
        assert "Summary" in result["summary"]

    @pytest.mark.asyncio
    async def test_poll_in_progress(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test polling research that's still in progress."""
        response = build_rpc_response(
            "e3bVqc",
            [
                [
                    "task_456",
                    [
                        None,
                        ["machine learning"],
                        None,
                        [],
                        1,  # status code 1 = in_progress
                    ],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.research.poll("nb_123")

        assert result["status"] == "in_progress"
        assert result["task_id"] == "task_456"

    @pytest.mark.asyncio
    async def test_poll_no_research(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test polling when no research exists."""
        response = build_rpc_response("e3bVqc", [])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.research.poll("nb_123")

        assert result["status"] == "no_research"

    @pytest.mark.asyncio
    async def test_import_sources(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test importing research sources."""
        # Response structure: [[[["src_id"], "title"], ...]]
        # The implementation unwraps this to access [["src_id"], "title"] items
        response = build_rpc_response(
            "LBwxtb",
            [
                [
                    [["src_001"], "Quantum Computing Guide"],
                    [["src_002"], "AI Research Paper"],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            sources_to_import = [
                {"url": "https://example.com/quantum", "title": "Quantum Computing Guide"},
                {"url": "https://example.com/ai", "title": "AI Research Paper"},
            ]
            result = await client.research.import_sources(
                "nb_123", "task_123", sources_to_import
            )

        assert len(result) == 2
        assert result[0]["id"] == "src_001"
        assert result[0]["title"] == "Quantum Computing Guide"

        request = httpx_mock.get_request()
        assert "LBwxtb" in str(request.url)

    @pytest.mark.asyncio
    async def test_import_sources_empty(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
    ):
        """Test importing empty sources list."""
        async with NotebookLMClient(auth_tokens) as client:
            result = await client.research.import_sources("nb_123", "task_123", [])

        assert result == []


# =============================================================================
# Sources API Tests (Additional)
# =============================================================================


class TestSourcesAPI:
    """Integration tests for SourcesAPI methods."""

    @pytest.mark.asyncio
    async def test_list_sources(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing sources with various types."""
        response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [
                        [["src_001"], "My Article", [None, 11, [1704067200, 0], None, 5, None, None, ["https://example.com"]], [None, 2]],
                        [["src_002"], "My Text", [None, 0, [1704153600, 0]], [None, 2]],
                        [["src_003"], "YouTube Video", [None, 11, [1704240000, 0], None, 5, None, None, ["https://youtube.com/watch?v=abc"]], [None, 2]],
                    ],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            sources = await client.sources.list("nb_123")

        assert len(sources) == 3
        assert sources[0].id == "src_001"
        assert sources[0].source_type == "url"
        assert sources[0].url == "https://example.com"
        assert sources[2].source_type == "youtube"

    @pytest.mark.asyncio
    async def test_list_sources_empty(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing sources from empty notebook."""
        response = build_rpc_response(
            "rLM1Ne",
            [["Empty Notebook", [], "nb_123", "📘", None, [None, None, None, None, None, [1704067200, 0]]]],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            sources = await client.sources.list("nb_123")

        assert sources == []

    @pytest.mark.asyncio
    async def test_get_source_not_found(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting a non-existent source."""
        response = build_rpc_response(
            "rLM1Ne",
            [["Notebook", [[["src_001"], "Source 1", [None, 0], [None, 2]]], "nb_123", "📘", None, [None, None, None, None, None, [1704067200, 0]]]],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            source = await client.sources.get("nb_123", "nonexistent")

        assert source is None

    @pytest.mark.asyncio
    async def test_add_drive_source(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test adding a Google Drive source."""
        response = build_rpc_response(
            "izAoDd",
            [[[["drive_001"], "My Doc", [None, 0], [None, 2]]]],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            source = await client.sources.add_drive(
                "nb_123",
                file_id="abc123xyz",
                title="My Doc",
                mime_type="application/vnd.google-apps.document",
            )

        assert source is not None
        request = httpx_mock.get_request()
        assert "izAoDd" in str(request.url)

    @pytest.mark.asyncio
    async def test_refresh_source(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test refreshing a source."""
        response = build_rpc_response("FLmJqe", None)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.sources.refresh("nb_123", "src_001")

        assert result is True
        request = httpx_mock.get_request()
        assert "FLmJqe" in str(request.url)

    @pytest.mark.asyncio
    async def test_check_freshness_fresh(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test checking freshness - source is fresh."""
        response = build_rpc_response("yR9Yof", True)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            is_fresh = await client.sources.check_freshness("nb_123", "src_001")

        assert is_fresh is True

    @pytest.mark.asyncio
    async def test_check_freshness_stale(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test checking freshness - source is stale."""
        response = build_rpc_response("yR9Yof", False)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            is_fresh = await client.sources.check_freshness("nb_123", "src_001")

        assert is_fresh is False

    @pytest.mark.asyncio
    async def test_get_guide(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting source guide."""
        response = build_rpc_response(
            "tr032e",
            [
                [
                    None,
                    ["This is a **summary** of the source content..."],
                    [["keyword1", "keyword2", "keyword3"]],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            guide = await client.sources.get_guide("nb_123", "src_001")

        assert "summary" in guide
        assert "keywords" in guide
        assert "**summary**" in guide["summary"]

    @pytest.mark.asyncio
    async def test_get_guide_empty(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting guide for source with no AI analysis."""
        response = build_rpc_response("tr032e", [[None, [], []]])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            guide = await client.sources.get_guide("nb_123", "src_001")

        assert guide["summary"] == ""
        assert guide["keywords"] == []

    @pytest.mark.asyncio
    async def test_rename_source(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test renaming a source."""
        response = build_rpc_response("b7Wfje", None)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            source = await client.sources.rename("nb_123", "src_001", "New Title")

        assert source.title == "New Title"

        request = httpx_mock.get_request()
        assert "b7Wfje" in str(request.url)


# =============================================================================
# Artifacts API Tests (Additional)
# =============================================================================


class TestArtifactsAPI:
    """Integration tests for ArtifactsAPI methods."""

    @pytest.mark.asyncio
    async def test_list_artifacts(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing all artifacts."""
        response = build_rpc_response(
            "gArtLc",
            [
                ["art_001", "Audio Overview", 1, None, "completed"],
                ["art_002", "Quiz", 4, None, "completed"],
                ["art_003", "Study Guide", 2, None, "completed"],
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            artifacts = await client.artifacts.list("nb_123")

        assert isinstance(artifacts, list)

    @pytest.mark.asyncio
    async def test_rename_artifact(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test renaming an artifact."""
        response = build_rpc_response("rc3d8d", None)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            # rename() returns None on success
            await client.artifacts.rename("nb_123", "art_001", "New Title")

        request = httpx_mock.get_request()
        assert "rc3d8d" in str(request.url)

    @pytest.mark.asyncio
    async def test_export_artifact(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test exporting an artifact."""
        response = build_rpc_response("Krh3pd", ["export_content_here"])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.export("nb_123", "art_001")

        assert result is not None
        request = httpx_mock.get_request()
        assert "Krh3pd" in str(request.url)

    @pytest.mark.asyncio
    async def test_generate_flashcards(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test generating flashcards."""
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        flashcards_response = build_rpc_response(
            "R7cb6c", [["fc_123", "Flashcards", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=flashcards_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_flashcards("nb_123")

        assert result is not None
        assert result.task_id == "fc_123"

    @pytest.mark.asyncio
    async def test_generate_study_guide(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test generating study guide."""
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        guide_response = build_rpc_response(
            "R7cb6c", [["sg_123", "Study Guide", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=guide_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_study_guide("nb_123")

        assert result is not None
        assert result.task_id == "sg_123"

    @pytest.mark.asyncio
    async def test_generate_infographic(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test generating infographic."""
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        infographic_response = build_rpc_response(
            "R7cb6c", [["ig_123", "Infographic", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=infographic_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_infographic("nb_123")

        assert result is not None
        assert result.task_id == "ig_123"

    @pytest.mark.asyncio
    async def test_generate_data_table(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test generating data table."""
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        table_response = build_rpc_response(
            "R7cb6c", [["dt_123", "Data Table", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=table_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_data_table("nb_123")

        assert result is not None
        assert result.task_id == "dt_123"

    @pytest.mark.asyncio
    async def test_get_artifact_not_found(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting a non-existent artifact returns None."""
        # get() uses list() internally then filters
        response = build_rpc_response("gArtLc", [])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.get("nb_123", "nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_audio_artifacts(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing audio artifacts."""
        response = build_rpc_response(
            "gArtLc",
            [
                ["art_001", "Audio Overview", 1, None, 3],  # type 1 = audio
                ["art_002", "Quiz", 4, None, 3],
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            artifacts = await client.artifacts.list_audio("nb_123")

        # Returns filtered audio only
        assert isinstance(artifacts, list)

    @pytest.mark.asyncio
    async def test_list_video_artifacts(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing video artifacts."""
        response = build_rpc_response(
            "gArtLc",
            [
                ["art_001", "Video Overview", 3, None, 3],  # type 3 = video
                ["art_002", "Audio Overview", 1, None, 3],
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            artifacts = await client.artifacts.list_video("nb_123")

        assert isinstance(artifacts, list)

    @pytest.mark.asyncio
    async def test_list_quiz_artifacts(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing quiz artifacts (list_quizzes)."""
        # Quiz artifacts have type 4 with variant marker
        response = build_rpc_response(
            "gArtLc",
            [
                ["art_001", "Quiz", 4, None, 3, None, [None, None, None, None, None, None, 2]],  # variant 2 = quiz
                ["art_002", "Flashcards", 4, None, 3, None, [None, None, None, None, None, None, 1]],  # variant 1 = flashcards
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            artifacts = await client.artifacts.list_quizzes("nb_123")

        assert isinstance(artifacts, list)

    @pytest.mark.asyncio
    async def test_delete_artifact(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test deleting an artifact."""
        # Note: delete() uses DELETE_STUDIO (V5N4be), not DELETE_ARTIFACT
        response = build_rpc_response("V5N4be", None)
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.delete("nb_123", "art_001")

        assert result is True
        request = httpx_mock.get_request()
        assert "V5N4be" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_audio_overview(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test getting audio overview status."""
        response = build_rpc_response(
            "VUsiyb",
            [["audio_001", "Audio Overview", None, None, 3, None]],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.get_audio_overview("nb_123")

        assert result is not None
        request = httpx_mock.get_request()
        assert "VUsiyb" in str(request.url)

    @pytest.mark.asyncio
    async def test_share_audio(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test sharing audio overview."""
        response = build_rpc_response(
            "RGP97b",
            ["https://notebooklm.google.com/share/abc123"],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.share_audio("nb_123", public=True)

        assert result is not None
        request = httpx_mock.get_request()
        assert "RGP97b" in str(request.url)

    @pytest.mark.asyncio
    async def test_list_flashcards(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing flashcard artifacts."""
        response = build_rpc_response(
            "gArtLc",
            [
                ["art_001", "Quiz", 4, None, 3, None, [None, None, None, None, None, None, 2]],  # quiz
                ["art_002", "Flashcards", 4, None, 3, None, [None, None, None, None, None, None, 1]],  # flashcards
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            artifacts = await client.artifacts.list_flashcards("nb_123")

        assert isinstance(artifacts, list)

    @pytest.mark.asyncio
    async def test_list_infographics(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing infographic artifacts."""
        response = build_rpc_response(
            "gArtLc",
            [
                ["art_001", "Infographic", 7, None, 3],  # type 7 = infographic
                ["art_002", "Audio", 1, None, 3],
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            artifacts = await client.artifacts.list_infographics("nb_123")

        assert isinstance(artifacts, list)

    @pytest.mark.asyncio
    async def test_list_slide_decks(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        """Test listing slide deck artifacts."""
        response = build_rpc_response(
            "gArtLc",
            [
                ["art_001", "Slide Deck", 8, None, 3],  # type 8 = slide deck
                ["art_002", "Video", 3, None, 3],
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            artifacts = await client.artifacts.list_slide_decks("nb_123")

        assert isinstance(artifacts, list)


# =============================================================================
# Notebooks API Tests (Additional)
# =============================================================================


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
    async def test_get_summary(
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
