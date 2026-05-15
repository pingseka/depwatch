"""Tests for depwatch.license_report"""

from __future__ import annotations

import json

import pytest

from depwatch.package_license import PackageLicenseInfo
from depwatch.license_report import render_text, render_json, has_policy_violations


@pytest.fixture()
def permissive_pkg() -> PackageLicenseInfo:
    return PackageLicenseInfo(
        name="requests", version="2.28.0", license="MIT",
        is_permissive=True, is_copyleft=False, is_unknown=False,
    )


@pytest.fixture()
def copyleft_pkg() -> PackageLicenseInfo:
    return PackageLicenseInfo(
        name="somepkg", version="1.0.0", license="GPL-3.0",
        is_permissive=False, is_copyleft=True, is_unknown=False,
    )


@pytest.fixture()
def unknown_pkg() -> PackageLicenseInfo:
    return PackageLicenseInfo(
        name="mypkg", version="0.1.0", license=None,
        is_permissive=False, is_copyleft=False, is_unknown=True,
    )


def test_render_text_contains_package_names(permissive_pkg, copyleft_pkg):
    out = render_text([permissive_pkg, copyleft_pkg])
    assert "requests" in out
    assert "somepkg" in out


def test_render_text_shows_tags(permissive_pkg, copyleft_pkg, unknown_pkg):
    out = render_text([permissive_pkg, copyleft_pkg, unknown_pkg])
    assert "permissive" in out
    assert "copyleft" in out
    assert "unknown" in out


def test_render_text_summary_counts(permissive_pkg, copyleft_pkg):
    out = render_text([permissive_pkg, copyleft_pkg])
    assert "Total: 2" in out
    assert "Copyleft: 1" in out


def test_render_json_valid(permissive_pkg, copyleft_pkg):
    raw = render_json([permissive_pkg, copyleft_pkg])
    data = json.loads(raw)
    assert len(data) == 2
    assert data[0]["name"] == "requests"
    assert data[1]["is_copyleft"] is True


def test_no_violation_all_permissive(permissive_pkg):
    assert has_policy_violations([permissive_pkg]) is False


def test_violation_copyleft_denied(copyleft_pkg):
    assert has_policy_violations([copyleft_pkg], allow_copyleft=False) is True


def test_no_violation_copyleft_allowed(copyleft_pkg):
    assert has_policy_violations([copyleft_pkg], allow_copyleft=True) is False


def test_violation_unknown_denied(unknown_pkg):
    assert has_policy_violations([unknown_pkg], allow_unknown=False) is True
