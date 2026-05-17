"""Analyse dependency tree complexity (depth and breadth) for packages."""
from __future__ import annotations

import subprocess
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ComplexityInfo:
    package: str
    direct_deps: int
    transitive_deps: int
    max_depth: int
    error: Optional[str] = None

    @property
    def total_deps(self) -> int:
        return self.direct_deps + self.transitive_deps

    @property
    def is_complex(self) -> bool:
        """Flag packages with a large transitive footprint or deep trees."""
        return self.total_deps > 20 or self.max_depth > 5


@dataclass
class ComplexityReport:
    packages: List[ComplexityInfo] = field(default_factory=list)

    @property
    def complex_packages(self) -> List[ComplexityInfo]:
        return [p for p in self.packages if p.is_complex]

    @property
    def has_complex(self) -> bool:
        return bool(self.complex_packages)


def _pipdeptree_json() -> Optional[list]:
    try:
        result = subprocess.run(
            ["pipdeptree", "--json-tree"],
            capture_output=True, text=True, timeout=30,
        )
        return json.loads(result.stdout)
    except Exception:
        return None


def _walk(node: dict, depth: int = 0) -> tuple[int, int]:
    """Return (transitive_count, max_depth) for a dependency node."""
    children = node.get("dependencies", [])
    if not children:
        return 0, depth
    counts, depths = zip(*[_walk(c, depth + 1) for c in children])
    return sum(counts) + len(children), max(depths)


def fetch_complexity(package: str) -> ComplexityInfo:
    tree = _pipdeptree_json()
    if tree is None:
        return ComplexityInfo(package=package, direct_deps=0, transitive_deps=0,
                              max_depth=0, error="pipdeptree unavailable")
    for node in tree:
        if node.get("package_name", "").lower() == package.lower():
            direct = node.get("dependencies", [])
            trans_total, max_d = 0, 0
            for child in direct:
                t, d = _walk(child, depth=1)
                trans_total += t
                max_d = max(max_d, d)
            return ComplexityInfo(
                package=package,
                direct_deps=len(direct),
                transitive_deps=trans_total,
                max_depth=max_d,
            )
    return ComplexityInfo(package=package, direct_deps=0, transitive_deps=0,
                          max_depth=0, error="package not found in tree")


def scan_complexity(packages: List[str]) -> ComplexityReport:
    return ComplexityReport(packages=[fetch_complexity(p) for p in packages])
