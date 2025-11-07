"""The command line interface module for the tonie-podcast-sync."""

from pathlib import Path

import tomli_w
from dynaconf.vendor.box.exceptions import BoxError
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from tonie_api.models import CreativeTonie
from typer import Typer

from tonie_podcast_sync.config import APP_SETTINGS_DIR, settings
from tonie_podcast_sync.podcast import EpisodeSorting, Podcast
from tonie_podcast_sync.toniepodcastsync import MAXIMUM_TONIE_MINUTES, ToniePodcastSync

app = Typer(pretty_exceptions_show_locals=False)


@app.command()
def update_tonies() -> None:
    """Update the tonies by using the settings file."""
    try:
        tps = ToniePodcastSync(settings.TONIE_CLOUD_ACCESS.USERNAME, settings.TONIE_CLOUD_ACCESS.PASSWORD)
    except BoxError:
        Console().print(
            "There was an error getting the username or password. Please create the settings file or setting the",
            "environment variables. TPS_TONIE_CLOUD_ACCESS_USERNAME and TPS_TONIE_CLOUD_ACCESS_PASSWORD.",
        )
        return
    for ct_key, ct_value in settings.CREATIVE_TONIES.items():
        tps.sync_podcast_to_tonie(
            Podcast(
                ct_value.podcast,
                episode_sorting=ct_value.episode_sorting,
                volume_adjustment=ct_value.volume_adjustment,
                episode_min_duration_sec=ct_value.episode_min_duration_sec,
            ),
            ct_key,
            ct_value.maximum_length,
        )


@app.command()
def list_tonies() -> None:
    """Prints an overview of all creative-tonies."""
    try:
        tps = ToniePodcastSync(settings.TONIE_CLOUD_ACCESS.USERNAME, settings.TONIE_CLOUD_ACCESS.PASSWORD)
        tps.print_tonies_overview()
    except BoxError:
        Console().print(
            "Could not find credentials. Please run 'tonie-podcast-sync create-settings-file' first.",
        )
        return


@app.command()
def create_settings_file() -> None:
    """Create a settings file in your user home."""
    keep_secrets = False
    if Path(APP_SETTINGS_DIR / ".secrets.toml").exists():
        keep_secrets = Confirm.ask("You already have secrets set, do you want to keep them?")

    if not keep_secrets:
        user_name = Prompt.ask("Enter your Tonie CloudAPI username")
        password = Prompt.ask("Enter your password for Tonie CloudAPI", password=True)
        save_login = Confirm.ask("Do you want to save your login data in a .secrets.toml file")

        if save_login:
            APP_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            with Path(APP_SETTINGS_DIR / ".secrets.toml").open("wb") as _fs:
                tomli_w.dump({"tonie_cloud_access": {"username": user_name, "password": password}}, _fs)
    else:
        user_name, password = settings.TONIE_CLOUD_ACCESS.USERNAME, settings.TONIE_CLOUD_ACCESS.PASSWORD
    try:
        tps = ToniePodcastSync(user=user_name, pwd=password)
    except KeyError:
        Console().print("It seems like you are not able to login, please provide different login data.")
        return
    tonies = tps.get_tonies()
    data = {}

    for tonie in tonies:
        podcast = Prompt.ask(
            f"Which podcast do you want to set for Tonie {tonie.name} with ID {tonie.id}?\n"
            "Please enter the URL to the podcast, or leave empty if you don't want to set it.",
        )
        if podcast:
            data[tonie.id] = {"podcast": podcast, "name": tonie.name}
        else:
            continue
        _ask_episode_order(data, tonie)
        _ask_maximum_tonie_length(data, tonie)
        _ask_minimum_episode_length(data, tonie)
        _ask_volume_adjustment(data, tonie)

    with Path(APP_SETTINGS_DIR / "settings.toml").open("wb") as _fs:
        tomli_w.dump({"creative_tonies": data}, _fs)


def _ask_episode_order(data: dict, tonie: CreativeTonie) -> None:
    episode_order_input = Prompt.ask(
        "How would you like your podcast episodes sorted?",
        choices=list(EpisodeSorting),
        default=EpisodeSorting.BY_DATE_NEWEST_FIRST,
    )
    data[tonie.id]["episode_sorting"] = episode_order_input


def _ask_maximum_tonie_length(data: dict, tonie: CreativeTonie) -> None:
    maximum_length_input = IntPrompt.ask(
        "What should be the maximum length of the podcast?\n"
        f"Defaults to the maximum of {MAXIMUM_TONIE_MINUTES} minutes.",
        default=90,
    )
    match maximum_length_input:
        case None:
            data[tonie.id]["maximum_length"] = MAXIMUM_TONIE_MINUTES
        case maximum_length if 0 < maximum_length <= MAXIMUM_TONIE_MINUTES:
            data[tonie.id]["maximum_length"] = maximum_length_input
        case maximum_length if maximum_length <= 0 or maximum_length > MAXIMUM_TONIE_MINUTES:
            Console().print(
                f"The value you have entered is out of range.Will be set to default value of {MAXIMUM_TONIE_MINUTES}.",
            )
            data[tonie.id]["maximum_length"] = MAXIMUM_TONIE_MINUTES


def _ask_minimum_episode_length(data: dict, tonie: CreativeTonie) -> None:
    minimum_length_input = IntPrompt.ask(
        "What should be the minimum length (in sec) of the podcast?\n"
        "Defaults to the minimum of 0 seconds.\n"
        "Podcasts shorter than the input, will not be uploaded.",
        default=0,
    )
    match minimum_length_input:
        case None:
            data[tonie.id]["episode_min_duration_sec"] = 0
        case x if x < 0:
            Console().print("The value you have set, is less than 0 and will be set to 0.")
            data[tonie.id]["episode_min_duration_sec"] = 0
        case x if x > 60 * data[tonie.id]["maximum_length"]:
            Console().print(
                "The value you have set, is less more than the maximum available length for the tonie."
                "It will be set to the maximum, but probably no Episode will be downloaded.",
            )
            data[tonie.id]["episode_min_duration_sec"] = 60 * data[tonie.id]["maximum_length"]
        case _:
            data[tonie.id]["episode_min_duration_sec"] = minimum_length_input


def _ask_volume_adjustment(data: dict, tonie: CreativeTonie) -> None:
    volume_adjustment_input = IntPrompt.ask(
        "Would you like to adjust the volume of the Episodes?\n"
        "If set, the downloaded audio will be adjusted by the given amount in dB.\n"
        "Defaults to 0, i.e. no adjustment",
        default=0,
    )
    match volume_adjustment_input:
        case None:
            data[tonie.id]["volume_adjustment"] = 0
        case x if x < 0:
            Console().print("The value you have set, is less than 0 and will be set to 0.")
            data[tonie.id]["volume_adjustment"] = 0
        case _:
            data[tonie.id]["volume_adjustment"] = volume_adjustment_input


if __name__ == "__main__":
    app()
