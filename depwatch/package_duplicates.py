"""Detect duplicate or conflicting package declarations in dependency files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DuplicateEntry:
    name: str
    versions: List[str]
    lines: List[int]

    @property
    def is_conflicting(self) -> bool:
        """True when the same package appears with different version specs."""
        unique = set(v.strip() for v in self.versions if v.strip())
        return len(unique) > 1

    @property
    def description(self) -> str:
        specs = ", ".join(
            f"line {ln}: {ver!r}" for ln, ver in zip(self.lines, self.versions)
        )
        tag = "CONFLICT" if self.is_conflicting else "DUPLICATE"
        return f"[{tag}] {self.name} — {specs}"


@dataclass
class DuplicateReport:
    path: str
    duplicates: List[DuplicateEntry] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.duplicates)

    @property
    def conflict_count(self) -> int:
        return sum(1 for d in self.duplicates if d.is_conflicting)

    @property
    def duplicate_count(self) -> int:
        return sum(1 for d in self.duplicates if not d.is_conflicting)


_REQ_LINE = re.compile(
    r"^\s*([A-Za-z0-9_\-\.]+)\s*([^#\n]*)?",
    re.IGNORECASE,
)


def scan_duplicates(requirements_path: str) -> DuplicateReport:
    """Parse a requirements.txt and return a DuplicateReport."""
    path = Path(requirements_path)
    seen: Dict[str, List[tuple]] = {}  # name -> [(line_no, version_spec)]

    if not path.exists():
        return DuplicateReport(path=requirements_path)

    with path.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            m = _REQ_LINE.match(line)
            if not m:
                continue
            pkg_name = m.group(1).lower()
            version_spec = (m.group(2) or "").strip().split("#")[0].strip()
            seen.setdefault(pkg_name, []).append((lineno, version_spec))

    duplicates: List[DuplicateEntry] = []
    for name, occurrences in seen.items():
        if len(occurrences) > 1:
            duplicates.append(
                DuplicateEntry(
                    name=name,
                    versions=[v for _, v in occurrences],
                    lines=[ln for ln, _ in occurrences],
                )
            )

    return DuplicateReport(path=requirements_path, duplicates=duplicates)
