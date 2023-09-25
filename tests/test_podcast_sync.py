import datetime
import locale
import platform
import textwrap
from pathlib import Path
from unittest import mock

import pytest
import responses
from tonie_api.models import Chapter, CreativeTonie, Household

from tonie_podcast_sync.podcast import Podcast
from tonie_podcast_sync.toniepodcastsync import ToniePodcastSync

locale.setlocale(locale.LC_TIME, "en_US")  # is only set for consistent tests

HOUSEHOLD = Household(id="1234", name="My House", ownerName="John", access="owner", canLeave=True)
CHAPTER_1 = Chapter(id="chap-1", title="The great chapter", file="123456789A", seconds=4711, transcoding=False)
CHAPTER_2 = Chapter(id="chap-2", title="The second chapter", file="223456789A", seconds=73, transcoding=False)

TONIE_1 = CreativeTonie(
    id="42",
    householdId="1234",
    name="Tonie #1",
    imageUrl="http://example.com/img.png",
    secondsRemaining=90 * 60,
    secondsPresent=0,
    chaptersPresent=0,
    chaptersRemaining=99,
    transcoding=False,
    lastUpdate=None,
    chapters=[],
)
TONIE_2 = CreativeTonie(
    id="73",
    householdId="1234",
    name="Tonie #2",
    imageUrl="http://example.com/img-1.png",
    secondsRemaining=90 * 60 - CHAPTER_1.seconds - CHAPTER_2.seconds,
    secondsPresent=CHAPTER_1.seconds + CHAPTER_2.seconds,
    chaptersPresent=2,
    chaptersRemaining=97,
    transcoding=False,
    lastUpdate=datetime.datetime(2016, 11, 25, 12, 00, tzinfo=datetime.timezone.utc),
    chapters=[CHAPTER_1, CHAPTER_2],
)

WINDOWS_RESULT = [
    "                         List of all creative tonies.                          ",
    "┌────┬───────────────┬──────────────────────┬───────────┬─────────────────────┐",
    "│ ID │ Name of Tonie │ Time of last update  │ Household │ Latest Episode name │",
    "├────┼───────────────┼──────────────────────┼───────────┼─────────────────────┤",
    "│ 42 │ Tonie #1      │                      │ My House  │ No latest chapter   │",
    "│    │               │                      │           │ available.          │",
    "│ 73 │ Tonie #2      │ 11/25/2016 12:00:00  │ My House  │ The great chapter   │",
    "│    │               │ PM                   │           │                     │",
    "└────┴───────────────┴──────────────────────┴───────────┴─────────────────────┘",
    "",
]

LINUX_RESULT = [
    "                          List of all creative tonies.                          ",
    "┏━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓",
    "┃ ID ┃ Name of Tonie ┃ Time of last update  ┃ Household ┃ Latest Episode name  ┃",
    "┡━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩",
    "│ 42 │ Tonie #1      │                      │ My House  │ No latest chapter    │",
    "│    │               │                      │           │ available.           │",
    "│ 73 │ Tonie #2      │ 11/25/2016 12:00:00  │ My House  │ The great chapter    │",
    "│    │               │ PM                   │           │                      │",
    "└────┴───────────────┴──────────────────────┴───────────┴──────────────────────┘",
    "",
]


def _get_tonie_api_mock() -> mock.MagicMock:
    tonie_api_mock = mock.MagicMock()
    tonie_api_mock.get_households.return_value = [
        HOUSEHOLD,
    ]
    tonie_api_mock.get_all_creative_tonies.return_value = [TONIE_1, TONIE_2]
    return tonie_api_mock


@pytest.fixture()
def mocked_tonie_api():
    with mock.patch("tonie_podcast_sync.toniepodcastsync.TonieAPI") as _mock:
        yield _mock


@pytest.fixture()
def mocked_responses():
    with responses.RequestsMock() as rsps:
        rsps._add_from_file("tests/res/responses.yaml")
        yield rsps


@pytest.fixture()
def overview_result():
    result = []
    match platform.system():
        case "Windows":
            result = WINDOWS_RESULT
        case "Linux":
            result = LINUX_RESULT
        case _unknown:
            raise NotImplementedError(_unknown)
    return textwrap.dedent("\n".join(result))


def test_show_overview(mocked_tonie_api: mock.Mock, capfd: pytest.CaptureFixture, overview_result):
    tonie_api_mock = _get_tonie_api_mock()
    mocked_tonie_api.return_value = tonie_api_mock
    tps = ToniePodcastSync("some user", "some_pass")
    tps.print_tonies_overview()
    mocked_tonie_api.assert_called_once_with("some user", "some_pass")
    tonie_api_mock.get_households.assert_called_once()
    captured = capfd.readouterr()
    assert captured.out == overview_result


def test_upload_podcast(mocked_tonie_api: mock.Mock, mocked_responses: responses.RequestsMock):
    tonie_api_mock = _get_tonie_api_mock()
    mocked_tonie_api.return_value = tonie_api_mock
    tps = ToniePodcastSync("some user", "some_pass")
    tps.sync_podcast_to_tonie(Podcast("tests/res/kakadu.xml"), "42")
    assert mocked_responses.assert_all_requests_are_fired
    tonie_api_mock.upload_file_to_tonie.assert_any_call(
        TONIE_1,
        Path("podcasts")
        / "Kakadu - Der Kinderpodcast"
        / "mon-14-aug-2023-10-35-24-0200_vom-gewinnen-und-verlieren-warum-spielen-wir-so-gern.mp3",
        "Vom Gewinnen und Verlieren - Warum spielen wir so gern? (Mon, 14 Aug 2023 10:35:24 +0200)",
    )
