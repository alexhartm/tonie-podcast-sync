"""Test for reshuffle logic bug in toniepodcastsync.py."""

from unittest import mock

import pytest

from tonie_podcast_sync.constants import MAX_SHUFFLE_ATTEMPTS
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


@pytest.mark.usefixtures("mock_tonie_api")
def test_reshuffle_with_single_episode_should_fail():
    """
    Test that reshuffle correctly handles case with only one episode.

    Bug: If there's only one episode and it matches the current episode on the tonie,
    shuffling will never find a different episode. The function should recognize this
    and handle it gracefully.
    """
    tps = ToniePodcastSync("user", "pass")

    # Create a podcast with only one episode
    test_feed_data = {
        "title": "Single Episode",
        "published": "Mon, 01 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-123",
        "itunes_duration": "10:30",
    }

    ep = Episode(podcast="Test Podcast", raw=test_feed_data, url="http://example.com/test.mp3")
    podcast = mock.MagicMock()
    podcast.epList = [ep]
    podcast.title = "Test Podcast"

    current_titles = ["Single Episode (Mon, 01 Jan 2024 10:00:00 +0000)"]

    # This should complete without infinite loop and log a warning
    # The bug is that it shuffles AFTER checking, not before
    with mock.patch("tonie_podcast_sync.toniepodcastsync.log") as mock_log:
        tps._ToniePodcastSync__reshuffle_until_different(podcast, current_titles)

        # Should log warning that it couldn't find different episode
        warning_calls = [
            call for call in mock_log.warning.call_args_list if "Could not find different first episode" in str(call)
        ]
        assert len(warning_calls) == 1, "Should warn when unable to find different episode"


@pytest.mark.usefixtures("mock_tonie_api", "monkeypatch")
def test_reshuffle_should_shuffle_before_checking():
    """
    Test that reshuffle shuffles BEFORE checking, not after.

    Bug: Current implementation checks the first episode BEFORE shuffling on each iteration.
    This means the first check is always against the unshuffled list, and subsequent
    checks happen before the shuffle. The shuffle should happen BEFORE each check.
    """
    tps = ToniePodcastSync("user", "pass")

    # Create a podcast with two episodes
    test_feed_data_1 = {
        "title": "Episode 1",
        "published": "Mon, 01 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-1",
        "itunes_duration": "10:30",
    }
    test_feed_data_2 = {
        "title": "Episode 2",
        "published": "Tue, 02 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 2, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-2",
        "itunes_duration": "10:30",
    }

    ep1 = Episode(podcast="Test Podcast", raw=test_feed_data_1, url="http://example.com/test1.mp3")
    ep2 = Episode(podcast="Test Podcast", raw=test_feed_data_2, url="http://example.com/test2.mp3")

    class PodcastMock(mock.MagicMock):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self.shuffle_call_count = 0
            self.epList = [ep1, ep2]
            self.title = "Test Podcast"

        def sort_episodes(self) -> None:
            self.shuffle_call_count += 1
            self.epList[0], self.epList[1] = self.epList[1], self.epList[0]

    podcast = PodcastMock()

    current_titles = [
        "Episode 1 (Mon, 01 Jan 2024 10:00:00 +0000)",
        "Episode 2 (Tue, 02 Jan 2024 10:00:00 +0000)",
    ]

    # The bug: with current implementation, it checks BEFORE shuffling
    # So the first check sees ep1, then shuffles to ep2, then checks ep2 (which is now correct)
    # But the logic is backwards - should shuffle FIRST then check

    tps._ToniePodcastSync__reshuffle_until_different(podcast, current_titles)

    # With the bug, shuffle is called on the first iteration (after failed check)
    # With the fix, shuffle should be called BEFORE the first check
    # For now, we just verify it eventually succeeds
    assert podcast.epList[0] == ep2, "Should have shuffled to different episode"
    assert podcast.shuffle_call_count >= 1, "Should have called shuffle at least once"


@pytest.mark.usefixtures("mock_tonie_api")
def test_reshuffle_succeeds_on_first_shuffle():
    """
    Test that reshuffle can succeed on the first attempt when episodes are different.

    This test ensures that if a shuffle immediately results in a different first episode,
    the function returns success on the first attempt.
    """
    tps = ToniePodcastSync("user", "pass")

    # Create episodes
    test_feed_data_1 = {
        "title": "Episode A",
        "published": "Mon, 01 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-a",
        "itunes_duration": "10:30",
    }
    test_feed_data_2 = {
        "title": "Episode B",
        "published": "Tue, 02 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 2, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-b",
        "itunes_duration": "10:30",
    }

    ep_a = Episode(podcast="Test Podcast", raw=test_feed_data_1, url="http://example.com/a.mp3")
    ep_b = Episode(podcast="Test Podcast", raw=test_feed_data_2, url="http://example.com/b.mp3")

    class PodcastMock(mock.MagicMock):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self.shuffle_call_count = 0
            self.epList = [ep_a, ep_b]
            self.title = "Test Podcast"

        def sort_episodes(self) -> None:
            self.shuffle_call_count += 1
            if self.epList[0] == ep_a:
                self.epList[0], self.epList[1] = self.epList[1], self.epList[0]

    podcast = PodcastMock()

    # Current tonie has Episode A and B
    current_titles = [
        "Episode A (Mon, 01 Jan 2024 10:00:00 +0000)",
        "Episode B (Tue, 02 Jan 2024 10:00:00 +0000)",
    ]

    with (
        mock.patch("tonie_podcast_sync.toniepodcastsync.log") as mock_log,
    ):
        tps._ToniePodcastSync__reshuffle_until_different(podcast, current_titles)

        # Should succeed and log success
        info_calls = [call for call in mock_log.info.call_args_list if "Successfully shuffled" in str(call)]
        assert len(info_calls) == 1, "Should log success message"

        # With the bug: needs to shuffle once (after first failed check)
        # With fix: should shuffle once (before first check succeeds)
        # Either way, should only shuffle once for this scenario
        assert podcast.shuffle_call_count == 1, f"Expected 1 shuffle call, got {podcast.shuffle_call_count}"


@pytest.mark.usefixtures("mock_tonie_api")
def test_reshuffle_exhausts_all_attempts():
    """
    Test that reshuffle exhausts all MAX_SHUFFLE_ATTEMPTS when it can't find a different episode.

    This ensures the retry logic is working correctly even when shuffling keeps returning
    the same first episode.
    """
    tps = ToniePodcastSync("user", "pass")

    # Create two episodes but mock shuffle to always keep same order
    test_feed_data_1 = {
        "title": "Episode X",
        "published": "Mon, 01 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-x",
        "itunes_duration": "10:30",
    }
    test_feed_data_2 = {
        "title": "Episode Y",
        "published": "Tue, 02 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 2, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-y",
        "itunes_duration": "10:30",
    }

    ep_x = Episode(podcast="Test Podcast", raw=test_feed_data_1, url="http://example.com/x.mp3")
    ep_y = Episode(podcast="Test Podcast", raw=test_feed_data_2, url="http://example.com/y.mp3")

    class PodcastMock(mock.MagicMock):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self.shuffle_call_count = 0
            self.epList = [ep_x, ep_y]
            self.title = "Test Podcast"

        def sort_episodes(self) -> None:
            # Don't actually shuffle - keep same order
            self.shuffle_call_count += 1

    podcast = PodcastMock()

    current_titles = [
        "Episode X (Mon, 01 Jan 2024 10:00:00 +0000)",
        "Episode Y (Tue, 02 Jan 2024 10:00:00 +0000)",
    ]

    with (
        mock.patch("tonie_podcast_sync.toniepodcastsync.log") as mock_log,
    ):
        tps._ToniePodcastSync__reshuffle_until_different(podcast, current_titles)

        # Should have attempted MAX_SHUFFLE_ATTEMPTS times
        assert podcast.shuffle_call_count == MAX_SHUFFLE_ATTEMPTS, (
            f"Expected {MAX_SHUFFLE_ATTEMPTS} shuffle attempts, got {podcast.shuffle_call_count}"
        )

        # Should log warning about exhausting attempts
        # Check for the warning call with the right format
        warning_calls = [
            call for call in mock_log.warning.call_args_list if "Could not find different first episode" in str(call)
        ]
        assert len(warning_calls) == 1, "Should warn after exhausting all attempts"

        # Verify the warning includes the correct number of attempts
        warning_call = warning_calls[0]
        assert MAX_SHUFFLE_ATTEMPTS in warning_call[0], f"Warning should mention {MAX_SHUFFLE_ATTEMPTS} attempts"
