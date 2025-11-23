"""Test for download retry logic bug in toniepodcastsync.py."""

from unittest import mock

import pytest
from requests.exceptions import RequestException

from tonie_podcast_sync.constants import DOWNLOAD_RETRY_COUNT
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
    """Create a temporary cache directory."""
    return tmp_path / "cache"


@pytest.mark.usefixtures("mock_tonie_api")
def test_download_respects_retry_count(temp_cache_dir):
    """
    Test that downloads respect DOWNLOAD_RETRY_COUNT and don't make extra requests.

    Bug: The current code has duplicate download logic after the retry loop,
    which causes an additional download attempt after all retries are exhausted.
    This means if DOWNLOAD_RETRY_COUNT=3, it actually makes 4 attempts total.
    """
    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = temp_cache_dir

    # Create a test episode
    test_feed_data = {
        "title": "Test Episode",
        "published": "Mon, 01 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-123",
        "itunes_duration": "10:30",
    }

    ep = Episode(podcast="Test Podcast", raw=test_feed_data, url="http://example.com/test.mp3")

    # Mock requests to always fail
    call_count = 0

    def mock_get(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        msg = "Network error"
        raise RequestException(msg)

    tps._session.get = mock_get
    result = tps._ToniePodcastSync__cache_episode(ep)

    # Should fail after DOWNLOAD_RETRY_COUNT attempts, not more
    assert result is False
    assert call_count == DOWNLOAD_RETRY_COUNT, (
        f"Expected exactly {DOWNLOAD_RETRY_COUNT} download attempts, "
        f"but got {call_count}. The bug causes an extra attempt after retry loop."
    )


@pytest.mark.usefixtures("mock_tonie_api")
def test_download_succeeds_on_first_attempt(temp_cache_dir):
    """Test that successful downloads on first attempt don't trigger retries."""
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

    call_count = 0

    def mock_get(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        response = mock.MagicMock()
        response.ok = True
        response.iter_content = mock.MagicMock(return_value=[b"fake audio content"])
        response.raise_for_status = mock.MagicMock()
        return response

    tps._session.get = mock_get
    result = tps._ToniePodcastSync__cache_episode(ep)

    assert result is True
    assert call_count == 1, f"Expected exactly 1 download attempt for successful download, but got {call_count}"


@pytest.mark.usefixtures("mock_tonie_api")
def test_download_succeeds_on_retry(temp_cache_dir):
    """Test that download succeeds on second attempt after first fails."""
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

    call_count = 0

    def mock_get(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            msg = "Network error"
            raise RequestException(msg)
        response = mock.MagicMock()
        response.ok = True
        response.iter_content = mock.MagicMock(return_value=[b"fake audio content"])
        response.raise_for_status = mock.MagicMock()
        return response

    with mock.patch("tonie_podcast_sync.toniepodcastsync.time.sleep"):  # Skip actual sleep
        tps._session.get = mock_get
        result = tps._ToniePodcastSync__cache_episode(ep)

    assert result is True
    assert call_count == 2, f"Expected 2 download attempts (1 fail + 1 success), but got {call_count}"
