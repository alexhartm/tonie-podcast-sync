from pathlib import Path
from podcast import Podcast, EpisodeSorting

import pytest


def test_url_type():
    """This test uses a rss feed from the real web, if this reference is not available it might fail"""
    podcast = Podcast(r"https://kinder.wdr.de/radio/diemaus/audio/maus-zoom/maus-zoom-106.podcast")
    assert podcast.epList


@pytest.mark.parametrize(
    "feed,title,length",
    [
        (str(Path(__file__).parent / "res" / "sandmann.xml"), "Unser Sandmännchen", 67),
        (str(Path(__file__).parent / "res" / "kakadu.xml"), "Kakadu – Der Kinderpodcast", 51),
        (str(Path(__file__).parent / "res" / "true_crime.xml"), "Crime Junkie", 334),
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
    for i in range(len(sorted_objects)):
        if sorted_objects[i] != objects[i]:
            return True
    return False
