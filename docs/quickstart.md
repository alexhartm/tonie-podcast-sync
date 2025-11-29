# Quick Start Guide

This guide will help you get started with tonie-podcast-sync in just a few minutes.

## Step 1: Create Settings File

Run the interactive configuration wizard:

```bash
tonie-podcast-sync create-settings-file
```

The wizard will guide you through:

1. Entering your TonieCloud credentials
2. Selecting your creative tonies
3. Configuring podcast feeds for each tonie

!!! info "Configuration Location"
    Settings and optional secret files are stored in `~/.toniepodcastsync`

## Step 2: List Your Tonies

View an overview of your creative tonies:

```bash
tonie-podcast-sync list-tonies
```

This displays all your tonies with their IDs and current status.

## Step 3: Sync Podcasts

Fetch new episodes and sync them to your tonies:

```bash
tonie-podcast-sync update-tonies
```

This command will:

- Download new episodes from configured podcast feeds
- Upload them to the appropriate creative tonies
- Respect your configured limits (duration, episode count, etc.)

## Step 4: Trigger Sync on TonieBox

To make your TonieBox fetch the new content from TonieCloud:

1. Remove any tonie from the box
2. Press one ear for 3 seconds
3. Wait for the "ping" sound

Your tonie should now have the new podcast episodes!

## Modifying Settings

To change podcasts or adjust settings:

```bash
# Edit the settings file directly
open ~/.toniepodcastsync/settings.toml
```

Or re-run the configuration wizard:

```bash
tonie-podcast-sync create-settings-file
```

## Automation

For automatic podcast updates, you can schedule the sync command:

=== "Linux (systemd)"
    Create a systemd timer to run the sync periodically

=== "macOS (launchd)"
    Create a launchd job to run the sync periodically

=== "cron"
    ```bash
    # Run every day at 6 AM
    0 6 * * * /path/to/tonie-podcast-sync update-tonies
    ```

## Next Steps

- Learn more about [CLI commands](usage/cli.md)
- Explore [configuration options](configuration/settings.md)
- See [example configurations](configuration/examples.md)
- Use as a [Python library](usage/library.md)
