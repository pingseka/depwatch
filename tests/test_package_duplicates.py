"""Tests for depwatch.package_duplicates and depwatch.duplicates_report."""
import json
from pathlib import Path

import pytest

from depwatch.package_duplicates import scan_duplicates, DuplicateEntry
from depwatch.duplicates_report import render_text, render_json, has_duplicate_violations


@pytest.fixture
def req_file(tmp_path):
    def _write(content: str) -> str:
        p = tmp_path / "requirements.txt"
        p.write_text(content)
        return str(p)
    return _write


def test_no_duplicates_clean_file(req_file):
    path = req_file("requests==2.31.0\nflask==3.0.0\n")
    report = scan_duplicates(path)
    assert not report.has_issues
    assert report.duplicates == []


def test_exact_duplicate_detected(req_file):
    path = req_file("requests==2.31.0\nrequests==2.31.0\n")
    report = scan_duplicates(path)
    assert report.has_issues
    assert len(report.duplicates) == 1
    entry = report.duplicates[0]
    assert entry.name == "requests"
    assert not entry.is_conflicting  # same spec
    assert report.duplicate_count == 1
    assert report.conflict_count == 0


def test_conflicting_versions_detected(req_file):
    path = req_file("requests==2.28.0\nflask==3.0.0\nrequests>=2.31.0\n")
    report = scan_duplicates(path)
    assert report.has_issues
    assert report.conflict_count == 1
    entry = report.duplicates[0]
    assert entry.is_conflicting
    assert "==2.28.0" in entry.versions
    assert ">=2.31.0" in entry.versions


def test_line_numbers_recorded(req_file):
    path = req_file("flask==3.0.0\nrequests==2.28.0\nrequests==2.31.0\n")
    report = scan_duplicates(path)
    entry = report.duplicates[0]
    assert 2 in entry.lines
    assert 3 in entry.lines


def test_missing_file_returns_empty_report(tmp_path):
    path = str(tmp_path / "nonexistent.txt")
    report = scan_duplicates(path)
    assert not report.has_issues


def test_comments_and_blank_lines_ignored(req_file):
    content = "# this is a comment\n\nrequests==2.31.0\n"
    path = req_file(content)
    report = scan_duplicates(path)
    assert not report.has_issues


def test_render_text_no_issues(req_file):
    path = req_file("requests==2.31.0\n")
    report = scan_duplicates(path)
    text = render_text(report)
    assert "No duplicate" in text
    assert "0 issue" in text


def test_render_text_with_conflict(req_file):
    path = req_file("requests==2.28.0\nrequests>=2.31.0\n")
    report = scan_duplicates(path)
    text = render_text(report)
    assert "CONFLICT" in text
    assert "requests" in text


def test_render_json_structure(req_file):
    path = req_file("requests==2.28.0\nrequests>=2.31.0\n")
    report = scan_duplicates(path)
    data = json.loads(render_json(report))
    assert "duplicates" in data
    assert data["conflict_count"] == 1
    assert isinstance(data["duplicates"], list)
    assert data["duplicates"][0]["name"] == "requests"


def test_has_duplicate_violations_false_for_exact_dupe(req_file):
    path = req_file("requests==2.31.0\nrequests==2.31.0\n")
    report = scan_duplicates(path)
    assert not has_duplicate_violations(report)


def test_has_duplicate_violations_true_for_conflict(req_file):
    path = req_file("requests==2.28.0\nrequests>=2.31.0\n")
    report = scan_duplicates(path)
    assert has_duplicate_violations(report)


def test_entry_description_contains_tag():
    entry = DuplicateEntry(name="flask", versions=["==3.0.0", "==2.0.0"], lines=[1, 5])
    assert "CONFLICT" in entry.description
    entry2 = DuplicateEntry(name="flask", versions=["==3.0.0", "==3.0.0"], lines=[1, 5])
    assert "DUPLICATE" in entry2.description
