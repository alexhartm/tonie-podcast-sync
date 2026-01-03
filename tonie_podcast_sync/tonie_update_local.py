"""
Local-only helper script.

This file is gitignored so you can keep credentials here if you want.
Copy/paste your credentials below and run:

    python3 tonie_podcast_sync/tonie_update_local.py

Alternative (module mode, from repo root):

    python3 -m tonie_podcast_sync.tonie_update_local

If you prefer not to hardcode, use:
    tonie-podcast-sync create-settings-file
and the standard CLI (`tonie-podcast-sync update-tonies`).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running this file directly (`python3 tonie_podcast_sync/tonie_update_local.py`)
# by ensuring the repo root is on sys.path.
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from tonie_podcast_sync.podcast import EpisodeSorting
from tonie_podcast_sync.toniepodcastsync import ToniePodcastSync

# Fill in your credentials (local file, not committed)
USERNAME = "georg.wuitschik@gmail.com"
PASSWORD = "vymxib-wencyf-fUcxa3"

tps = ToniePodcastSync(USERNAME, PASSWORD)
tps.sync_combined_podcasts_to_tonies(
    podcast_urls=[
        "https://feeds.br.de/checkpod-der-podcast-mit-checker-tobi/feed.xml",
        # PodcastIndex podcast/7101101 (Alle gegen Nico - Zockt um die Quizkrone!)
        "https://feeds.br.de/alle-gegen-nico-zockt-um-die-quizkrone/feed.xml",
        # SRF Kids Reporter:in (MP3 enclosures)
        "https://www.srf.ch/feed/podcast/sd/27fbe150-ade2-4bbe-84ab-a4d745f8e492.xml",
        # Theo erzählt – ein Kinderpodcast (kinderpodcast.ch; hosted on Libsyn)
        "https://kinderpodcast.libsyn.com/rss",
    ],
    tonie_ids=["6608C419500304E0", "C96FD620500304E0", "17699823500304E0"],
    episode_selection=EpisodeSorting.RANDOM,
    first_tonie_newest_then_random=True,
    max_minutes_per_tonie=90,
    episode_min_duration_sec=0,
    volume_adjustment=0,
    wipe=True,
)


