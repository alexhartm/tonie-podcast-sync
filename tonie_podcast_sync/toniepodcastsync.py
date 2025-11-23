"""The Tonie Podcast Sync API."""

import logging
import platform
import random
import subprocess
import tempfile
import time
from io import BytesIO
from pathlib import Path

import requests
from pathvalidate import sanitize_filename, sanitize_filepath
from pydub import AudioSegment
from requests.exceptions import HTTPError, RequestException
from rich.console import Console
from rich.progress import track
from rich.table import Table
from tonie_api.api import TonieAPI
from tonie_api.models import CreativeTonie

from tonie_podcast_sync.constants import (
    DOWNLOAD_RETRY_COUNT,
    MAX_SHUFFLE_ATTEMPTS,
    MAXIMUM_TONIE_MINUTES,
    RETRY_DELAY_SECONDS,
    UPLOAD_RETRY_COUNT,
)
from tonie_podcast_sync.podcast import (
    Episode,
    EpisodeSorting,
    Podcast,
)

console = Console()
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ToniePodcastSync:
    """The class of syncing podcasts to given tonies."""

    def __init__(self, user: str, pwd: str) -> None:
        """Initialize ToniePodcastSync and connect to the TonieAPI.

        Args:
            user: The username for the Tonie Cloud API
            pwd: The password for the Tonie Cloud API
        """
        self._api = TonieAPI(user, pwd)
        self._households = {household.id: household for household in self._api.get_households()}
        self._update_tonies()

    def _update_tonies(self) -> None:
        """Refresh the internal cache of creative tonies."""
        self._tonies = {tonie.id: tonie for tonie in self._api.get_all_creative_tonies()}

    def get_tonies(self) -> list[CreativeTonie]:
        """Return a list of all creative tonies.

        Returns:
            A list of CreativeTonie objects.
        """
        return list(self._tonies.values())

    def print_tonies_overview(self) -> None:
        """Print a table of all available creative tonies to the console."""
        table = Table(title="List of all creative tonies.")
        table.add_column("ID", no_wrap=True)
        table.add_column("Name of Tonie")
        table.add_column("Time of last update")
        table.add_column("Household")
        table.add_column("Latest Episode name")

        for tonie in self._tonies.values():
            last_update = tonie.lastUpdate.strftime("%c") if tonie.lastUpdate else None
            latest_chapter = tonie.chapters[0].title if tonie.chaptersPresent > 0 else "No latest chapter available."
            table.add_row(
                tonie.id,
                tonie.name,
                last_update,
                self._households[tonie.householdId].name,
                latest_chapter,
            )
        console.print(table)

    def sync_podcast_to_tonie(
        self,
        podcast: Podcast,
        tonie_id: str,
        max_minutes: int = 90,
        wipe: bool = True,  # noqa: FBT001, FBT002
    ) -> None:
        """Sync new episodes from a podcast feed to a creative Tonie.

        Downloads and uploads new podcast episodes to the specified Tonie.
        Limits total episode duration to max_minutes.

        Args:
            podcast: The podcast to sync episodes from
            tonie_id: The ID of the target Tonie
            max_minutes: Maximum total duration of episodes in minutes. Defaults to 90.
            wipe: Whether to clear existing content before syncing. Defaults to True.
        """
        with tempfile.TemporaryDirectory() as podcast_cache_directory:
            self.podcast_cache_directory = Path(podcast_cache_directory)
            log.debug("Cache path is %s", self.podcast_cache_directory)

            if not self._validate_tonie_exists(tonie_id):
                return

            if not self._validate_podcast_has_episodes(podcast, tonie_id):
                return

            if not self._should_update_tonie(podcast, tonie_id):
                return

            if wipe:
                self._wipe_tonie(tonie_id)

            # For RANDOM mode, reshuffle before caching to ensure fresh episodes
            if podcast.epSorting == EpisodeSorting.RANDOM and not self._is_tonie_empty(tonie_id):
                latest_episode_tonie = self._tonies[tonie_id].chapters[0].title
                self.__reshuffle_until_different(podcast, latest_episode_tonie)

            cached_episodes = self.__cache_podcast_episodes(podcast, max_minutes)
            self._upload_episodes_to_tonie(podcast, cached_episodes, tonie_id)

    def _validate_tonie_exists(self, tonie_id: str) -> bool:
        """Check if a Tonie with the given ID exists.

        Args:
            tonie_id: The ID of the Tonie to check

        Returns:
            True if the Tonie exists, False otherwise
        """
        if tonie_id not in self._tonies:
            msg = f"Cannot find tonie with ID {tonie_id}"
            log.error(msg)
            console.print(f"ERROR: {msg}", style="red")
            return False
        return True

    def _validate_podcast_has_episodes(self, podcast: Podcast, tonie_id: str) -> bool:
        """Check if the podcast has any episodes available.

        Args:
            podcast: The podcast to check
            tonie_id: The ID of the target Tonie (for error message)

        Returns:
            True if episodes are available, False otherwise
        """
        if len(podcast.epList) == 0:
            msg = f"Cannot find any episodes for podcast '{podcast.title}' to put on tonie with ID {tonie_id}"
            log.warning(msg)
            console.print(f"ERROR: {msg}", style="orange")
            return False
        return True

    def _should_update_tonie(self, podcast: Podcast, tonie_id: str) -> bool:
        """Determine if the Tonie should be updated with new episodes.

        Args:
            podcast: The podcast to check for new episodes
            tonie_id: The ID of the Tonie to check

        Returns:
            True if the Tonie should be updated, False otherwise
        """
        if self._is_tonie_empty(tonie_id):
            log.info("Tonie is empty, proceeding with sync")
            return True

        # Skip check in random mode - always update
        if podcast.epSorting == EpisodeSorting.RANDOM:
            return True

        # Check if new feed has newer episodes than tonie
        latest_episode_feed = self._generate_chapter_title(podcast.epList[0])
        latest_episode_tonie = self._tonies[tonie_id].chapters[0].title

        if latest_episode_tonie == latest_episode_feed:
            msg = f"Podcast '{podcast.title}' has no new episodes, latest episode is '{latest_episode_tonie}'"
            log.info(msg)
            console.print(msg)
            return False

        return True

    def _upload_episodes_to_tonie(
        self,
        podcast: Podcast,
        episodes: list[Episode],
        tonie_id: str,
    ) -> None:
        """Upload a list of episodes to a Tonie.

        Args:
            podcast: The podcast object (for title information)
            episodes: List of episodes to upload
            tonie_id: The ID of the target Tonie
        """
        successfully_uploaded = []
        failed_episodes = []

        for episode in track(
            episodes,
            description=(f"{podcast.title}: transferring {len(episodes)} episodes to {self._tonies[tonie_id].name}"),
            total=len(episodes),
            transient=True,
            refresh_per_second=2,
        ):
            if self._upload_episode(episode, tonie_id):
                successfully_uploaded.append(episode)
            else:
                failed_episodes.append(episode)

        self._report_upload_results(podcast.title, tonie_id, successfully_uploaded, failed_episodes)

    def _report_upload_results(
        self,
        podcast_title: str,
        tonie_id: str,
        successfully_uploaded: list[Episode],
        failed_episodes: list[Episode],
    ) -> None:
        """Report the results of episode uploads to the user.

        Args:
            podcast_title: The title of the podcast
            tonie_id: The ID of the Tonie
            successfully_uploaded: List of successfully uploaded episodes
            failed_episodes: List of episodes that failed to upload
        """
        if successfully_uploaded:
            episode_info = [f"{episode.title} ({episode.published})" for episode in successfully_uploaded]
            console.print(
                f"{podcast_title}: Successfully uploaded {episode_info} to "
                f"{self._tonies[tonie_id].name} ({self._tonies[tonie_id].id})",
            )

        if failed_episodes:
            failed_info = [episode.title for episode in failed_episodes]
            console.print(
                f"{podcast_title}: Failed to upload {len(failed_episodes)} episode(s): {failed_info}",
                style="red",
            )

    def _upload_episode(self, episode: Episode, tonie_id: str) -> bool:
        """Upload a single episode to a creative Tonie.

        Args:
            episode: The episode to upload
            tonie_id: The ID of the target Tonie

        Returns:
            True if upload was successful, False otherwise
        """
        tonie = self._tonies[tonie_id]
        for _attempt in range(UPLOAD_RETRY_COUNT):
            try:
                self._api.upload_file_to_tonie(tonie, episode.fpath, self._generate_chapter_title(episode))
                return True  # noqa: TRY300
            except HTTPError as e:  # noqa: PERF203
                log.warning("Upload failed for %s, retrying in %d seconds: %s", episode.title, RETRY_DELAY_SECONDS, e)
                time.sleep(RETRY_DELAY_SECONDS)

        log.error("Unable to upload file %s after %d attempts", episode.title, UPLOAD_RETRY_COUNT)
        return False

    def _wipe_tonie(self, tonie_id: str) -> None:
        """Remove all chapters from a Tonie.

        Args:
            tonie_id: The ID of the Tonie to wipe
        """
        tonie = self._tonies[tonie_id]
        console.print(f"Wipe all chapters of Tonie '{tonie.name}'")
        self._api.clear_all_chapter_of_tonie(tonie)
        self._update_tonies()

    def __cache_podcast_episodes(self, podcast: Podcast, max_minutes: int = MAXIMUM_TONIE_MINUTES) -> list[Episode]:
        """Download podcast episodes locally, limited to max_minutes total duration.

        Args:
            podcast: The podcast to cache episodes from
            max_minutes: Maximum total duration in minutes

        Returns:
            List of successfully cached episodes
        """
        if max_minutes <= 0 or max_minutes > MAXIMUM_TONIE_MINUTES:
            max_minutes = MAXIMUM_TONIE_MINUTES

        episodes_to_cache = self._select_episodes_within_time_limit(podcast, max_minutes)

        if not episodes_to_cache:
            msg = f"No episodes found for podcast '{podcast.title}' that fit within {max_minutes} minutes"
            log.warning(msg)
            console.print(f"WARNING: {msg}", style="yellow")
            return []

        # Track available fallback episodes
        available_episodes = [ep for ep in podcast.epList if ep not in episodes_to_cache]

        cached_episodes, failed_episodes = self._download_episodes_with_fallback(
            podcast, episodes_to_cache, available_episodes, max_minutes
        )

        self._log_caching_summary(podcast, cached_episodes, failed_episodes)
        return cached_episodes

    def _select_episodes_within_time_limit(self, podcast: Podcast, max_minutes: int) -> list[Episode]:
        """Select episodes from podcast that fit within the time limit.

        Args:
            podcast: The podcast to select episodes from
            max_minutes: Maximum total duration in minutes

        Returns:
            List of episodes that fit within the time limit
        """
        episodes = []
        total_seconds = 0
        max_seconds = max_minutes * 60

        for episode in podcast.epList:
            if (total_seconds + episode.duration_sec) > max_seconds:
                break
            total_seconds += episode.duration_sec
            episodes.append(episode)

        return episodes

    def _download_episodes_with_fallback(
        self,
        podcast: Podcast,
        episodes_to_cache: list[Episode],
        available_episodes: list[Episode],
        max_minutes: int,
    ) -> tuple[list[Episode], list[Episode]]:
        """Download episodes with fallback to alternative episodes on failure.

        Args:
            podcast: The podcast object
            episodes_to_cache: Primary list of episodes to download
            available_episodes: List of fallback episodes
            max_minutes: Maximum total duration in minutes

        Returns:
            Tuple of (successfully cached episodes, failed episodes without replacement)
        """
        cached_episodes: list[Episode] = []
        failed_episodes = []
        current_duration = 0
        max_seconds = max_minutes * 60

        for episode in track(
            episodes_to_cache,
            description=f"{podcast.title}: Cache episodes ...",
            total=len(episodes_to_cache),
            transient=True,
            refresh_per_second=2,
        ):
            if self.__cache_episode(episode):
                cached_episodes.append(episode)
                current_duration += episode.duration_sec
            else:
                failed_episodes.append(episode)
                replacement = self._find_replacement_episode(available_episodes, max_seconds, current_duration)

                if replacement and self._try_cache_replacement(podcast, replacement, episode):
                    cached_episodes.append(replacement)
                    available_episodes.remove(replacement)
                    current_duration += replacement.duration_sec
                    failed_episodes.remove(episode)

        return cached_episodes, failed_episodes

    def _try_cache_replacement(self, podcast: Podcast, replacement: Episode, failed_episode: Episode) -> bool:
        """Attempt to cache a replacement episode.

        Args:
            podcast: The podcast object
            replacement: The replacement episode to try
            failed_episode: The episode that failed to download

        Returns:
            True if replacement was successfully cached, False otherwise
        """
        log.info(
            "%s: Attempting replacement episode '%s' for failed download of '%s'",
            podcast.title,
            replacement.title,
            failed_episode.title,
        )

        if self.__cache_episode(replacement):
            return True

        log.warning(
            "%s: Replacement episode '%s' also failed to download",
            podcast.title,
            replacement.title,
        )
        return False

    def _log_caching_summary(
        self, podcast: Podcast, cached_episodes: list[Episode], failed_episodes: list[Episode]
    ) -> None:
        """Log a summary of the caching operation.

        Args:
            podcast: The podcast object
            cached_episodes: List of successfully cached episodes
            failed_episodes: List of episodes that failed to cache
        """
        if failed_episodes:
            log.warning(
                "%s: %d episode(s) failed to download and could not be replaced",
                podcast.title,
                len(failed_episodes),
            )

        total_duration_minutes = sum(ep.duration_sec for ep in cached_episodes) / 60
        log.info(
            "%s: providing %d episodes with %.1f min total",
            podcast.title,
            len(cached_episodes),
            total_duration_minutes,
        )

    def _find_replacement_episode(
        self,
        available_episodes: list[Episode],
        max_seconds: int,
        current_seconds: int,
    ) -> Episode | None:
        """Find a replacement episode when download fails.

        Args:
            available_episodes: List of episodes not yet selected
            max_seconds: Maximum total seconds allowed
            current_seconds: Current total seconds already downloaded

        Returns:
            A replacement episode if found, None otherwise
        """
        for episode in available_episodes:
            if (current_seconds + episode.duration_sec) <= max_seconds:
                return episode
        return None

    def __cache_episode(self, episode: Episode) -> bool:
        """Download a single episode to local cache.

        Args:
            episode: The episode to download

        Returns:
            True if download was successful, False otherwise
        """
        podcast_path = self.podcast_cache_directory / sanitize_filepath(episode.podcast)
        podcast_path.mkdir(parents=True, exist_ok=True)

        filepath = podcast_path / self._generate_filename(episode)
        if filepath.exists():
            log.info("File %s exists, will be overwritten", episode.guid)
            filepath.unlink()

        for _attempt in range(DOWNLOAD_RETRY_COUNT):
            try:
                response = requests.get(episode.url, timeout=180)
                response.raise_for_status()

                content = self._process_audio_content(response.content, episode.volume_adjustment)

                with filepath.open("wb") as file:
                    file.write(content)
                    episode.fpath = filepath

                return True  # noqa: TRY300
            except RequestException as e:  # noqa: PERF203
                log.warning(
                    "Download failed for %s, retrying in %d seconds: %s",
                    episode.url,
                    RETRY_DELAY_SECONDS,
                    e,
                )
                time.sleep(RETRY_DELAY_SECONDS)

        log.error("Unable to download file from %s after %d attempts", episode.url, DOWNLOAD_RETRY_COUNT)
        return False

    def _process_audio_content(self, content: bytes, volume_adjustment: int) -> bytes:
        """Process audio content, applying volume adjustment if needed.

        Args:
            content: The raw audio content
            volume_adjustment: Volume adjustment in dB (0 means no adjustment)

        Returns:
            Processed audio content
        """
        if volume_adjustment != 0 and self._is_ffmpeg_available():
            return self._adjust_volume(content, volume_adjustment)
        return content

    def _generate_filename(self, episode: Episode) -> str:
        """Generate a canonical filename for local episode cache.

        Args:
            episode: The episode to generate a filename for

        Returns:
            Sanitized filename string
        """
        return sanitize_filename(f"{episode.published} {episode.title}.mp3")

    def _generate_chapter_title(self, episode: Episode) -> str:
        """Generate chapter title for display on Tonie.

        Args:
            episode: The episode to generate a title for

        Returns:
            Formatted chapter title string
        """
        return f"{episode.title} ({episode.published})"

    def _is_tonie_empty(self, tonie_id: str) -> bool:
        """Check if a Tonie has no chapters.

        Args:
            tonie_id: The ID of the Tonie to check

        Returns:
            True if the Tonie is empty, False otherwise
        """
        return self._tonies[tonie_id].chaptersPresent == 0

    def __reshuffle_until_different(self, podcast: Podcast, current_first_episode_title: str) -> None:
        """Re-shuffle podcast episodes until first episode differs from current one on Tonie.

        Args:
            podcast: The podcast with episodes to shuffle
            current_first_episode_title: The title of the current first episode on the Tonie
        """
        for attempt in range(MAX_SHUFFLE_ATTEMPTS):
            random.shuffle(podcast.epList)
            first_episode_title = self._generate_chapter_title(podcast.epList[0])

            if first_episode_title != current_first_episode_title:
                log.info(
                    "%s: Successfully shuffled to new first episode after %d attempt(s)",
                    podcast.title,
                    attempt + 1,
                )
                return

            log.info(
                "%s: Shuffle attempt %d - first episode still matches, re-shuffling",
                podcast.title,
                attempt + 1,
            )

        log.warning(
            "%s: Could not find different first episode after %d shuffle attempts",
            podcast.title,
            MAX_SHUFFLE_ATTEMPTS,
        )

    def _adjust_volume(self, audio_bytes: bytes, volume_adjustment: int) -> bytes:
        """Adjust the volume of audio content.

        Args:
            audio_bytes: The raw audio data
            volume_adjustment: Volume adjustment in dB

        Returns:
            Adjusted audio data
        """
        audio = AudioSegment.from_file(BytesIO(audio_bytes), format="mp3")
        adjusted_audio = audio + volume_adjustment

        byte_io = BytesIO()
        adjusted_audio.export(byte_io, format="mp3")

        return byte_io.getvalue()

    def _is_ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available on the system.

        Returns:
            True if ffmpeg is available, False otherwise
        """
        try:
            executable = "ffmpeg" if platform.system().lower() != "windows" else "ffmpeg.exe"
            subprocess.run([executable, "-version"], check=True, capture_output=True)  # noqa: S603
            return True  # noqa: TRY300
        except (FileNotFoundError, subprocess.CalledProcessError):
            console.print(
                "Warning: you tried to adjust the volume without having 'ffmpeg' available. "
                "Please install 'ffmpeg' or set no volume adjustment.",
                style="red",
            )
            return False
