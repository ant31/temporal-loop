from datetime import timedelta

import pytest

from temporalloop.utils import time_interval


@pytest.mark.parametrize(
    "time_str, expected",
    [
        ("1h", timedelta(hours=1)),
        ("30m", timedelta(minutes=30)),
        ("15s", timedelta(seconds=15)),
        ("1h30m", timedelta(hours=1, minutes=30)),
        ("1h15s", timedelta(hours=1, seconds=15)),
        ("30m15s", timedelta(minutes=30, seconds=15)),
        ("1h30m15s", timedelta(hours=1, minutes=30, seconds=15)),
    ],
)
def test_time_interval(time_str: str, expected: timedelta):
    """Test valid time interval strings."""
    assert time_interval(time_str) == expected


def test_time_interval_invalid():
    """Test invalid time interval string."""
    with pytest.raises(ValueError, match="Invalid time string invalid"):
        time_interval("invalid")
