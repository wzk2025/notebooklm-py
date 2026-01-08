import pytest
from .conftest import requires_auth
from notebooklm import AudioFormat, AudioLength, VideoFormat, VideoStyle


@requires_auth
@pytest.mark.e2e
class TestAudioGeneration:
    """Audio generation tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_audio_default(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(generation_notebook.id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_audio_deep_dive_long(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(
            generation_notebook.id,
            audio_format=AudioFormat.DEEP_DIVE,
            audio_length=AudioLength.LONG,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_audio_brief_short(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(
            generation_notebook.id,
            audio_format=AudioFormat.BRIEF,
            audio_length=AudioLength.SHORT,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_audio_critique(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(
            generation_notebook.id,
            audio_format=AudioFormat.CRITIQUE,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_audio_debate(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(
            generation_notebook.id,
            audio_format=AudioFormat.DEBATE,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_audio_with_language(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(
            generation_notebook.id,
            language="en",
        )
        assert result is not None


@requires_auth
@pytest.mark.e2e
class TestVideoGeneration:
    """Video generation tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_video_default(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(generation_notebook.id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_video_explainer_anime(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_format=VideoFormat.EXPLAINER,
            video_style=VideoStyle.ANIME,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_video_brief_whiteboard(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_format=VideoFormat.BRIEF,
            video_style=VideoStyle.WHITEBOARD,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_video_with_instructions(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_format=VideoFormat.EXPLAINER,
            video_style=VideoStyle.CLASSIC,
            instructions="Focus on key concepts for beginners",
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_video_kawaii_style(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_style=VideoStyle.KAWAII,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_video_watercolor_style(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_style=VideoStyle.WATERCOLOR,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.exhaustive
    async def test_generate_video_auto_style(
        self, client, generation_notebook, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_style=VideoStyle.AUTO_SELECT,
        )
        assert result is not None
