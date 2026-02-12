# Settings File Configuration

The settings file (`~/.toniepodcastsync/settings.toml`) uses TOML format and allows you to configure all aspects of your podcast syncing.

## File Location

- **Linux/macOS:** `~/.toniepodcastsync/settings.toml`
- **Windows:** `%USERPROFILE%\.toniepodcastsync\settings.toml`

## Basic Structure

```toml
[creative_tonies.<tonie-id>]
podcast = "https://example.com/podcast.xml"
name = "My Tonie Name"
```

## Configuration Options

### Required Fields

#### `podcast`
The RSS feed URL of the podcast.

```toml
podcast = "https://feeds.br.de/pumuckl/feed.xml"
```

#### `name`
A friendly name for your tonie (for reference only).

```toml
name = "Pumuckl Tonie"
```

### Optional Fields

#### `episode_sorting`
Controls the order in which episodes are placed on the tonie.

**Options:**
- `by_date_newest_first` (default) - Newest episodes first
- `by_date_oldest_first` - Oldest episodes first
- `random` - Random order

```toml
episode_sorting = "by_date_newest_first"
```

#### `maximum_length`
Maximum total duration of episodes on the tonie in minutes. Default is 90 minutes.

```toml
maximum_length = 60  # 60 minutes for bedtime stories
```

#### `episode_min_duration_sec`
Filter out episodes shorter than this duration in seconds.

```toml
episode_min_duration_sec = 30  # Skip episodes shorter than 30 seconds
```

#### `episode_max_duration_sec`
Filter out individual episodes longer than this duration in seconds.

```toml
episode_max_duration_sec = 5400  # Skip episodes longer than 90 minutes
```

!!! note "Difference from maximum_length"
    - `episode_max_duration_sec` filters out individual long episodes
    - `maximum_length` controls the total duration of all episodes placed on the tonie

#### `volume_adjustment`
Adjust audio volume in decibels (dB). Positive values increase volume, negative values decrease it.

!!! warning "Requires ffmpeg"
    This feature requires ffmpeg to be installed on your system.

```toml
volume_adjustment = -2  # Decrease by 2 dB
volume_adjustment = 3   # Increase by 3 dB
volume_adjustment = 0   # No adjustment (default)
```

#### `excluded_title_strings`
List of strings to filter out episodes by title (case-insensitive matching).

```toml
excluded_title_strings = ["vampir", "brokkoli", "gruselig"]
```

If an episode title contains any of these strings, it will be excluded from syncing.

#### `pinned_episode_names`
List of episode title strings to pin (prioritize) for uploading (case-insensitive matching, partial matches allowed).

```toml
pinned_episode_names = ["the golden goose", "hans in luck"]
```

Episodes matching these strings are prioritized and uploaded first, followed by remaining episodes sorted according to `episode_sorting`. Useful for keeping favorite episodes always available.

#### `wipe`
Controls whether existing content on the tonie should be cleared before syncing new episodes.

**Default:** `true` (existing content is removed before adding new episodes)

```toml
wipe = true   # Clear existing content before syncing (default)
wipe = false  # Append new episodes without removing existing content
```

When `wipe = false`, new episodes are appended to existing content on the tonie. This is useful for building a collection over time or combining multiple podcasts on one tonie.

!!! tip "Combining Multiple Podcasts"
    Use `wipe = false` to add episodes from multiple podcasts to a single tonie. Note: Each podcast still requires its own configuration section - to truly combine podcasts, use the [Python library](../usage/library.md) with `wipe=False`.

## Complete Example

```toml
[creative_tonies.12345678-1234-1234-1234-123456789abc]
podcast = "https://feeds.br.de/pumuckl/feed.xml"
name = "Green Tonie - Pumuckl"
episode_sorting = "by_date_newest_first"
maximum_length = 90

[creative_tonies.87654321-4321-4321-4321-cba987654321]
podcast = "https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast"
name = "Orange Tonie - Maus Bedtime"
episode_sorting = "random"
maximum_length = 60
volume_adjustment = -2
excluded_title_strings = ["vampir", "grusel"]
pinned_episode_names = ["die maus", "sterntaler"]

[creative_tonies.abcdef01-abcd-abcd-abcd-0123456789ef]
podcast = "https://feeds.br.de/checkpod-der-podcast-mit-checker-tobi/feed.xml"
name = "Blue Tonie - Checker Tobi"
episode_sorting = "random"
maximum_length = 45
episode_min_duration_sec = 30
episode_max_duration_sec = 3600
```

## Editing the Settings File

### Using the CLI Wizard

```bash
tonie-podcast-sync create-settings-file
```

This interactive wizard helps you create or update the settings file.

### Manual Editing

You can edit the file directly with any text editor:

```bash
# macOS
open ~/.toniepodcastsync/settings.toml

# Linux
nano ~/.toniepodcastsync/settings.toml
# or
vim ~/.toniepodcastsync/settings.toml

# Windows
notepad %USERPROFILE%\.toniepodcastsync\settings.toml
```

## Finding Tonie IDs

Use the list command to see your tonie IDs:

```bash
tonie-podcast-sync list-tonies
```

The IDs are displayed in the format: `12345678-1234-1234-1234-123456789abc`

## Validation

After editing the settings file, validate it by running:

```bash
tonie-podcast-sync update-tonies --dry-run
```

This shows what would be synced without actually performing the sync.

## Tips

!!! tip "Backup Your Settings"
    Keep a backup of your settings file, especially if you have complex configurations.

!!! tip "Multiple Podcasts Per Tonie"
    Currently, each tonie can only sync one podcast. To combine multiple podcasts, use the Python library with `wipe=False`.

!!! tip "Testing Changes"
    Use `--dry-run` when testing new settings to preview changes without syncing.
