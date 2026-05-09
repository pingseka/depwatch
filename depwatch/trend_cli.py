"""CLI helpers for the 'trend' sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from depwatch.trend import build_trend, render_trend_text


def add_trend_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'trend' sub-command onto *subparsers*."""
    p = subparsers.add_parser(
        "trend",
        help="Show historical trend for a dependency file.",
    )
    p.add_argument(
        "dep_file",
        help="Path to the dependency file (e.g. requirements.txt).",
    )
    p.add_argument(
        "--history-dir",
        default=".depwatch",
        metavar="DIR",
        help="Directory where history files are stored (default: .depwatch).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=10,
        metavar="N",
        help="Maximum number of history entries to display (default: 10).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    p.set_defaults(func=cmd_trend)


def cmd_trend(args: argparse.Namespace) -> int:
    """Execute the 'trend' sub-command; returns an exit code."""
    report = build_trend(
        dep_file=args.dep_file,
        history_dir=args.history_dir,
        limit=args.limit,
    )

    if args.output_format == "json":
        payload = {
            "dep_file": args.dep_file,
            "outdated_delta": report.outdated_delta,
            "vulnerable_delta": report.vulnerable_delta,
            "is_worsening": report.is_worsening,
            "is_improving": report.is_improving,
            "points": [
                {
                    "timestamp": pt.timestamp,
                    "outdated_count": pt.outdated_count,
                    "vulnerable_count": pt.vulnerable_count,
                }
                for pt in report.points
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(render_trend_text(report))

    # Non-zero exit if trend is worsening so CI pipelines can react.
    return 1 if report.is_worsening else 0


if __name__ == "__main__":  # pragma: no cover
    import argparse as _ap

    _parser = _ap.ArgumentParser(prog="depwatch-trend")
    _subs = _parser.add_subparsers()
    add_trend_subparser(_subs)
    _args = _parser.parse_args()
    if hasattr(_args, "func"):
        sys.exit(_args.func(_args))
    else:
        _parser.print_help()
        sys.exit(0)
