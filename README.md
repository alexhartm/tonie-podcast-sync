# tonie-podcast-sync

tonie-podcast-sync allows synching podcast episodes to [creative tonies](https://tonies.com).

This is a purely private project and has no association with Boxine GmbH.

# Prerequesites

- dependencies are installed (see list below)
- [tonie_api](https://github.com/moritzj29/tonie_api) in `./../tonie_api`
    - needs to provide a method to remove content from tonies (`remove_all_chapters`) You can use [this fork](https://github.com/alexhartm/tonie_api) in case the method is [not yet](https://github.com/moritzj29/tonie_api/pull/3) available in the original project.

# Constraints and Limitations

- currently limited to podcasts providing mp3 files
- tested with the following podcasts:
    - [WDR: Gute Nacht mit der Maus](https://www.wdrmaus.de/hoeren/gute_nacht_mit_der_maus.php5)
    - [Bayern 2: Pumuckl - Der Hörspiel-Klassiker](https://www.br.de/mediathek/podcast/pumuckl/830)


# Usage

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

# Dependencies
- tonie_api
- [wget](https://pypi.org/project/wget/)
- [requests](https://pypi.org/project/requests/)
- [requests-oauthlib](https://pypi.org/project/requests-oauthlib/)
- [BeautifulSoup (bs4)](https://pypi.org/project/beautifulsoup4/)
- [config-with-yaml](https://pypi.org/project/config-with-yaml/)
- if missing on your system, you might also require `sudo apt-get install python3-lxml`. Otherwise, parsing of episodes will fail.


# builds upon work of / kudos to
- moritj29's awesome [tonie_api](https://github.com/moritzj29/tonie_api)
- [Tobias Raabe](https://tobiasraabe.github.io/blog/how-to-download-files-with-python.html)
- [Matthew Wimberly](https://codeburst.io/building-an-rss-feed-scraper-with-python-73715ca06e1f)