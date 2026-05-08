"""Write depwatch reports to files or stdout."""

from __future__ import annotations

import sys
from pathlib import Path

from depwatch.scanner import ScanResult
from depwatch.reporter import ReportFormat, generate_report


def write_report(
    result: ScanResult,
    fmt: ReportFormat = "text",
    output_path: str | None = None,
) -> None:
    """Generate a report and write it to *output_path* or stdout.

    Args:
        result: The scan result to report on.
        fmt: Output format — ``"text"``, ``"json"``, or ``"csv"``.
        output_path: Destination file path.  ``None`` means stdout.
    """
    content = generate_report(result, fmt)

    if output_path is None:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")
        return

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    mode = "w"
    encoding = "utf-8"
    dest.write_text(content, encoding=encoding)


def report_path_for_file(
    dependency_file: str,
    fmt: ReportFormat = "text",
    reports_dir: str = "reports",
) -> str:
    """Return a suggested report file path based on the dependency file name."""
    stem = Path(dependency_file).stem
    extension = {"text": "txt", "json": "json", "csv": "csv"}.get(fmt, "txt")
    return str(Path(reports_dir) / f"{stem}_report.{extension}")
