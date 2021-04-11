# tonie-podcast-sync

tonie-podcast-sync allows synching podcast episodes to [creative tonies](https://tonies.com)

This is a purely private project and has no association with Boxine GmbH.

# Prerequesites

- dependencies are installed
- if missing, you might also require `sudo apt-get install python-lxml` 
- [tonie_api](https://github.com/moritzj29/tonie_api) in `./../tonie_api`


# Usage

```python
from toniepodcastsync import ToniePodcastSync, Podcast

# create two Podcast objects, providing feed URL to each  
pumuckl = Podcast("https://feeds.br.de/pumuckl/feed.xml")
maus = Podcast("https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast")


# create instance of ToniePodcastSync
tps = ToniePodcastSync("<toniecloud-username>", "<toniecloud-password>")

# for an overview of your creative tonies and their IDs
tps.printToniesOverview()

# define creative tonies based on their ID
greenTonie = "<your-tonieID>"
orangeTonie = "<your-tonieID>"

# fetch new podcast episodes and copy them to greenTonie
tps.syncPodcast2Tonie(pumuckl, greenTonie)

# kid's should fall asleep, so podcast episodes on this
# tonie should be limited to 60 minutes in total.
# use the optional parameter for this:
tps.syncPodcast2Tonie(maus, orangeTonie, 60)  
```

For the tonie to fetch new content from tonie-cloud, you have to press one ear for 3s (until the "ping" sound) with no tonie on the box.

# Dependencies
- BeautifulSoup (bs4)
- wget
- requests
- requests-oauthlib

# builds upon work of
- moritj29's awesome [tonie_api](https://github.com/moritzj29/tonie_api)
- [Tobias Raabe](https://tobiasraabe.github.io/blog/how-to-download-files-with-python.html)
- [Matthew Wimberly](https://codeburst.io/building-an-rss-feed-scraper-with-python-73715ca06e1f)