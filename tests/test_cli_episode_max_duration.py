"""Test for episode_max_duration_sec default value bug in CLI."""

from unittest import mock


def test_episode_max_duration_defaults_to_5399_not_maximum_length():
    """
    Test that episode_max_duration_sec defaults to MAXIMUM_TONIE_MINUTES * 60 (5400 seconds),
    NOT to maximum_length * 60.

    Bug: When episode_max_duration_sec is not in config, it was incorrectly defaulting
    to maximum_length * 60, which is wrong. It should default to MAXIMUM_TONIE_MINUTES * 60.

    Example: If maximum_length=30 (30 min total for tonie), the buggy code
    set episode_max_duration_sec=1800 (30 min), filtering out individual episodes
    longer than 30 minutes. This is incorrect - episodes up to 90 minutes should
    be allowed, and maximum_length only controls the total duration on the tonie.
    """
    # Create mock settings
    mock_settings = mock.MagicMock()
    mock_settings.TONIE_CLOUD_ACCESS.USERNAME = "test_user"
    mock_settings.TONIE_CLOUD_ACCESS.PASSWORD = "test_pass"

    # Configure a tonie with maximum_length=30 minutes but no episode_max_duration_sec
    mock_tonie_config = mock.MagicMock()
    mock_tonie_config.podcast = "https://example.com/feed.xml"
    mock_tonie_config.episode_sorting = "by_date_newest_first"
    mock_tonie_config.volume_adjustment = 0
    mock_tonie_config.episode_min_duration_sec = 0
    mock_tonie_config.maximum_length = 30  # 30 minutes total

    # Simulate that episode_max_duration_sec is not set in config
    mock_tonie_config.get = mock.MagicMock(
        side_effect=lambda key, default=None: {
            "excluded_title_strings": [],
            "episode_max_duration_sec": default,  # Will return the default value
        }.get(key, default)
    )

    mock_settings.CREATIVE_TONIES = {"test-tonie-id": mock_tonie_config}

    # Mock the dependencies
    with (
        mock.patch("tonie_podcast_sync.cli.settings", mock_settings),
        mock.patch("tonie_podcast_sync.cli.ToniePodcastSync") as mock_tps_class,
        mock.patch("tonie_podcast_sync.cli.Podcast") as mock_podcast_class,
    ):
        # Mock ToniePodcastSync instance
        mock_tps_instance = mock.MagicMock()
        mock_tps_class.return_value = mock_tps_instance

        # Mock Podcast class to capture initialization arguments
        mock_podcast_instance = mock.MagicMock()
        mock_podcast_class.return_value = mock_podcast_instance

        # Import and run the update_tonies function
        from tonie_podcast_sync.cli import update_tonies  # noqa: PLC0415

        update_tonies()

        # Verify ToniePodcastSync was instantiated
        mock_tps_class.assert_called_once_with("test_user", "test_pass")

        # Verify Podcast was created with correct arguments
        mock_podcast_class.assert_called_once()
        call_args = mock_podcast_class.call_args

        # Extract the episode_max_duration_sec argument
        episode_max_duration_sec = call_args.kwargs.get("episode_max_duration_sec")

        # The fix: Now this should be 5400 (90 * 60), not 1800 (maximum_length * 60)
        assert episode_max_duration_sec == 5400, (
            f"episode_max_duration_sec should default to 5400 (MAXIMUM_TONIE_MINUTES * 60), "
            f"not {episode_max_duration_sec} (maximum_length * 60). "
            f"Individual episode duration limit should be independent of "
            f"total tonie duration limit."
        )


def test_episode_max_duration_respects_explicit_value():
    """
    Test that when episode_max_duration_sec IS explicitly set in config,
    that value is used (not the default).
    """
    # Create mock settings
    mock_settings = mock.MagicMock()
    mock_settings.TONIE_CLOUD_ACCESS.USERNAME = "test_user"
    mock_settings.TONIE_CLOUD_ACCESS.PASSWORD = "test_pass"

    # Configure a tonie with explicit episode_max_duration_sec
    mock_tonie_config = mock.MagicMock()
    mock_tonie_config.podcast = "https://example.com/feed.xml"
    mock_tonie_config.episode_sorting = "by_date_newest_first"
    mock_tonie_config.volume_adjustment = 0
    mock_tonie_config.episode_min_duration_sec = 0
    mock_tonie_config.maximum_length = 30  # 30 minutes total

    # Set explicit value
    explicit_max_duration = 3600  # 60 minutes
    mock_tonie_config.get = mock.MagicMock(
        side_effect=lambda key, default=None: {
            "excluded_title_strings": [],
            "episode_max_duration_sec": explicit_max_duration,
        }.get(key, default)
    )

    mock_settings.CREATIVE_TONIES = {"test-tonie-id": mock_tonie_config}

    # Mock the dependencies
    with (
        mock.patch("tonie_podcast_sync.cli.settings", mock_settings),
        mock.patch("tonie_podcast_sync.cli.ToniePodcastSync") as mock_tps_class,
        mock.patch("tonie_podcast_sync.cli.Podcast") as mock_podcast_class,
    ):
        # Mock ToniePodcastSync instance
        mock_tps_instance = mock.MagicMock()
        mock_tps_class.return_value = mock_tps_instance

        # Mock Podcast class
        mock_podcast_instance = mock.MagicMock()
        mock_podcast_class.return_value = mock_podcast_instance

        # Import and run the update_tonies function
        from tonie_podcast_sync.cli import update_tonies  # noqa: PLC0415

        update_tonies()

        # Verify Podcast was created with the explicit value
        call_args = mock_podcast_class.call_args
        episode_max_duration_sec = call_args.kwargs.get("episode_max_duration_sec")

        assert episode_max_duration_sec == explicit_max_duration, (
            f"episode_max_duration_sec should use the explicit config value {explicit_max_duration}, "
            f"but got {episode_max_duration_sec}"
        )
