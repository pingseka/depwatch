"""Suppression list: ignore known vulnerabilities or outdated packages."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

DEFAULT_SUPPRESSION_PATH = os.path.join(
    os.path.expanduser("~"), ".depwatch", "suppressions.json"
)


@dataclass
class SuppressionEntry:
    package: str
    reason: str
    expires: Optional[str] = None  # ISO date string YYYY-MM-DD
    vulnerability_id: Optional[str] = None  # e.g. CVE-2023-1234

    def is_expired(self) -> bool:
        if self.expires is None:
            return False
        try:
            expiry = date.fromisoformat(self.expires)
            return date.today() > expiry
        except ValueError:
            return False

    def matches(self, package: str, vulnerability_id: Optional[str] = None) -> bool:
        if self.is_expired():
            return False
        if self.package.lower() != package.lower():
            return False
        if self.vulnerability_id and vulnerability_id:
            return self.vulnerability_id == vulnerability_id
        return True


@dataclass
class SuppressionList:
    entries: List[SuppressionEntry] = field(default_factory=list)

    def is_suppressed(self, package: str, vulnerability_id: Optional[str] = None) -> bool:
        return any(e.matches(package, vulnerability_id) for e in self.entries)

    def active_entries(self) -> List[SuppressionEntry]:
        return [e for e in self.entries if not e.is_expired()]


def load_suppressions(path: str = DEFAULT_SUPPRESSION_PATH) -> SuppressionList:
    if not os.path.exists(path):
        return SuppressionList()
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    entries = [SuppressionEntry(**item) for item in raw.get("suppressions", [])]
    return SuppressionList(entries=entries)


def save_suppressions(
    suppression_list: SuppressionList, path: str = DEFAULT_SUPPRESSION_PATH
) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "suppressions": [
            {
                "package": e.package,
                "reason": e.reason,
                "expires": e.expires,
                "vulnerability_id": e.vulnerability_id,
            }
            for e in suppression_list.entries
        ]
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def add_suppression(
    package: str,
    reason: str,
    expires: Optional[str] = None,
    vulnerability_id: Optional[str] = None,
    path: str = DEFAULT_SUPPRESSION_PATH,
) -> SuppressionList:
    sl = load_suppressions(path)
    sl.entries.append(
        SuppressionEntry(
            package=package,
            reason=reason,
            expires=expires,
            vulnerability_id=vulnerability_id,
        )
    )
    save_suppressions(sl, path)
    return sl
