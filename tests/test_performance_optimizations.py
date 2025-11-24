"""Tests for performance optimizations."""

from collections import deque
from unittest import mock

import pytest

from tonie_podcast_sync.podcast import Episode
from tonie_podcast_sync.toniepodcastsync import ToniePodcastSync


@pytest.fixture
def mock_tonie_api():
    """Mock TonieAPI."""
    with mock.patch("tonie_podcast_sync.toniepodcastsync.TonieAPI") as _mock:
        api_mock = mock.MagicMock()
        api_mock.get_households.return_value = []
        api_mock.get_all_creative_tonies.return_value = []
        _mock.return_value = api_mock
        yield _mock


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.mark.usefixtures("mock_tonie_api")
def test_session_reuse_for_http_requests(temp_cache_dir):
    """Test that ToniePodcastSync reuses HTTP session for connection pooling."""
    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = temp_cache_dir

    # Verify session is created on initialization
    assert hasattr(tps, "_session")
    assert tps._session is not None


@pytest.mark.usefixtures("mock_tonie_api")
def test_streaming_download_uses_iter_content(temp_cache_dir):
    """Test that downloads use streaming (iter_content) instead of loading entire file to memory."""
    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = temp_cache_dir

    test_feed_data = {
        "title": "Test Episode",
        "published": "Mon, 01 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-123",
        "itunes_duration": "10:30",
    }
    ep = Episode(podcast="Test Podcast", raw=test_feed_data, url="http://example.com/test.mp3")

    # Mock response with iter_content
    mock_response = mock.MagicMock()
    mock_response.ok = True
    mock_response.raise_for_status = mock.MagicMock()

    # Track whether iter_content was called (streaming) vs content property (in-memory)
    iter_content_called = False

    def mock_iter_content(chunk_size=8192):  # noqa: ARG001
        nonlocal iter_content_called
        iter_content_called = True
        yield b"chunk1"
        yield b"chunk2"

    mock_response.iter_content = mock_iter_content
    tps._session.get = mock.MagicMock(return_value=mock_response)

    result = tps._ToniePodcastSync__cache_episode(ep)

    assert result is True
    assert iter_content_called, "Download should use iter_content for streaming, not load entire file to memory"


@pytest.mark.usefixtures("mock_tonie_api")
def test_volume_adjustment_loads_to_memory_when_needed(temp_cache_dir):
    """Test that volume adjustment loads file to memory (required for pydub processing)."""
    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = temp_cache_dir

    test_feed_data = {
        "title": "Test Episode",
        "published": "Mon, 01 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-123",
        "itunes_duration": "10:30",
    }
    ep = Episode(
        podcast="Test Podcast",
        raw=test_feed_data,
        url="http://example.com/test.mp3",
        volume_adjustment=5,  # Volume adjustment required
    )

    # Mock response
    mock_response = mock.MagicMock()
    mock_response.ok = True
    mock_response.raise_for_status = mock.MagicMock()
    mock_response.iter_content = mock.MagicMock(return_value=[b"fake audio content"])
    tps._session.get = mock.MagicMock(return_value=mock_response)

    # Mock ffmpeg availability
    with (
        mock.patch.object(tps, "_is_ffmpeg_available", return_value=True),
        mock.patch.object(tps, "_adjust_volume", return_value=b"adjusted audio") as mock_adjust,
    ):
        result = tps._ToniePodcastSync__cache_episode(ep)

        assert result is True
        # When volume adjustment is needed, audio is loaded to memory for processing
        assert mock_adjust.called


@pytest.mark.usefixtures("mock_tonie_api")
def test_deque_used_for_fallback_episodes(temp_cache_dir):
    """Test that fallback episode selection uses efficient data structure."""

    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = temp_cache_dir

    # Create test episodes
    test_episodes = []
    for i in range(1, 4):
        test_feed_data = {
            "title": f"Episode {i}",
            "published": f"Mon, 0{i} Jan 2024 10:00:00 +0000",
            "published_parsed": (2024, 1, i, 10, 0, 0, 0, 1, 0),
            "id": f"test-guid-{i}",
            "itunes_duration": "10:00",
        }
        ep = Episode(podcast="Test Podcast", raw=test_feed_data, url=f"http://example.com/ep{i}.mp3")
        test_episodes.append(ep)

    # Test that _find_replacement_episode accepts deque
    test_deque = deque(test_episodes)
    replacement = tps._find_replacement_episode(test_deque, max_seconds=1800, current_seconds=0)

    assert replacement is not None
    assert replacement.title == "Episode 1"
    # Verify the episode was removed from the deque (efficient removal)
    assert len(test_deque) == 2
