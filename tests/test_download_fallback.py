"""Test for download fallback when episode download fails."""

from unittest import mock

import pytest
from requests.exceptions import RequestException

from tonie_podcast_sync.podcast import Episode, EpisodeSorting
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
def test_fallback_to_next_episode_on_download_failure(temp_cache_dir):
    """Test that when an episode fails to download, the next available one is used as fallback."""
    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = temp_cache_dir

    # Create test episodes
    test_episodes = []
    for i in range(1, 6):
        test_feed_data = {
            "title": f"Episode {i}",
            "published": f"Mon, 0{i} Jan 2024 10:00:00 +0000",
            "published_parsed": (2024, 1, i, 10, 0, 0, 0, 1, 0),
            "id": f"test-guid-{i}",
            "itunes_duration": "10:00",  # 10 minutes each
        }
        ep = Episode(podcast="Test Podcast", raw=test_feed_data, url=f"http://example.com/ep{i}.mp3")
        test_episodes.append(ep)

    # Create a mock podcast with 5 episodes (sorted newest first)
    podcast = mock.MagicMock()
    podcast.epList = test_episodes
    podcast.title = "Test Podcast"
    podcast.epSorting = EpisodeSorting.BY_DATE_NEWEST_FIRST

    # Mock requests to fail for Episode 2, but succeed for others
    call_count = 0

    def mock_get(url, *_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        if "ep2.mp3" in url:
            msg = "Network error for ep2"
            raise RequestException(msg)
        response = mock.MagicMock()
        response.ok = True
        response.raise_for_status = mock.MagicMock()
        response.content = b"fake audio data"
        return response

    with mock.patch("tonie_podcast_sync.toniepodcastsync.requests.get", side_effect=mock_get):
        # Request 30 minutes total, which would fit 3 episodes normally
        cached_episodes = tps._ToniePodcastSync__cache_podcast_episodes(podcast, max_minutes=30)

    # Should have 3 episodes: Episode 1, Episode 4 (fallback for failed Episode 2), Episode 3
    assert len(cached_episodes) == 3
    assert cached_episodes[0].title == "Episode 1"
    # Episode 2 failed, so Episode 4 was used as fallback (first available episode)
    assert cached_episodes[1].title == "Episode 4"
    assert cached_episodes[2].title == "Episode 3"


@pytest.mark.usefixtures("mock_tonie_api")
def test_fallback_in_random_mode(temp_cache_dir):
    """Test that fallback works in random mode without reshuffling."""
    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = temp_cache_dir

    # Create test episodes
    test_episodes = []
    for i in range(1, 6):
        test_feed_data = {
            "title": f"Episode {i}",
            "published": f"Mon, 0{i} Jan 2024 10:00:00 +0000",
            "published_parsed": (2024, 1, i, 10, 0, 0, 0, 1, 0),
            "id": f"test-guid-{i}",
            "itunes_duration": "10:00",  # 10 minutes each
        }
        ep = Episode(podcast="Test Podcast", raw=test_feed_data, url=f"http://example.com/ep{i}.mp3")
        test_episodes.append(ep)

    # Create a mock podcast in RANDOM mode
    podcast = mock.MagicMock()
    podcast.epList = test_episodes  # Already shuffled
    podcast.title = "Test Podcast"
    podcast.epSorting = EpisodeSorting.RANDOM

    # Mock requests to fail for first episode, succeed for others
    call_count = 0

    def mock_get(url, *_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        if "ep1.mp3" in url:
            msg = "Network error for ep1"
            raise RequestException(msg)
        response = mock.MagicMock()
        response.ok = True
        response.raise_for_status = mock.MagicMock()
        response.content = b"fake audio data"
        return response

    with mock.patch("tonie_podcast_sync.toniepodcastsync.requests.get", side_effect=mock_get):
        # Request 30 minutes total
        cached_episodes = tps._ToniePodcastSync__cache_podcast_episodes(podcast, max_minutes=30)

    # Should have 3 episodes, with Episode 4 as fallback for failed Episode 1
    assert len(cached_episodes) == 3
    # Episode 1 failed, so next available (Episode 4) was used
    episode_titles = [ep.title for ep in cached_episodes]
    assert "Episode 1" not in episode_titles
    assert "Episode 4" in episode_titles


@pytest.mark.usefixtures("mock_tonie_api")
def test_no_fallback_when_all_remaining_episodes_too_long(temp_cache_dir):
    """Test that no fallback is used if remaining episodes would exceed time limit."""
    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = temp_cache_dir

    # Create test episodes with varying durations
    test_episodes = []
    durations = ["10:00", "10:00", "10:00", "50:00"]  # Last one is 50 minutes
    for i in range(1, 5):
        test_feed_data = {
            "title": f"Episode {i}",
            "published": f"Mon, 0{i} Jan 2024 10:00:00 +0000",
            "published_parsed": (2024, 1, i, 10, 0, 0, 0, 1, 0),
            "id": f"test-guid-{i}",
            "itunes_duration": durations[i - 1],
        }
        ep = Episode(podcast="Test Podcast", raw=test_feed_data, url=f"http://example.com/ep{i}.mp3")
        test_episodes.append(ep)

    podcast = mock.MagicMock()
    podcast.epList = test_episodes
    podcast.title = "Test Podcast"
    podcast.epSorting = EpisodeSorting.BY_DATE_NEWEST_FIRST

    # Mock requests to fail for Episode 3
    def mock_get(url, *_args, **_kwargs):
        if "ep3.mp3" in url:
            msg = "Network error for ep3"
            raise RequestException(msg)
        response = mock.MagicMock()
        response.ok = True
        response.raise_for_status = mock.MagicMock()
        response.content = b"fake audio data"
        return response

    with mock.patch("tonie_podcast_sync.toniepodcastsync.requests.get", side_effect=mock_get):
        # Request 30 minutes total - can fit episodes 1, 2, 3
        # Episode 3 fails, but Episode 4 (50 min) is too long as replacement
        cached_episodes = tps._ToniePodcastSync__cache_podcast_episodes(podcast, max_minutes=30)

    # Should have only 2 episodes (1 and 2), no fallback for 3
    assert len(cached_episodes) == 2
    assert cached_episodes[0].title == "Episode 1"
    assert cached_episodes[1].title == "Episode 2"
