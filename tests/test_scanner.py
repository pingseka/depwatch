"""Tests for depwatch.scanner module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from depwatch.scanner import PackageInfo, ScanResult, scan_file, scan_requirements_txt


REQUIREMENTS_CONTENT = """# sample requirements
requests==2.28.0
flask==2.2.0
numpy==1.24.0
"""

OUTDATED_JSON = json.dumps([
    {"name": "requests", "version": "2.28.0", "latest_version": "2.31.0"},
])


@pytest.fixture
def requirements_file(tmp_path: Path) -> Path:
    req = tmp_path / "requirements.txt"
    req.write_text(REQUIREMENTS_CONTENT)
    return req


def test_package_info_outdated():
    pkg = PackageInfo(name="requests", current_version="2.28.0", latest_version="2.31.0")
    assert pkg.is_outdated is True


def test_package_info_up_to_date():
    pkg = PackageInfo(name="flask", current_version="2.2.0", latest_version="2.2.0")
    assert pkg.is_outdated is False


def test_package_info_vulnerable():
    pkg = PackageInfo(name="numpy", current_version="1.24.0", vulnerabilities=["CVE-2023-1234"])
    assert pkg.is_vulnerable is True


def test_scan_result_filters():
    packages = [
        PackageInfo("a", "1.0", latest_version="2.0"),
        PackageInfo("b", "1.0", latest_version="1.0"),
        PackageInfo("c", "1.0", vulnerabilities=["CVE-XYZ"]),
    ]
    result = ScanResult(dep_file="requirements.txt", packages=packages)
    assert len(result.outdated) == 1
    assert result.outdated[0].name == "a"
    assert len(result.vulnerable) == 1
    assert result.vulnerable[0].name == "c"


@patch("depwatch.scanner.subprocess.run")
def test_scan_requirements_txt_success(mock_run, requirements_file):
    mock_run.return_value = MagicMock(stdout=OUTDATED_JSON, returncode=0)
    result = scan_requirements_txt(str(requirements_file))

    assert result.errors == []
    assert len(result.packages) == 3
    outdated = result.outdated
    assert len(outdated) == 1
    assert outdated[0].name == "requests"
    assert outdated[0].latest_version == "2.31.0"


def test_scan_requirements_txt_missing_file(tmp_path):
    result = scan_requirements_txt(str(tmp_path / "nonexistent.txt"))
    assert len(result.errors) == 1
    assert "not found" in result.errors[0]


def test_scan_file_unsupported():
    result = scan_file("package.json")
    assert len(result.errors) == 1
    assert "Unsupported" in result.errors[0]


@patch("depwatch.scanner.subprocess.run")
def test_scan_file_dispatches_requirements(mock_run, requirements_file):
    mock_run.return_value = MagicMock(stdout="[]", returncode=0)
    result = scan_file(str(requirements_file))
    assert result.dep_file == str(requirements_file)
