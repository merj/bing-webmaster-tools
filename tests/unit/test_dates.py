""".NET JSON dates as Bing sends them; the values are taken from recorded API responses."""

import time
from datetime import date, datetime, timedelta, timezone

import pytest

from bing_webmaster_tools.utils import format_date_for_api, parse_timestamp_from_api

pytestmark = pytest.mark.unit

PDT = timezone(timedelta(hours=-7))


@pytest.mark.parametrize(
    "raw, expected",
    [
        # GetCrawlStats: midnight Pacific with the offset (daylight time)
        ("/Date(1728975600000-0700)/", datetime(2024, 10, 15, tzinfo=PDT)),
        # midnight Pacific in standard time
        ("/Date(1731916800000-0800)/", datetime(2024, 11, 18, tzinfo=timezone(timedelta(hours=-8)))),
        # GetKeywordStats: the same instant with no offset, so it stays in UTC
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


def test_daily_values_land_on_the_pacific_day_whatever_the_machine_time_zone(monkeypatch):
    """The old parser used the machine's local zone, so west of UTC-7 every day shifted back by one."""
    if not hasattr(time, "tzset"):
        pytest.skip("time.tzset is not available on this platform")
    monkeypatch.setenv("TZ", "Pacific/Honolulu")
    time.tzset()
    try:
        assert parse_timestamp_from_api("/Date(1728975600000-0700)/").date() == date(2024, 10, 15)
    finally:
        monkeypatch.undo()
        time.tzset()


@pytest.mark.parametrize("raw", ["/Date(-62135596800000)/", "/Date(-62135596800000-0800)/"])
def test_net_min_value_means_never_and_parses_on_every_platform(raw):
    assert parse_timestamp_from_api(raw) == datetime(1, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize("raw", ["2024-10-15", "/Date(abc)/", 1728975600000])
def test_parse_rejects_other_formats(raw):
    with pytest.raises(ValueError):
        parse_timestamp_from_api(raw)


def test_format_round_trips_and_treats_naive_as_utc():
    aware = datetime(2024, 10, 15, tzinfo=PDT)
    assert format_date_for_api(aware) == "/Date(1728975600000+0000)/"
    assert parse_timestamp_from_api(format_date_for_api(aware)) == aware
    assert format_date_for_api(datetime(2024, 10, 15, 7)) == "/Date(1728975600000+0000)/"
