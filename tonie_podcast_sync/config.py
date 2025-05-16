"""The configuration module for the tonie_podcast_sync."""

from pathlib import Path

from dynaconf import Dynaconf

APP_NAME = "tonie-podcast-sync-cli"
APP_SETTINGS_DIR = Path.home() / ".toniepodcastsync"

settings = Dynaconf(
    envvar_prefix="TPS",
    root_path=str(APP_SETTINGS_DIR),
    settings_files=["settings.toml", ".secrets.toml"],
)

# `envvar_prefix` = export envvars with `export TPS_FOO=bar`.
# `settings_files` = Load these files in the order.
