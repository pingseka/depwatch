"""Tests for depwatch.ownership_report."""
from __future__ import annotations

import json

import pytest

from depwatch.package_ownership import PackageOwnershipInfo
from depwatch.ownership_report import (
    render_text,
    render_json,
    has_ownership_violations,
)


@pytest.fixture()
def sole_pkg() -> PackageOwnershipInfo:
    return PackageOwnershipInfo(
        package="tiny",
        maintainers=["Alice"],
        maintainer_count=1,
        sole_maintainer=True,
    )


@pytest.fixture()
def multi_pkg() -> PackageOwnershipInfo:
    return PackageOwnershipInfo(
        package="big",
        maintainers=["Alice", "Bob"],
        maintainer_count=2,
        sole_maintainer=False,
    )


@pytest.fixture()
def error_pkg() -> PackageOwnershipInfo:
    return PackageOwnershipInfo(package="broken", error="timeout")


def test_render_text_contains_package_names(sole_pkg, multi_pkg):
    text = render_text([sole_pkg, multi_pkg])
    assert "tiny" in text
    assert "big" in text


def test_render_text_flags_sole_maintainer(sole_pkg):
    text = render_text([sole_pkg])
    assert "SOLE MAINTAINER" in text


def test_render_text_ok_for_multi(multi_pkg):
    text = render_text([multi_pkg])
    assert "[OK]" in text


def test_render_text_shows_error(error_pkg):
    text = render_text([error_pkg])
    assert "ERROR" in text
    assert "timeout" in text


def test_render_json_valid(sole_pkg, multi_pkg):
    out = render_json([sole_pkg, multi_pkg])
    data = json.loads(out)
    assert len(data) == 2
    packages = {d["package"] for d in data}
    assert "tiny" in packages and "big" in packages


def test_render_json_sole_maintainer_flag(sole_pkg):
    data = json.loads(render_json([sole_pkg]))
    assert data[0]["sole_maintainer"] is True


def test_has_ownership_violations_true(sole_pkg):
    assert has_ownership_violations([sole_pkg]) is True


def test_has_ownership_violations_false(multi_pkg):
    assert has_ownership_violations([multi_pkg]) is False


def test_has_ownership_violations_ignores_errors(error_pkg):
    assert has_ownership_violations([error_pkg]) is False
