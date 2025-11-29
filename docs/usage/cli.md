# CLI Guide

The command-line interface provides an easy way to manage your podcast syncing.

## Available Commands

### `create-settings-file`

Creates or updates the configuration file through an interactive wizard.

```bash
tonie-podcast-sync create-settings-file
```

This command guides you through:

- TonieCloud authentication
- Tonie selection
- Podcast feed configuration
- Episode sorting and filtering options

### `list-tonies`

Lists all your creative tonies with their IDs and status.

```bash
tonie-podcast-sync list-tonies
```

**Example output:**
```
╭─────────────────────────────────────────────╮
│ Your Creative Tonies                        │
├─────────────────┬───────────────────────────┤
│ Name            │ ID                        │
├─────────────────┼───────────────────────────┤
│ Green Tonie     │ 12345678-1234-1234-...    │
│ Orange Tonie    │ 87654321-4321-4321-...    │
│ Grey Tonie      │ ABCDEF01-ABCD-ABCD-...    │
╰─────────────────┴───────────────────────────╯
```

### `update-tonies`

Syncs podcast episodes to your configured tonies.

```bash
tonie-podcast-sync update-tonies
```

This command:

1. Fetches the latest episodes from your configured podcasts
2. Applies filters (duration, title exclusions, etc.)
3. Sorts episodes according to your settings
4. Uploads episodes to your tonies (respecting duration limits)

**Options:**

```bash
# Dry run - show what would be synced without actually syncing
tonie-podcast-sync update-tonies --dry-run

# Verbose output
tonie-podcast-sync update-tonies --verbose
```

### `--help`

Display help information for any command.

```bash
# General help
tonie-podcast-sync --help

# Command-specific help
tonie-podcast-sync update-tonies --help
```

## Global Options

```bash
--version          # Show version and exit
--config PATH      # Use custom config file location
--log-level LEVEL  # Set logging level (DEBUG, INFO, WARNING, ERROR)
```

## Common Workflows

### Initial Setup

```bash
# 1. Install
pip install tonie-podcast-sync

# 2. Configure
tonie-podcast-sync create-settings-file

# 3. Verify
tonie-podcast-sync list-tonies

# 4. Sync
tonie-podcast-sync update-tonies
```

### Regular Maintenance

```bash
# Check your tonies
tonie-podcast-sync list-tonies

# Update with new episodes
tonie-podcast-sync update-tonies

# Edit settings if needed
open ~/.toniepodcastsync/settings.toml
```

### Troubleshooting

```bash
# Enable debug logging
tonie-podcast-sync --log-level DEBUG update-tonies

# Validate configuration
tonie-podcast-sync create-settings-file

# Check version
tonie-podcast-sync --version
```

## Tips

!!! tip "Scheduling Updates"
    Use cron, systemd timers, or launchd to automatically run `update-tonies` daily or weekly.

!!! tip "Multiple Configurations"
    Use the `--config` option to maintain separate configurations for different scenarios.

!!! tip "Testing Changes"
    Always use `--dry-run` first when testing new configuration changes.
