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


def test_included_title_strings():
    """Test that only episodes with included title strings are kept."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Test without inclusion filter - should have 51 episodes
    podcast_no_filter = Podcast(feed)
    assert len(podcast_no_filter.epList) == 51

    # Test with inclusion for "Update" - should only keep episodes containing this string
    podcast_with_filter = Podcast(feed, included_title_strings=["Update"])

    # Should have fewer episodes than full feed
    assert len(podcast_with_filter.epList) < 51
    # Verify all remaining episodes contain the included string
    for episode in podcast_with_filter.epList:
        assert "update" in episode.title.lower()


def test_included_title_strings_case_insensitive():
    """Test that title inclusion is case-insensitive."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Test with different case variations
    podcast_upper = Podcast(feed, included_title_strings=["UPDATE"])
    podcast_lower = Podcast(feed, included_title_strings=["update"])
    podcast_mixed = Podcast(feed, included_title_strings=["UpDaTe"])

    # All should filter the same episodes
    assert len(podcast_upper.epList) == len(podcast_lower.epList)
    assert len(podcast_lower.epList) == len(podcast_mixed.epList)


def test_included_title_strings_multiple():
    """Test filtering with multiple included strings (OR logic)."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Get count with single include string
    podcast_single = Podcast(feed, included_title_strings=["Update"])
    single_count = len(podcast_single.epList)

    # Test with multiple inclusion strings - should include episodes matching ANY string
    podcast_multi = Podcast(feed, included_title_strings=["Update", "Vorurteile"])

    # Multiple strings should include more (or same) episodes than single string
    assert len(podcast_multi.epList) >= single_count

    # Verify all remaining episodes contain at least one of the included strings
    for episode in podcast_multi.epList:
        title_lower = episode.title.lower()
        assert "update" in title_lower or "vorurteile" in title_lower


def test_included_title_strings_empty_list():
    """Test that empty inclusion list doesn't filter anything."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    podcast_empty_list = Podcast(feed, included_title_strings=[])
    podcast_no_param = Podcast(feed)

    # Both should have the same number of episodes
    assert len(podcast_empty_list.epList) == len(podcast_no_param.epList)


def test_included_and_excluded_combined():
    """Test that both include and exclude filters work together."""
    feed = str(Path(__file__).parent / "res" / "kakadu.xml")

    # Get counts for individual filters
    podcast_include_only = Podcast(feed, included_title_strings=["Warum"])
    include_only_count = len(podcast_include_only.epList)

    # Combined: must match include AND not match exclude
    podcast_combined = Podcast(
        feed,
        included_title_strings=["Warum"],
        excluded_title_strings=["Update"],
    )

    # Combined should have same or fewer than include-only
    assert len(podcast_combined.epList) <= include_only_count

    # Verify all remaining episodes match include and don't match exclude
    for episode in podcast_combined.epList:
        title_lower = episode.title.lower()
        assert "warum" in title_lower
        assert "update" not in title_lower
