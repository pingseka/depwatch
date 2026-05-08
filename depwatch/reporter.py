"""Report generation for depwatch scan results."""

from __future__ import annotations

import json
import csv
import io
from datetime import datetime, timezone
from typing import Literal

from depwatch.scanner import ScanResult, PackageInfo

ReportFormat = Literal["text", "json", "csv"]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _package_dict(pkg: PackageInfo) -> dict:
    return {
        "name": pkg.name,
        "current_version": pkg.current_version,
        "latest_version": pkg.latest_version,
        "vulnerabilities": pkg.vulnerabilities,
        "outdated": pkg.is_outdated,
        "vulnerable": pkg.is_vulnerable,
    }


def render_text(result: ScanResult) -> str:
    lines = [
        f"Depwatch Report — {_utcnow()}",
        f"Scanned file : {result.dependency_file}",
        f"Total packages : {len(result.packages)}",
        f"Outdated       : {len(result.outdated_packages)}",
        f"Vulnerable     : {len(result.vulnerable_packages)}",
        "",
    ]
    if result.outdated_packages:
        lines.append("Outdated packages:")
        for pkg in result.outdated_packages:
            lines.append(
                f"  {pkg.name}: {pkg.current_version} → {pkg.latest_version}"
            )
        lines.append("")
    if result.vulnerable_packages:
        lines.append("Vulnerable packages:")
        for pkg in result.vulnerable_packages:
            vulns = ", ".join(pkg.vulnerabilities)
            lines.append(f"  {pkg.name} {pkg.current_version}: {vulns}")
    return "\n".join(lines)


def render_json(result: ScanResult) -> str:
    payload = {
        "generated_at": _utcnow(),
        "dependency_file": result.dependency_file,
        "summary": {
            "total": len(result.packages),
            "outdated": len(result.outdated_packages),
            "vulnerable": len(result.vulnerable_packages),
        },
        "packages": [_package_dict(p) for p in result.packages],
    }
    return json.dumps(payload, indent=2)


def render_csv(result: ScanResult) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=["name", "current_version", "latest_version",
                    "outdated", "vulnerable", "vulnerabilities"],
    )
    writer.writeheader()
    for pkg in result.packages:
        row = _package_dict(pkg)
        row["vulnerabilities"] = "|".join(pkg.vulnerabilities)
        writer.writerow(row)
    return buf.getvalue()


def generate_report(result: ScanResult, fmt: ReportFormat = "text") -> str:
    """Return a formatted report string for *result*."""
    if fmt == "json":
        return render_json(result)
    if fmt == "csv":
        return render_csv(result)
    return render_text(result)
