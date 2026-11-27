""".NET JSON dates as Bing sends them; the values are taken from recorded API responses."""

import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest

from bing_webmaster_tools.utils import format_date_for_api, parse_timestamp_from_api

pytestmark = pytest.mark.unit

PDT = timezone(timedelta(hours=-7))


@pytest.mark.parametrize(
    "raw, expected",
    [
        # GetRankAndTrafficStats and GetCrawlStats today: midnight UTC, no offset
        ("/Date(1795305600000)/", datetime(2026, 11, 22, tzinfo=timezone.utc)),
        # GetCrawlStats in 2024: midnight Pacific with the offset (daylight time)
        ("/Date(1728975600000-0700)/", datetime(2024, 10, 15, tzinfo=PDT)),
        # midnight Pacific in standard time
        ("/Date(1731916800000-0800)/", datetime(2024, 11, 18, tzinfo=timezone(timedelta(hours=-8)))),
        # GetKeywordStats: an instant with no offset stays in UTC
        ("/Date(1716015600000)/", datetime(2024, 5, 18, 7, tzinfo=timezone.utc)),
        ("/Date(1716015600000+0000)/", datetime(2024, 5, 18, 7, tzinfo=timezone.utc)),
        # a positive offset with minutes
        (
            "/Date(1730000000000+0530)/",
            datetime(2024, 10, 27, 9, 3, 20, tzinfo=timezone(timedelta(hours=5, minutes=30))),
        ),
    ],
)
def test_parse_keeps_the_offset_bing_sent(raw, expected):
    parsed = parse_timestamp_from_api(raw)
    assert parsed == expected
    assert parsed.utcoffset() == expected.utcoffset()


@pytest.mark.parametrize(
    "raw, day",
    [
        ("/Date(1795305600000)/", "2026-11-22"),  # midnight UTC, as Bing sends daily figures today
        ("/Date(1728975600000-0700)/", "2024-10-15"),  # midnight Pacific, as it used to
    ],
)
@pytest.mark.parametrize("machine_tz", ["UTC0", "PST8PDT", "HST10", "JST-9"])
def test_the_day_does_not_depend_on_the_machine_time_zone(raw, day, machine_tz):
    """The old parser converted to the machine's local time, so west of UTC every daily row moved back a day.

    Each case runs in a fresh interpreter with TZ set before it starts: Windows has no time.tzset().
    """
    code = f"from bing_webmaster_tools.utils import parse_timestamp_from_api as p; print(p({raw!r}).date())"
    result = subprocess.run(
        [sys.executable, "-c", code],
        env={**os.environ, "TZ": machine_tz},
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == day


@pytest.mark.parametrize("raw", ["/Date(-62135596800000)/", "/Date(-62135596800000-0800)/"])
def test_net_min_value_means_never_and_parses_on_every_platform(raw):
    assert parse_timestamp_from_api(raw) == datetime(1, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize("raw", ["2024-10-15", "/Date(abc)/", 1728975600000])
def test_parse_rejects_other_formats(raw):
    with pytest.raises(ValueError):
        parse_timestamp_from_api(raw)


def test_format_round_trips_an_aware_datetime():
    aware = datetime(2024, 10, 15, tzinfo=PDT)
    assert format_date_for_api(aware) == "/Date(1728975600000+0000)/"
    assert parse_timestamp_from_api(format_date_for_api(aware)) == aware


@pytest.mark.parametrize("machine_tz", ["UTC0", "PST8PDT", "HST10", "JST-9"])
def test_format_takes_a_naive_datetime_as_utc_whatever_the_machine_time_zone(machine_tz):
    """The old formatter read a naive datetime as the machine's local time, shifting it by the offset."""
    code = (
        "from datetime import datetime; from bing_webmaster_tools.utils import format_date_for_api as f; "
        "print(f(datetime(2024, 10, 15, 7)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env={**os.environ, "TZ": machine_tz},
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "/Date(1728975600000+0000)/"
