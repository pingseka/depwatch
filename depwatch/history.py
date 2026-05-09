"""Scan history tracking: persist and retrieve past scan results."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_FILE = ".depwatch_history.json"
_MAX_ENTRIES = 100


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _history_path(path: Optional[str] = None) -> Path:
    return Path(path or DEFAULT_HISTORY_FILE)


def load_history(path: Optional[str] = None) -> List[dict]:
    """Load existing scan history from disk. Returns empty list if not found."""
    p = _history_path(path)
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def append_entry(
    dep_file: str,
    outdated_count: int,
    vulnerable_count: int,
    packages: List[str],
    path: Optional[str] = None,
) -> dict:
    """Append a scan result entry to the history file and return the new entry."""
    entry = {
        "timestamp": _utcnow(),
        "dep_file": dep_file,
        "outdated_count": outdated_count,
        "vulnerable_count": vulnerable_count,
        "packages": packages,
    }
    history = load_history(path)
    history.append(entry)
    # Keep only the most recent entries to avoid unbounded growth
    if len(history) > _MAX_ENTRIES:
        history = history[-_MAX_ENTRIES:]
    p = _history_path(path)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2)
    return entry


def last_entry(dep_file: str, path: Optional[str] = None) -> Optional[dict]:
    """Return the most recent history entry for a given dependency file."""
    history = load_history(path)
    for entry in reversed(history):
        if entry.get("dep_file") == dep_file:
            return entry
    return None


def clear_history(path: Optional[str] = None) -> None:
    """Delete the history file if it exists."""
    p = _history_path(path)
    if p.exists():
        p.unlink()
