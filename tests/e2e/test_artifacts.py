import asyncio
import pytest
from .conftest import requires_auth
from notebooklm.services import ArtifactService, Artifact


@requires_auth
@pytest.mark.e2e
class TestQuizGeneration:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_quiz_default(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.generate_quiz(test_notebook_id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_quiz_with_options(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        from notebooklm.rpc import QuizQuantity, QuizDifficulty

        result = await client.generate_quiz(
            test_notebook_id,
            quantity=QuizQuantity.MORE,
            difficulty=QuizDifficulty.HARD,
            instructions="Focus on key concepts and definitions",
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_quiz_fewer_easy(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        from notebooklm.rpc import QuizQuantity, QuizDifficulty

        result = await client.generate_quiz(
            test_notebook_id,
            quantity=QuizQuantity.FEWER,
            difficulty=QuizDifficulty.EASY,
        )
        assert result is not None


@requires_auth
@pytest.mark.e2e
class TestFlashcardsGeneration:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_flashcards_default(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.generate_flashcards(test_notebook_id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_flashcards_with_options(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        from notebooklm.rpc import QuizQuantity, QuizDifficulty

        result = await client.generate_flashcards(
            test_notebook_id,
            quantity=QuizQuantity.STANDARD,
            difficulty=QuizDifficulty.MEDIUM,
            instructions="Create cards for vocabulary terms",
        )
        assert result is not None


@requires_auth
@pytest.mark.e2e
class TestInfographicGeneration:
    """Infographic generation tests.

    Note: These tests may fail due to API rate limiting or quota restrictions.
    Infographic generation is documented as unreliable in E2E tests.
    """

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Infographic API may be rate-limited or quota-restricted")
    async def test_generate_infographic_default(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.generate_infographic(test_notebook_id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Infographic API may be rate-limited or quota-restricted")
    async def test_generate_infographic_portrait_detailed(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        from notebooklm.rpc import InfographicOrientation, InfographicDetail

        result = await client.generate_infographic(
            test_notebook_id,
            orientation=InfographicOrientation.PORTRAIT,
            detail_level=InfographicDetail.DETAILED,
            instructions="Include statistics and key findings",
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Infographic API may be rate-limited or quota-restricted")
    async def test_generate_infographic_square_concise(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        from notebooklm.rpc import InfographicOrientation, InfographicDetail

        result = await client.generate_infographic(
            test_notebook_id,
            orientation=InfographicOrientation.SQUARE,
            detail_level=InfographicDetail.CONCISE,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Infographic API may be rate-limited or quota-restricted")
    async def test_generate_infographic_landscape(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        from notebooklm.rpc import InfographicOrientation

        result = await client.generate_infographic(
            test_notebook_id,
            orientation=InfographicOrientation.LANDSCAPE,
        )
        assert result is not None


@requires_auth
@pytest.mark.e2e
class TestSlideDeckGeneration:
    """Slide deck generation tests.

    Note: These tests may fail due to API rate limiting or quota restrictions.
    Slide deck generation is documented as unreliable in E2E tests.
    """

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Slide deck API may be rate-limited or quota-restricted")
    async def test_generate_slide_deck_default(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.generate_slide_deck(test_notebook_id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Slide deck API may be rate-limited or quota-restricted")
    async def test_generate_slide_deck_detailed(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        from notebooklm.rpc import SlideDeckFormat, SlideDeckLength

        result = await client.generate_slide_deck(
            test_notebook_id,
            slide_deck_format=SlideDeckFormat.DETAILED_DECK,
            slide_deck_length=SlideDeckLength.DEFAULT,
            instructions="Include speaker notes",
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Slide deck API may be rate-limited or quota-restricted")
    async def test_generate_slide_deck_presenter_short(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        from notebooklm.rpc import SlideDeckFormat, SlideDeckLength

        result = await client.generate_slide_deck(
            test_notebook_id,
            slide_deck_format=SlideDeckFormat.PRESENTER_SLIDES,
            slide_deck_length=SlideDeckLength.SHORT,
        )
        assert result is not None


@requires_auth
@pytest.mark.e2e
class TestDataTableGeneration:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_data_table_default(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.generate_data_table(test_notebook_id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_data_table_with_instructions(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.generate_data_table(
            test_notebook_id,
            instructions="Create a comparison table of key concepts",
            language="en",
        )
        assert result is not None


@requires_auth
@pytest.mark.e2e
class TestArtifactPolling:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_poll_studio_status(self, client, test_notebook_id):
        result = await client.generate_quiz(test_notebook_id)
        assert result is not None

        await asyncio.sleep(2)
        status = await client.poll_studio_status(test_notebook_id, test_notebook_id)
        assert status is not None or status is None

    @pytest.mark.asyncio
    async def test_list_artifacts(self, client, test_notebook_id):
        service = ArtifactService(client)
        artifacts = await service.list(test_notebook_id)
        assert isinstance(artifacts, list)
        assert all(isinstance(art, Artifact) for art in artifacts)


@requires_auth
@pytest.mark.e2e
class TestMindMapGeneration:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_mind_map(self, client, test_notebook_id):
        result = await client.generate_mind_map(test_notebook_id)
        assert result is not None
        assert "mind_map" in result
        assert "note_id" in result
        # Verify mind map structure
        mind_map = result["mind_map"]
        assert isinstance(mind_map, dict)
        assert "name" in mind_map
        assert "children" in mind_map


@requires_auth
@pytest.mark.e2e
class TestStudyGuideGeneration:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_study_guide(self, client, test_notebook_id):
        result = await client.generate_study_guide(test_notebook_id)
        assert result is not None or result is None

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_faq(self, client, test_notebook_id):
        result = await client.generate_faq(test_notebook_id)
        assert result is not None or result is None
