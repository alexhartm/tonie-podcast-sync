from tonie_podcast_sync.toniepodcastsync import ToniePodcastSync
from tonie_podcast_sync.podcast import EpisodeSorting

tps = ToniePodcastSync("georg.wuitschik@gmail.com", "vymxib-wencyf-fUcxa3")
tps.sync_combined_podcasts_to_tonies(
    podcast_urls=[
        "https://feeds.br.de/checkpod-der-podcast-mit-checker-tobi/feed.xml",
        # PodcastIndex podcast/7101101 (Alle gegen Nico - Zockt um die Quizkrone!)
        "https://feeds.br.de/alle-gegen-nico-zockt-um-die-quizkrone/feed.xml",
        "https://proxyfeed.svmaudio.com/aa/geolino-spezial",
        "https://flipsi-findets-raus.podigee.io/feed/mp3",
        "https://anchor.fm/s/dce83154/podcast/rss",
        "https://planetariumberlin.podcaster.de/abgespaced.rss",
        "https://galileo-kids.podigee.io/feed/mp3",
        "https://klugschnabeln.podigee.io/feed/mp3",
        "https://schlaulicht.info/feed/mp3",
        "https://www.br.de/kinder/hoeren/podcasts/anna-und-die-wilden-tiere-tierabenteuer-podcast-100~rss.xml",
        "https://taxi-ins-mich.podigee.io/feed/mp3",
        "https://kinder-wollens-wissen.podigee.io/feed/mp3",
        "https://www.ndr.de/podcast/podcast4096.xml",
        "https://kruschelerklaerts.podigee.io/feed/mp3",
        "https://hoer-dich-klug.podigee.io/feed/mp3",
        "https://feeds.buzzsprout.com/2522641.rss",
        "https://anchor.fm/s/109d94bf8/podcast/rss",
        "https://clever-nachgefragt.podigee.io/feed/mp3",
        # SRF Kids Reporter:in (MP3 enclosures)
        "https://www.srf.ch/feed/podcast/sd/27fbe150-ade2-4bbe-84ab-a4d745f8e492.xml",
        # Theo erzählt – ein Kinderpodcast (kinderpodcast.ch; hosted on Libsyn)
        "https://kinderpodcast.libsyn.com/rss",
    ],
    tonie_ids=["6608C419500304E0", "C96FD620500304E0"],
    episode_selection=EpisodeSorting.RANDOM,
    first_tonie_newest_then_random=True,
    max_minutes_per_tonie=90,
    episode_min_duration_sec=0,
    volume_adjustment=0,
    wipe=True,
)
