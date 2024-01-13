# tonie-podcast-sync
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

tonie-podcast-sync allows synching podcast episodes to [creative tonies](https://tonies.com).

This is a purely private project and has no association with Boxine GmbH.

# Constraints and Limitations

- currently limited to podcasts providing mp3 files
- tested with the following podcasts:
    - WDR [Maus Podcasts](https://www.wdrmaus.de/hoeren/MausLive/Podcasts/podcasts.php5), e.g. 
        - [Gute Nacht mit der Maus](https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast)
        - [Maus zum Hören - 60 Minuten](https://kinder.wdr.de/radio/diemaus/audio/diemaus-60/diemaus-60-106.podcast)
        - [Maus Zoom - Kindernachrichten](https://kinder.wdr.de/radio/diemaus/audio/maus-zoom/maus-zoom-106.podcast)
    - [Bayern 2: Pumuckl - Der Hörspiel-Klassiker](https://www.br.de/mediathek/podcast/pumuckl/830)
    - [Checker Tobi Podcast](https://www.br.de/mediathek/podcast/checkpod-der-podcast-mit-checker-tobi/859)
    - [Anna und die wilden Tiere - der Podcast](https://www.br.de/mediathek/podcast/anna-und-die-wilden-tiere/858)
- ... but in general, it should hopefully work with all podcasts out there

# Usage

tonie-podcast-sync is available as [a pip package on pypi](https://pypi.org/project/tonie-podcast-sync). Install via

`pip install tonie-podcast-sync`

Then, use it as shown in the following example code:

```python
from toniepodcastsync import ToniePodcastSync, Podcast

# create two Podcast objects, providing the feed URL to each
pumuckl = Podcast("https://feeds.br.de/pumuckl/feed.xml")
maus = Podcast("https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast")

# create instance of ToniePodcastSync
tps = ToniePodcastSync("<toniecloud-username>", "<toniecloud-password>")

# for an overview of your creative tonies and their IDs
tps.print_tonies_overview()

# define creative tonies based on their ID
greenTonie = "<your-tonieID>"
orangeTonie = "<your-tonieID>"

# Fetch new podcast episodes and copy them to greenTonie.
# The tonie will be filled with as much episodes as fit (90 min max).
# Episode are ordered with newest first.
tps.sync_podcast_to_tonie(pumuckl, greenTonie)

# Kid's should fall asleep, so let's limit the podcast 
# episodes on this tonie to 60 minutes in total.
# Use the optional parameter for this:
tps.sync_podcast_to_tonie(maus, orangeTonie, 60)  
```

For the tonie to fetch new content from tonie-cloud, you have to press one ear for 3s (until the "ping" sound) with no tonie on the box (refer also to TonieBox manual).


# builds upon work of / kudos to
- moritj29's awesome [tonie_api](https://github.com/moritzj29/tonie_api)
- [Tobias Raabe](https://tobiasraabe.github.io/blog/how-to-download-files-with-python.html)
- [Matthew Wimberly](https://codeburst.io/building-an-rss-feed-scraper-with-python-73715ca06e1f)
## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/alexhartm"><img src="https://avatars.githubusercontent.com/u/16985220?v=4?s=100" width="100px;" alt="Alexander Hartmann"/><br /><sub><b>Alexander Hartmann</b></sub></a><br /><a href="https://github.com/alexhartm/tonie-podcast-sync/commits?author=alexhartm" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!