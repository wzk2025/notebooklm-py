"""Unit tests for new service layer methods."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from notebooklm.services import (
    NotebookService,
    NotebookDescription,
    SuggestedTopic,
    SourceService,
    Source,
    ArtifactService,
    ReportSuggestion,
    ConversationService,
    ChatMode,
)
from notebooklm.rpc import ChatGoal, ChatResponseLength, DriveMimeType


class TestConversationServiceConfigure:
    """Tests for ConversationService.configure() and set_mode()."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.configure_chat = AsyncMock(return_value=None)
        return client

    @pytest.fixture
    def service(self, mock_client):
        return ConversationService(mock_client)

    @pytest.mark.asyncio
    async def test_configure_calls_client(self, service, mock_client):
        """Test configure() calls client.configure_chat()."""
        await service.configure(
            "notebook_123",
            goal=ChatGoal.LEARNING_GUIDE,
            response_length=ChatResponseLength.LONGER,
        )

        mock_client.configure_chat.assert_called_once_with(
            "notebook_123",
            ChatGoal.LEARNING_GUIDE,
            ChatResponseLength.LONGER,
            None,
        )

    @pytest.mark.asyncio
    async def test_configure_with_custom_prompt(self, service, mock_client):
        """Test configure() with custom prompt."""
        await service.configure(
            "notebook_123",
            goal=ChatGoal.CUSTOM,
            custom_prompt="Be an expert analyst",
        )

        mock_client.configure_chat.assert_called_once()
        call_args = mock_client.configure_chat.call_args
        assert call_args[0][3] == "Be an expert analyst"

    @pytest.mark.asyncio
    async def test_set_mode_default(self, service, mock_client):
        """Test set_mode() with DEFAULT mode."""
        await service.set_mode("notebook_123", ChatMode.DEFAULT)

        mock_client.configure_chat.assert_called_once_with(
            "notebook_123",
            ChatGoal.DEFAULT,
            ChatResponseLength.DEFAULT,
            None,
        )

    @pytest.mark.asyncio
    async def test_set_mode_learning_guide(self, service, mock_client):
        """Test set_mode() with LEARNING_GUIDE mode."""
        await service.set_mode("notebook_123", ChatMode.LEARNING_GUIDE)

        mock_client.configure_chat.assert_called_once_with(
            "notebook_123",
            ChatGoal.LEARNING_GUIDE,
            ChatResponseLength.LONGER,
            None,
        )

    @pytest.mark.asyncio
    async def test_set_mode_concise(self, service, mock_client):
        """Test set_mode() with CONCISE mode."""
        await service.set_mode("notebook_123", ChatMode.CONCISE)

        mock_client.configure_chat.assert_called_once_with(
            "notebook_123",
            ChatGoal.DEFAULT,
            ChatResponseLength.SHORTER,
            None,
        )

    @pytest.mark.asyncio
    async def test_set_mode_detailed(self, service, mock_client):
        """Test set_mode() with DETAILED mode."""
        await service.set_mode("notebook_123", ChatMode.DETAILED)

        mock_client.configure_chat.assert_called_once_with(
            "notebook_123",
            ChatGoal.DEFAULT,
            ChatResponseLength.LONGER,
            None,
        )


class TestNotebookServiceGetDescription:
    """Tests for NotebookService.get_description()."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        return client

    @pytest.fixture
    def service(self, mock_client):
        return NotebookService(mock_client)

    @pytest.mark.asyncio
    async def test_get_description_parses_response(self, service, mock_client):
        """Test get_description() correctly parses API response."""
        mock_client.get_notebook_description = AsyncMock(return_value={
            "summary": "This notebook covers **AI** and **ML**.",
            "suggested_topics": [
                {"question": "What is AI?", "prompt": "Explain artificial intelligence..."},
                {"question": "How does ML work?", "prompt": "Describe machine learning..."},
            ],
        })

        result = await service.get_description("notebook_123")

        assert isinstance(result, NotebookDescription)
        assert "AI" in result.summary
        assert len(result.suggested_topics) == 2
        assert isinstance(result.suggested_topics[0], SuggestedTopic)
        assert result.suggested_topics[0].question == "What is AI?"
        assert "artificial intelligence" in result.suggested_topics[0].prompt

    @pytest.mark.asyncio
    async def test_get_description_handles_empty(self, service, mock_client):
        """Test get_description() handles empty response."""
        mock_client.get_notebook_description = AsyncMock(return_value={
            "summary": "",
            "suggested_topics": [],
        })

        result = await service.get_description("notebook_123")

        assert result.summary == ""
        assert result.suggested_topics == []


class TestSourceServiceAddDriveFile:
    """Tests for SourceService.add_drive_file()."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        return client

    @pytest.fixture
    def service(self, mock_client):
        return SourceService(mock_client)

    @pytest.mark.asyncio
    async def test_add_drive_file_calls_client(self, service, mock_client):
        """Test add_drive_file() calls client with correct params."""
        mock_client.add_source_drive = AsyncMock(return_value=[
            [[["source_123"], "My Document"]]
        ])

        result = await service.add_drive_file(
            "notebook_123",
            file_id="drive_file_abc",
            title="My Document",
            mime_type=DriveMimeType.GOOGLE_DOC.value,
        )

        mock_client.add_source_drive.assert_called_once_with(
            "notebook_123",
            "drive_file_abc",
            "My Document",
            "application/vnd.google-apps.document",
        )
        assert isinstance(result, Source)

    @pytest.mark.asyncio
    async def test_add_drive_file_default_mime_type(self, service, mock_client):
        """Test add_drive_file() uses default MIME type."""
        mock_client.add_source_drive = AsyncMock(return_value=[
            [[["source_123"], "Test Doc"]]
        ])

        await service.add_drive_file(
            "notebook_123",
            file_id="drive_file_xyz",
            title="Test Doc",
        )

        call_args = mock_client.add_source_drive.call_args
        assert call_args[0][3] == "application/vnd.google-apps.document"


class TestArtifactServiceSuggestReports:
    """Tests for ArtifactService.suggest_reports()."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        return client

    @pytest.fixture
    def service(self, mock_client):
        return ArtifactService(mock_client)

    @pytest.mark.asyncio
    async def test_suggest_reports_parses_response(self, service, mock_client):
        """Test suggest_reports() correctly parses API response."""
        mock_client.get_suggested_report_formats = AsyncMock(return_value=[
            {"title": "Executive Summary", "description": "High-level overview", "prompt": "Create an executive...", "audience_level": 2},
            {"title": "Beginner's Guide", "description": "Introduction to topic", "prompt": "Write a beginner...", "audience_level": 1},
        ])

        result = await service.suggest_reports("notebook_123")

        assert len(result) == 2
        assert all(isinstance(r, ReportSuggestion) for r in result)
        assert result[0].title == "Executive Summary"
        assert result[0].audience_level == 2
        assert result[1].audience_level == 1

    @pytest.mark.asyncio
    async def test_suggest_reports_with_source_ids(self, service, mock_client):
        """Test suggest_reports() passes source_ids to client."""
        mock_client.get_suggested_report_formats = AsyncMock(return_value=[])

        await service.suggest_reports("notebook_123", source_ids=["src1", "src2"])

        mock_client.get_suggested_report_formats.assert_called_once_with(
            "notebook_123", ["src1", "src2"]
        )

    @pytest.mark.asyncio
    async def test_suggest_reports_handles_empty(self, service, mock_client):
        """Test suggest_reports() handles empty response."""
        mock_client.get_suggested_report_formats = AsyncMock(return_value=[])

        result = await service.suggest_reports("notebook_123")

        assert result == []


class TestChatModeEnum:
    """Tests for ChatMode enum."""

    def test_chat_mode_values(self):
        """Test ChatMode enum has expected values."""
        assert ChatMode.DEFAULT.value == "default"
        assert ChatMode.LEARNING_GUIDE.value == "learning_guide"
        assert ChatMode.CONCISE.value == "concise"
        assert ChatMode.DETAILED.value == "detailed"

    def test_chat_mode_is_iterable(self):
        """Test ChatMode enum is iterable."""
        modes = list(ChatMode)
        assert len(modes) == 4


class TestDataclasses:
    """Tests for new dataclasses."""

    def test_notebook_description_from_api_response(self):
        """Test NotebookDescription.from_api_response()."""
        data = {
            "summary": "Test summary",
            "suggested_topics": [
                {"question": "Q1?", "prompt": "P1"},
            ],
        }
        result = NotebookDescription.from_api_response(data)

        assert result.summary == "Test summary"
        assert len(result.suggested_topics) == 1
        assert result.suggested_topics[0].question == "Q1?"

    def test_report_suggestion_from_api_response(self):
        """Test ReportSuggestion.from_api_response()."""
        data = {
            "title": "Report Title",
            "description": "Report Desc",
            "prompt": "Generate...",
            "audience_level": 1,
        }
        result = ReportSuggestion.from_api_response(data)

        assert result.title == "Report Title"
        assert result.description == "Report Desc"
        assert result.prompt == "Generate..."
        assert result.audience_level == 1

    def test_report_suggestion_default_audience_level(self):
        """Test ReportSuggestion default audience_level."""
        data = {"title": "T", "description": "D", "prompt": "P"}
        result = ReportSuggestion.from_api_response(data)

        assert result.audience_level == 2  # Default
