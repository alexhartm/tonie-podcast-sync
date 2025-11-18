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
