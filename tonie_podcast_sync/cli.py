"""The command line interface module for the tonie-podcast-sync."""

import warnings

import tomli_w
from dynaconf.vendor.box.exceptions import BoxError
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from tonie_api.models import CreativeTonie
from typer import Typer

from tonie_podcast_sync.config import APP_SETTINGS_DIR, settings
from tonie_podcast_sync.constants import MAXIMUM_TONIE_MINUTES
from tonie_podcast_sync.podcast import EpisodeSorting, Podcast
from tonie_podcast_sync.toniepodcastsync import ToniePodcastSync

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pydub")

app = Typer(pretty_exceptions_show_locals=False)
_console = Console()


@app.command()
def update_tonies() -> None:
    """Update the tonies by using the settings file."""
    tps = _create_tonie_podcast_sync()
    if not tps:
        return

    for tonie_id, tonie_config in settings.CREATIVE_TONIES.items():
        podcast = _create_podcast_from_config(tonie_config)
        tps.sync_podcast_to_tonie(podcast, tonie_id, tonie_config.maximum_length)


def _create_tonie_podcast_sync() -> ToniePodcastSync | None:
    """Create ToniePodcastSync instance from settings.

    Returns:
        ToniePodcastSync instance if successful, None otherwise
    """
    try:
        return ToniePodcastSync(settings.TONIE_CLOUD_ACCESS.USERNAME, settings.TONIE_CLOUD_ACCESS.PASSWORD)
    except BoxError:
        _console.print(
            "There was an error getting the username or password. Please create the settings file or set the "
            "environment variables TPS_TONIE_CLOUD_ACCESS_USERNAME and TPS_TONIE_CLOUD_ACCESS_PASSWORD.",
        )
        return None


def _create_podcast_from_config(config: dict) -> Podcast:
    """Create a Podcast instance from configuration.

    Args:
        config: The configuration dictionary for a Tonie

    Returns:
        Configured Podcast instance
    """
    excluded_title_strings = config.get("excluded_title_strings", [])
    included_title_strings = config.get("included_title_strings", [])
    episode_max_duration_sec = config.get("episode_max_duration_sec", MAXIMUM_TONIE_MINUTES * 60)

    return Podcast(
        config.podcast,
        episode_sorting=config.episode_sorting,
        volume_adjustment=config.volume_adjustment,
        episode_min_duration_sec=config.episode_min_duration_sec,
        episode_max_duration_sec=episode_max_duration_sec,
        excluded_title_strings=excluded_title_strings,
        included_title_strings=included_title_strings,
    )


@app.command()
def list_tonies() -> None:
    """Print an overview of all creative-tonies."""
    tps = _create_tonie_podcast_sync()
    if tps:
        tps.print_tonies_overview()
    else:
        _console.print("Could not find credentials. Please run 'tonie-podcast-sync create-settings-file' first.")


@app.command()
def create_settings_file() -> None:
    """Create a settings file in your user home."""
    username, password = _get_credentials()

    tps = _validate_and_create_tps(username, password)
    if not tps:
        return

    tonies = tps.get_tonies()
    tonie_configs = _configure_tonies(tonies)

    _save_settings_file(tonie_configs)


def _get_credentials() -> tuple[str, str]:
    """Get user credentials from existing secrets or prompt user.

    Returns:
        Tuple of (username, password)
    """
    secrets_file = APP_SETTINGS_DIR / ".secrets.toml"

    if secrets_file.exists() and Confirm.ask("You already have secrets set, do you want to keep them?"):
        return settings.TONIE_CLOUD_ACCESS.USERNAME, settings.TONIE_CLOUD_ACCESS.PASSWORD

    username = Prompt.ask("Enter your Tonie CloudAPI username")
    password = Prompt.ask("Enter your password for Tonie CloudAPI", password=True)

    if Confirm.ask("Do you want to save your login data in a .secrets.toml file"):
        _save_credentials(username, password)

    return username, password


def _save_credentials(username: str, password: str) -> None:
    """Save user credentials to secrets file.

    Args:
        username: The Tonie Cloud username
        password: The Tonie Cloud password
    """
    APP_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    secrets_file = APP_SETTINGS_DIR / ".secrets.toml"

    with secrets_file.open("wb") as file:
        tomli_w.dump({"tonie_cloud_access": {"username": username, "password": password}}, file)


def _validate_and_create_tps(username: str, password: str) -> ToniePodcastSync | None:
    """Validate credentials and create ToniePodcastSync instance.

    Args:
        username: The Tonie Cloud username
        password: The Tonie Cloud password

    Returns:
        ToniePodcastSync instance if successful, None otherwise
    """
    try:
        return ToniePodcastSync(user=username, pwd=password)
    except KeyError:
        _console.print("It seems like you are not able to login, please provide different login data.")
        return None


def _configure_tonies(tonies: list[CreativeTonie]) -> dict:
    """Interactively configure podcasts for tonies.

    Args:
        tonies: List of available creative tonies

    Returns:
        Dictionary of tonie configurations
    """
    configs = {}

    for tonie in tonies:
        podcast_url = Prompt.ask(
            f"Which podcast do you want to set for Tonie {tonie.name} with ID {tonie.id}?\n"
            "Please enter the URL to the podcast, or leave empty if you don't want to set it.",
        )

        if not podcast_url:
            continue

        configs[tonie.id] = {"podcast": podcast_url, "name": tonie.name}
        _configure_tonie_settings(configs, tonie)

    return configs


def _configure_tonie_settings(configs: dict, tonie: CreativeTonie) -> None:
    """Configure settings for a specific tonie.

    Args:
        configs: The configuration dictionary to update
        tonie: The tonie to configure
    """
    _ask_episode_order(configs, tonie)
    _ask_maximum_tonie_length(configs, tonie)
    _ask_minimum_episode_length(configs, tonie)
    _ask_volume_adjustment(configs, tonie)


def _save_settings_file(configs: dict) -> None:
    """Save tonie configurations to settings file.

    Args:
        configs: Dictionary of tonie configurations
    """
    settings_file = APP_SETTINGS_DIR / "settings.toml"

    with settings_file.open("wb") as file:
        tomli_w.dump({"creative_tonies": configs}, file)


def _ask_episode_order(configs: dict, tonie: CreativeTonie) -> None:
    """Ask user for episode sorting preference.

    Args:
        configs: The configuration dictionary to update
        tonie: The tonie being configured
    """
    episode_order = Prompt.ask(
        "How would you like your podcast episodes sorted?",
        choices=list(EpisodeSorting),
        default=EpisodeSorting.BY_DATE_NEWEST_FIRST,
    )
    configs[tonie.id]["episode_sorting"] = episode_order


def _ask_maximum_tonie_length(configs: dict, tonie: CreativeTonie) -> None:
    """Ask user for maximum tonie length.

    Args:
        configs: The configuration dictionary to update
        tonie: The tonie being configured
    """
    max_length = IntPrompt.ask(
        "What should be the maximum total duration of all episodes on this tonie?\n"
        f"Defaults to {MAXIMUM_TONIE_MINUTES} minutes (the tonie's maximum).\n"
        "Only episodes up to these many minutes in total will be uploaded.\n",
        default=90,
    )

    if max_length is None or max_length <= 0 or max_length > MAXIMUM_TONIE_MINUTES:
        if max_length is not None:
            _console.print(
                f"The value you have entered is out of range. Will be set to default value of {MAXIMUM_TONIE_MINUTES}.",
            )
        configs[tonie.id]["maximum_length"] = MAXIMUM_TONIE_MINUTES
    else:
        configs[tonie.id]["maximum_length"] = max_length


def _ask_minimum_episode_length(configs: dict, tonie: CreativeTonie) -> None:
    """Ask user for minimum episode length.

    Args:
        configs: The configuration dictionary to update
        tonie: The tonie being configured
    """
    min_length = IntPrompt.ask(
        "What should be the minimum length (in sec) of each episode?\n"
        "Defaults to the minimum of 0 seconds, ie. no minimum length considered.\n"
        "Podcast episodes shorter than this value will not be uploaded.",
        default=0,
    )

    if min_length is None or min_length < 0:
        if min_length is not None and min_length < 0:
            _console.print("The value you have set is less than 0 and will be set to 0.")
        configs[tonie.id]["episode_min_duration_sec"] = 0
    elif min_length > 60 * configs[tonie.id]["maximum_length"]:
        _console.print(
            "The value you have set conflicts with the configured maximum available length for the tonie. "
            "It will be set to the maximum, but this might result in no episode being downloaded.",
        )
        configs[tonie.id]["episode_min_duration_sec"] = 60 * configs[tonie.id]["maximum_length"]
    else:
        configs[tonie.id]["episode_min_duration_sec"] = min_length


def _ask_volume_adjustment(configs: dict, tonie: CreativeTonie) -> None:
    """Ask user for volume adjustment setting.

    Args:
        configs: The configuration dictionary to update
        tonie: The tonie being configured
    """
    volume_adjustment = IntPrompt.ask(
        "Would you like to adjust the volume of the Episodes?\n"
        "If set, the downloaded audio will be adjusted by the given amount in dB.\n"
        "Defaults to 0, i.e. no adjustment",
        default=0,
    )

    if volume_adjustment is None or volume_adjustment < 0:
        if volume_adjustment is not None and volume_adjustment < 0:
            _console.print("The value you have set is less than 0 and will be set to 0.")
        configs[tonie.id]["volume_adjustment"] = 0
    else:
        configs[tonie.id]["volume_adjustment"] = volume_adjustment


if __name__ == "__main__":
    app()
