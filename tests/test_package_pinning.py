"""Tests for package_pinning and pinning_report modules."""

from __future__ import annotations

import json
import textwrap

import pytest

from depwatch.package_pinning import PinningIssue, PinningReport, scan_pinning
from depwatch.pinning_report import (
    has_pinning_violations,
    render_json,
    render_text,
)


@pytest.fixture
def req_file(tmp_path):
    def _write(content: str):
        p = tmp_path / "requirements.txt"
        p.write_text(textwrap.dedent(content))
        return str(p)

    return _write


def test_scan_pinning_exact_pins_no_issues(req_file):
    path = req_file("""
        requests==2.31.0
        flask==3.0.0
    """)
    report = scan_pinning(path)
    assert not report.has_issues


def test_scan_pinning_detects_unpinned(req_file):
    path = req_file("""
        requests
        flask==3.0.0
    """)
    report = scan_pinning(path)
    assert len(report.unpinned) == 1
    assert report.unpinned[0].package == "requests"


def test_scan_pinning_detects_loose(req_file):
    path = req_file("""
        requests>=2.0
        flask==3.0.0
    """)
    report = scan_pinning(path)
    assert len(report.loose) == 1
    assert report.loose[0].package == "requests"
    assert report.loose[0].kind == "loose"


def test_scan_pinning_ignores_comments_and_blank_lines(req_file):
    path = req_file("""
        # this is a comment

        flask==3.0.0
    """)
    report = scan_pinning(path)
    assert not report.has_issues


def test_scan_pinning_missing_file(tmp_path):
    report = scan_pinning(str(tmp_path / "nonexistent.txt"))
    assert not report.has_issues


def test_render_text_all_pinned(req_file):
    path = req_file("requests==2.31.0\n")
    report = scan_pinning(path)
    text = render_text(report)
    assert "All packages are exactly pinned" in text


def test_render_text_shows_issues(req_file):
    path = req_file("requests\nflask>=2.0\n")
    report = scan_pinning(path)
    text = render_text(report)
    assert "UNPINNED" in text
    assert "LOOSE" in text
    assert "requests" in text
    assert "flask" in text


def test_render_json_structure(req_file):
    path = req_file("requests\nflask==3.0.0\n")
    report = scan_pinning(path)
    data = json.loads(render_json(report))
    assert data["total_issues"] == 1
    assert data["unpinned"] == 1
    assert data["loose"] == 0
    assert data["issues"][0]["package"] == "requests"


def test_has_pinning_violations_true(req_file):
    path = req_file("requests\n")
    report = scan_pinning(path)
    assert has_pinning_violations(report) is True


def test_has_pinning_violations_false(req_file):
    path = req_file("requests==2.31.0\n")
    report = scan_pinning(path)
    assert has_pinning_violations(report) is False


def test_pinning_issue_description_unpinned():
    issue = PinningIssue(package="boto3", specifier="", kind="unpinned")
    assert "unpinned" in issue.description
    assert "boto3" in issue.description


def test_pinning_issue_description_loose():
    issue = PinningIssue(package="boto3", specifier=">=1.0", kind="loose")
    assert ">=1.0" in issue.description
    assert "boto3" in issue.description
