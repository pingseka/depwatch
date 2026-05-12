"""CLI sub-commands for digest inspection and management."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from depwatch.digest_store import load_store, remove_digest


def add_digest_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *digest* sub-command group."""
    parser = subparsers.add_parser(
        "digest",
        help="Inspect or manage stored scan digests.",
    )
    sub = parser.add_subparsers(dest="digest_cmd", required=True)

    # digest list
    list_p = sub.add_parser("list", help="List all stored digests.")
    list_p.add_argument(
        "--store",
        default=None,
        metavar="PATH",
        help="Path to digest store file (default: ~/.depwatch/digests.json).",
    )
    list_p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output as JSON.",
    )

    # digest remove
    rm_p = sub.add_parser("remove", help="Remove a stored digest entry.")
    rm_p.add_argument("dep_file", help="Dependency file whose digest to remove.")
    rm_p.add_argument(
        "--store",
        default=None,
        metavar="PATH",
    )

    parser.set_defaults(func=cmd_digest)


def cmd_digest(args: argparse.Namespace) -> int:
    """Dispatch digest sub-commands."""
    if args.digest_cmd == "list":
        return _cmd_list(args)
    if args.digest_cmd == "remove":
        return _cmd_remove(args)
    print(f"Unknown digest sub-command: {args.digest_cmd}", file=sys.stderr)
    return 1


def _cmd_list(args: argparse.Namespace) -> int:
    store = load_store(args.store)
    if not store:
        print("No digests stored.")
        return 0
    if getattr(args, "as_json", False):
        print(json.dumps(store, indent=2))
    else:
        for dep_file, digest in sorted(store.items()):
            print(f"{dep_file}: {digest}")
    return 0


def _cmd_remove(args: argparse.Namespace) -> int:
    remove_digest(args.dep_file, path=args.store)
    print(f"Removed digest for '{args.dep_file}'.")
    return 0
