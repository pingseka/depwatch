"""Dependency file scanner that detects outdated and vulnerable packages."""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PackageInfo:
    name: str
    current_version: str
    latest_version: Optional[str] = None
    vulnerabilities: list[str] = field(default_factory=list)

    @property
    def is_outdated(self) -> bool:
        return self.latest_version is not None and self.current_version != self.latest_version

    @property
    def is_vulnerable(self) -> bool:
        return len(self.vulnerabilities) > 0


@dataclass
class ScanResult:
    dep_file: str
    packages: list[PackageInfo] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def outdated(self) -> list[PackageInfo]:
        return [p for p in self.packages if p.is_outdated]

    @property
    def vulnerable(self) -> list[PackageInfo]:
        return [p for p in self.packages if p.is_vulnerable]


def scan_requirements_txt(filepath: str) -> ScanResult:
    """Scan a requirements.txt file for outdated packages."""
    result = ScanResult(dep_file=filepath)
    path = Path(filepath)

    if not path.exists():
        result.errors.append(f"File not found: {filepath}")
        return result

    try:
        proc = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        outdated_data = json.loads(proc.stdout) if proc.stdout else []
        outdated_map = {pkg["name"].lower(): pkg["latest_version"] for pkg in outdated_data}
    except Exception as exc:
        result.errors.append(f"Failed to fetch outdated packages: {exc}")
        outdated_map = {}

    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
            current = line.split("==")[1].strip() if "==" in line else "unknown"
            latest = outdated_map.get(name.lower())
            result.packages.append(PackageInfo(name=name, current_version=current, latest_version=latest))

    return result


def scan_file(filepath: str) -> ScanResult:
    """Dispatch scan based on file type."""
    if filepath.endswith("requirements.txt"):
        return scan_requirements_txt(filepath)
    return ScanResult(dep_file=filepath, errors=[f"Unsupported dependency file: {filepath}"])
