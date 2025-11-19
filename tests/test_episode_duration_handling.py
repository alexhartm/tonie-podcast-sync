"""Test for missing or malformed duration handling in Episode class."""

from tonie_podcast_sync.podcast import Episode


def test_episode_missing_duration_should_default_to_zero():
    """
    Test that episodes without itunes_duration field don't crash.

    Bug: If an RSS feed doesn't include itunes_duration (which is optional in
    the RSS spec), Episode.__init__ raises KeyError and crashes the entire sync.

    Real RSS feeds in the wild may not always include duration information.
    The code should handle this gracefully with a sensible default.
    """
    test_feed_data = {
        "title": "Episode Without Duration",
        "published": "Mon, 01 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-no-duration",
        # itunes_duration is missing
    }

    # Should not raise exception, should default to 0
    ep = Episode(podcast="Test Podcast", raw=test_feed_data, url="http://example.com/test.mp3")

    assert ep.duration_sec == 0, "Missing duration should default to 0 seconds"
    assert ep.duration_str == "0", "Missing duration string should default to '0'"


def test_episode_empty_duration_should_default_to_zero():
    """Test that empty duration strings are handled gracefully."""
    test_feed_data = {
        "title": "Episode With Empty Duration",
        "published": "Mon, 01 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-empty-duration",
        "itunes_duration": "",  # Empty string
    }

    ep = Episode(podcast="Test Podcast", raw=test_feed_data, url="http://example.com/test.mp3")

    assert ep.duration_sec == 0, "Empty duration should default to 0 seconds"


def test_episode_malformed_duration_should_default_to_zero():
    """Test that malformed duration strings are handled gracefully."""
    test_feed_data = {
        "title": "Episode With Malformed Duration",
        "published": "Mon, 01 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-malformed",
        "itunes_duration": "invalid::time::format",
    }

    ep = Episode(podcast="Test Podcast", raw=test_feed_data, url="http://example.com/test.mp3")

    assert ep.duration_sec == 0, "Malformed duration should default to 0 seconds"


def test_episode_valid_duration_formats():
    """Test that valid duration formats are parsed correctly."""
    test_cases = [
        ("30", 30),  # Seconds only
        ("5:30", 330),  # Minutes:seconds
        ("1:05:30", 3930),  # Hours:minutes:seconds
    ]

    for duration_str, expected_seconds in test_cases:
        test_feed_data = {
            "title": f"Episode {duration_str}",
            "published": "Mon, 01 Jan 2024 10:00:00 +0000",
            "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
            "id": f"test-guid-{duration_str}",
            "itunes_duration": duration_str,
        }

        ep = Episode(podcast="Test Podcast", raw=test_feed_data, url="http://example.com/test.mp3")

        assert ep.duration_sec == expected_seconds, (
            f"Duration '{duration_str}' should parse to {expected_seconds} seconds, got {ep.duration_sec}"
        )


def test_episode_non_numeric_duration_should_default_to_zero():
    """Test that non-numeric duration values are handled gracefully."""
    test_feed_data = {
        "title": "Episode With Text Duration",
        "published": "Mon, 01 Jan 2024 10:00:00 +0000",
        "published_parsed": (2024, 1, 1, 10, 0, 0, 0, 1, 0),
        "id": "test-guid-text",
        "itunes_duration": "about 30 minutes",  # Text instead of numbers
    }

    ep = Episode(podcast="Test Podcast", raw=test_feed_data, url="http://example.com/test.mp3")

    assert ep.duration_sec == 0, "Non-numeric duration should default to 0 seconds"
