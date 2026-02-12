"""Container environment detection utilities.

This module provides functionality to detect if the code is running inside a
container environment (Docker, Podman, Kubernetes, LXC, etc.).

Note: This is an isolated feature that can be removed if needed by:
1. Deleting this file
2. Removing the import from toniepodcastsync.py
3. Updating _get_soft_wrap_setting() to not use is_running_in_container()
"""

from pathlib import Path


def is_running_in_container() -> bool:
    """Detect if running inside a container.

    Checks both cgroup v1 and v2 formats. Returns False if unable to determine.

    Returns:
        True if running in a container, False otherwise or if detection fails.
    """
    return _check_cgroup_v1() or _check_cgroup_v2()


def _check_cgroup_v1() -> bool:
    """Check cgroup v1 format for container indicators.

    In cgroup v1, container runtimes typically include their name in the
    cgroup paths (e.g., /docker/, /podman/, /kubepods/).
    """
    try:
        with Path("/proc/1/cgroup").open(encoding="utf-8") as f:
            content = f.read()
            indicators = ["docker", "containerd", "kubepods", "lxc", "podman"]
            return any(indicator in content for indicator in indicators)
    except OSError:
        return False


def _check_cgroup_v2() -> bool:
    """Check cgroup v2 format for container indicators.

    In cgroup v2, the format is different. Container detection is done by:
    1. Checking if cgroup contains just "0::/" (typical container pattern)
    2. Verifying init process is not systemd/init.scope (host indicator)
    """
    try:
        # First check current process cgroup
        with Path("/proc/self/cgroup").open(encoding="utf-8") as f:
            lines = f.readlines()
            # In some containers, cgroup shows minimal "0::/" entry
            if len(lines) == 1 and lines[0].strip() == "0::/":
                return True

        # Check init process cgroup for host indicators
        with Path("/proc/1/cgroup").open(encoding="utf-8") as f:
            init_content = f.read()
            # Host systems typically have systemd or init.scope
            host_indicators = ["init.scope", "systemd"]
            is_host_init = any(indicator in init_content for indicator in host_indicators)
            return not is_host_init

    except OSError:
        return False
