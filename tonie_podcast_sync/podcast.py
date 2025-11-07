"""The podcast module to fetch all information of a podcast feed."""

import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from time import struct_time

import feedparser

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class EpisodeSorting(str, Enum):
    """An enum to select which sorting of the episode shall be applied."""

    BY_DATE_NEWEST_FIRST = "by_date_newest_first"
    BY_DATE_OLDEST_FIRST = "by_date_oldest_first"
    RANDOM = "random"


class Podcast:
    """The representation of a podcast feed."""

    def __init__(
        self,
        url: str,
        episode_sorting: EpisodeSorting = EpisodeSorting.BY_DATE_NEWEST_FIRST,
        volume_adjustment: int = 0,
        episode_min_duration_sec: int = 0,
    ) -> None:
        """Initializes the podcast feed and fetches all episodes.

        Args:
            url (str): The url of the podcast
            episode_sorting (EpisodeSorting, optional): Set how the episodes are sorted.
                                                        Defaults to EpisodeSorting.BY_DATE_NEWEST_FIRST.
            volume_adjustment (int, optional): If set, the downloaded audio will be adjusted by the given amount in dB.
                                                        Defaults to 0, i.e. no adjustment
            episode_min_duration_sec (int, optional): all episodes with duration < this value
                                                        [in seconds] will be ignored
        """
        self.volume_adjustment = volume_adjustment
        self.episode_min_duration_sec = episode_min_duration_sec

        self.epList = []  # a list of all episodes
        self.epSorting = episode_sorting  # the sorting of the episode list

        self.feed = feedparser.parse(url)
        if self.feed.bozo:
            raise self.feed.bozo_exception
        self.title = self.feed.feed.title  # title of podcast
        self.refresh_feed()  # reads feed and populates the episode list

    def refresh_feed(self) -> None:
        """Refresh the podcast feed and get the episodes list."""
        # reads feed and populates the episode list
        for item in self.feed.entries:
            # for most feeds, the item.id contains a URL to the audio file
            # but not in all cases. The audio file is to my knowledge available
            # in the enclosure section as href.
            url = item.id
            for iterator in item.links:
                if iterator["rel"] == "enclosure":
                    url = iterator["href"]

            # filter out all episodes that are longer than the max capacity
            # of 90 minutes per tonie
            max_duration_min = 90
            max_duration_sec = (max_duration_min * 60) - 5  # 5 seconds buffer
            if Episode(podcast=self.title, raw=item, url=url).duration_sec >= max_duration_sec:
                log.debug(
                    "%s: skipping episode '%s' as it is longer than %s min.",
                    self.title,
                    item.title,
                    max_duration_min,
                )
                continue

            self.epList.append(Episode(podcast=self.title, raw=item, url=url, volume_adjustment=self.volume_adjustment))

        match self.epSorting:
            case EpisodeSorting.BY_DATE_NEWEST_FIRST:
                self.epList.sort(key=lambda x: x.published_parsed, reverse=True)
            case EpisodeSorting.BY_DATE_OLDEST_FIRST:
                self.epList.sort(key=lambda x: x.published_parsed)
            case EpisodeSorting.RANDOM:
                random.shuffle(self.epList)

        log.info("%s: feed refreshed, %s episodes found.", self.title, len(self.epList))


@dataclass
class Episode:
    """A dataclass for a podcast episode."""

    podcast: str  # Podcast Title this episode belongs to
    raw: dict
    title: str = field(init=False)
    published: str = field(init=False)  # date when published
    published_parsed: struct_time = field(init=False)  # parsed published date
    url: str = ""
    guid: str = field(init=False)
    fpath: Path = field(init=False, compare=False)
    duration_str: str = field(init=False)
    duration_sec: int = field(init=False)
    volume_adjustment: int = 0

    def __post_init__(self) -> None:
        self.title = self.raw["title"]
        self.published = self.raw["published"]
        self.published_parsed = self.raw["published_parsed"]
        self.guid = self.raw["id"]
        self.duration_str = self.raw["itunes_duration"]
        self.duration_sec = self.__dur_str_in_sec(self.duration_str)

    @staticmethod
    def __dur_str_in_sec(duration_str: str) -> int:
        h, m, s = 0, 0, 0
        match duration_str.count(":"):
            case 0:
                s = duration_str
            case 1:
                m, s = duration_str.split(":")
            case 2:
                h, m, s = duration_str.split(":")
            case _:
                log.warning("Could not match time string.")

        return int(h) * 3600 + int(m) * 60 + int(s)
