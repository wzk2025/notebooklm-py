import pytest
from .conftest import requires_auth
from notebooklm import Notebook, NotebookDescription, ChatMode, ChatGoal


@requires_auth
@pytest.mark.e2e
class TestNotebookOperations:
    @pytest.mark.asyncio
    async def test_list_notebooks(self, client):
        notebooks = await client.notebooks.list()
        assert isinstance(notebooks, list)
        assert all(isinstance(nb, Notebook) for nb in notebooks)

    @pytest.mark.asyncio
    async def test_get_notebook(self, client, test_notebook_id):
        notebook = await client.notebooks.get(test_notebook_id)
        assert notebook is not None
        assert isinstance(notebook, Notebook)
        assert notebook.id == test_notebook_id

    @pytest.mark.asyncio
    async def test_create_rename_delete_notebook(
        self, client, created_notebooks, cleanup_notebooks
    ):
        # Create
        notebook = await client.notebooks.create("E2E Test Notebook")
        assert isinstance(notebook, Notebook)
        assert notebook.title == "E2E Test Notebook"
        created_notebooks.append(notebook.id)

        # Rename
        await client.notebooks.rename(notebook.id, "E2E Test Renamed")

        # Delete
        deleted = await client.notebooks.delete(notebook.id)
        assert deleted is True
        created_notebooks.remove(notebook.id)

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, client, test_notebook_id):
        history = await client.chat.get_history(test_notebook_id)
        assert history is not None


@requires_auth
@pytest.mark.e2e
class TestNotebookAsk:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_ask_notebook(self, client, test_notebook_id):
        result = await client.chat.ask(test_notebook_id, "What is this notebook about?")
        assert result.answer is not None
        assert result.conversation_id is not None


@requires_auth
@pytest.mark.e2e
class TestNotebookDescription:
    @pytest.mark.asyncio
    async def test_get_description(self, client, test_notebook_id):
        description = await client.notebooks.get_description(test_notebook_id)

        assert isinstance(description, NotebookDescription)
        assert description.summary is not None
        assert isinstance(description.suggested_topics, list)


@requires_auth
@pytest.mark.e2e
class TestNotebookConfigure:
    @pytest.mark.asyncio
    async def test_configure_learning_mode(self, client, test_notebook_id):
        await client.chat.set_mode(test_notebook_id, ChatMode.LEARNING_GUIDE)

    @pytest.mark.asyncio
    async def test_configure_custom_persona(self, client, test_notebook_id):
        await client.chat.configure(
            test_notebook_id,
            goal=ChatGoal.CUSTOM,
            custom_prompt="You are a helpful science tutor",
        )

    @pytest.mark.asyncio
    async def test_reset_to_default(self, client, test_notebook_id):
        await client.chat.set_mode(test_notebook_id, ChatMode.DEFAULT)
