"""Render size scan results as text or JSON."""
from __future__ import annotations

import json
from typing import List

from depwatch.package_size import PackageSizeInfo


def render_text(results: List[PackageSizeInfo]) -> str:
    if not results:
        return "No packages scanned.\n"

    lines: List[str] = ["Package Size Report", "=" * 40]
    for info in results:
        if info.error:
            lines.append(f"  {info.name}: ERROR — {info.error}")
            continue
        size_str = f"{info.size_kb} KB" if info.size_kb is not None else "unknown"
        flag = " [LARGE]" if info.is_large else ""
        lines.append(f"  {info.name}=={info.version}: {size_str}{flag}")

    large = [i for i in results if i.is_large]
    lines.append("")
    lines.append(f"Total packages: {len(results)}")
    lines.append(f"Large packages: {len(large)}")
    return "\n".join(lines) + "\n"


def _serialise(info: PackageSizeInfo) -> dict:
    return {
        "name": info.name,
        "version": info.version,
        "size_bytes": info.size_bytes,
        "size_kb": info.size_kb,
        "threshold_bytes": info.threshold_bytes,
        "is_large": info.is_large,
        "error": info.error,
    }


def render_json(results: List[PackageSizeInfo]) -> str:
    return json.dumps([_serialise(r) for r in results], indent=2)


def has_large_packages(results: List[PackageSizeInfo]) -> bool:
    return any(r.is_large for r in results)
