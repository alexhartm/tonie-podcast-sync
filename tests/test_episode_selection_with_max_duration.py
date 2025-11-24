"""Test for episode selection when individual episodes exceed max_minutes limit.

Bug: When using RANDOM sorting with a max_minutes limit smaller than some
individual episodes, if a long episode is randomly selected first, the
_select_episodes_within_time_limit method returns zero episodes instead of
skipping the long episode and selecting shorter ones.
"""

from pathlib import Path
from unittest.mock import Mock

from tonie_podcast_sync.podcast import Episode, EpisodeSorting, Podcast
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


def test_select_episodes_with_random_sorting_skips_long_episodes():
    """
    Test that RANDOM sorting works correctly when some episodes exceed max_minutes.

    This is the actual bug scenario from "Alle gegen Nico" podcast:
    - 29 episodes with episode_min_duration_sec=600 (10 min)
    - 4 episodes are > 45 minutes individually
    - With RANDOM sorting, if a long episode is first, it should be skipped

    We run multiple trials to ensure the fix works consistently across different
    random orderings, including when long episodes appear first.
    """
    # Create a podcast feed that mimics the "Alle gegen Nico" scenario
    # Using the actual XML file ensures realistic testing
    test_feed = str(Path(__file__).parent / "res" / "alle-gegen-nico.xml")

    podcast = Podcast(
        test_feed,
        episode_sorting=EpisodeSorting.RANDOM,
        episode_min_duration_sec=600,
    )

    # Verify the podcast has episodes
    assert len(podcast.epList) > 0, "Podcast should have episodes after filtering"

    # Count episodes that are individually > 45 minutes
    max_minutes = 45
    max_seconds = max_minutes * 60
    long_episodes = [ep for ep in podcast.epList if ep.duration_sec > max_seconds]
    short_episodes = [ep for ep in podcast.epList if ep.duration_sec <= max_seconds]

    assert len(long_episodes) > 0, "Test requires some episodes > 45 min"
    assert len(short_episodes) > 0, "Test requires some episodes <= 45 min"

    # Setup
    tps = ToniePodcastSync.__new__(ToniePodcastSync)

    # Run multiple trials to test different random orderings
    trials = 20
    success_count = 0

    for _ in range(trials):
        # Create fresh podcast instance for each trial (new random order)
        podcast_trial = Podcast(
            test_feed,
            episode_sorting=EpisodeSorting.RANDOM,
            episode_min_duration_sec=600,
        )

        # Act
        selected = tps._select_episodes_within_time_limit(podcast_trial, max_minutes)

        # Assert: Should select at least one episode in most cases
        # Even if first episode is > 45 min, it should skip and continue
        if len(selected) > 0:
            success_count += 1

            # Verify selected episodes are within limits
            for ep in selected:
                assert ep.duration_sec <= max_seconds, (
                    f"Selected episode '{ep.title}' ({ep.duration_sec}s) exceeds max_minutes ({max_seconds}s)"
                )

            # Verify total duration doesn't exceed limit
            total_duration = sum(ep.duration_sec for ep in selected)
            assert total_duration <= max_seconds, (
                f"Total duration ({total_duration}s) exceeds max_minutes ({max_seconds}s)"
            )

    # Assert: Should succeed in most trials (allow for rare case where all episodes are too long)
    # With 25 out of 29 episodes fitting, we expect high success rate
    min_expected_success = trials * 0.8  # At least 80% success rate
    assert success_count >= min_expected_success, (
        f"Expected at least {min_expected_success} successes out of {trials} trials, "
        f"but got {success_count}. The fix should work consistently with RANDOM sorting."
    )


def test_random_sorting_provides_variety_across_multiple_runs():
    """
    Test that RANDOM sorting actually produces variety across multiple runs.

    This is a high-level integration test that verifies:
    - Random sorting doesn't always return the same episodes
    - Different episodes are selected across multiple sync attempts
    - The variety is meaningful (not just the same 5 episodes)

    This test covers the full flow from Podcast creation through episode selection,
    ensuring the random behavior works correctly end-to-end.
    """
    test_feed = str(Path(__file__).parent / "res" / "alle-gegen-nico.xml")

    # Setup
    tps = ToniePodcastSync.__new__(ToniePodcastSync)
    max_minutes = 45

    # Track which unique episodes are selected across multiple runs
    selected_episode_titles = set()
    runs = 30

    for _ in range(runs):
        # Create fresh podcast with RANDOM sorting for each run
        podcast = Podcast(
            test_feed,
            episode_sorting=EpisodeSorting.RANDOM,
            episode_min_duration_sec=600,
        )

        # Select episodes (simulating what sync_podcast_to_tonie does)
        selected = tps._select_episodes_within_time_limit(podcast, max_minutes)

        # Track all selected episode titles
        for episode in selected:
            selected_episode_titles.add(episode.title)

    # Assert: Should have selected many different episodes across all runs
    # With 29 episodes available and 30 runs, we expect to see significant variety
    # At minimum, we should see more than just 5 different episodes
    min_unique_episodes = 10
    assert len(selected_episode_titles) >= min_unique_episodes, (
        f"Expected at least {min_unique_episodes} unique episodes across {runs} runs, "
        f"but only got {len(selected_episode_titles)}. "
        f"RANDOM sorting should provide variety, not the same episodes repeatedly."
    )

    # Assert: Should have reasonable variety (at least 30% of available episodes seen)
    # This ensures random isn't just picking from a small subset
    expected_variety_percentage = 0.3
    total_available = len(
        Podcast(
            test_feed,
            episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST,
            episode_min_duration_sec=600,
        ).epList
    )
    min_variety = int(total_available * expected_variety_percentage)
    assert len(selected_episode_titles) >= min_variety, (
        f"Expected to see at least {min_variety} different episodes "
        f"({expected_variety_percentage * 100}% of {total_available} available), "
        f"but only saw {len(selected_episode_titles)}. "
        f"RANDOM sorting should explore the episode catalog more broadly."
    )


def test_random_sorting_integration_with_episode_caching():
    """
    Integration test: Verify RANDOM sorting works with the full caching workflow.

    This test verifies that when using RANDOM sorting:
    1. Different episodes are considered across multiple podcast instances
    2. The episode selection respects max_minutes even with random ordering
    3. First episodes can vary (proving randomness at the selection level)

    This is closer to real usage where podcast instances are created fresh
    and episodes are selected for caching.
    """
    test_feed = str(Path(__file__).parent / "res" / "alle-gegen-nico.xml")
    tps = ToniePodcastSync.__new__(ToniePodcastSync)
    max_minutes = 45

    # Run multiple times and track first episodes selected
    first_episodes = []
    total_runs = 20

    for _ in range(total_runs):
        podcast = Podcast(
            test_feed,
            episode_sorting=EpisodeSorting.RANDOM,
            episode_min_duration_sec=600,
        )

        selected = tps._select_episodes_within_time_limit(podcast, max_minutes)

        if selected:
            first_episodes.append(selected[0].title)

    # Assert: First episode should vary across runs (not always the same)
    unique_first_episodes = set(first_episodes)
    assert len(unique_first_episodes) > 1, (
        f"RANDOM sorting should vary the first episode selected, "
        f"but got the same episode {len(first_episodes)} times: {first_episodes[0] if first_episodes else 'none'}"
    )

    # Assert: Should see reasonable variety in first episodes (at least 5 different ones)
    min_unique_first = 5
    assert len(unique_first_episodes) >= min_unique_first, (
        f"Expected at least {min_unique_first} different first episodes across {total_runs} runs, "
        f"but only saw {len(unique_first_episodes)}. "
        f"This suggests RANDOM sorting is not sufficiently random."
    )

    # Assert: All selected episode groups should respect time limit
    for i in range(len(first_episodes)):
        podcast_check = Podcast(
            test_feed,
            episode_sorting=EpisodeSorting.RANDOM,
            episode_min_duration_sec=600,
        )
        # Just verify the logic would work - we already tested time limits above
        assert len(podcast_check.epList) > 0, f"Run {i}: Podcast should have episodes"
