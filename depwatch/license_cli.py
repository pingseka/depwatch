"""CLI sub-command: depwatch license"""

from __future__ import annotations

import argparse
import sys
from typing import List

from depwatch.package_license import scan_licenses
from depwatch.license_report import render_text, render_json, has_policy_violations


def add_license_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("license", help="Check licenses of listed packages")
    p.add_argument(
        "packages",
        nargs="+",
        metavar="PACKAGE",
        help="Package names to inspect (e.g. requests flask)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--deny-copyleft",
        action="store_true",
        default=False,
        help="Exit with code 1 if any copyleft license is found",
    )
    p.add_argument(
        "--deny-unknown",
        action="store_true",
        default=False,
        help="Exit with code 1 if any unknown license is found",
    )
    p.set_defaults(func=cmd_license)


def cmd_license(args: argparse.Namespace) -> int:
    results = scan_licenses(args.packages)

    if args.fmt == "json":
        print(render_json(results))
    else:
        print(render_text(results))

    violated = has_policy_violations(
        results,
        allow_copyleft=not args.deny_copyleft,
        allow_unknown=not args.deny_unknown,
    )
    return 1 if violated else 0
