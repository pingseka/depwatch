"""Render maintainer health reports as text or JSON."""
from __future__ import annotations

import json
from typing import List

from depwatch.package_maintainer import PackageMaintainerInfo


def render_text(infos: List[PackageMaintainerInfo]) -> str:
    lines: List[str] = ["Maintainer Health Report", "=" * 40]
    for info in infos:
        status = "ABANDONED" if info.is_abandoned else "ok"
        author_str = info.author or "(unknown)"
        lines.append(f"  {info.name} {info.version}  [{status}]")
        lines.append(f"    author      : {author_str}")
        if info.author_email:
            lines.append(f"    author_email: {info.author_email}")
        if info.warning:
            lines.append(f"    WARNING     : {info.warning}")
    abandoned = sum(1 for i in infos if i.is_abandoned)
    lines.append("=" * 40)
    lines.append(f"Total: {len(infos)}  Abandoned: {abandoned}")
    return "\n".join(lines)


def render_json(infos: List[PackageMaintainerInfo]) -> str:
    records = [
        {
            "name": i.name,
            "version": i.version,
            "author": i.author,
            "author_email": i.author_email,
            "maintainers": i.maintainers,
            "is_abandoned": i.is_abandoned,
            "warning": i.warning,
        }
        for i in infos
    ]
    return json.dumps(records, indent=2)


def has_abandoned_packages(infos: List[PackageMaintainerInfo]) -> bool:
    """Return True if any package appears abandoned."""
    return any(i.is_abandoned for i in infos)
