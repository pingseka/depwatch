"""Filter scan results by minimum severity level."""

from __future__ import annotations

from typing import List

from depwatch.scanner import PackageInfo, ScanResult

# Ordered from least to most severe
SEVERITY_LEVELS = ["low", "medium", "high", "critical"]


def _severity_rank(severity: str) -> int:
    """Return numeric rank for a severity string (case-insensitive)."""
    try:
        return SEVERITY_LEVELS.index(severity.lower())
    except ValueError:
        return -1


def meets_minimum_severity(pkg: PackageInfo, min_severity: str) -> bool:
    """Return True if the package's vulnerability severity meets the minimum.

    Outdated-only packages (no vuln_severity) are always included.
    """
    if pkg.vuln_severity is None:
        return True
    return _severity_rank(pkg.vuln_severity) >= _severity_rank(min_severity)


def filter_by_severity(result: ScanResult, min_severity: str) -> ScanResult:
    """Return a new ScanResult containing only packages that meet *min_severity*.

    Packages with no vulnerability (outdated-only) are always retained.
    """
    filtered: List[PackageInfo] = [
        pkg for pkg in result.packages if meets_minimum_severity(pkg, min_severity)
    ]
    return ScanResult(packages=filtered, scanned_file=result.scanned_file)


def severity_counts(result: ScanResult) -> dict:
    """Return a mapping of severity label -> count for vulnerable packages."""
    counts: dict = {level: 0 for level in SEVERITY_LEVELS}
    counts["unknown"] = 0
    for pkg in result.packages:
        if pkg.vuln_severity is not None:
            key = pkg.vuln_severity.lower()
            if key in counts:
                counts[key] += 1
            else:
                counts["unknown"] += 1
    return counts
