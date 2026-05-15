"""Tests for depwatch.package_score."""

from __future__ import annotations

import pytest

from depwatch.scanner import PackageInfo, ScanResult
from depwatch.scanner import VulnerabilityInfo  # type: ignore[attr-defined]
from depwatch.package_score import (
    PackageScore,
    average_score,
    score_package,
    score_scan_result,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _vuln(severity: str = "high") -> "VulnerabilityInfo":
    try:
        from depwatch.scanner import VulnerabilityInfo
        return VulnerabilityInfo(id="CVE-0000-0001", description="test", severity=severity)
    except Exception:
        # Fallback: plain object
        class V:
            def __init__(self, sev):
                self.id = "CVE-0000-0001"
                self.description = "test"
                self.severity = sev
        return V(severity)


def _pkg(name="foo", current="1.0", latest="1.0", vulns=None):
    outdated = current != latest
    return PackageInfo(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
        vulnerabilities=vulns or [],
    )


# ---------------------------------------------------------------------------
# score_package
# ---------------------------------------------------------------------------

def test_perfect_score_healthy_package():
    pkg = _pkg()
    s = score_package(pkg)
    assert s.score == 100
    assert s.grade == "A"
    assert s.penalties == []


def test_outdated_deducts_30():
    pkg = _pkg(current="1.0", latest="2.0")
    s = score_package(pkg)
    assert s.score == 70
    assert any("outdated" in p for p in s.penalties)


def test_critical_vuln_deducts_40():
    pkg = _pkg(vulns=[_vuln("critical")])
    s = score_package(pkg)
    assert s.score == 60  # 100 - 40*1.0


def test_vuln_penalty_capped_at_60():
    pkg = _pkg(vulns=[_vuln("critical"), _vuln("critical"), _vuln("critical")])
    s = score_package(pkg)
    assert s.score == 40  # 100 - cap(120, 60)


def test_stale_deducts_10():
    pkg = _pkg()
    s = score_package(pkg, age_days=400, stale_threshold_days=365)
    assert s.score == 90
    assert any("stale" in p for p in s.penalties)


def test_not_stale_below_threshold():
    pkg = _pkg()
    s = score_package(pkg, age_days=100, stale_threshold_days=365)
    assert s.score == 100


def test_score_never_below_zero():
    pkg = _pkg(current="1.0", latest="2.0", vulns=[_vuln("critical"), _vuln("critical"), _vuln("critical")])
    s = score_package(pkg, age_days=500)
    assert s.score >= 0


def test_grade_boundaries():
    for score, expected in [(95, "A"), (80, "B"), (60, "C"), (30, "D"), (10, "F")]:
        ps = PackageScore(name="x", version="1.0", score=score)
        assert ps.grade == expected


# ---------------------------------------------------------------------------
# score_scan_result / average_score
# ---------------------------------------------------------------------------

def test_score_scan_result_returns_one_per_package():
    result = ScanResult(packages=[_pkg("a"), _pkg("b")])
    scores = score_scan_result(result)
    assert len(scores) == 2
    assert {s.name for s in scores} == {"a", "b"}


def test_average_score_empty():
    assert average_score([]) == 100.0


def test_average_score_mixed():
    scores = [
        PackageScore(name="a", version="1", score=80),
        PackageScore(name="b", version="1", score=60),
    ]
    assert average_score(scores) == pytest.approx(70.0)


def test_age_map_passed_through():
    result = ScanResult(packages=[_pkg("old")])
    scores = score_scan_result(result, age_map={"old": 400}, stale_threshold_days=365)
    assert any("stale" in p for p in scores[0].penalties)
