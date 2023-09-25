"""The command line interface module for the tonie-podcast-sync."""
from pathlib import Path

import tomli_w
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from typer import Typer

from tonie_podcast_sync.toniepodcastsync import MAXIMUM_TONIE_MINUTES, ToniePodcastSync

app = Typer()


@app.command()
def create_settings_file() -> None:
    """Create a settings file in your user home."""
    user_name = Prompt.ask("Enter your Tonie CloudAPI username")
    password = Prompt.ask("Enter your password for Tonie CloudAPI", password=True)
    save_login = Confirm.ask("Do you want to save your login data in a .secrets.toml file")

    if save_login:
        settings_dir = Path.home() / ".toniepodcastsync"
        settings_dir.mkdir(parents=True, exist_ok=True)
        with Path(settings_dir / ".secrets.toml").open("wb") as _fs:
            tomli_w.dump({"tonie-cloud-access": {"username": user_name, "password": password}}, _fs)

    tps = ToniePodcastSync(user=user_name, pwd=password)

    tonies = tps.get_tonies()
    data = {}

    for tonie in tonies:
        podcast = Prompt.ask(
            f"Which podcast do you want to set for Tonie {tonie.name} with ID {tonie.id}? "
            "Please enter the URL to the podcast, or leave empty if you don't want to set it.",
        )
        if podcast:
            data[tonie.id] = {"podcast": podcast}
        else:
            continue

        maximum_length_input = IntPrompt.ask(
            "What should be the maximum length of the podcast?"
            f"Defaults to the maximum of {MAXIMUM_TONIE_MINUTES} minutes.",
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

    with Path(Path.home() / ".toniepodcastsync" / "settings.toml").open("wb") as _fs:
        tomli_w.dump(data, _fs)
