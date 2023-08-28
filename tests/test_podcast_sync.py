from unittest import mock

import pytest

from toniepodcastsync import ToniePodcastSync


@pytest.fixture()
def mocked_tonie_api():
    with mock.patch("toniepodcastsync.TonieAPI") as _mock:
        yield _mock


def test_show_overview(mocked_tonie_api: mock.Mock):
    tps = ToniePodcastSync("some user", "some_pass")
    tps.print_tonies_overview()
    mocked_tonie_api.assert_called_once_with("some user", "some_pass")
