import datetime
import locale
from unittest import mock

import pytest
import responses
from tonie_api.models import Chapter, CreativeTonie, Household

from tonie_podcast_sync.podcast import Podcast
from tonie_podcast_sync.toniepodcastsync import ToniePodcastSync

locale.setlocale(locale.LC_TIME, "en_US.UTF-8")  # is only set for consistent tests

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


def _get_tonie_api_mock() -> mock.MagicMock:
    tonie_api_mock = mock.MagicMock()
    tonie_api_mock.get_households.return_value = [
        HOUSEHOLD,
    ]
    tonie_api_mock.get_all_creative_tonies.return_value = [TONIE_1, TONIE_2]
    return tonie_api_mock


@pytest.fixture
def mocked_tonie_api():
    with mock.patch("tonie_podcast_sync.toniepodcastsync.TonieAPI") as _mock:
        yield _mock


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        rsps._add_from_file("tests/res/responses.yaml")
        yield rsps


@pytest.fixture
def mocked_responses_assert_false():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps._add_from_file("tests/res/responses.yaml")
        yield rsps


def test_show_overview(mocked_tonie_api: mock.Mock, capfd: pytest.CaptureFixture):
    tonie_api_mock = _get_tonie_api_mock()
    mocked_tonie_api.return_value = tonie_api_mock
    tps = ToniePodcastSync("some user", "some_pass")
    tps.print_tonies_overview()
    mocked_tonie_api.assert_called_once_with("some user", "some_pass")
    tonie_api_mock.get_households.assert_called_once()
    captured = capfd.readouterr()
    assert "List of all creative tonies." in captured.out
    assert "ID" in captured.out
    assert "Name of Tonie" in captured.out
    assert "Time of last update" in captured.out
    assert "Household" in captured.out
    assert "Latest Episode name" in captured.out
    assert "42" in captured.out
    assert "Tonie #1" in captured.out
    assert "No latest chapter" in captured.out
    assert "73" in captured.out
    assert "Tonie #2" in captured.out
    assert "The great chapter" in captured.out
    assert "My House" in captured.out


@mock.patch("tonie_podcast_sync.toniepodcastsync.tempfile.TemporaryDirectory")
def test_upload_podcast(
    mock_tempdir, mocked_tonie_api: mock.Mock, mocked_responses_assert_false: responses.RequestsMock, tmp_path
):
    mock_tempdir.return_value.__enter__.return_value = str(tmp_path)
    tonie_api_mock = _get_tonie_api_mock()
    mocked_tonie_api.return_value = tonie_api_mock
    tps = ToniePodcastSync("some user", "some_pass")
    tps.sync_podcast_to_tonie(Podcast("tests/res/kakadu.xml"), "42")
    tonie_api_mock.upload_file_to_tonie.assert_any_call(
        TONIE_1,
        tmp_path
        / "Kakadu - Der Kinderpodcast"
        / "Mon, 14 Aug 2023 103524 +0200 Vom Gewinnen und Verlieren - Warum spielen wir so gern.mp3",
        "Vom Gewinnen und Verlieren - Warum spielen wir so gern? (Mon, 14 Aug 2023 10:35:24 +0200)",
    )


@mock.patch("tonie_podcast_sync.toniepodcastsync.tempfile.TemporaryDirectory")
def test_upload_podcast_with_title_filter(
    mock_tempdir, mocked_tonie_api: mock.Mock, mocked_responses_assert_false: responses.RequestsMock, tmp_path
):
    mock_tempdir.return_value.__enter__.return_value = str(tmp_path)
    tonie_api_mock = _get_tonie_api_mock()
    mocked_tonie_api.return_value = tonie_api_mock
    tps = ToniePodcastSync("some user", "some_pass")
    tps.sync_podcast_to_tonie(
        Podcast("tests/res/kakadu.xml", exclude_episode_titles=["Gewinnen"]),
        "42",
    )
    assert len(mocked_responses_assert_false.calls) == 3
    assert tonie_api_mock.upload_file_to_tonie.call_count == 3
