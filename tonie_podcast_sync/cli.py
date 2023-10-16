"""The command line interface module for the tonie-podcast-sync."""
from pathlib import Path

import tomli_w
from dynaconf.vendor.box.exceptions import BoxError
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from typer import Typer

from tonie_podcast_sync.config import APP_SETTINGS_DIR, settings
from tonie_podcast_sync.podcast import Podcast
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
        tps.sync_podcast_to_tonie(Podcast(ct_value.podcast), ct_key, ct_value.maximum_length)


@app.command()
def create_settings_file() -> None:
    """Create a settings file in your user home."""
    user_name = Prompt.ask("Enter your Tonie CloudAPI username")
    password = Prompt.ask("Enter your password for Tonie CloudAPI", password=True)
    save_login = Confirm.ask("Do you want to save your login data in a .secrets.toml file")

    if save_login:
        APP_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        with Path(APP_SETTINGS_DIR / ".secrets.toml").open("wb") as _fs:
            tomli_w.dump({"tonie_cloud_access": {"username": user_name, "password": password}}, _fs)

    tps = ToniePodcastSync(user=user_name, pwd=password)

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
                    "The value you have entered is out of range."
                    f"Will be set to default value of {MAXIMUM_TONIE_MINUTES}.",
                )
                data[tonie.id]["maximum_length"] = MAXIMUM_TONIE_MINUTES

    with Path(APP_SETTINGS_DIR / "settings.toml").open("wb") as _fs:
        tomli_w.dump({"creative_tonies": data}, _fs)


if __name__ == "__main__":
    app()
