"""Persist and retrieve the latest scan digest for each watched file."""

from __future__ import annotations

import json
import os
from typing import Dict, Optional

_DEFAULT_STORE = os.path.join(
    os.path.expanduser("~"), ".depwatch", "digests.json"
)


def _store_path(path: Optional[str] = None) -> str:
    return path or _DEFAULT_STORE


def load_store(path: Optional[str] = None) -> Dict[str, str]:
    """Load the digest store from disk, returning an empty dict on failure."""
    fpath = _store_path(path)
    if not os.path.exists(fpath):
        return {}
    try:
        with open(fpath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def save_digest(dep_file: str, digest: str, path: Optional[str] = None) -> None:
    """Persist *digest* for *dep_file* in the store."""
    fpath = _store_path(path)
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    store = load_store(path)
    store[dep_file] = digest
    with open(fpath, "w", encoding="utf-8") as fh:
        json.dump(store, fh, indent=2)


def get_digest(dep_file: str, path: Optional[str] = None) -> Optional[str]:
    """Return the stored digest for *dep_file*, or None if not found."""
    return load_store(path).get(dep_file)


def remove_digest(dep_file: str, path: Optional[str] = None) -> None:
    """Remove the stored digest entry for *dep_file*."""
    fpath = _store_path(path)
    store = load_store(path)
    if dep_file in store:
        del store[dep_file]
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, "w", encoding="utf-8") as fh:
            json.dump(store, fh, indent=2)
