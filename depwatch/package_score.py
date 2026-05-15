"""Compute a simple health score for each package in a ScanResult.

Score is 0-100 (higher = healthier). Deductions:
  - outdated:  -30
  - vulnerable: -40 per vulnerability (capped at -60)
  - stale (age-based, if age_days provided): -10
Severity multiplier applied to vulnerability deduction:
  critical=1.0, high=0.75, medium=0.5, low=0.25
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from depwatch.scanner import PackageInfo, ScanResult

_SEVERITY_MULT = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
_OUTDATED_PENALTY = 30
_VULN_PENALTY_EACH = 40
_VULN_PENALTY_CAP = 60
_STALE_PENALTY = 10


@dataclass
class PackageScore:
    name: str
    version: str
    score: int  # 0-100
    penalties: List[str] = field(default_factory=list)

    @property
    def grade(self) -> str:
        if self.score >= 90:
            return "A"
        if self.score >= 75:
            return "B"
        if self.score >= 50:
            return "C"
        if self.score >= 25:
            return "D"
        return "F"


def score_package(
    pkg: PackageInfo,
    age_days: Optional[float] = None,
    stale_threshold_days: int = 365,
) -> PackageScore:
    """Return a PackageScore for a single PackageInfo."""
    deduction = 0
    penalties: List[str] = []

    if pkg.is_outdated:
        deduction += _OUTDATED_PENALTY
        penalties.append(f"outdated ({pkg.current_version} -> {pkg.latest_version})")

    if pkg.vulnerabilities:
        vuln_deduction = 0
        for vuln in pkg.vulnerabilities:
            mult = _SEVERITY_MULT.get((vuln.severity or "").lower(), 0.5)
            vuln_deduction += int(_VULN_PENALTY_EACH * mult)
        vuln_deduction = min(vuln_deduction, _VULN_PENALTY_CAP)
        deduction += vuln_deduction
        penalties.append(f"{len(pkg.vulnerabilities)} vulnerability/ies (-{vuln_deduction} pts)")

    if age_days is not None and age_days >= stale_threshold_days:
        deduction += _STALE_PENALTY
        penalties.append(f"stale release ({int(age_days)} days old)")

    score = max(0, 100 - deduction)
    return PackageScore(name=pkg.name, version=pkg.current_version, score=score, penalties=penalties)


def score_scan_result(
    result: ScanResult,
    age_map: Optional[dict] = None,
    stale_threshold_days: int = 365,
) -> List[PackageScore]:
    """Score all packages in a ScanResult.

    age_map: optional dict mapping package name -> age in days.
    """
    age_map = age_map or {}
    return [
        score_package(pkg, age_days=age_map.get(pkg.name), stale_threshold_days=stale_threshold_days)
        for pkg in result.packages
    ]


def average_score(scores: List[PackageScore]) -> float:
    """Return the mean score across all packages, or 100.0 if none."""
    if not scores:
        return 100.0
    return sum(s.score for s in scores) / len(scores)
