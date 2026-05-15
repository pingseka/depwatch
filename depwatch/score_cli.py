"""CLI subcommand: depwatch score — display per-package health scores."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from depwatch.package_score import PackageScore, average_score, score_scan_result
from depwatch.scanner import ScanResult


def add_score_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("score", help="Show health scores for scanned packages")
    p.add_argument("dep_file", help="Path to requirements.txt (or similar)")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--min-score",
        type=int,
        default=0,
        metavar="N",
        help="Only show packages with score below N (0 = show all)",
    )
    p.set_defaults(func=cmd_score)


def _render_text(scores: List[PackageScore], avg: float) -> str:
    lines = [f"{'Package':<30} {'Version':<15} {'Score':>5}  Grade  Penalties"]
    lines.append("-" * 80)
    for s in scores:
        penalty_str = "; ".join(s.penalties) if s.penalties else "none"
        lines.append(f"{s.name:<30} {s.version:<15} {s.score:>5}  {s.grade:<5}  {penalty_str}")
    lines.append("-" * 80)
    lines.append(f"Average score: {avg:.1f}")
    return "\n".join(lines)


def _render_json(scores: List[PackageScore], avg: float) -> str:
    data = {
        "average_score": round(avg, 2),
        "packages": [
            {
                "name": s.name,
                "version": s.version,
                "score": s.score,
                "grade": s.grade,
                "penalties": s.penalties,
            }
            for s in scores
        ],
    }
    return json.dumps(data, indent=2)


def cmd_score(args: argparse.Namespace) -> None:
    from depwatch.scanner import scan  # local import to avoid circular deps

    result: ScanResult = scan(args.dep_file)
    scores = score_scan_result(result)

    if args.min_score > 0:
        scores = [s for s in scores if s.score < args.min_score]

    avg = average_score(scores)

    if args.format == "json":
        print(_render_json(scores, avg))
    else:
        print(_render_text(scores, avg))

    if any(s.score < 50 for s in scores):
        sys.exit(1)
