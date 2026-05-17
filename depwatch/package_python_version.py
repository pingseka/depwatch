"""Check whether packages declare compatibility with the current Python version."""
from __future__ import annotations

import sys
import urllib.request
import urllib.error
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PythonVersionInfo:
    name: str
    version: str
    requires_python: Optional[str]  # e.g. ">=3.8"
    compatible: bool
    current_python: str
    error: Optional[str] = None


def _pypi_url(name: str, version: Optional[str] = None) -> str:
    if version:
        return f"https://pypi.org/pypi/{name}/{version}/json"
    return f"https://pypi.org/pypi/{name}/json"


def _check_compatible(requires_python: Optional[str], current: tuple) -> bool:
    """Very small subset: handles >=X.Y, >X.Y, ==X.Y, !=X.Y, <X.Y, <=X.Y."""
    if not requires_python:
        return True
    import re
    for spec in [s.strip() for s in requires_python.split(",")]:
        m = re.match(r"([><=!]+)(\d+)\.(\d+)", spec)
        if not m:
            continue
        op, maj, mn = m.group(1), int(m.group(2)), int(m.group(3))
        req = (maj, mn)
        if op == ">="  and not (current >= req): return False
        if op == ">"   and not (current >  req): return False
        if op == "<="  and not (current <= req): return False
        if op == "<"   and not (current <  req): return False
        if op == "=="  and not (current == req): return False
        if op == "!="  and     (current == req): return False
    return True


def fetch_python_version(name: str, version: Optional[str] = None) -> PythonVersionInfo:
    current_tuple = (sys.version_info.major, sys.version_info.minor)
    current_str = f"{current_tuple[0]}.{current_tuple[1]}"
    used_version = version or "latest"
    try:
        url = _pypi_url(name, version)
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        info = data.get("info", {})
        used_version = info.get("version", used_version)
        requires_python = info.get("requires_python") or None
        compatible = _check_compatible(requires_python, current_tuple)
        return PythonVersionInfo(
            name=name,
            version=used_version,
            requires_python=requires_python,
            compatible=compatible,
            current_python=current_str,
        )
    except urllib.error.URLError as exc:
        return PythonVersionInfo(
            name=name, version=used_version,
            requires_python=None, compatible=True,
            current_python=current_str,
            error=f"network error: {exc}",
        )
    except Exception as exc:
        return PythonVersionInfo(
            name=name, version=used_version,
            requires_python=None, compatible=True,
            current_python=current_str,
            error=str(exc),
        )


def scan_python_versions(packages: List[tuple]) -> List[PythonVersionInfo]:
    """packages: list of (name, version_or_None) tuples."""
    return [fetch_python_version(name, ver) for name, ver in packages]
