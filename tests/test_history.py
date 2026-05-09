"""Tests for depwatch.history module."""

import json
import pytest
from pathlib import Path

from depwatch.history import (
    append_entry,
    clear_history,
    last_entry,
    load_history,
    _MAX_ENTRIES,
)


@pytest.fixture
def history_file(tmp_path):
    return str(tmp_path / "test_history.json")


def test_load_history_missing_file(history_file):
    result = load_history(history_file)
    assert result == []


def test_load_history_invalid_json(history_file):
    Path(history_file).write_text("not valid json", encoding="utf-8")
    result = load_history(history_file)
    assert result == []


def test_append_entry_creates_file(history_file):
    entry = append_entry(
        dep_file="requirements.txt",
        outdated_count=2,
        vulnerable_count=1,
        packages=["requests", "flask"],
        path=history_file,
    )
    assert Path(history_file).exists()
    assert entry["outdated_count"] == 2
    assert entry["vulnerable_count"] == 1
    assert "timestamp" in entry
    assert entry["dep_file"] == "requirements.txt"


def test_append_entry_accumulates(history_file):
    for i in range(3):
        append_entry(
            dep_file="requirements.txt",
            outdated_count=i,
            vulnerable_count=0,
            packages=[],
            path=history_file,
        )
    history = load_history(history_file)
    assert len(history) == 3


def test_append_entry_respects_max_entries(history_file):
    for i in range(_MAX_ENTRIES + 10):
        append_entry(
            dep_file="requirements.txt",
            outdated_count=i,
            vulnerable_count=0,
            packages=[],
            path=history_file,
        )
    history = load_history(history_file)
    assert len(history) == _MAX_ENTRIES


def test_last_entry_returns_most_recent(history_file):
    append_entry("req.txt", 1, 0, ["a"], path=history_file)
    append_entry("req.txt", 3, 2, ["b", "c"], path=history_file)
    entry = last_entry("req.txt", path=history_file)
    assert entry is not None
    assert entry["outdated_count"] == 3


def test_last_entry_filters_by_dep_file(history_file):
    append_entry("req.txt", 1, 0, [], path=history_file)
    append_entry("setup.cfg", 5, 3, ["x"], path=history_file)
    entry = last_entry("req.txt", path=history_file)
    assert entry is not None
    assert entry["dep_file"] == "req.txt"


def test_last_entry_none_when_no_match(history_file):
    append_entry("setup.cfg", 0, 0, [], path=history_file)
    assert last_entry("missing.txt", path=history_file) is None


def test_clear_history(history_file):
    append_entry("req.txt", 1, 0, [], path=history_file)
    clear_history(history_file)
    assert not Path(history_file).exists()


def test_clear_history_noop_if_missing(history_file):
    # Should not raise even if file doesn't exist
    clear_history(history_file)
