"""Detect transitive (indirect) dependencies in a requirements file."""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TransitiveDep:
    name: str
    version: str
    required_by: List[str] = field(default_factory=list)

    @property
    def is_direct(self) -> bool:
        return len(self.required_by) == 0


@dataclass
class TransitiveReport:
    direct: List[TransitiveDep] = field(default_factory=list)
    transitive: List[TransitiveDep] = field(default_factory=list)

    @property
    def has_transitive(self) -> bool:
        return len(self.transitive) > 0

    @property
    def all_packages(self) -> List[TransitiveDep]:
        return self.direct + self.transitive


def _run_pipdeptree() -> Optional[Dict[str, dict]]:
    """Run pipdeptree --json and return parsed output, or None on failure."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pipdeptree", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None
        import json
        return json.loads(result.stdout)
    except Exception:
        return None


def scan_transitive(direct_names: List[str]) -> TransitiveReport:
    """Given a list of direct dependency names, classify all installed
    packages as direct or transitive."""
    direct_lower = {n.lower() for n in direct_names}
    tree = _run_pipdeptree()
    if tree is None:
        # Fallback: treat everything as direct
        return TransitiveReport(
            direct=[TransitiveDep(name=n, version="unknown") for n in direct_names]
        )

    # Build a map: package_name -> {version, dependencies[]}
    pkg_map: Dict[str, dict] = {}
    for entry in tree:
        pkg = entry.get("package", {})
        name = pkg.get("package_name", "").lower()
        version = pkg.get("installed_version", "unknown")
        deps = [
            d.get("package_name", "").lower()
            for d in entry.get("dependencies", [])
        ]
        pkg_map[name] = {"version": version, "deps": deps}

    # Collect which packages are required by direct deps
    required_by: Dict[str, List[str]] = {}
    for entry in tree:
        pkg = entry.get("package", {})
        parent_name = pkg.get("package_name", "").lower()
        if parent_name not in direct_lower:
            continue
        for dep in entry.get("dependencies", []):
            child = dep.get("package_name", "").lower()
            required_by.setdefault(child, []).append(parent_name)

    report = TransitiveReport()
    for name_lower, info in pkg_map.items():
        dep = TransitiveDep(
            name=name_lower,
            version=info["version"],
            required_by=required_by.get(name_lower, []),
        )
        if name_lower in direct_lower:
            report.direct.append(dep)
        elif dep.required_by:
            report.transitive.append(dep)

    return report
