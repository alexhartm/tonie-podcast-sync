# Configuration Examples

This page provides real-world configuration examples for common use cases.

## Bedtime Stories

Limit duration and reduce volume for better sleep:

```toml
[creative_tonies.12345678-1234-1234-1234-123456789abc]
podcast = "https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast"
name = "Orange Tonie - Bedtime Stories"
episode_sorting = "random"
maximum_length = 45  # Shorter for bedtime
volume_adjustment = -3  # Quieter for sleep
excluded_title_strings = ["aufregend", "spannend", "gruselig"]  # Filter exciting content
```

## Kids' Educational Content

Keep episodes fresh with newest-first sorting and filter out very short announcements:

```toml
[creative_tonies.87654321-4321-4321-4321-cba987654321]
podcast = "https://feeds.br.de/checkpod-der-podcast-mit-checker-tobi/feed.xml"
name = "Blue Tonie - Checker Tobi"
episode_sorting = "by_date_newest_first"
maximum_length = 90
episode_min_duration_sec = 60  # Skip short announcements
```

## Long Road Trips

Maximum content with older episodes first to work through a series:

```toml
[creative_tonies.abcdef01-abcd-abcd-abcd-0123456789ef]
podcast = "https://feeds.br.de/pumuckl/feed.xml"
name = "Green Tonie - Pumuckl Complete Series"
episode_sorting = "by_date_oldest_first"
maximum_length = 90  # Fill to maximum
```

## Variety Pack

Random episodes for variety, with age-appropriate filtering:

```toml
[creative_tonies.11111111-1111-1111-1111-111111111111]
podcast = "https://kinder.wdr.de/radio/diemaus/audio/diemaus-60/diemaus-60-106.podcast"
name = "Grey Tonie - Maus Random Mix"
episode_sorting = "random"
maximum_length = 90
excluded_title_strings = ["vampir", "zombies", "monster"]  # Age-appropriate filtering
episode_max_duration_sec = 3600  # Skip episodes longer than 1 hour
```

## Quiet Podcast

Some podcasts are recorded too quietly and need volume boost:

```toml
[creative_tonies.22222222-2222-2222-2222-222222222222]
podcast = "https://feeds.br.de/anna-und-die-wilden-tiere/feed.xml"
name = "Red Tonie - Anna und die wilden Tiere"
episode_sorting = "random"
maximum_length = 90
volume_adjustment = 4  # Boost quiet podcast
```

## Multiple Tonies Setup

Complete configuration for multiple tonies with different purposes:

```toml
# Bedtime tonie - calm and short
[creative_tonies.12345678-1234-1234-1234-123456789abc]
podcast = "https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast"
name = "Orange Tonie - Bedtime"
episode_sorting = "random"
maximum_length = 45
volume_adjustment = -2
excluded_title_strings = ["spannend", "aufregend"]

# Learning tonie - newest content
[creative_tonies.87654321-4321-4321-4321-cba987654321]
podcast = "https://feeds.br.de/checkpod-der-podcast-mit-checker-tobi/feed.xml"
name = "Blue Tonie - Learning"
episode_sorting = "by_date_newest_first"
maximum_length = 90
episode_min_duration_sec = 60

# Entertainment tonie - maximum content
[creative_tonies.abcdef01-abcd-abcd-abcd-0123456789ef]
podcast = "https://feeds.br.de/pumuckl/feed.xml"
name = "Green Tonie - Entertainment"
episode_sorting = "by_date_oldest_first"
maximum_length = 90

# Variety tonie - random selection
[creative_tonies.11111111-1111-1111-1111-111111111111]
podcast = "https://kinder.wdr.de/radio/diemaus/audio/diemaus-60/diemaus-60-106.podcast"
name = "Grey Tonie - Variety"
episode_sorting = "random"
maximum_length = 75
episode_max_duration_sec = 2400
```

## Python Library Equivalent

Some complex scenarios are easier with the Python library. Here's a bedtime tonie with multiple podcasts:

```python
from tonie_podcast_sync.toniepodcastsync import ToniePodcastSync, Podcast, EpisodeSorting

# Define multiple podcasts for bedtime
maus_bedtime = Podcast(
    "https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast",
    episode_sorting=EpisodeSorting.RANDOM,
    volume_adjustment=-2
)

sleep_stories = Podcast(
    "https://example.com/sleep-stories.xml",
    episode_sorting=EpisodeSorting.RANDOM,
    volume_adjustment=-3
)

tps = ToniePodcastSync("username", "password")
tonie_id = "12345678-1234-1234-1234-123456789abc"

# Add 30 minutes of each podcast
tps.sync_podcast_to_tonie(maus_bedtime, tonie_id, maximum_length=30)
tps.sync_podcast_to_tonie(sleep_stories, tonie_id, maximum_length=30, wipe=False)
```

## Tips for Common Scenarios

### Filtering Scary Content

```toml
excluded_title_strings = [
    "vampir", "zombie", "monster", "geist", "gruselig",
    "dunkel", "friedhof", "hexe", "spuk"
]
```

### German Children's Podcasts

Popular German children's podcast feeds:

- **Pumuckl:** `https://feeds.br.de/pumuckl/feed.xml`
- **Die Maus (60min):** `https://kinder.wdr.de/radio/diemaus/audio/diemaus-60/diemaus-60-106.podcast`
- **Gute Nacht mit der Maus:** `https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast`
- **Checker Tobi:** `https://feeds.br.de/checkpod-der-podcast-mit-checker-tobi/feed.xml`
- **Anna und die wilden Tiere:** `https://feeds.br.de/anna-und-die-wilden-tiere/feed.xml`

### Volume Adjustment Guidelines

- **-3 to -5 dB:** Bedtime stories (quieter)
- **-2 to 0 dB:** Normal listening
- **+2 to +4 dB:** Quiet podcasts that need boosting
- **+5 to +8 dB:** Very quiet podcasts (use carefully to avoid distortion)

!!! warning "Audio Quality"
    Extreme volume adjustments (> ±8 dB) may cause audio distortion. Test with small adjustments first.
