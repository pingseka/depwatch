"""Tests for depwatch.maintainer_report"""
from __future__ import annotations

import json

import pytest

from depwatch.package_maintainer import PackageMaintainerInfo
from depwatch.maintainer_report import (
    render_text,
    render_json,
    has_abandoned_packages,
)


@pytest.fixture()
def active_pkg() -> PackageMaintainerInfo:
    return PackageMaintainerInfo(
        name="active-lib",
        version="3.0.0",
        author="Bob",
        author_email="bob@example.com",
    )


@pytest.fixture()
def abandoned_pkg() -> PackageMaintainerInfo:
    return PackageMaintainerInfo(
        name="dead-lib",
        version="0.1.0",
        is_abandoned=True,
    )


def test_render_text_contains_package_names(active_pkg, abandoned_pkg):
    output = render_text([active_pkg, abandoned_pkg])
    assert "active-lib" in output
    assert "dead-lib" in output


def test_render_text_shows_abandoned_status(abandoned_pkg):
    output = render_text([abandoned_pkg])
    assert "ABANDONED" in output


def test_render_text_shows_ok_for_active(active_pkg):
    output = render_text([active_pkg])
    assert "ok" in output


def test_render_text_summary_counts(active_pkg, abandoned_pkg):
    output = render_text([active_pkg, abandoned_pkg])
    assert "Total: 2" in output
    assert "Abandoned: 1" in output


def test_render_json_valid(active_pkg, abandoned_pkg):
    raw = render_json([active_pkg, abandoned_pkg])
    records = json.loads(raw)
    assert len(records) == 2
    names = {r["name"] for r in records}
    assert "active-lib" in names
    assert "dead-lib" in names


def test_render_json_abandoned_flag(abandoned_pkg):
    records = json.loads(render_json([abandoned_pkg]))
    assert records[0]["is_abandoned"] is True


def test_has_abandoned_packages_true(active_pkg, abandoned_pkg):
    assert has_abandoned_packages([active_pkg, abandoned_pkg]) is True


def test_has_abandoned_packages_false(active_pkg):
    assert has_abandoned_packages([active_pkg]) is False


def test_has_abandoned_packages_empty():
    assert has_abandoned_packages([]) is False
