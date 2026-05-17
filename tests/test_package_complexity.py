"""Tests for package_complexity and complexity_report modules."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from depwatch.package_complexity import (
    ComplexityInfo,
    ComplexityReport,
    _walk,
    fetch_complexity,
    scan_complexity,
)
from depwatch.complexity_report import (
    render_text,
    render_json,
    has_complexity_violations,
)


# ---------------------------------------------------------------------------
# ComplexityInfo unit tests
# ---------------------------------------------------------------------------

def test_total_deps_sum():
    info = ComplexityInfo(package="foo", direct_deps=3, transitive_deps=10, max_depth=2)
    assert info.total_deps == 13


def test_is_complex_by_total():
    info = ComplexityInfo(package="foo", direct_deps=5, transitive_deps=20, max_depth=2)
    assert info.is_complex  # total == 25 > 20


def test_is_complex_by_depth():
    info = ComplexityInfo(package="foo", direct_deps=1, transitive_deps=1, max_depth=6)
    assert info.is_complex


def test_not_complex_small_tree():
    info = ComplexityInfo(package="foo", direct_deps=2, transitive_deps=3, max_depth=2)
    assert not info.is_complex


# ---------------------------------------------------------------------------
# _walk helper
# ---------------------------------------------------------------------------

def test_walk_leaf_node():
    node = {"package_name": "leaf", "dependencies": []}
    trans, depth = _walk(node, depth=1)
    assert trans == 0
    assert depth == 1


def test_walk_nested():
    tree = {
        "package_name": "root",
        "dependencies": [
            {"package_name": "child", "dependencies": [
                {"package_name": "grandchild", "dependencies": []}
            ]}
        ],
    }
    trans, depth = _walk(tree, depth=0)
    assert trans == 2   # child + grandchild
    assert depth == 2


# ---------------------------------------------------------------------------
# fetch_complexity
# ---------------------------------------------------------------------------

_TREE = [
    {
        "package_name": "requests",
        "dependencies": [
            {"package_name": "urllib3", "dependencies": []},
            {"package_name": "certifi", "dependencies": [
                {"package_name": "ca-certs", "dependencies": []}
            ]},
        ],
    }
]


def test_fetch_complexity_known_package():
    with patch("depwatch.package_complexity._pipdeptree_json", return_value=_TREE):
        info = fetch_complexity("requests")
    assert info.package == "requests"
    assert info.direct_deps == 2
    assert info.transitive_deps == 1  # ca-certs under certifi
    assert info.max_depth == 2
    assert info.error is None


def test_fetch_complexity_unknown_package():
    with patch("depwatch.package_complexity._pipdeptree_json", return_value=_TREE):
        info = fetch_complexity("nonexistent")
    assert info.error == "package not found in tree"


def test_fetch_complexity_pipdeptree_unavailable():
    with patch("depwatch.package_complexity._pipdeptree_json", return_value=None):
        info = fetch_complexity("anything")
    assert "unavailable" in (info.error or "")


# ---------------------------------------------------------------------------
# scan_complexity + report rendering
# ---------------------------------------------------------------------------

def test_scan_complexity_returns_report():
    with patch("depwatch.package_complexity._pipdeptree_json", return_value=_TREE):
        report = scan_complexity(["requests"])
    assert len(report.packages) == 1
    assert report.packages[0].package == "requests"


def test_render_text_contains_package_name():
    report = ComplexityReport(packages=[
        ComplexityInfo(package="requests", direct_deps=2, transitive_deps=1, max_depth=2)
    ])
    text = render_text(report)
    assert "requests" in text


def test_render_text_flags_complex():
    report = ComplexityReport(packages=[
        ComplexityInfo(package="heavy", direct_deps=10, transitive_deps=50, max_depth=8)
    ])
    text = render_text(report)
    assert "COMPLEX" in text
    assert "WARNING" in text


def test_render_json_structure():
    report = ComplexityReport(packages=[
        ComplexityInfo(package="foo", direct_deps=1, transitive_deps=0, max_depth=1)
    ])
    data = json.loads(render_json(report))
    assert data["total"] == 1
    assert "packages" in data
    assert data["packages"][0]["package"] == "foo"


def test_has_complexity_violations_true():
    report = ComplexityReport(packages=[
        ComplexityInfo(package="heavy", direct_deps=10, transitive_deps=50, max_depth=8)
    ])
    assert has_complexity_violations(report)


def test_has_complexity_violations_false():
    report = ComplexityReport(packages=[
        ComplexityInfo(package="light", direct_deps=1, transitive_deps=1, max_depth=1)
    ])
    assert not has_complexity_violations(report)
