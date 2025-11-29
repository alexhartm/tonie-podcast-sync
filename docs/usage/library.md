# Python Library Usage

You can use tonie-podcast-sync as a Python library in your own scripts for more programmatic control.

## Basic Example

```python
from tonie_podcast_sync.toniepodcastsync import ToniePodcastSync, Podcast, EpisodeSorting

# Create Podcast objects with feed URLs
pumuckl = Podcast("https://feeds.br.de/pumuckl/feed.xml")

# Initialize ToniePodcastSync with credentials
tps = ToniePodcastSync("<toniecloud-username>", "<toniecloud-password>")

# Get overview of your creative tonies and their IDs
tps.print_tonies_overview()

# Define tonie ID
greenTonie = "<your-tonie-id>"

# Sync podcast to tonie (fills up to 90 minutes by default)
tps.sync_podcast_to_tonie(pumuckl, greenTonie)
```

## Episode Sorting

Control the order in which episodes are placed on tonies:

```python
from tonie_podcast_sync.toniepodcastsync import Podcast, EpisodeSorting

# Newest episodes first (default)
podcast_newest = Podcast(
    "https://example.com/feed.xml",
    episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST
)

# Oldest episodes first
podcast_oldest = Podcast(
    "https://example.com/feed.xml",
    episode_sorting=EpisodeSorting.BY_DATE_OLDEST_FIRST
)

# Random order
podcast_random = Podcast(
    "https://example.com/feed.xml",
    episode_sorting=EpisodeSorting.RANDOM
)
```

## Duration Limits

Limit the total duration of episodes on a tonie:

```python
# Limit to 60 minutes for bedtime stories
tps.sync_podcast_to_tonie(bedtime_podcast, orangeTonie, maximum_length=60)

# Limit to 30 minutes
tps.sync_podcast_to_tonie(short_podcast, greyTonie, maximum_length=30)

# Use default (90 minutes)
tps.sync_podcast_to_tonie(standard_podcast, blueTonie)
```

## Volume Adjustment

Adjust podcast volume (requires ffmpeg):

```python
# Decrease volume by 2 dB
quiet_podcast = Podcast(
    "https://example.com/feed.xml",
    volume_adjustment=-2
)

# Increase volume by 3 dB
loud_podcast = Podcast(
    "https://example.com/feed.xml",
    volume_adjustment=3
)
```

## Episode Filtering

### Minimum Duration

Filter out very short episodes:

```python
# Skip episodes shorter than 30 seconds
checker_tobi = Podcast(
    "https://feeds.br.de/checkpod-der-podcast-mit-checker-tobi/feed.xml",
    episode_min_duration_sec=30
)
```

### Maximum Episode Duration

Filter out episodes that exceed a certain duration:

```python
# Skip individual episodes longer than 90 minutes (5400 seconds)
podcast = Podcast(
    "https://example.com/feed.xml",
    episode_max_duration_sec=5400
)
```

### Title Exclusions

Filter out episodes by title keywords:

```python
# Exclude episodes with certain words in the title
maus_filtered = Podcast(
    "https://kinder.wdr.de/radio/diemaus/audio/maus-gute-nacht/maus-gute-nacht-148.podcast",
    excluded_title_strings=["vampir", "brokkoli"]  # Case-insensitive
)
```

## Additive Syncing

By default, syncing replaces all content on a tonie. Use `wipe=False` to add episodes without removing existing content:

```python
# Replace all content (default behavior)
tps.sync_podcast_to_tonie(podcast1, greyTonie, 30)

# Add episodes without removing existing content
tps.sync_podcast_to_tonie(podcast2, greyTonie, 30, wipe=False)
```

## Complete Example

```python
from tonie_podcast_sync.toniepodcastsync import ToniePodcastSync, Podcast, EpisodeSorting

# Define podcasts with various configurations
pumuckl = Podcast("https://feeds.br.de/pumuckl/feed.xml")

maus_60min = Podcast(
    "https://kinder.wdr.de/radio/diemaus/audio/diemaus-60/diemaus-60-106.podcast",
    episode_sorting=EpisodeSorting.BY_DATE_NEWEST_FIRST
)

maus_gute_nacht = Podcast(
    "https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast",
    episode_sorting=EpisodeSorting.RANDOM
)

anna_und_die_wilden_tiere = Podcast(
    "https://feeds.br.de/anna-und-die-wilden-tiere/feed.xml",
    episode_sorting=EpisodeSorting.RANDOM,
    volume_adjustment=-2
)

checker_tobi = Podcast(
    "https://feeds.br.de/checkpod-der-podcast-mit-checker-tobi/feed.xml",
    episode_sorting=EpisodeSorting.RANDOM,
    episode_min_duration_sec=30
)

maus_filtered = Podcast(
    "https://kinder.wdr.de/radio/diemaus/audio/maus-gute-nacht/maus-gute-nacht-148.podcast",
    excluded_title_strings=["vampir", "brokkoli"]
)

# Initialize and authenticate
tps = ToniePodcastSync("<toniecloud-username>", "<toniecloud-password>")

# Print overview
tps.print_tonies_overview()

# Define tonie IDs
greenTonie = "<your-tonieID>"
orangeTonie = "<your-tonieID>"
greyTonie = "<your-tonieID>"

# Sync podcasts to tonies
tps.sync_podcast_to_tonie(pumuckl, greenTonie)
tps.sync_podcast_to_tonie(maus_gute_nacht, orangeTonie, 60)
tps.sync_podcast_to_tonie(checker_tobi, greyTonie, 30)
tps.sync_podcast_to_tonie(anna_und_die_wilden_tiere, greyTonie, 30, wipe=False)
```

## API Reference

### ToniePodcastSync

```python
ToniePodcastSync(username: str, password: str)
```

Main class for interacting with TonieCloud.

**Methods:**

- `print_tonies_overview()` - Print all creative tonies with their IDs
- `sync_podcast_to_tonie(podcast, tonie_id, maximum_length=90, wipe=True)` - Sync a podcast to a tonie

### Podcast

```python
Podcast(
    feed_url: str,
    episode_sorting: EpisodeSorting = EpisodeSorting.BY_DATE_NEWEST_FIRST,
    volume_adjustment: int = 0,
    episode_min_duration_sec: int = 0,
    episode_max_duration_sec: int = None,
    excluded_title_strings: List[str] = None
)
```

Represents a podcast feed with configuration options.

### EpisodeSorting

Enum for episode sorting options:

- `BY_DATE_NEWEST_FIRST` - Newest episodes first (default)
- `BY_DATE_OLDEST_FIRST` - Oldest episodes first
- `RANDOM` - Random order
