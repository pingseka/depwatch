"""Tests for depwatch.package_age."""

from datetime import datetime, timezone, timedelta

import pytest

from depwatch.package_age import PackageAgeInfo, package_age_info


FIXED_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _release(days_ago: int) -> datetime:
    return FIXED_NOW - timedelta(days=days_ago)


# ---------------------------------------------------------------------------
# PackageAgeInfo dataclass
# ---------------------------------------------------------------------------

def test_package_age_info_fields():
    info = PackageAgeInfo(
        name="requests",
        version="2.28.0",
        release_date=_release(400),
        age_days=400,
        is_stale=True,
    )
    assert info.name == "requests"
    assert info.version == "2.28.0"
    assert info.age_days == 400
    assert info.is_stale is True


# ---------------------------------------------------------------------------
# package_age_info logic (no network)
# ---------------------------------------------------------------------------

def test_stale_when_old_enough():
    info = package_age_info(
        "requests", "2.28.0",
        stale_days=365,
        _now=FIXED_NOW,
        _release_date=_release(400),
    )
    assert info.is_stale is True
    assert info.age_days == 400


def test_not_stale_when_recent():
    info = package_age_info(
        "requests", "2.31.0",
        stale_days=365,
        _now=FIXED_NOW,
        _release_date=_release(100),
    )
    assert info.is_stale is False
    assert info.age_days == 100


def test_exactly_on_boundary_is_stale():
    info = package_age_info(
        "flask", "3.0.0",
        stale_days=180,
        _now=FIXED_NOW,
        _release_date=_release(180),
    )
    assert info.is_stale is True


def test_one_day_before_boundary_is_not_stale():
    info = package_age_info(
        "flask", "3.0.0",
        stale_days=180,
        _now=FIXED_NOW,
        _release_date=_release(179),
    )
    assert info.is_stale is False


def test_unknown_release_date_not_stale():
    info = package_age_info(
        "unknown-pkg", "0.1.0",
        stale_days=365,
        _now=FIXED_NOW,
        _release_date=None,
    )
    assert info.release_date is None
    assert info.age_days is None
    assert info.is_stale is False


def test_naive_release_date_treated_as_utc():
    naive_date = datetime(2023, 1, 1, 0, 0, 0)  # no tzinfo
    info = package_age_info(
        "somelib", "1.0.0",
        stale_days=365,
        _now=FIXED_NOW,
        _release_date=naive_date,
    )
    expected_days = (FIXED_NOW - naive_date.replace(tzinfo=timezone.utc)).days
    assert info.age_days == expected_days
    assert info.is_stale is True
