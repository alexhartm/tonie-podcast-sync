"""Tests for the wipe setting in settings.toml."""

from unittest import mock


def test_wipe_parameter_defaults_to_true_when_omitted():
    """Test that wipe defaults to True when not specified in config.

    This verifies that:
    1. The code calls tonie_config.get("wipe", True)
    2. When "wipe" is not in the config, the default True is used
    3. The value is passed to sync_podcast_to_tonie
    """
    # Create mock settings
    mock_settings = mock.MagicMock()
    mock_settings.TONIE_CLOUD_ACCESS.USERNAME = "test_user"
    mock_settings.TONIE_CLOUD_ACCESS.PASSWORD = "test_pass"

    # Configure a tonie config - use a real dict to simulate dynaconf Box behavior
    # The config does NOT have a "wipe" key
    mock_tonie_config = mock.MagicMock()
    mock_tonie_config.podcast = "https://example.com/feed.xml"
    mock_tonie_config.episode_sorting = "by_date_newest_first"
    mock_tonie_config.volume_adjustment = 0
    mock_tonie_config.episode_min_duration_sec = 0
    mock_tonie_config.maximum_length = 90

    # Create a mock for .get() that tracks calls
    mock_get = mock.MagicMock(side_effect=lambda key, default=None: {
        "excluded_title_strings": [],
        "pinned_episode_names": [],
        "episode_max_duration_sec": 5400,
    }.get(key, default))
    mock_tonie_config.get = mock_get

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

        # VERIFY: The code called .get("wipe", True) on the config
        mock_get.assert_any_call("wipe", True)

        # VERIFY: sync_podcast_to_tonie was called with wipe=True (the default)
        mock_tps_instance.sync_podcast_to_tonie.assert_called_once()
        call_kwargs = mock_tps_instance.sync_podcast_to_tonie.call_args.kwargs
        assert call_kwargs["wipe"] is True, "wipe should default to True when not specified in config"


def test_wipe_parameter_respects_false_value():
    """Test that wipe=False is passed through correctly.

    This verifies that:
    1. The code calls tonie_config.get("wipe", True)
    2. When "wipe" is False in the config, that value is retrieved
    3. The False value is passed to sync_podcast_to_tonie
    """
    # Create mock settings
    mock_settings = mock.MagicMock()
    mock_settings.TONIE_CLOUD_ACCESS.USERNAME = "test_user"
    mock_settings.TONIE_CLOUD_ACCESS.PASSWORD = "test_pass"

    # Configure a tonie config with wipe=False
    mock_tonie_config = mock.MagicMock()
    mock_tonie_config.podcast = "https://example.com/feed.xml"
    mock_tonie_config.episode_sorting = "by_date_newest_first"
    mock_tonie_config.volume_adjustment = 0
    mock_tonie_config.episode_min_duration_sec = 0
    mock_tonie_config.maximum_length = 90

    # Set wipe=False explicitly in the config
    mock_get = mock.MagicMock(side_effect=lambda key, default=None: {
        "excluded_title_strings": [],
        "pinned_episode_names": [],
        "episode_max_duration_sec": 5400,
        "wipe": False,  # Explicit False value in config
    }.get(key, default))
    mock_tonie_config.get = mock_get

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

        # VERIFY: The code called .get("wipe", True) on the config
        mock_get.assert_any_call("wipe", True)

        # VERIFY: sync_podcast_to_tonie was called with wipe=False (from config)
        mock_tps_instance.sync_podcast_to_tonie.assert_called_once()
        call_kwargs = mock_tps_instance.sync_podcast_to_tonie.call_args.kwargs
        assert call_kwargs["wipe"] is False, "wipe should be False when explicitly set to False in config"


def test_wipe_parameter_respects_true_value():
    """Test that wipe=True is passed through correctly when explicitly set.

    This verifies that:
    1. The code calls tonie_config.get("wipe", True)
    2. When "wipe" is True in the config, that value is retrieved
    3. The True value is passed to sync_podcast_to_tonie
    """
    # Create mock settings
    mock_settings = mock.MagicMock()
    mock_settings.TONIE_CLOUD_ACCESS.USERNAME = "test_user"
    mock_settings.TONIE_CLOUD_ACCESS.PASSWORD = "test_pass"

    # Configure a tonie config with wipe=True explicitly
    mock_tonie_config = mock.MagicMock()
    mock_tonie_config.podcast = "https://example.com/feed.xml"
    mock_tonie_config.episode_sorting = "by_date_newest_first"
    mock_tonie_config.volume_adjustment = 0
    mock_tonie_config.episode_min_duration_sec = 0
    mock_tonie_config.maximum_length = 90

    # Set wipe=True explicitly in the config
    mock_get = mock.MagicMock(side_effect=lambda key, default=None: {
        "excluded_title_strings": [],
        "pinned_episode_names": [],
        "episode_max_duration_sec": 5400,
        "wipe": True,  # Explicit True value in config
    }.get(key, default))
    mock_tonie_config.get = mock_get

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

        # VERIFY: The code called .get("wipe", True) on the config
        mock_get.assert_any_call("wipe", True)

        # VERIFY: sync_podcast_to_tonie was called with wipe=True (from config)
        mock_tps_instance.sync_podcast_to_tonie.assert_called_once()
        call_kwargs = mock_tps_instance.sync_podcast_to_tonie.call_args.kwargs
        assert call_kwargs["wipe"] is True, "wipe should be True when explicitly set to True in config"
