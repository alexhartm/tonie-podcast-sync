# Installation

## Prerequisites

Before installing tonie-podcast-sync, ensure you have:

- **Python** >= 3.10.11
- **ffmpeg** (optional, required only if using the `volume_adjustment` feature)

### Installing ffmpeg

=== "macOS"
    ```bash
    brew install ffmpeg
    ```

=== "Ubuntu/Debian"
    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```

=== "Windows"
    Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

## Install via pip

The easiest way to install tonie-podcast-sync is via pip:

```bash
pip install tonie-podcast-sync
```

This will install the package and make the `tonie-podcast-sync` command available in your terminal.

## Verify Installation

To verify the installation was successful:

```bash
tonie-podcast-sync --help
```

You should see the help output with available commands.

## Update to Latest Version

To update to the latest version:

```bash
pip install --upgrade tonie-podcast-sync
```

## Next Steps

Once installed, proceed to the [Quick Start Guide](quickstart.md) to set up your configuration.
