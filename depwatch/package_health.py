"""Aggregate health check combining score, age, popularity, and deprecation signals."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from depwatch.package_score import PackageScore, score_package
from depwatch.package_age import PackageAgeInfo, package_age_info
from depwatch.package_popularity import PackagePopularityInfo, fetch_popularity
from depwatch.package_deprecation import PackageDeprecationInfo, fetch_deprecation
from depwatch.scanner import PackageInfo


@dataclass
class PackageHealthReport:
    name: str
    version: str
    score: PackageScore
    age: Optional[PackageAgeInfo]
    popularity: Optional[PackagePopularityInfo]
    deprecation: Optional[PackageDeprecationInfo]
    warnings: List[str] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return len(self.warnings) == 0

    @property
    def summary(self) -> str:
        status = "OK" if self.is_healthy else "WARN"
        return f"[{status}] {self.name}=={self.version} grade={self.score.grade} warnings={len(self.warnings)}"


def _collect_warnings(
    score: PackageScore,
    age: Optional[PackageAgeInfo],
    popularity: Optional[PackagePopularityInfo],
    deprecation: Optional[PackageDeprecationInfo],
) -> List[str]:
    warnings: List[str] = []
    if score.grade in ("D", "F"):
        warnings.append(f"Low package score: {score.total}/100 (grade {score.grade})")
    if age and age.is_stale:
        days = age.age_days
        warnings.append(f"Package not updated in {days} days (stale)")
    if popularity and popularity.is_low_popularity:
        warnings.append(f"Low download count: {popularity.monthly_downloads}/month")
    if deprecation and deprecation.is_deprecated:
        msg = "Package is deprecated"
        if deprecation.successor:
            msg += f"; consider using '{deprecation.successor}'"
        warnings.append(msg)
    return warnings


def check_package_health(pkg: PackageInfo) -> PackageHealthReport:
    """Run all health checks for a single package and return a consolidated report."""
    score = score_package(pkg)
    age = package_age_info(pkg.name, pkg.version)
    popularity = fetch_popularity(pkg.name)
    deprecation = fetch_deprecation(pkg.name, pkg.version)
    warnings = _collect_warnings(score, age, popularity, deprecation)
    return PackageHealthReport(
        name=pkg.name,
        version=pkg.version,
        score=score,
        age=age,
        popularity=popularity,
        deprecation=deprecation,
        warnings=warnings,
    )


def scan_health(packages: List[PackageInfo]) -> List[PackageHealthReport]:
    """Run health checks across a list of packages."""
    return [check_package_health(pkg) for pkg in packages]
