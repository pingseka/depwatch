"""CLI sub-command: depwatch size — report distribution sizes of packages."""
from __future__ import annotations

import argparse
import sys
from typing import List

from depwatch.package_size import scan_sizes, DEFAULT_SIZE_THRESHOLD
from depwatch.size_report import render_text, render_json, has_large_packages


def add_size_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "size",
        help="Report distribution sizes for packages.",
    )
    p.add_argument(
        "packages",
        nargs="+",
        metavar="PACKAGE",
        help="Package names to inspect.",
    )
    p.add_argument(
        "--threshold-mb",
        type=float,
        default=DEFAULT_SIZE_THRESHOLD / (1024 * 1024),
        metavar="MB",
        help="Flag packages whose total dist size exceeds this value (default: 10 MB).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--fail-on-large",
        action="store_true",
        default=False,
        help="Exit with code 1 if any large packages are found.",
    )
    p.set_defaults(func=cmd_size)


def cmd_size(args: argparse.Namespace) -> None:
    threshold_bytes = int(args.threshold_mb * 1024 * 1024)
    results = scan_sizes(args.packages, threshold_bytes=threshold_bytes)

    if args.output_format == "json":
        print(render_json(results))
    else:
        print(render_text(results), end="")

    if args.fail_on_large and has_large_packages(results):
        sys.exit(1)
