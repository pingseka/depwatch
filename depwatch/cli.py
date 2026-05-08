"""Command-line interface for depwatch."""

import argparse
import sys
import threading

from depwatch.config import load_config
from depwatch.scheduler import Scheduler
from depwatch.scanner import scan
from depwatch.reporter import render_text, render_json, render_csv
from depwatch.report_writer import write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="depwatch",
        description="Monitor dependency files for outdated or vulnerable packages.",
    )
    parser.add_argument(
        "-c", "--config", default="depwatch/config_example.json",
        help="Path to configuration file (default: depwatch/config_example.json)",
    )
    subparsers = parser.add_subparsers(dest="command")

    # 'run' subcommand — start the daemon
    run_parser = subparsers.add_parser("run", help="Start the depwatch daemon")
    run_parser.add_argument(
        "--once", action="store_true",
        help="Scan once and exit instead of running continuously",
    )

    # 'scan' subcommand — one-shot scan with optional report output
    scan_parser = subparsers.add_parser("scan", help="Run a one-shot scan and print results")
    scan_parser.add_argument(
        "--format", choices=["text", "json", "csv"], default="text",
        help="Output format (default: text)",
    )
    scan_parser.add_argument(
        "--out", default=None,
        help="Write report to this file path instead of stdout",
    )

    return parser


def cmd_run(args) -> int:
    config = load_config(args.config)
    stop_event = threading.Event()
    scheduler = Scheduler(config, stop_event)
    if args.once:
        scheduler.run_once()
    else:
        try:
            scheduler.run()
        except KeyboardInterrupt:
            stop_event.set()
    return 0


def cmd_scan(args) -> int:
    config = load_config(args.config)
    results = {}
    for dep_file in config.dependency_files:
        result = scan(dep_file)
        results[dep_file] = result

    for dep_file, result in results.items():
        if args.format == "json":
            output = render_json(result)
        elif args.format == "csv":
            output = render_csv(result)
        else:
            output = render_text(result)

        if args.out:
            write_report(args.out, output)
        else:
            print(output)
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return cmd_run(args)
    elif args.command == "scan":
        return cmd_scan(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
