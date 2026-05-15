"""Detect unpinned or loosely-pinned dependencies in requirements files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# Regex for a requirements.txt line (ignores comments and blank lines)
_REQ_LINE = re.compile(
    r"^(?P<name>[A-Za-z0-9_\-\.]+)\s*(?P<spec>[^#]*)?"
)
_EXACT_PIN = re.compile(r"==")
_LOOSE_SPECS = re.compile(r"[><!~^]")


@dataclass
class PinningIssue:
    package: str
    specifier: str  # raw specifier string, empty means unpinned
    kind: str  # "unpinned" | "loose"

    @property
    def description(self) -> str:
        if self.kind == "unpinned":
            return f"{self.package}: no version specifier (unpinned)"
        return f"{self.package}: loose specifier '{self.specifier}'"


@dataclass
class PinningReport:
    path: str
    issues: List[PinningIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    @property
    def unpinned(self) -> List[PinningIssue]:
        return [i for i in self.issues if i.kind == "unpinned"]

    @property
    def loose(self) -> List[PinningIssue]:
        return [i for i in self.issues if i.kind == "loose"]


def _classify(name: str, specifier: str) -> Optional[PinningIssue]:
    spec = specifier.strip()
    if not spec:
        return PinningIssue(package=name, specifier=spec, kind="unpinned")
    if not _EXACT_PIN.search(spec):
        return PinningIssue(package=name, specifier=spec, kind="loose")
    return None


def scan_pinning(requirements_path: str) -> PinningReport:
    """Parse *requirements_path* and return a PinningReport."""
    path = Path(requirements_path)
    report = PinningReport(path=str(path))
    if not path.exists():
        return report
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        m = _REQ_LINE.match(line)
        if not m:
            continue
        name = m.group("name")
        specifier = (m.group("spec") or "").split("#")[0].strip()
        issue = _classify(name, specifier)
        if issue:
            report.issues.append(issue)
    return report
