"""Tests for the TPS_SOFT_WRAP environment variable setting and container detection."""

import importlib
import os
from io import StringIO
from unittest import mock

import tonie_podcast_sync.toniepodcastsync as tps_module
from tonie_podcast_sync.container_detection import _check_cgroup_v1, _check_cgroup_v2


class TestSoftWrapSetting:
    """Tests for the soft wrap console setting controlled by TPS_SOFT_WRAP env var."""

    def test_soft_wrap_is_true_when_env_var_set_to_true(self):
        """Test that soft_wrap is True when TPS_SOFT_WRAP=true."""
        with mock.patch.dict(os.environ, {"TPS_SOFT_WRAP": "true"}):
            importlib.reload(tps_module)

            assert tps_module.console.soft_wrap is True

    def test_soft_wrap_is_false_when_env_var_set_to_false(self):
        """Test that soft_wrap is False when TPS_SOFT_WRAP=false."""
        with mock.patch.dict(os.environ, {"TPS_SOFT_WRAP": "false"}):
            importlib.reload(tps_module)

            assert tps_module.console.soft_wrap is False

    def test_soft_wrap_is_false_case_insensitive(self):
        """Test that soft_wrap is False when TPS_SOFT_WRAP=FALSE (uppercase)."""
        with mock.patch.dict(os.environ, {"TPS_SOFT_WRAP": "FALSE"}):
            importlib.reload(tps_module)

            assert tps_module.console.soft_wrap is False

    def test_soft_wrap_is_true_for_any_other_value(self):
        """Test that soft_wrap is True for any non-false value."""
        with mock.patch.dict(os.environ, {"TPS_SOFT_WRAP": "yes"}):
            importlib.reload(tps_module)

            assert tps_module.console.soft_wrap is True


class TestContainerAutoDetection:
    """Tests for container auto-detection and its interaction with soft wrap."""

    def test_cgroup_v1_detects_docker(self):
        """Test cgroup v1 detection with docker in cgroup file."""
        cgroup_content = "12:hugetlb:/docker/abc123"
        with mock.patch("pathlib.Path.open", mock.mock_open(read_data=cgroup_content)):
            assert _check_cgroup_v1() is True

    def test_cgroup_v1_detects_podman(self):
        """Test cgroup v1 detection with podman in cgroup file."""
        cgroup_content = "12:hugetlb:/user.slice/user-1000.slice/user@1000.service/user.slice/podman-123"
        with mock.patch("pathlib.Path.open", mock.mock_open(read_data=cgroup_content)):
            assert _check_cgroup_v1() is True

    def test_cgroup_v1_no_container(self):
        """Test cgroup v1 returns False for host system."""
        cgroup_content = "12:hugetlb:/user.slice"
        with mock.patch("pathlib.Path.open", mock.mock_open(read_data=cgroup_content)):
            assert _check_cgroup_v1() is False

    def test_cgroup_v1_file_error(self):
        """Test cgroup v1 returns False on file error."""
        with mock.patch("pathlib.Path.open", side_effect=PermissionError()):
            assert _check_cgroup_v1() is False

    def test_cgroup_v2_detects_container(self):
        """Test cgroup v2 detection with minimal cgroup entry."""
        # Mock the self cgroup check
        mock_file = StringIO("0::/\n")
        with mock.patch("pathlib.Path.open", return_value=mock_file):
            assert _check_cgroup_v2() is True

    def test_cgroup_v2_no_container(self):
        """Test cgroup v2 returns False for host system with systemd."""
        # First call reads /proc/self/cgroup (not minimal)
        # Second call reads /proc/1/cgroup (has systemd)
        calls = [
            StringIO(
                "0::/user.slice/user-1000.slice/user@1000.service/app.slice/app-org.gnome.Terminal.slice/vte-spawn-xyz.scope"
            ),
            StringIO("0::/init.scope"),
        ]

        def side_effect(*_args, **_kwargs):
            return calls.pop(0)

        with mock.patch("pathlib.Path.open", side_effect=side_effect):
            assert _check_cgroup_v2() is False

    def test_cgroup_v2_file_error(self):
        """Test cgroup v2 returns False on file error."""
        with mock.patch("pathlib.Path.open", side_effect=PermissionError()):
            assert _check_cgroup_v2() is False

    def test_env_var_overrides_container_detection(self):
        """Test that TPS_SOFT_WRAP env var takes precedence over auto-detection."""
        # Mock container detection to return True (in container)
        with (
            mock.patch.dict(os.environ, {"TPS_SOFT_WRAP": "true"}),
            mock.patch("tonie_podcast_sync.toniepodcastsync.is_running_in_container", return_value=True),
        ):
            importlib.reload(tps_module)
            # Even though in container, env var forces soft_wrap=True
            assert tps_module.console.soft_wrap is True

    def test_env_var_override_false_in_container(self):
        """Test TPS_SOFT_WRAP=false overrides even when not in container."""
        with (
            mock.patch.dict(os.environ, {"TPS_SOFT_WRAP": "false"}),
            mock.patch("tonie_podcast_sync.toniepodcastsync.is_running_in_container", return_value=False),
        ):
            importlib.reload(tps_module)
            # Even though not in container, env var forces soft_wrap=False
            assert tps_module.console.soft_wrap is False

    def test_auto_detect_disables_soft_wrap_in_container(self):
        """Test soft_wrap is disabled when in container and no env var set."""
        env_without_soft_wrap = {k: v for k, v in os.environ.items() if k != "TPS_SOFT_WRAP"}
        with (
            mock.patch.dict(os.environ, env_without_soft_wrap, clear=True),
            mock.patch("tonie_podcast_sync.container_detection._check_cgroup_v1", return_value=True),
            mock.patch("tonie_podcast_sync.container_detection._check_cgroup_v2", return_value=False),
        ):
            importlib.reload(tps_module)
            # In container without env var -> soft_wrap=False
            assert tps_module.console.soft_wrap is False

    def test_auto_detect_enables_soft_wrap_on_host(self):
        """Test soft_wrap is enabled on host and no env var set."""
        env_without_soft_wrap = {k: v for k, v in os.environ.items() if k != "TPS_SOFT_WRAP"}
        with (
            mock.patch.dict(os.environ, env_without_soft_wrap, clear=True),
            mock.patch("tonie_podcast_sync.container_detection._check_cgroup_v1", return_value=False),
            mock.patch("tonie_podcast_sync.container_detection._check_cgroup_v2", return_value=False),
        ):
            importlib.reload(tps_module)
            # On host without env var -> soft_wrap=True
            assert tps_module.console.soft_wrap is True
