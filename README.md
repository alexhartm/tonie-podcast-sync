# tonie-podcast-sync

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
from toniepodcastsync import ToniePodcastSync, Podcast, EpisodeSorting

# create some Podcast objects, providing the feed URL to each
pumuckl = Podcast("https://feeds.br.de/pumuckl/feed.xml")
maus = Podcast("https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast")
# by default, podcasts are placed onto tonies by newest episode first
# (EpisodeSorting.BY_DATE_NEWEST_FIRST).
# it is also possible to sort BY_DATE_OLDEST_FIRST or getting RANDOM episodes:
checker_tobi = Podcast("https://feeds.br.de/checkpod-der-podcast-mit-checker-tobi/feed.xml", EpisodeSorting.RANDOM)

# create instance of ToniePodcastSync
tps = ToniePodcastSync("<toniecloud-username>", "<toniecloud-password>")

# for an overview of your creative tonies and their IDs
# the IDs are needed to address specific tonies in the next step
tps.print_tonies_overview()

# define creative tonies based on their ID
greenTonie = "<your-tonieID>"
orangeTonie = "<your-tonieID>"

# Fetch new podcast episodes and copy them to greenTonie.
# The tonie will be filled with as much episodes as fit (90 min max).
tps.sync_podcast_to_tonie(pumuckl, greenTonie)

# Kid's should fall asleep, so let's limit the podcast
# episodes on this tonie to 60 minutes in total.
# Use the optional parameter for this:
tps.sync_podcast_to_tonie(maus, orangeTonie, 60)
```

For the tonie to fetch new content from tonie-cloud, you have to press one ear for 3s (until the "ping" sound) with no tonie on the box (refer also to TonieBox manual).

# Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/alexhartm"><img src="https://avatars.githubusercontent.com/u/16985220?v=4?s=100" width="100px;" alt="Alexander Hartmann"/><br /><sub><b>Alexander Hartmann</b></sub></a><br /><a href="#code-alexhartm" title="Code">💻</a> <a href="#ideas-alexhartm" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-alexhartm" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Wilhelmsson177"><img src="https://avatars.githubusercontent.com/u/16141053?v=4?s=100" width="100px;" alt="Wilhelmsson177"/><br /><sub><b>Wilhelmsson177</b></sub></a><br /><a href="#code-Wilhelmsson177" title="Code">💻</a> <a href="#ideas-Wilhelmsson177" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-Wilhelmsson177" title="Maintenance">🚧</a> <a href="#test-Wilhelmsson177" title="Tests">⚠️</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://cv.maltebaer.vercel.app/"><img src="https://avatars.githubusercontent.com/u/29504917?v=4?s=100" width="100px;" alt="Malte Bär"/><br /><sub><b>Malte Bär</b></sub></a><br /><a href="#bug-maltebaer" title="Bug reports">🐛</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

> Use the [all-contributors github bot](https://allcontributors.org/docs/en/bot/usage) to add contributors here.

## builds upon work of / kudos to
- moritj29's awesome [tonie_api](https://github.com/moritzj29/tonie_api)
- [Tobias Raabe](https://tobiasraabe.github.io/blog/how-to-download-files-with-python.html)
- [Matthew Wimberly](https://codeburst.io/building-an-rss-feed-scraper-with-python-73715ca06e1f)
