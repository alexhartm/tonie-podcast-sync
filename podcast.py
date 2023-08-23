"""The podcast module to fetch all information of a podcast feed."""
import logging
from enum import Enum
import random
from dataclasses import dataclass, field
from time import struct_time
import feedparser

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class EpisodeSorting(Enum):
    """An enum to select which sorting of the episode shall be applied."""

    BY_DATE_NEWEST_FIRST = 1
    BY_DATE_OLDEST_FIRST = 2
    RANDOM = 3


class Podcast:
    def __init__(
        self: "Podcast", url: str, episode_sorting: EpisodeSorting = EpisodeSorting.BY_DATE_NEWEST_FIRST
    ) -> None:
        self.epList = []  # a list of all episodes
        self.epSorting = episode_sorting  # the sorting of the episode list

        self.feed = feedparser.parse(url)
        self.title = self.feed.feed.title  # title of podcast
        self.refreshFeed()  # reads feed and populates the episode list

    def refreshFeed(self: "Podcast"):
        # reads feed and populates the episode list
        for item in self.feed.entries:
            self.epList.append(Episode(podcast=self.title, raw=item))

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
    """A dataclass for a podcast episode"""

    podcast: str  # Podcast Title this episode belongs to
    raw: dict
    title: str = field(init=False)
    published: str = field(init=False)  # date when published
    published_parsed: struct_time = field(init=False)  # parsed published date
    url: str = field(init=False)
    guid: str = field(init=False)
    fname: str = ""
    fpath: str = ""
    durationStr: str = field(init=False)
    durationSec: int = field(init=False)

    def __post_init__(self):
        self.title = self.raw.title
        self.published = self.raw.published
        self.published_parsed = self.raw.published_parsed
        self.url = self.raw.id
        self.guid = self.raw.id
        self.durationStr = self.raw.itunes_duration
        self.durationSec = self.__durStr2sec(self.durationStr)

    @staticmethod
    def __durStr2sec(str):
        h, m, s = 0, 0, 0
        match str.count(":"):
            case 0:
                s = str
            case 1:
                m, s = str.split(":")
            case 2:
                h, m, s = str.split(":")
            case _:
                log.warning("Could not match time string.")

        return int(h) * 3600 + int(m) * 60 + int(s)
