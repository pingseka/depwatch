"""CLI subcommand: depwatch pinning."""

from __future__ import annotations

import argparse
import sys

from depwatch.package_pinning import scan_pinning
from depwatch.pinning_report import render_json, render_text


def add_pinning_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "pinning",
        help="Check requirements file for unpinned or loosely-pinned packages.",
    )
    p.add_argument(
        "requirements",
        nargs="?",
        default="requirements.txt",
        help="Path to requirements file (default: requirements.txt)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any issues are found.",
    )
    p.set_defaults(func=cmd_pinning)


def cmd_pinning(args: argparse.Namespace) -> None:
    report = scan_pinning(args.requirements)

    if args.format == "json":
        print(render_json(report))
    else:
        print(render_text(report))

    if args.strict and report.has_issues:
        sys.exit(1)
