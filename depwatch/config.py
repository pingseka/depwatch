"""Configuration loader for depwatch daemon."""

import os
import json
from dataclasses import dataclass, field
from typing import List, Optional


DEFAULT_CONFIG_PATH = os.path.expanduser("~/.depwatch/config.json")
DEFAULT_CHECK_INTERVAL = 3600  # seconds


@dataclass
class DepwatchConfig:
    watch_paths: List[str] = field(default_factory=list)
    check_interval: int = DEFAULT_CHECK_INTERVAL
    alert_email: Optional[str] = None
    alert_webhook: Optional[str] = None
    ignore_packages: List[str] = field(default_factory=list)
    severity_threshold: str = "low"  # low, medium, high, critical

    def validate(self) -> None:
        valid_severities = {"low", "medium", "high", "critical"}
        if self.severity_threshold not in valid_severities:
            raise ValueError(
                f"Invalid severity_threshold '{self.severity_threshold}'. "
                f"Must be one of: {', '.join(sorted(valid_severities))}"
            )
        if self.check_interval < 60:
            raise ValueError("check_interval must be at least 60 seconds.")
        if not self.watch_paths:
            raise ValueError("At least one watch_path must be specified.")


def load_config(path: str = DEFAULT_CONFIG_PATH) -> DepwatchConfig:
    """Load configuration from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    config = DepwatchConfig(
        watch_paths=raw.get("watch_paths", []),
        check_interval=raw.get("check_interval", DEFAULT_CHECK_INTERVAL),
        alert_email=raw.get("alert_email"),
        alert_webhook=raw.get("alert_webhook"),
        ignore_packages=raw.get("ignore_packages", []),
        severity_threshold=raw.get("severity_threshold", "low"),
    )
    config.validate()
    return config
