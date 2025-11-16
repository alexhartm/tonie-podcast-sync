"""The Tonie Podcast Sync API."""

import logging
import platform
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

from tonie_podcast_sync.podcast import (
    Episode,
    EpisodeSorting,  # noqa: F401
    Podcast,
)

console = Console()
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

MAXIMUM_TONIE_MINUTES = 90
DOWNLOAD_RETRY_COUNT = 3
UPLOAD_RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 3


class ToniePodcastSync:
    """The class of syncing podcasts to given tonies."""

    def __init__(self, user: str, pwd: str) -> None:
        """Initialitaion of the ToniePodcastSync and connecting to the TonieAPI.

        Args:
            user (str): the username to the tonie Cloud API
            pwd (_type_): the password to the tonie Cloud API
        """
        self.__api = TonieAPI(user, pwd)
        self._households = {x.id: x for x in self.__api.get_households()}
        self._update_tonies()

    def _update_tonies(self) -> None:
        self.__tonieDict = {x.id: x for x in self.__api.get_all_creative_tonies()}

    def get_tonies(self) -> list[CreativeTonie]:
        """Returns a list of all tonies.

        Returns:
            [CreativeTonie]: A list of CreativeTonies.
        """
        return list(self.__tonieDict.values())

    def print_tonies_overview(self) -> None:
        """Print out a table to console of all available tonies."""
        table = Table(title="List of all creative tonies.")
        table.add_column("ID", no_wrap=True)
        table.add_column("Name of Tonie")
        table.add_column("Time of last update")
        table.add_column("Household")
        table.add_column("Latest Episode name")
        for tonie in self.__tonieDict.values():
            table.add_row(
                tonie.id,
                tonie.name,
                tonie.lastUpdate.strftime("%c") if tonie.lastUpdate else None,
                self._households[tonie.householdId].name,
                tonie.chapters[0].title if tonie.chaptersPresent > 0 else "No latest chapter available.",
            )
        console.print(table)

    def sync_podcast_to_tonie(
        self,
        podcast: Podcast,
        tonie_id: str,
        max_minutes: int = 90,
        wipe: bool = True,  # noqa: FBT001, FBT002
    ) -> None:
        """Sync new episodes from podcast feed to creative Tonie.

        It is done by wiping the tonie and writing all new episodes. Limit episodes on tonie to max_minutes in total.
        If no new episode exists in podcast, nothing will happen.

        Args:
            podcast (Podcast): The podcast to get the newest episodes from
            tonie_id (str): The id of the tonie
            max_minutes (int, optional): The maximum time of podcasts in length. Defaults to 90.
            wipe (bool, optional): Wipes the tonie before syncing. Defaults to True.
        """
        with tempfile.TemporaryDirectory() as podcast_cache_directory:
            self.podcast_cache_directory = Path(podcast_cache_directory)
            msg = f"DEBUG: cache path is {self.podcast_cache_directory}"
            log.debug(msg)
            if tonie_id not in self.__tonieDict:
                msg = f"ERROR: Cannot find tonie with ID {tonie_id}"
                log.error(msg)
                console.print(msg, style="red")
                return
            if len(podcast.epList) == 0:
                msg = (
                    f"ERROR: Cannot find any episodes at all for podcast '{podcast.title}'"
                    f"to put on tonie with ID {tonie_id}"
                )
                log.warning(msg)
                console.print(msg, style="orange")
                return
            if not self.__is_tonie_empty(tonie_id):
                # check if new feed has newer epsiodes than tonie
                latest_episode_feed = self.__generate_chapter_title(podcast.epList[0])
                latest_episode_tonie = self.__tonieDict[tonie_id].chapters[0].title
                if latest_episode_tonie == latest_episode_feed:
                    msg = f"Podcast '{podcast.title}' has no new episodes, latest episode is '{latest_episode_tonie}'"
                    log.info(msg)
                    console.print(msg)
                    return
            else:
                log.info("### tonie is empty")
            # add new episodes to tonie
            if wipe:
                self.__wipe_tonie(tonie_id)
            cached_episodes = self.__cache_podcast_episodes(podcast, max_minutes)

            for e in track(
                cached_episodes,
                description=(
                    f"{podcast.title}: transferring {len(cached_episodes)} episodes"
                    f" to {self.__tonieDict[tonie_id].name}"
                ),
                total=len(cached_episodes),
                transient=True,
                refresh_per_second=2,
            ):
                self.__upload_episode(e, tonie_id)

            episode_info = [f"{episode.title} ({episode.published})" for episode in cached_episodes]
            console.print(
                f"{podcast.title}: Successfully uploaded {episode_info} to "
                f"{self.__tonieDict[tonie_id].name} ({self.__tonieDict[tonie_id].id})",
            )

    def __upload_episode(self, ep: Episode, tonie_id: str) -> None:
        # upload a given episode to a creative tonie
        tonie = self.__tonieDict[tonie_id]
        for _i in range(UPLOAD_RETRY_COUNT):
            try:
                self.__api.upload_file_to_tonie(tonie, ep.fpath, self.__generate_chapter_title(ep))
            except HTTPError as e:  # noqa: PERF203
                log.warning("Upload failed for %s, retrying in %d seconds: %s", ep.title, RETRY_DELAY_SECONDS, e)
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                return True
        log.error("Was not able to upload file %s", ep.title)
        return False

    def __wipe_tonie(self, tonie_id: str) -> None:
        tonie = self.__tonieDict[tonie_id]
        console.print(f"Wipe all chapters of Tonie '{tonie.name}'")
        self.__api.clear_all_chapter_of_tonie(tonie)
        self._update_tonies()

    def __cache_podcast_episodes(self, podcast: Podcast, max_minutes: int = MAXIMUM_TONIE_MINUTES) -> list[Episode]:
        # local download of all episodes of a podcast, limited to maxMin minutes in total
        if max_minutes <= 0 or max_minutes > MAXIMUM_TONIE_MINUTES:
            max_minutes = MAXIMUM_TONIE_MINUTES

        episodes_to_cache = []
        total_seconds = 0
        max_seconds = max_minutes * 60
        for ep in podcast.epList:
            # this filters out all episodes of the podcast that are shorter then the given time
            if ep.duration_sec < podcast.episode_min_duration_sec:
                log.info(
                    "%s: skipping episode %s as too short (%d sec)",
                    podcast.title,
                    ep.title,
                    ep.duration_sec,
                )
                continue
            # this filters out all episodes that are longer than the configured max duration
            if ep.duration_sec > max_seconds:
                log.info(
                    "%s: skipping episode %s as too long (%d sec, max is %d sec)",
                    podcast.title,
                    ep.title,
                    ep.duration_sec,
                    max_seconds,
                )
                continue
            # this is to stop if we are already over the maximum specified time
            if (total_seconds + ep.duration_sec) >= max_seconds:
                break
            total_seconds += ep.duration_sec
            episodes_to_cache.append(ep)

        if len(episodes_to_cache) == 0:
            msg = (
                f"WARNING: No episodes found for podcast '{podcast.title}' "
                f"that match the duration criteria (min: {podcast.episode_min_duration_sec}s, max: {max_seconds}s)"
            )
            log.warning(msg)
            console.print(msg, style="yellow")
            return []

        ep_list: list[Episode] = []

        for ep in track(
            episodes_to_cache,
            description=f"{podcast.title}: Cache episodes ...",
            total=len(episodes_to_cache),
            transient=True,
            refresh_per_second=2,
        ):
            if self.__cache_episode(ep):
                ep_list.append(ep)  # noqa: PERF401

        log.info(
            "%s: providing all %s episodes with %d.1 min total",
            podcast.title,
            len(episodes_to_cache),
            (total_seconds / 60),
        )
        return ep_list

    def __cache_episode(self, ep: Episode) -> bool:
        # local download of a single episode into a subfolder
        # file name is build according to __generateFilename
        podcast_path = self.podcast_cache_directory / sanitize_filepath(ep.podcast)
        podcast_path.mkdir(parents=True, exist_ok=True)

        fname = podcast_path / self.__generate_filename(ep)
        if fname.exists():
            log.info("file %s exists already, will be overwritten", ep.guid)
            fname.unlink()

        # the download part
        for _i in range(DOWNLOAD_RETRY_COUNT):
            try:
                r = requests.get(ep.url, timeout=180)
                r.raise_for_status()
                with fname.open("wb") as _fs:
                    if ep.volume_adjustment != 0 and self.__is_ffmpeg_available():
                        adjusted_content = self.__adjust_volume__(r.content, ep.volume_adjustment)
                    else:
                        adjusted_content = r.content

                    _fs.write(adjusted_content)
                    ep.fpath = fname
            except RequestException as e:  # noqa: PERF203
                log.warning("Download failed for %s, retrying in %d seconds: %s", ep.url, RETRY_DELAY_SECONDS, e)
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                return True
        r = requests.get(ep.url, timeout=180)
        if r.ok:
            with fname.open("wb") as _fs:
                if ep.volume_adjustment != 0 and self.__is_ffmpeg_available():
                    adjusted_content = self.__adjust_volume__(r.content, ep.volume_adjustment)
                else:
                    adjusted_content = r.content

                _fs.write(adjusted_content)
                ep.fpath = fname
            return True

        log.error("Was not able to get file from %s with error %s - %s", ep.url, r.status_code, r.text)
        return False

    def __generate_filename(self, ep: Episode) -> str:
        # generates canonical filename for local episode cache
        return sanitize_filename(f"{ep.published} {ep.title}.mp3")

    def __generate_chapter_title(self, ep: Episode) -> str:
        # generate chapter title used when writing on tonie
        return ep.title + " (" + ep.published + ")"

    def __is_tonie_empty(self, tonie_id: str) -> bool:
        tonie = self.__tonieDict[tonie_id]
        return tonie.chaptersPresent == 0

    def __adjust_volume__(self, audio_bytes: bytes, volume_adjustment: int) -> bytes:
        audio = AudioSegment.from_file(BytesIO(audio_bytes), format="mp3")

        adjusted_audio = audio + volume_adjustment

        byte_io = BytesIO()

        adjusted_audio.export(byte_io, format="mp3")

        return byte_io.getvalue()

    def __is_ffmpeg_available(self) -> bool:
        try:
            # Safe to use untrusted input: executable is hardcoded
            executable = "ffmpeg" if platform.system().lower() != "windows" else "ffmpeg.exe"
            subprocess.run([executable, "-version"], check=True, capture_output=True)  # noqa: S603
        except (FileNotFoundError, subprocess.CalledProcessError):
            console.print(
                "Warning: you tried to adjust the volume without having 'ffmpeg' available. "
                "Please install 'ffmpeg' or set no volume adjustmet.",
                style="red",
            )

            return False
        return True
