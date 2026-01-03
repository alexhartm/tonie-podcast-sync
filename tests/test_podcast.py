from pathlib import Path

import pytest

from tonie_podcast_sync.podcast import EpisodeSorting, Podcast


def test_url_type():
    """This test uses a rss feed from the real web, if this reference is not available it might fail"""
    podcast = Podcast(r"https://kinder.wdr.de/radio/diemaus/audio/maus-zoom/maus-zoom-106.podcast")
    assert podcast.epList


@pytest.mark.parametrize(
    ("feed", "title", "length"),
    [
        (str(Path(__file__).parent / "res" / "sandmann.xml"), "Unser Sandmännchen", 67),
        (str(Path(__file__).parent / "res" / "kakadu.xml"), "Kakadu - Der Kinderpodcast", 51),
        (str(Path(__file__).parent / "res" / "true_crime.xml"), "Crime Junkie", 333),
        (str(Path(__file__).parent / "res" / "pumuckl.xml"), "Pumuckl - Der Hörspiel-Klassiker", 15),
        (str(Path(__file__).parent / "res" / "diemaus.xml"), "Die Maus zum Hören", 47),
    ],
)
class TestPodcast:
    def test_podcast_initialization(self, feed, title, length):
        podcast = Podcast(feed)
        assert podcast.title == title
        assert len(podcast.epList) == length

    def test_episode_sorting_default(self, feed, title, length):
        podcast = Podcast(feed)
        assert podcast.epList[0].published_parsed > podcast.epList[-1].published_parsed

    def test_episode_sorting_newest_first(self, feed, title, length):
        podcast = Podcast(feed, episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST)
        assert podcast.epList[0].published_parsed > podcast.epList[-1].published_parsed

    def test_episode_sorting_oldest_first(self, feed, title, length):
        podcast = Podcast(feed, episode_sorting=EpisodeSorting.BY_DATE_OLDEST_FIRST)
        assert podcast.epList[0].published_parsed < podcast.epList[-1].published_parsed

    def test_episode_sorting_random(self, feed, title, length):
        podcast = Podcast(feed, episode_sorting=EpisodeSorting.RANDOM)
        assert is_list_sorted(podcast.epList)


def is_list_sorted(objects: list) -> bool:
    sorted_objects = sorted(objects, key=lambda x: x.published_parsed)
    return any(sorted_objects[i] != objects[i] for i in range(len(sorted_objects)))


def test_excluded_title_strings():
    """Test that episodes with excluded title strings are filtered out."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Test without exclusion - should have 51 episodes
    podcast_no_filter = Podcast(feed)
    assert len(podcast_no_filter.epList) == 51

    # Test with exclusion for "Update:" - should filter out episodes containing this string
    podcast_with_filter = Podcast(feed, excluded_title_strings=["Update:"])
    # At least one episode should be filtered
    assert len(podcast_with_filter.epList) < 51
    # Verify no remaining episodes contain the excluded string
    for episode in podcast_with_filter.epList:
        assert "update:" not in episode.title.lower()


def test_excluded_title_strings_case_insensitive():
    """Test that title filtering is case-insensitive."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Test with different case variations
    podcast_upper = Podcast(feed, excluded_title_strings=["UPDATE"])
    podcast_lower = Podcast(feed, excluded_title_strings=["update"])
    podcast_mixed = Podcast(feed, excluded_title_strings=["UpDaTe"])

    # All should filter the same episodes
    assert len(podcast_upper.epList) == len(podcast_lower.epList)
    assert len(podcast_lower.epList) == len(podcast_mixed.epList)


def test_excluded_title_strings_multiple():
    """Test filtering with multiple excluded strings."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Test with multiple exclusion strings
    podcast_multi = Podcast(feed, excluded_title_strings=["Update:", "Vorurteile"])

    # Verify no episodes contain any of the excluded strings
    for episode in podcast_multi.epList:
        assert "update:" not in episode.title.lower()
        assert "vorurteile" not in episode.title.lower()


def test_excluded_title_strings_empty_list():
    """Test that empty exclusion list doesn't filter anything."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    podcast_empty_list = Podcast(feed, excluded_title_strings=[])
    podcast_no_param = Podcast(feed)

    # Both should have the same number of episodes
    assert len(podcast_empty_list.epList) == len(podcast_no_param.epList)


def test_episode_min_duration_filtering():
    """Test that episodes shorter than min duration are filtered out."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Get baseline
    podcast_no_filter = Podcast(feed)
    baseline_count = len(podcast_no_filter.epList)

    # Filter out episodes shorter than 1500 seconds (25 minutes)
    podcast_with_min = Podcast(feed, episode_min_duration_sec=1500)

    # Should have fewer episodes (kakadu has episodes between 1190s and 1639s)
    assert len(podcast_with_min.epList) < baseline_count
    # All remaining episodes should be at least 1500 seconds
    for episode in podcast_with_min.epList:
        assert episode.duration_sec >= 1500


def test_episode_max_duration_filtering():
    """Test that episodes longer than max duration are filtered out."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Get baseline
    podcast_no_filter = Podcast(feed)
    baseline_count = len(podcast_no_filter.epList)

    # Filter out episodes longer than 1200 seconds (20 minutes)
    podcast_with_max = Podcast(feed, episode_max_duration_sec=1200)

    # Should have fewer or equal episodes
    assert len(podcast_with_max.epList) <= baseline_count
    # All remaining episodes should be at most 1200 seconds
    for episode in podcast_with_max.epList:
        assert episode.duration_sec <= 1200


def test_pinned_episode():
    """Test that single episoded can be pinned with an exact title match."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Podcasts with different sorting methods but no pinned episodes
    podcast_newest_no_pin = Podcast(feed, episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST)
    podcast_oldest_no_pin = Podcast(feed, episode_sorting=EpisodeSorting.BY_DATE_OLDEST_FIRST)

    # Choose an episode that is neither the newest nor the oldest
    pinned_names = ["Mampfis Metamorphose - Woher kommen Schmetterlinge?"]

    # Test that the episode is never the first one without pinning
    for podcast in [podcast_newest_no_pin, podcast_oldest_no_pin]:
        assert len([ep for ep in podcast.epList if ep.pinned]) == 0
        assert podcast.epList[0].title != pinned_names[0]

    # Podcasts with pinned episode and different sorting methods
    # All should have a single pinned episode
    podcast_newest_pinned = Podcast(
        feed, pinned_episode_names=pinned_names, episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST
    )
    podcast_oldest_pinned = Podcast(
        feed, pinned_episode_names=pinned_names, episode_sorting=EpisodeSorting.BY_DATE_OLDEST_FIRST
    )
    podcast_random_pinned = Podcast(feed, pinned_episode_names=pinned_names, episode_sorting=EpisodeSorting.RANDOM)

    # Test that all variants have the pinned episode as their first one
    for podcast in [podcast_newest_pinned, podcast_oldest_pinned, podcast_random_pinned]:
        assert len([ep for ep in podcast.epList if ep.pinned]) == 1
        assert podcast.epList[0].title == pinned_names[0]


def test_episode_pinning_maintains_ordering():
    """Test that episode pinning does not interfere with the ordering of any remaining episodes."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Choose an episode that is neither the newest nor the oldest
    pinned_names = ["Mampfis Metamorphose - Woher kommen Schmetterlinge?"]

    # Podcasts with pinned episode and different sorting methods
    podcast_newest_pinned = Podcast(
        feed, pinned_episode_names=pinned_names, episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST
    )
    podcast_oldest_pinned = Podcast(
        feed, pinned_episode_names=pinned_names, episode_sorting=EpisodeSorting.BY_DATE_OLDEST_FIRST
    )

    # Test that all podcast variants have the pinned episode as their first one
    for podcast in [podcast_newest_pinned, podcast_oldest_pinned]:
        assert len([ep for ep in podcast.epList if ep.pinned]) == 1
        assert podcast.epList[0].title == pinned_names[0]

    # Test that newest ordering is maintained
    newest_episodes = sorted(podcast_newest_pinned.epList[1:], key=lambda x: x.published_parsed, reverse=True)
    assert all(
        ep1.title == ep2.title for ep1, ep2 in zip(newest_episodes, podcast_newest_pinned.epList[1:], strict=True)
    )

    # Test that oldest ordering is maintained
    oldest_episodes = sorted(podcast_newest_pinned.epList[1:], key=lambda x: x.published_parsed, reverse=False)
    assert all(
        ep1.title == ep2.title for ep1, ep2 in zip(oldest_episodes, podcast_oldest_pinned.epList[1:], strict=True)
    )


def test_multiple_pinned_episodes():
    """Test that multiple episodes can be pinned with exact title matches"""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Choose episodes to pin
    pinned_names = [
        "Mampfis Metamorphose - Woher kommen Schmetterlinge?",
        "Neurologie - Wie kommen die Gedanken in den Kopf?",
    ]

    # Podcasts with pinned episode and different sorting methods
    # All should have both episodes pinned
    podcast_newest_pinned = Podcast(
        feed, pinned_episode_names=pinned_names, episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST
    )
    podcast_oldest_pinned = Podcast(
        feed, pinned_episode_names=pinned_names, episode_sorting=EpisodeSorting.BY_DATE_OLDEST_FIRST
    )
    podcast_random_pinned = Podcast(feed, pinned_episode_names=pinned_names, episode_sorting=EpisodeSorting.RANDOM)

    # Test that all variants have the pinned episode as their first one
    for podcast in [podcast_newest_pinned, podcast_oldest_pinned, podcast_random_pinned]:
        assert len([ep for ep in podcast.epList if ep.pinned]) == 2
        # Ordering of the pinned episodes is currently also determined by the sorting method
        # Just ensure that both episodes are at the start
        for pinned_name in pinned_names:
            assert pinned_name in [ep.title for ep in podcast.epList[:2]]


def test_pinned_episode_approx_match():
    """Test that episodes can be pinned with partial and case insensitive title matches"""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    episode_name = "Mampfis Metamorphose - Woher kommen Schmetterlinge?"

    podcast_exact_match = Podcast(
        feed, pinned_episode_names=[episode_name], episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST
    )
    podcast_lowercase_match = Podcast(
        feed, pinned_episode_names=[episode_name.lower()], episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST
    )
    podcast_partial_match = Podcast(
        feed, pinned_episode_names=["metamorphose"], episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST
    )

    # Test that all variants have the pinned episode as their first one
    for podcast in [podcast_exact_match, podcast_lowercase_match, podcast_partial_match]:
        assert len([ep for ep in podcast.epList if ep.pinned]) == 1
        assert podcast.epList[0].title == episode_name
