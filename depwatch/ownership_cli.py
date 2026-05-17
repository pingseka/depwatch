"""CLI sub-command for package ownership analysis."""
from __future__ import annotations

import argparse
import sys
from typing import List

from depwatch.package_ownership import scan_ownership
from depwatch.ownership_report import render_text, render_json, has_ownership_violations


def add_ownership_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "ownership",
        help="Check PyPI package ownership and flag sole-maintainer packages.",
    )
    p.add_argument("packages", nargs="+", help="Package names to inspect")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail-on-violations",
        action="store_true",
        help="Exit with code 1 if sole-maintainer packages are found",
    )
    p.set_defaults(func=cmd_ownership)


def cmd_ownership(args: argparse.Namespace) -> None:
    results = scan_ownership(args.packages)
    if args.format == "json":
        print(render_json(results))
    else:
        print(render_text(results))
    if args.fail_on_violations and has_ownership_violations(results):
        sys.exit(1)
