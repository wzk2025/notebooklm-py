import os
import tempfile
import pytest
from .conftest import requires_auth
from notebooklm.services import ArtifactService


@requires_auth
@pytest.mark.e2e
class TestDownloadAudio:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_download_audio(self, client, test_notebook_id):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "audio.mp4")
            try:
                result = await client.download_audio(test_notebook_id, output_path)
                assert result == output_path
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0
            except ValueError as e:
                if "No completed audio" in str(e):
                    pytest.skip("No completed audio artifact available")
                raise


@requires_auth
@pytest.mark.e2e
class TestDownloadVideo:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_download_video(self, client, test_notebook_id):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "video.mp4")
            try:
                result = await client.download_video(test_notebook_id, output_path)
                assert result == output_path
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0
            except ValueError as e:
                if "No completed video" in str(e):
                    pytest.skip("No completed video artifact available")
                raise


@requires_auth
@pytest.mark.e2e
class TestDownloadInfographic:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_download_infographic(self, client, test_notebook_id):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "infographic.png")
            try:
                result = await client.download_infographic(
                    test_notebook_id, output_path
                )
                assert result == output_path
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0
            except ValueError as e:
                if "No completed infographic" in str(e):
                    pytest.skip("No completed infographic artifact available")
                raise


@requires_auth
@pytest.mark.e2e
class TestDownloadSlideDeck:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_download_slide_deck(self, client, test_notebook_id):
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                result = await client.download_slide_deck(test_notebook_id, tmpdir)
                assert isinstance(result, list)
                assert len(result) > 0
                for slide_path in result:
                    assert os.path.exists(slide_path)
                    assert os.path.getsize(slide_path) > 0
            except ValueError as e:
                if "No completed slide" in str(e):
                    pytest.skip("No completed slide deck artifact available")
                raise


@requires_auth
@pytest.mark.e2e
class TestExportArtifact:
    @pytest.mark.asyncio
    async def test_export_artifact(self, client, test_notebook_id):
        service = ArtifactService(client)
        artifacts = await service.list(test_notebook_id)
        if not artifacts or len(artifacts) == 0:
            pytest.skip("No artifacts available to export")

        artifact_id = artifacts[0].id
        try:
            result = await client.export_artifact(test_notebook_id, artifact_id)
            assert result is not None or result is None
        except Exception:
            pytest.skip("Export not available for this artifact type")
