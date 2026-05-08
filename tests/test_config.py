"""Tests for depwatch configuration loader."""

import json
import os
import pytest
from depwatch.config import DepwatchConfig, load_config


@pytest.fixture
def config_file(tmp_path):
    """Write a minimal valid config JSON and return its path."""
    data = {
        "watch_paths": ["/project/requirements.txt"],
        "check_interval": 600,
        "alert_email": "dev@example.com",
        "severity_threshold": "medium",
    }
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(data))
    return str(cfg)


def test_load_config_success(config_file):
    config = load_config(config_file)
    assert config.watch_paths == ["/project/requirements.txt"]
    assert config.check_interval == 600
    assert config.alert_email == "dev@example.com"
    assert config.severity_threshold == "medium"
    assert config.ignore_packages == []
    assert config.alert_webhook is None


def test_load_config_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "nonexistent.json"))


def test_validate_invalid_severity():
    cfg = DepwatchConfig(watch_paths=["/some/path"], severity_threshold="extreme")
    with pytest.raises(ValueError, match="Invalid severity_threshold"):
        cfg.validate()


def test_validate_interval_too_low():
    cfg = DepwatchConfig(watch_paths=["/some/path"], check_interval=30)
    with pytest.raises(ValueError, match="check_interval"):
        cfg.validate()


def test_validate_no_watch_paths():
    cfg = DepwatchConfig(watch_paths=[])
    with pytest.raises(ValueError, match="watch_path"):
        cfg.validate()


def test_defaults_are_valid():
    cfg = DepwatchConfig(watch_paths=["/app/requirements.txt"])
    cfg.validate()  # should not raise
    assert cfg.check_interval == 3600
    assert cfg.severity_threshold == "low"
