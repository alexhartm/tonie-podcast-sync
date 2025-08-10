"""The Tonie Podcast Sync API."""

import logging
import random
import time
import platform
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from datetime import timedelta

import requests
from pathvalidate import sanitize_filename, sanitize_filepath
from pydub import AudioSegment
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
        self.__api.upload_file_to_tonie(tonie, ep.fpath, self.__generate_chapter_title(ep))

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
        for ep in podcast.epList:
            # this is to stop if we are already over the maximum specified time
            if (total_seconds + ep.duration_sec) >= (max_minutes * 60):
                break
            # this filters out all episodes of the podcast that are shorter then the given time
            if ep.duration_sec < podcast.episode_min_duration_sec:
                log.info(
                    "%s: skipping episode %s as too short (%d sec)",
                    podcast.title,
                    ep.title,
                    ep.duration_sec,
                )
                continue
            total_seconds += ep.duration_sec
            episodes_to_cache.append(ep)
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

    def sync_combined_podcasts_to_tonies(
        self,
        podcast_urls: list[str],
        tonie_ids: list[str],
        max_minutes_per_tonie: int = MAXIMUM_TONIE_MINUTES,
        episode_min_duration_sec: int = 0,
        volume_adjustment: int = 0,
        wipe: bool = True,  # noqa: FBT001, FBT002
        episode_selection: EpisodeSorting = EpisodeSorting.BY_DATE_NEWEST_FIRST,
        smart_random: bool = False,
        smart_random_days: int = 7,
        first_tonie_newest_then_random: bool = False,
    ) -> None:
        """Fill multiple tonies with newest episodes from multiple podcasts.

        This method merges all episodes from the provided podcast feeds and distributes
        them across the provided tonies.

        Selection is controlled by ``episode_selection``. Supported values:
        - EpisodeSorting.BY_DATE_NEWEST_FIRST: newest-first
        - EpisodeSorting.BY_DATE_OLDEST_FIRST: oldest-first
        - EpisodeSorting.RANDOM: random selection/order per tonie

        Additionally, set ``smart_random=True`` to ensure all episodes from the last
        ``smart_random_days`` are selected first, and fill remaining time with random
        older episodes. If ``first_tonie_newest_then_random=True``, the first tonie is
        filled newest-first while others are filled randomly.

        Args:
            podcast_urls (list[str]): List of podcast feed URLs.
            tonie_ids (list[str]): List of creative tonie IDs to fill.
            max_minutes_per_tonie (int, optional): Max minutes per tonie. Defaults to 90.
            episode_min_duration_sec (int, optional): Skip episodes shorter than this.
                Defaults to 0.
            volume_adjustment (int, optional): Adjust volume (in dB) of downloaded audio.
                Defaults to 0.
            wipe (bool, optional): Wipe tonies before syncing. Defaults to True.
        """
        with tempfile.TemporaryDirectory() as podcast_cache_directory:
            self.podcast_cache_directory = Path(podcast_cache_directory)

            # Clamp minutes per tonie to valid bounds
            if max_minutes_per_tonie <= 0 or max_minutes_per_tonie > MAXIMUM_TONIE_MINUTES:
                max_minutes_per_tonie = MAXIMUM_TONIE_MINUTES

            # Validate tonies
            unknown_tonies = [tid for tid in tonie_ids if tid not in self.__tonieDict]
            if unknown_tonies:
                msg = f"ERROR: Cannot find tonies with IDs: {', '.join(unknown_tonies)}"
                log.error(msg)
                console.print(msg, style="red")
                # Continue with valid tonies only
                tonie_ids = [tid for tid in tonie_ids if tid in self.__tonieDict]
                if not tonie_ids:
                    return

            # Build podcast objects and merge episode lists
            podcasts: list[Podcast] = []
            for url in podcast_urls:
                try:
                    podcasts.append(
                        Podcast(
                            url,
                            episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST,
                            volume_adjustment=volume_adjustment,
                            episode_min_duration_sec=episode_min_duration_sec,
                        ),
                    )
                except Exception as exc:  # noqa: BLE001
                    log.warning("Skipping podcast '%s' due to error: %s", url, exc)

            combined_episodes: list[Episode] = []
            for podcast in podcasts:
                combined_episodes.extend(podcast.epList)

            if not combined_episodes:
                msg = "ERROR: No episodes available across all provided podcasts."
                log.error(msg)
                console.print(msg, style="red")
                return

            # Pre-filter by minimum duration
            combined_episodes = [ep for ep in combined_episodes if ep.duration_sec >= episode_min_duration_sec]

            # Distribute episodes to each tonie, filling up to the max per tonie, without duplicates across tonies
            for tonie_id in tonie_ids:
                if wipe:
                    self.__wipe_tonie(tonie_id)

                total_seconds = 0
                selected_for_tonie: list[Episode] = []

                # Determine strategy for this tonie
                use_smart_random = smart_random
                if first_tonie_newest_then_random and tonie_id == tonie_ids[0]:
                    use_smart_random = False
                    effective_selection = EpisodeSorting.BY_DATE_NEWEST_FIRST
                else:
                    effective_selection = episode_selection

                if use_smart_random:
                    now_epoch = time.time()
                    cutoff_epoch = now_epoch - (smart_random_days * 24 * 3600)

                    # Priority: recent episodes within the last `smart_random_days`
                    recent_candidates = [
                        ep for ep in combined_episodes if time.mktime(ep.published_parsed) >= cutoff_epoch
                    ]
                    # Sort by newest first for priority portion
                    recent_candidates.sort(key=lambda ep: ep.published_parsed, reverse=True)

                    # Fill with recent episodes first
                    idx = 0
                    while idx < len(recent_candidates):
                        ep = recent_candidates[idx]
                        if (total_seconds + ep.duration_sec) >= (max_minutes_per_tonie * 60):
                            break
                        selected_for_tonie.append(ep)
                        total_seconds += ep.duration_sec
                        # Remove from global pool to avoid duplicates across tonies
                        if ep in combined_episodes:
                            combined_episodes.remove(ep)
                        idx += 1

                    # Fill remaining capacity with random episodes from the remaining pool
                    if total_seconds < (max_minutes_per_tonie * 60) and combined_episodes:
                        remaining_candidates = list(combined_episodes)
                        random.shuffle(remaining_candidates)
                        for ep in remaining_candidates:
                            if (total_seconds + ep.duration_sec) >= (max_minutes_per_tonie * 60):
                                break
                            selected_for_tonie.append(ep)
                            total_seconds += ep.duration_sec
                            if ep in combined_episodes:
                                combined_episodes.remove(ep)
                else:
                    # Standard strategies: newest, oldest, random
                    if effective_selection == EpisodeSorting.BY_DATE_NEWEST_FIRST:
                        ordered_pool = sorted(combined_episodes, key=lambda ep: ep.published_parsed, reverse=True)
                    elif effective_selection == EpisodeSorting.BY_DATE_OLDEST_FIRST:
                        ordered_pool = sorted(combined_episodes, key=lambda ep: ep.published_parsed)
                    else:  # EpisodeSorting.RANDOM
                        ordered_pool = list(combined_episodes)
                        random.shuffle(ordered_pool)

                    for ep in ordered_pool:
                        if (total_seconds + ep.duration_sec) >= (max_minutes_per_tonie * 60):
                            break
                        selected_for_tonie.append(ep)
                        total_seconds += ep.duration_sec
                        if ep in combined_episodes:
                            combined_episodes.remove(ep)

                if not selected_for_tonie:
                    console.print(
                        f"No suitable episodes available to fill {self.__tonieDict[tonie_id].name} ({tonie_id}).",
                        style="orange",
                    )
                    continue

                # Order episodes on the tonie depending on selection. Keep random order when RANDOM.
                if use_smart_random:
                    # Keep newest first for clarity on tonie
                    selected_for_tonie.sort(key=lambda ep: ep.published_parsed, reverse=True)
                elif effective_selection == EpisodeSorting.BY_DATE_NEWEST_FIRST:
                    selected_for_tonie.sort(key=lambda ep: ep.published_parsed, reverse=True)
                elif effective_selection == EpisodeSorting.BY_DATE_OLDEST_FIRST:
                    selected_for_tonie.sort(key=lambda ep: ep.published_parsed)
                else:
                    # RANDOM: keep the random order as selected
                    pass

                for ep in track(
                    selected_for_tonie,
                    description=(
                        f"Transferring {len(selected_for_tonie)} episodes to {self.__tonieDict[tonie_id].name}"
                    ),
                    total=len(selected_for_tonie),
                    transient=True,
                    refresh_per_second=2,
                ):
                    if self.__cache_episode(ep):
                        self.__upload_episode(ep, tonie_id)

                episode_info = [f"{episode.title} ({episode.published})" for episode in selected_for_tonie]
                console.print(
                    f"Successfully uploaded {episode_info} to {self.__tonieDict[tonie_id].name} ({tonie_id})",
                )
