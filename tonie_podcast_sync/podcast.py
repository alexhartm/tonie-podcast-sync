"""The podcast module to fetch all information of a podcast feed."""

from __future__ import annotations

import logging
import random
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import feedparser

from tonie_podcast_sync.constants import MAXIMUM_TONIE_MINUTES

if TYPE_CHECKING:
    from pathlib import Path
    from time import struct_time

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

MAX_EPISODE_TITLES_IN_WARNING = 3


def normalize_unicode_caseless(s: str) -> str:
    """Converts string to lower-case with unambiguous unicode representation of special characters.

    Args:
            s: The string to convert

    Returns:
            Converted lower-case string
    """

    def nfd(s: str) -> str:
        return unicodedata.normalize("NFD", s)

    return nfd(nfd(s).casefold())


def compare_unicode_caseless(s1: str, s2: str) -> bool:
    """Compares strings in unambiguous lower-case unicode representation.

    This allows in particular the lower-case comparison of strings including umlauts.

    Args:
            s1: The first string
            s2: The second string

    Returns:
            True, if both strings have the same representation, False otherwise.
    """
    return normalize_unicode_caseless(s1) == normalize_unicode_caseless(s2)


class EpisodeSorting(str, Enum):
    """Enum to select the sorting method for podcast episodes."""

    BY_DATE_NEWEST_FIRST = "by_date_newest_first"
    BY_DATE_OLDEST_FIRST = "by_date_oldest_first"
    RANDOM = "random"


class Podcast:
    """Representation of a podcast feed."""

    def __init__(  # noqa: PLR0913
        self,
        url: str,
        episode_sorting: EpisodeSorting = EpisodeSorting.BY_DATE_NEWEST_FIRST,
        volume_adjustment: int = 0,
        episode_min_duration_sec: int = 0,
        episode_max_duration_sec: int = MAXIMUM_TONIE_MINUTES * 60,
        excluded_title_strings: list[str] | None = None,
        pinned_episode_names: list[str] | None = None,
    ) -> None:
        """Initialize the podcast feed and fetch all episodes.

        Args:
            url: The URL of the podcast feed
            episode_sorting: How to sort episodes. Defaults to BY_DATE_NEWEST_FIRST.
            volume_adjustment: Volume adjustment in dB (0 = no adjustment)
            episode_min_duration_sec: Minimum episode duration to include (in seconds)
            episode_max_duration_sec: Maximum individual episode duration (in seconds).
                Defaults to MAXIMUM_TONIE_MINUTES * 60 (90 min)
            excluded_title_strings: List of strings to filter out from episode titles
                (case-insensitive matching)
            pinned_episode_names: List of episode names that will always be prioritized
                in episode sorting. (parital, case-insensitive matching)
        """
        self.volume_adjustment = volume_adjustment
        self.episode_min_duration_sec = episode_min_duration_sec
        self.episode_max_duration_sec = episode_max_duration_sec
        self.excluded_title_strings = (
            [normalize_unicode_caseless(s) for s in excluded_title_strings] if excluded_title_strings else []
        )
        self.pinned_episode_names = (
            [normalize_unicode_caseless(s) for s in pinned_episode_names] if pinned_episode_names else []
        )

        self.epList: list[Episode] = []
        self.epSorting = episode_sorting

        self.feed = feedparser.parse(url)
        if self.feed.bozo:
            raise self.feed.bozo_exception
        self.title = self.feed.feed.title
        self.refresh_feed()

    def _should_include_episode(self, episode: Episode) -> bool:
        """Check if an episode should be included based on filters.

        Args:
            episode: The episode to check

        Returns:
            True if episode passes all filters, False otherwise
        """
        # Only apply episode filter for non-pinned episoded
        if not episode.pinned:
            if episode.duration_sec < self.episode_min_duration_sec:
                log.info(
                    "%s: skipping episode '%s' as too short (%d sec, min is %d sec)",
                    self.title,
                    episode.title,
                    episode.duration_sec,
                    self.episode_min_duration_sec,
                )
                return False

            if episode.duration_sec > self.episode_max_duration_sec:
                log.info(
                    "%s: skipping episode '%s' as too long (%d sec, max is %d sec)",
                    self.title,
                    episode.title,
                    episode.duration_sec,
                    self.episode_max_duration_sec,
                )
                return False

            if self.excluded_title_strings and any(
                excluded_string in normalize_unicode_caseless(episode.title)
                for excluded_string in self.excluded_title_strings
            ):
                log.info(
                    "%s: skipping episode '%s' as title contains excluded string",
                    self.title,
                    episode.title,
                )
                return False

        return True

    def _should_pin_episode(self, episode: Episode) -> bool:
        """Check if an episode should pinned based on settings.

        Args:
            episode: The episode to check

        Returns:
            True if episode should be pinned, False otherwise
        """
        return self.pinned_episode_names and any(
            pinned_name in normalize_unicode_caseless(episode.title) for pinned_name in self.pinned_episode_names
        )

    def refresh_feed(self) -> None:
        """Refresh the podcast feed and populate the episodes list."""
        episodes_without_duration = []

        for item in self.feed.entries:
            url = self._extract_episode_url(item)

            if self._is_missing_duration(item):
                episodes_without_duration.append(item.title)

            episode = Episode(
                podcast=self.title,
                raw=item,
                url=url,
                volume_adjustment=self.volume_adjustment,
            )
            episode.pinned = self._should_pin_episode(episode)

            if self._should_include_episode(episode):
                self.epList.append(episode)

        self._warn_about_missing_durations(episodes_without_duration)
        self.sort_episodes()
        log.info("%s: feed refreshed, %d episodes found", self.title, len(self.epList))

    def _extract_episode_url(self, item: dict) -> str:
        """Extract the episode audio URL from a feed item.

        Args:
            item: The feed item dictionary

        Returns:
            The URL to the audio file
        """
        url = item.id
        for link in item.links:
            if link["rel"] == "enclosure":
                url = link["href"]
                break
        return url

    def _is_missing_duration(self, item: dict) -> bool:
        """Check if a feed item is missing duration information.

        Args:
            item: The feed item dictionary

        Returns:
            True if duration is missing or empty, False otherwise
        """
        return "itunes_duration" not in item or not item.get("itunes_duration", "").strip()

    def _warn_about_missing_durations(self, episodes_without_duration: list[str]) -> None:
        """Log a warning if episodes are missing duration information.

        Args:
            episodes_without_duration: List of episode titles without duration
        """
        if not episodes_without_duration:
            return

        displayed_titles = episodes_without_duration[:MAX_EPISODE_TITLES_IN_WARNING]
        title_list = ", ".join(displayed_titles)
        if len(episodes_without_duration) > MAX_EPISODE_TITLES_IN_WARNING:
            title_list += "..."

        log.warning(
            "%s: %d episode(s) in feed are missing duration information: %s",
            self.title,
            len(episodes_without_duration),
            title_list,
        )

    def sort_episodes(self) -> None:
        """Sort episodes according to the configured sorting method."""
        match self.epSorting:
            # Prioritize pinned epsiodes, then use regular sorting criterium
            case EpisodeSorting.BY_DATE_NEWEST_FIRST:
                self.epList.sort(key=lambda x: (x.pinned, x.published_parsed), reverse=True)
            case EpisodeSorting.BY_DATE_OLDEST_FIRST:
                self.epList.sort(key=lambda x: (not x.pinned, x.published_parsed))
            case EpisodeSorting.RANDOM:
                pinned_episoded = [ep for ep in self.epList if ep.pinned]
                sorting_episodes = [ep for ep in self.epList if not ep.pinned]
                random.shuffle(sorting_episodes)
                self.epList = pinned_episoded + sorting_episodes


@dataclass
class Episode:
    """A dataclass representing a podcast episode."""

    podcast: str
    raw: dict
    title: str = field(init=False)
    published: str = field(init=False)
    published_parsed: struct_time = field(init=False)
    url: str = ""
    guid: str = field(init=False)
    fpath: Path = field(init=False, compare=False)
    duration_str: str = field(init=False)
    duration_sec: int = field(init=False)
    volume_adjustment: int = 0
    pinned: bool = False

    def __post_init__(self) -> None:
        """Initialize derived fields from raw feed data."""
        self.title = self.raw["title"]
        self.published = self.raw["published"]
        self.published_parsed = self.raw["published_parsed"]
        self.guid = self.raw["id"]
        self.duration_str = self.raw.get("itunes_duration", "0")
        self.duration_sec = self._parse_duration(self.duration_str)

    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        """Parse duration string into seconds.

        Handles formats: "SS", "MM:SS", or "HH:MM:SS"

        Args:
            duration_str: The duration string to parse

        Returns:
            Duration in seconds, or 0 if parsing fails
        """
        if not duration_str or not duration_str.strip():
            return 0

        try:
            parts = duration_str.split(":")

            match len(parts):
                case 1:
                    return int(parts[0])
                case 2:
                    minutes, seconds = parts
                    return int(minutes) * 60 + int(seconds)
                case 3:
                    hours, minutes, seconds = parts
                    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
                case _:
                    return 0
        except (ValueError, TypeError):
            return 0
