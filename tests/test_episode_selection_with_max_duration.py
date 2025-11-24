"""Test for episode selection when individual episodes exceed max_minutes limit.

Bug: When using RANDOM sorting with a max_minutes limit smaller than some
individual episodes, if a long episode is randomly selected first, the
_select_episodes_within_time_limit method returns zero episodes instead of
skipping the long episode and selecting shorter ones.
"""

from unittest.mock import Mock

from tonie_podcast_sync.podcast import Episode
from tonie_podcast_sync.toniepodcastsync import ToniePodcastSync


def _create_mock_episode(duration_sec: int, title: str = "Test Episode") -> Episode:
    """Create a mock episode with specified duration."""
    episode = Mock(spec=Episode)
    episode.duration_sec = duration_sec
    episode.title = title
    return episode


def test_select_episodes_skips_individual_episodes_exceeding_max_minutes():
    """
    Test that episodes exceeding max_minutes individually are skipped.

    Scenario: Podcast has episodes of 46min, 40min, 35min (in that order)
              max_minutes is 45
    Expected: Should skip 46min episode and select 40min episode
    Actual (bug): Returns empty list because first episode exceeds limit
    """
    # Setup
    tps = ToniePodcastSync.__new__(ToniePodcastSync)

    # Create mock podcast with episodes in order: 46min, 40min, 35min
    mock_podcast = Mock()
    mock_podcast.title = "Test Podcast"
    mock_podcast.epList = [
        _create_mock_episode(2760, "Episode 1 - 46 minutes"),  # Exceeds 45 min
        _create_mock_episode(2400, "Episode 2 - 40 minutes"),  # Fits
        _create_mock_episode(2100, "Episode 3 - 35 minutes"),  # Fits
    ]

    max_minutes = 45

    # Act
    selected = tps._select_episodes_within_time_limit(mock_podcast, max_minutes)

    # Assert
    assert len(selected) > 0, (
        "Should select at least one episode when shorter episodes are available, "
        "even if first episode exceeds max_minutes"
    )
    assert selected[0].title == "Episode 2 - 40 minutes", (
        "Should skip first episode (46min) and select second episode (40min)"
    )
    assert len(selected) == 1, (
        "Should select only first episode that fits (40min), as adding 35min would exceed 45min total"
    )


def test_select_episodes_fits_multiple_when_skipping_long_ones():
    """
    Test that multiple episodes can be selected when skipping long ones.

    Scenario: Episodes of 50min, 20min, 15min, 50min, 10min
              max_minutes is 45
    Expected: Skip 50min episodes, select 20min + 15min + 10min = 45min total
    """
    # Setup
    tps = ToniePodcastSync.__new__(ToniePodcastSync)

    mock_podcast = Mock()
    mock_podcast.title = "Test Podcast"
    mock_podcast.epList = [
        _create_mock_episode(3000, "Episode 1 - 50 minutes"),  # Too long
        _create_mock_episode(1200, "Episode 2 - 20 minutes"),  # Fits
        _create_mock_episode(900, "Episode 3 - 15 minutes"),  # Fits
        _create_mock_episode(3000, "Episode 4 - 50 minutes"),  # Too long
        _create_mock_episode(600, "Episode 5 - 10 minutes"),  # Fits
    ]

    max_minutes = 45

    # Act
    selected = tps._select_episodes_within_time_limit(mock_podcast, max_minutes)

    # Assert
    assert len(selected) == 3, "Should select 3 episodes (20min + 15min + 10min)"
    assert selected[0].title == "Episode 2 - 20 minutes"
    assert selected[1].title == "Episode 3 - 15 minutes"
    assert selected[2].title == "Episode 5 - 10 minutes"

    total_duration = sum(ep.duration_sec for ep in selected)
    assert total_duration <= max_minutes * 60, "Total duration should not exceed max_minutes"
    assert total_duration == 2700, "Total should be 45 minutes (2700 seconds)"


def test_select_episodes_returns_empty_when_all_exceed_limit():
    """
    Test that empty list is returned when all episodes exceed max_minutes.

    Scenario: All episodes are 50+ minutes, max_minutes is 45
    Expected: Return empty list (no episodes fit)
    """
    # Setup
    tps = ToniePodcastSync.__new__(ToniePodcastSync)

    mock_podcast = Mock()
    mock_podcast.title = "Test Podcast"
    mock_podcast.epList = [
        _create_mock_episode(3000, "Episode 1 - 50 minutes"),
        _create_mock_episode(3300, "Episode 2 - 55 minutes"),
        _create_mock_episode(3600, "Episode 3 - 60 minutes"),
    ]

    max_minutes = 45

    # Act
    selected = tps._select_episodes_within_time_limit(mock_podcast, max_minutes)

    # Assert
    assert len(selected) == 0, "Should return empty list when all individual episodes exceed max_minutes"


def test_select_episodes_works_normally_when_all_fit():
    """
    Test that normal behavior is preserved when all episodes fit individually.

    Scenario: Episodes of 20min, 30min, 40min, max_minutes is 45
    Expected: Select 20min only (adding 30min would exceed limit)
    """
    # Setup
    tps = ToniePodcastSync.__new__(ToniePodcastSync)

    mock_podcast = Mock()
    mock_podcast.title = "Test Podcast"
    mock_podcast.epList = [
        _create_mock_episode(1200, "Episode 1 - 20 minutes"),
        _create_mock_episode(1800, "Episode 2 - 30 minutes"),
        _create_mock_episode(2400, "Episode 3 - 40 minutes"),
    ]

    max_minutes = 45

    # Act
    selected = tps._select_episodes_within_time_limit(mock_podcast, max_minutes)

    # Assert
    assert len(selected) == 1, "Should select only first episode (20min)"
    assert selected[0].title == "Episode 1 - 20 minutes"
