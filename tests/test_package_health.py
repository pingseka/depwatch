"""Tests for package_health and health_report modules."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from depwatch.package_health import (
    PackageHealthReport,
    _collect_warnings,
    check_package_health,
    scan_health,
)
from depwatch.health_report import render_text, render_json, has_health_violations
from depwatch.scanner import PackageInfo
from depwatch.package_score import PackageScore
from depwatch.package_age import PackageAgeInfo
from depwatch.package_popularity import PackagePopularityInfo
from depwatch.package_deprecation import PackageDeprecationInfo


def _score(total: int = 80) -> PackageScore:
    s = MagicMock(spec=PackageScore)
    s.total = total
    s.grade = "A" if total >= 80 else ("D" if total < 50 else "C")
    return s


def _age(stale: bool = False, days: int = 30) -> PackageAgeInfo:
    a = MagicMock(spec=PackageAgeInfo)
    a.is_stale = stale
    a.age_days = days
    a.release_date = None
    return a


def _popularity(low: bool = False, downloads: int = 50000) -> PackagePopularityInfo:
    p = MagicMock(spec=PackagePopularityInfo)
    p.is_low_popularity = low
    p.monthly_downloads = downloads
    return p


def _deprecation(deprecated: bool = False, successor: str | None = None) -> PackageDeprecationInfo:
    d = MagicMock(spec=PackageDeprecationInfo)
    d.is_deprecated = deprecated
    d.successor = successor
    return d


def _pkg(name: str = "mypkg", version: str = "1.0.0") -> PackageInfo:
    return PackageInfo(name=name, version=version, latest_version=version, vulnerabilities=[])


# --- _collect_warnings ---

def test_no_warnings_for_healthy_package():
    warnings = _collect_warnings(_score(90), _age(False), _popularity(False), _deprecation(False))
    assert warnings == []


def test_warns_on_low_score():
    warnings = _collect_warnings(_score(40), None, None, None)
    assert any("score" in w.lower() for w in warnings)


def test_warns_on_stale_age():
    warnings = _collect_warnings(_score(90), _age(True, 400), None, None)
    assert any("stale" in w.lower() for w in warnings)


def test_warns_on_low_popularity():
    warnings = _collect_warnings(_score(90), None, _popularity(True, 100), None)
    assert any("download" in w.lower() for w in warnings)


def test_warns_on_deprecation_with_successor():
    warnings = _collect_warnings(_score(90), None, None, _deprecation(True, "newpkg"))
    assert any("newpkg" in w for w in warnings)


def test_warns_on_deprecation_without_successor():
    warnings = _collect_warnings(_score(90), None, None, _deprecation(True, None))
    assert any("deprecated" in w.lower() for w in warnings)


# --- check_package_health integration ---

@patch("depwatch.package_health.fetch_deprecation")
@patch("depwatch.package_health.fetch_popularity")
@patch("depwatch.package_health.package_age_info")
@patch("depwatch.package_health.score_package")
def test_check_package_health_healthy(mock_score, mock_age, mock_pop, mock_dep):
    mock_score.return_value = _score(90)
    mock_age.return_value = _age(False)
    mock_pop.return_value = _popularity(False)
    mock_dep.return_value = _deprecation(False)

    report = check_package_health(_pkg())
    assert report.is_healthy
    assert report.name == "mypkg"
    assert report.warnings == []


@patch("depwatch.package_health.fetch_deprecation")
@patch("depwatch.package_health.fetch_popularity")
@patch("depwatch.package_health.package_age_info")
@patch("depwatch.package_health.score_package")
def test_check_package_health_unhealthy(mock_score, mock_age, mock_pop, mock_dep):
    mock_score.return_value = _score(30)
    mock_age.return_value = _age(True, 500)
    mock_pop.return_value = _popularity(True, 50)
    mock_dep.return_value = _deprecation(True, "replacement")

    report = check_package_health(_pkg())
    assert not report.is_healthy
    assert len(report.warnings) == 4


# --- health_report rendering ---

def _make_report(healthy: bool = True) -> PackageHealthReport:
    warnings = [] if healthy else ["Something is wrong"]
    return PackageHealthReport(
        name="testpkg",
        version="2.0.0",
        score=_score(85 if healthy else 40),
        age=_age(not healthy),
        popularity=_popularity(not healthy),
        deprecation=_deprecation(not healthy),
        warnings=warnings,
    )


def test_render_text_empty():
    assert "No packages" in render_text([])


def test_render_text_shows_package_name():
    out = render_text([_make_report(True)])
    assert "testpkg" in out


def test_render_text_shows_warning():
    out = render_text([_make_report(False)])
    assert "Something is wrong" in out


def test_render_json_structure():
    data = json.loads(render_json([_make_report(True)]))
    assert isinstance(data, list)
    assert data[0]["name"] == "testpkg"
    assert "grade" in data[0]
    assert "warnings" in data[0]


def test_has_health_violations_true():
    assert has_health_violations([_make_report(False)])


def test_has_health_violations_false():
    assert not has_health_violations([_make_report(True)])
