"""CLI sub-commands for the audit trail feature."""
from __future__ import annotations

import argparse
import sys

from depwatch.audit_report import has_alerts, render_json, render_text, summary_stats
from depwatch.package_audit_trail import clear_audit_trail, load_audit_trail


def add_audit_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("audit", help="View or manage the scan audit trail")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--audit-file",
        default=None,
        metavar="PATH",
        help="Path to audit trail file (default: ~/.depwatch/audit_trail.jsonl)",
    )
    p.add_argument(
        "--stats",
        action="store_true",
        help="Print summary statistics instead of individual entries",
    )
    p.add_argument(
        "--clear",
        action="store_true",
        help="Delete all audit trail entries",
    )
    p.set_defaults(func=cmd_audit)


def cmd_audit(args: argparse.Namespace) -> int:
    if args.clear:
        clear_audit_trail(audit_file=args.audit_file)
        print("Audit trail cleared.")
        return 0

    entries = load_audit_trail(audit_file=args.audit_file)

    if args.stats:
        stats = summary_stats(entries)
        if args.format == "json":
            import json
            print(json.dumps(stats, indent=2))
        else:
            for k, v in stats.items():
                print(f"{k}: {v}")
        return 0

    if args.format == "json":
        print(render_json(entries))
    else:
        print(render_text(entries))

    return 1 if has_alerts(entries) else 0
