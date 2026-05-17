"""CLI sub-command: depwatch complexity."""
from __future__ import annotations

import argparse
import sys

from depwatch.package_complexity import scan_complexity
from depwatch.complexity_report import render_text, render_json, has_complexity_violations


def add_complexity_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "complexity",
        help="Analyse dependency-tree complexity for listed packages.",
    )
    p.add_argument(
        "packages",
        nargs="+",
        metavar="PACKAGE",
        help="One or more package names to analyse.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--fail-on-complex",
        action="store_true",
        default=False,
        help="Exit with code 1 if any complex packages are found.",
    )
    p.set_defaults(func=cmd_complexity)


def cmd_complexity(args: argparse.Namespace) -> None:
    report = scan_complexity(args.packages)

    if args.fmt == "json":
        print(render_json(report))
    else:
        print(render_text(report))

    if args.fail_on_complex and has_complexity_violations(report):
        sys.exit(1)
