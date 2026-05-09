"""Filter ScanResult packages using a SuppressionList."""

from __future__ import annotations

from typing import List

from depwatch.scanner import PackageInfo, ScanResult
from depwatch.suppression import SuppressionList


def filter_scan_result(
    result: ScanResult, suppression_list: SuppressionList
) -> ScanResult:
    """Return a new ScanResult with suppressed packages removed."""
    filtered: List[PackageInfo] = []
    suppressed_names: List[str] = []

    for pkg in result.packages:
        vuln_id = pkg.vulnerability_id if hasattr(pkg, "vulnerability_id") else None
        if suppression_list.is_suppressed(pkg.name, vuln_id):
            suppressed_names.append(pkg.name)
        else:
            filtered.append(pkg)

    if suppressed_names:
        import logging
        logging.getLogger(__name__).info(
            "Suppressed %d package(s): %s",
            len(suppressed_names),
            ", ".join(suppressed_names),
        )

    return ScanResult(packages=filtered, scanned_file=result.scanned_file)


def suppressed_packages(
    result: ScanResult, suppression_list: SuppressionList
) -> List[PackageInfo]:
    """Return only the packages that are suppressed."""
    vuln_attr = "vulnerability_id"
    return [
        pkg
        for pkg in result.packages
        if suppression_list.is_suppressed(
            pkg.name,
            getattr(pkg, vuln_attr, None),
        )
    ]
