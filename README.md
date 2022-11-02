# tonie-podcast-sync

tonie-podcast-sync allows synching podcast episodes to [creative tonies](https://tonies.com).

This is a purely private project and has no association with Boxine GmbH.

# Constraints and Limitations

- currently limited to podcasts providing mp3 files
- tested with the following podcasts:
    - [WDR: Gute Nacht mit der Maus](https://www.wdrmaus.de/hoeren/gute_nacht_mit_der_maus.php5)
    - [Bayern 2: Pumuckl - Der Hörspiel-Klassiker](https://www.br.de/mediathek/podcast/pumuckl/830)
    - [Checker Tobi Podcast](https://www.br.de/mediathek/podcast/checkpod-der-podcast-mit-checker-tobi/859)
    - [Anna und die wilden Tiere - der Podcast](https://www.br.de/mediathek/podcast/anna-und-die-wilden-tiere/858)
- ... but in general, it should work hopefully work with all podcasts out there

# Usage

Use like shown in this example code:

```python
from toniepodcastsync import ToniePodcastSync, Podcast

# create two Podcast objects, providing the feed URL to each
pumuckl = Podcast("https://feeds.br.de/pumuckl/feed.xml")
maus = Podcast("https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast")

# create instance of ToniePodcastSync
tps = ToniePodcastSync("<toniecloud-username>", "<toniecloud-password>")

# for an overview of your creative tonies and their IDs
tps.printToniesOverview()

# define creative tonies based on their ID
greenTonie = "<your-tonieID>"
orangeTonie = "<your-tonieID>"

# Fetch new podcast episodes and copy them to greenTonie.
# The tonie will be filled with as much episodes as fit (90 min max).
# Episode are ordered with newest first.
tps.syncPodcast2Tonie(pumuckl, greenTonie)

# Kid's should fall asleep, so let's limit the podcast 
# episodes on this tonie to 60 minutes in total.
# Use the optional parameter for this:
tps.syncPodcast2Tonie(maus, orangeTonie, 60)  
```

For the tonie to fetch new content from tonie-cloud, you have to press one ear for 3s (until the "ping" sound) with no tonie on the box (refer also to TonieBox manual).


# builds upon work of / kudos to
- moritj29's awesome [tonie_api](https://github.com/moritzj29/tonie_api)
- [Tobias Raabe](https://tobiasraabe.github.io/blog/how-to-download-files-with-python.html)
- [Matthew Wimberly](https://codeburst.io/building-an-rss-feed-scraper-with-python-73715ca06e1f)