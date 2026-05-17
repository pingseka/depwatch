"""Tests for depwatch.package_transitive."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from depwatch.package_transitive import (
    TransitiveDep,
    TransitiveReport,
    scan_transitive,
    _run_pipdeptree,
)


PIPDEPTREE_OUTPUT = [
    {
        "package": {"package_name": "requests", "installed_version": "2.31.0"},
        "dependencies": [
            {"package_name": "urllib3", "required_version": ">=1.21", "installed_version": "2.0.7"},
            {"package_name": "certifi", "required_version": ">=2017.4.17", "installed_version": "2024.2.2"},
        ],
    },
    {
        "package": {"package_name": "urllib3", "installed_version": "2.0.7"},
        "dependencies": [],
    },
    {
        "package": {"package_name": "certifi", "installed_version": "2024.2.2"},
        "dependencies": [],
    },
]


def _mock_subprocess(output: list):
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = json.dumps(output)
    return mock


# ---------------------------------------------------------------------------
# TransitiveDep
# ---------------------------------------------------------------------------

def test_transitive_dep_is_direct_when_no_required_by():
    dep = TransitiveDep(name="requests", version="2.31.0")
    assert dep.is_direct is True


def test_transitive_dep_is_not_direct_when_required_by_set():
    dep = TransitiveDep(name="urllib3", version="2.0.7", required_by=["requests"])
    assert dep.is_direct is False


# ---------------------------------------------------------------------------
# TransitiveReport
# ---------------------------------------------------------------------------

def test_report_has_transitive_true():
    report = TransitiveReport(
        direct=[TransitiveDep("requests", "2.31.0")],
        transitive=[TransitiveDep("urllib3", "2.0.7", required_by=["requests"])],
    )
    assert report.has_transitive is True


def test_report_has_transitive_false_when_empty():
    report = TransitiveReport(direct=[TransitiveDep("requests", "2.31.0")])
    assert report.has_transitive is False


def test_report_all_packages_combines_both():
    d = TransitiveDep("requests", "2.31.0")
    t = TransitiveDep("urllib3", "2.0.7", required_by=["requests"])
    report = TransitiveReport(direct=[d], transitive=[t])
    assert len(report.all_packages) == 2


# ---------------------------------------------------------------------------
# scan_transitive
# ---------------------------------------------------------------------------

def test_scan_transitive_classifies_direct_and_indirect():
    with patch("depwatch.package_transitive.subprocess.run",
               return_value=_mock_subprocess(PIPDEPTREE_OUTPUT)):
        report = scan_transitive(["requests"])

    direct_names = {d.name for d in report.direct}
    transitive_names = {d.name for d in report.transitive}

    assert "requests" in direct_names
    assert "urllib3" in transitive_names
    assert "certifi" in transitive_names


def test_scan_transitive_fallback_on_pipdeptree_failure():
    with patch("depwatch.package_transitive.subprocess.run",
               side_effect=FileNotFoundError):
        report = scan_transitive(["requests", "flask"])

    # Fallback returns direct entries only
    assert report.has_transitive is False
    direct_names = {d.name for d in report.direct}
    assert "requests" in direct_names
    assert "flask" in direct_names


def test_scan_transitive_nonzero_returncode_triggers_fallback():
    mock = MagicMock()
    mock.returncode = 1
    mock.stdout = ""
    with patch("depwatch.package_transitive.subprocess.run", return_value=mock):
        report = scan_transitive(["numpy"])

    assert len(report.direct) == 1
    assert report.direct[0].name == "numpy"


def test_scan_transitive_required_by_populated():
    with patch("depwatch.package_transitive.subprocess.run",
               return_value=_mock_subprocess(PIPDEPTREE_OUTPUT)):
        report = scan_transitive(["requests"])

    urllib3 = next((d for d in report.transitive if d.name == "urllib3"), None)
    assert urllib3 is not None
    assert "requests" in urllib3.required_by
