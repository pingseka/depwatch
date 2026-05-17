"""Audit trail: record every scan event with timestamp and summary."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from depwatch.scanner import ScanResult

_DEFAULT_AUDIT_FILE = os.path.join(
    os.path.expanduser("~"), ".depwatch", "audit_trail.jsonl"
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AuditEntry:
    timestamp: str
    dep_file: str
    total_packages: int
    outdated_count: int
    vulnerable_count: int
    triggered_alert: bool
    notes: str = ""
    extra: dict = field(default_factory=dict)


def _audit_path(path: Optional[str] = None) -> Path:
    return Path(path or _DEFAULT_AUDIT_FILE)


def record_event(
    dep_file: str,
    result: ScanResult,
    triggered_alert: bool = False,
    notes: str = "",
    audit_file: Optional[str] = None,
) -> AuditEntry:
    """Append one audit entry for *result* and return it."""
    entry = AuditEntry(
        timestamp=_utcnow(),
        dep_file=dep_file,
        total_packages=len(result.packages),
        outdated_count=len(result.outdated()),
        vulnerable_count=len(result.vulnerable()),
        triggered_alert=triggered_alert,
        notes=notes,
    )
    dest = _audit_path(audit_file)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry)) + "\n")
    return entry


def load_audit_trail(audit_file: Optional[str] = None) -> List[AuditEntry]:
    """Return all audit entries from *audit_file* (oldest first)."""
    dest = _audit_path(audit_file)
    if not dest.exists():
        return []
    entries: List[AuditEntry] = []
    with dest.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(AuditEntry(**json.loads(line)))
    return entries


def clear_audit_trail(audit_file: Optional[str] = None) -> None:
    """Remove all entries from the audit trail file."""
    dest = _audit_path(audit_file)
    if dest.exists():
        dest.unlink()
