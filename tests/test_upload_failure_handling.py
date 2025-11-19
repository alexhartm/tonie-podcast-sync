"""Test for upload failure handling bug in toniepodcastsync.py."""

from unittest import mock

import pytest
from requests.exceptions import HTTPError
from tonie_api.models import CreativeTonie, Household

from tonie_podcast_sync.constants import UPLOAD_RETRY_COUNT
from tonie_podcast_sync.podcast import Episode, EpisodeSorting
from tonie_podcast_sync.toniepodcastsync import ToniePodcastSync


@pytest.fixture
def mock_tonie_api_with_tonie():
    """Mock TonieAPI with a configured tonie."""
    with mock.patch("tonie_podcast_sync.toniepodcastsync.TonieAPI") as _mock:
        household = Household(
            id="household-1", name="Test House", ownerName="Test Owner", access="owner", canLeave=True
        )

        tonie = CreativeTonie(
            id="tonie-123",
            householdId="household-1",
            name="Test Tonie",
            imageUrl="http://example.com/img.png",
            secondsRemaining=5400,
            secondsPresent=0,
            chaptersPresent=0,
            chaptersRemaining=99,
            transcoding=False,
            lastUpdate=None,
            chapters=[],
        )

        api_mock = mock.MagicMock()
        api_mock.get_households.return_value = [household]
        api_mock.get_all_creative_tonies.return_value = [tonie]
        _mock.return_value = api_mock
        yield api_mock


@pytest.fixture
def temp_podcast_with_episodes(tmp_path):
    """Create a temporary directory with mock episode files."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Create mock episode files
    podcast_dir = cache_dir / "Test Podcast"
    podcast_dir.mkdir()

    episodes = []
    for i in range(3):
        test_feed_data = {
            "title": f"Episode {i + 1}",
            "published": f"Mon, 0{i + 1} Jan 2024 10:00:00 +0000",
            "published_parsed": (2024, 1, i + 1, 10, 0, 0, 0, 1, 0),
            "id": f"test-guid-{i + 1}",
            "itunes_duration": "10:30",
        }
        ep = Episode(podcast="Test Podcast", raw=test_feed_data, url=f"http://example.com/ep{i + 1}.mp3")

        # Create a fake file for the episode
        ep_file = podcast_dir / f"episode_{i + 1}.mp3"
        ep_file.write_bytes(b"fake audio content")
        ep.fpath = ep_file

        episodes.append(ep)

    return cache_dir, episodes


def test_upload_failure_should_not_report_success(mock_tonie_api_with_tonie, temp_podcast_with_episodes, capsys):
    """
    Test that when uploads fail, the function doesn't report success.

    Bug: Currently __upload_episode returns True/False but the return value is ignored.
    The function always prints "Successfully uploaded" even if uploads failed.
    """
    cache_dir, episodes = temp_podcast_with_episodes

    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = cache_dir

    # Mock the upload to always fail
    mock_tonie_api_with_tonie.upload_file_to_tonie.side_effect = HTTPError("Upload failed")

    # Create a mock podcast
    podcast = mock.MagicMock()
    podcast.epList = episodes
    podcast.title = "Test Podcast"
    podcast.epSorting = EpisodeSorting.BY_DATE_NEWEST_FIRST

    # Mock download to succeed so we actually reach the upload part
    with mock.patch("tonie_podcast_sync.toniepodcastsync.requests.get") as mock_get:
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.content = b"fake audio"
        mock_response.raise_for_status = mock.MagicMock()
        mock_get.return_value = mock_response

        # Mock time.sleep to speed up test
        with mock.patch("tonie_podcast_sync.toniepodcastsync.time.sleep"):
            # This should NOT print "Successfully uploaded" when uploads fail
            tps.sync_podcast_to_tonie(podcast, "tonie-123", max_minutes=90)

    captured = capsys.readouterr()

    # Bug: Currently this assertion FAILS because "Successfully uploaded" is printed even on failure
    assert "Successfully uploaded" not in captured.out, "Should not print 'Successfully uploaded' when uploads fail"
    # Should show error message
    assert "Failed to upload" in captured.out, "Should print error message when uploads fail"


def test_partial_upload_failure_should_report_correctly(mock_tonie_api_with_tonie, temp_podcast_with_episodes, capsys):
    """
    Test that when some uploads fail, only successful uploads are reported.

    Bug: Currently the function reports all episodes as successfully uploaded,
    even if some failed.
    """
    cache_dir, episodes = temp_podcast_with_episodes

    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = cache_dir

    # Mock the upload to fail for the second episode (all retries)
    upload_call_count = 0

    def mock_upload(_tonie, _file_path, title):
        nonlocal upload_call_count
        upload_call_count += 1
        # Fail all attempts for Episode 2
        if "Episode 2" in title:
            msg = "Upload failed"
            raise HTTPError(msg)

    mock_tonie_api_with_tonie.upload_file_to_tonie.side_effect = mock_upload

    # Create a mock podcast
    podcast = mock.MagicMock()
    podcast.epList = episodes
    podcast.title = "Test Podcast"
    podcast.epSorting = EpisodeSorting.BY_DATE_NEWEST_FIRST

    # Mock download to succeed
    with mock.patch("tonie_podcast_sync.toniepodcastsync.requests.get") as mock_get:
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.content = b"fake audio"
        mock_response.raise_for_status = mock.MagicMock()
        mock_get.return_value = mock_response

        # Mock time.sleep to speed up test
        with mock.patch("tonie_podcast_sync.toniepodcastsync.time.sleep"):
            tps.sync_podcast_to_tonie(podcast, "tonie-123", max_minutes=90)

    captured = capsys.readouterr()

    # Should report successful uploads (Episodes 1 and 3)
    assert "Successfully uploaded" in captured.out
    # Should also report failures
    assert "Failed to upload" in captured.out
    # Should show 1 failed episode
    assert "1 episode(s)" in captured.out
    # Episode 2 should be in the failure list
    assert "Episode 2" in captured.out


def test_all_uploads_succeed(mock_tonie_api_with_tonie, temp_podcast_with_episodes, capsys):
    """
    Test that when all uploads succeed, success is correctly reported.

    This test ensures our fix doesn't break the success case.
    """
    cache_dir, episodes = temp_podcast_with_episodes

    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = cache_dir

    # Mock successful uploads
    mock_tonie_api_with_tonie.upload_file_to_tonie.return_value = None

    # Create a mock podcast
    podcast = mock.MagicMock()
    podcast.epList = episodes
    podcast.title = "Test Podcast"
    podcast.epSorting = EpisodeSorting.BY_DATE_NEWEST_FIRST

    # Mock download to succeed
    with mock.patch("tonie_podcast_sync.toniepodcastsync.requests.get") as mock_get:
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.content = b"fake audio"
        mock_response.raise_for_status = mock.MagicMock()
        mock_get.return_value = mock_response

        tps.sync_podcast_to_tonie(podcast, "tonie-123", max_minutes=90)

    captured = capsys.readouterr()

    # Should report success when all uploads succeed
    assert "Successfully uploaded" in captured.out, "Should print 'Successfully uploaded' when uploads succeed"
    # All 3 episodes should be mentioned
    assert "Episode 1" in captured.out
    assert "Episode 2" in captured.out
    assert "Episode 3" in captured.out
    # Should NOT show failure message
    assert "Failed to upload" not in captured.out


def test_upload_respects_retry_count(mock_tonie_api_with_tonie, temp_podcast_with_episodes):
    """
    Test that upload retries are limited to UPLOAD_RETRY_COUNT.
    """
    cache_dir, episodes = temp_podcast_with_episodes

    tps = ToniePodcastSync("user", "pass")
    tps.podcast_cache_directory = cache_dir

    # Track upload attempts
    attempt_count = 0

    def mock_upload_always_fail(*_args, **_kwargs):
        nonlocal attempt_count
        attempt_count += 1
        msg = "Upload failed"
        raise HTTPError(msg)

    mock_tonie_api_with_tonie.upload_file_to_tonie.side_effect = mock_upload_always_fail

    # Create a mock podcast with just one episode
    podcast = mock.MagicMock()
    podcast.epList = [episodes[0]]
    podcast.title = "Test Podcast"
    podcast.epSorting = EpisodeSorting.BY_DATE_NEWEST_FIRST

    # Mock download to succeed
    with mock.patch("tonie_podcast_sync.toniepodcastsync.requests.get") as mock_get:
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.content = b"fake audio"
        mock_response.raise_for_status = mock.MagicMock()
        mock_get.return_value = mock_response

        with mock.patch("tonie_podcast_sync.toniepodcastsync.time.sleep"):
            tps.sync_podcast_to_tonie(podcast, "tonie-123", max_minutes=90)

    # Should have attempted UPLOAD_RETRY_COUNT times
    assert attempt_count == UPLOAD_RETRY_COUNT, f"Expected {UPLOAD_RETRY_COUNT} upload attempts, got {attempt_count}"
