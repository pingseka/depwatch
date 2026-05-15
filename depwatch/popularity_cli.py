"""CLI sub-command: depwatch popularity."""
from __future__ import annotations

import argparse
import sys

from depwatch.package_popularity import scan_popularity
from depwatch.popularity_report import render_text, render_json, has_low_popularity


def add_popularity_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "popularity",
        help="Check download popularity of packages.",
    )
    p.add_argument(
        "packages",
        nargs="+",
        metavar="PACKAGE",
        help="One or more package names to check.",
    )
    p.add_argument(
        "--threshold",
        type=int,
        default=1000,
        metavar="N",
        help="Monthly download count below which a package is considered low-popularity (default: 1000).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--fail-on-low",
        action="store_true",
        default=False,
        help="Exit with code 1 if any low-popularity package is found.",
    )
    p.set_defaults(func=cmd_popularity)


def cmd_popularity(args: argparse.Namespace) -> int:
    infos = scan_popularity(args.packages, low_threshold=args.threshold)

    if args.fmt == "json":
        print(render_json(infos))
    else:
        print(render_text(infos))

    if args.fail_on_low and has_low_popularity(infos):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(prog="depwatch-popularity")
    subs = parser.add_subparsers()
    add_popularity_subparser(subs)
    parsed = parser.parse_args()
    sys.exit(cmd_popularity(parsed))
