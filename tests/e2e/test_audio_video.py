import pytest
from .conftest import requires_auth
from notebooklm import AudioFormat, AudioLength, VideoFormat, VideoStyle


@requires_auth
@pytest.mark.e2e
class TestAudioGeneration:
    """Audio generation tests.

    Note: These tests may fail due to API rate limiting or quota restrictions.
    Audio generation is documented as unreliable in E2E tests.
    """

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Audio API may be rate-limited or quota-restricted")
    async def test_generate_audio_default(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(test_notebook_id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Audio API may be rate-limited or quota-restricted")
    async def test_generate_audio_deep_dive_long(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(
            test_notebook_id,
            audio_format=AudioFormat.DEEP_DIVE,
            audio_length=AudioLength.LONG,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Audio API may be rate-limited or quota-restricted")
    async def test_generate_audio_brief_short(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(
            test_notebook_id,
            audio_format=AudioFormat.BRIEF,
            audio_length=AudioLength.SHORT,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Audio API may be rate-limited or quota-restricted")
    async def test_generate_audio_critique(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(
            test_notebook_id,
            audio_format=AudioFormat.CRITIQUE,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Audio API may be rate-limited or quota-restricted")
    async def test_generate_audio_debate(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(
            test_notebook_id,
            audio_format=AudioFormat.DEBATE,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Audio API may be rate-limited or quota-restricted")
    async def test_generate_audio_with_language(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_audio(
            test_notebook_id,
            language="en",
        )
        assert result is not None


@requires_auth
@pytest.mark.e2e
class TestVideoGeneration:
    """Video generation tests.

    Note: These tests may fail due to API rate limiting or quota restrictions.
    Video generation is documented as unreliable in E2E tests.
    """

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Video API may be rate-limited or quota-restricted")
    async def test_generate_video_default(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(test_notebook_id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Video API may be rate-limited or quota-restricted")
    async def test_generate_video_explainer_anime(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            test_notebook_id,
            video_format=VideoFormat.EXPLAINER,
            video_style=VideoStyle.ANIME,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Video API may be rate-limited or quota-restricted")
    async def test_generate_video_brief_whiteboard(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            test_notebook_id,
            video_format=VideoFormat.BRIEF,
            video_style=VideoStyle.WHITEBOARD,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Video API may be rate-limited or quota-restricted")
    async def test_generate_video_with_instructions(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            test_notebook_id,
            video_format=VideoFormat.EXPLAINER,
            video_style=VideoStyle.CLASSIC,
            instructions="Focus on key concepts for beginners",
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Video API may be rate-limited or quota-restricted")
    async def test_generate_video_kawaii_style(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            test_notebook_id,
            video_style=VideoStyle.KAWAII,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Video API may be rate-limited or quota-restricted")
    async def test_generate_video_watercolor_style(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            test_notebook_id,
            video_style=VideoStyle.WATERCOLOR,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Video API may be rate-limited or quota-restricted")
    async def test_generate_video_auto_style(
        self, client, test_notebook_id, created_artifacts, cleanup_artifacts
    ):
        result = await client.artifacts.generate_video(
            test_notebook_id,
            video_style=VideoStyle.AUTO_SELECT,
        )
        assert result is not None


@requires_auth
@pytest.mark.e2e
class TestAudioOperations:
    @pytest.mark.asyncio
    @pytest.mark.golden
    async def test_get_audio_overview(self, client, test_notebook_id):
        """Read-only test - gets existing audio overview."""
        result = await client.artifacts.get_audio_overview(test_notebook_id)
        assert result is None or isinstance(result, list)

    @pytest.mark.asyncio
    @pytest.mark.golden
    async def test_share_audio(self, client, test_notebook_id):
        """Read-only test - checks share status."""
        result = await client.artifacts.share_audio(test_notebook_id, public=False)
        assert result is None or result is not None
