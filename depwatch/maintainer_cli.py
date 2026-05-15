"""CLI sub-command: depwatch maintainer"""
from __future__ import annotations

import argparse
import sys

from depwatch.package_maintainer import scan_maintainers
from depwatch.maintainer_report import render_text, render_json, has_abandoned_packages


def add_maintainer_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "maintainer",
        help="Check maintainer/ownership health for packages",
    )
    p.add_argument(
        "packages",
        nargs="+",
        metavar="PACKAGE",
        help="One or more PyPI package names to inspect",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail-on-abandoned",
        action="store_true",
        default=False,
        help="Exit with code 1 if any package appears abandoned",
    )
    p.set_defaults(func=cmd_maintainer)


def cmd_maintainer(args: argparse.Namespace) -> int:
    infos = scan_maintainers(args.packages)

    if args.fmt == "json":
        print(render_json(infos))
    else:
        print(render_text(infos))

    if args.fail_on_abandoned and has_abandoned_packages(infos):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    import argparse as _ap
    _parser = _ap.ArgumentParser()
    _subs = _parser.add_subparsers()
    add_maintainer_subparser(_subs)
    _args = _parser.parse_args()
    sys.exit(_args.func(_args))
