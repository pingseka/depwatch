"""Scheduler module: runs periodic dependency scans and dispatches notifications."""

import logging
import time
from pathlib import Path
from typing import Callable, Optional

from depwatch.config import DepwatchConfig
from depwatch.notifier import NotifierConfig, notify_log, notify_webhook, notify_email
from depwatch.reporter import render_text
from depwatch.report_writer import write_report
from depwatch.scanner import scan
from depwatch.watcher import DependencyWatcher

logger = logging.getLogger(__name__)


class Scheduler:
    """Periodically watches dependency files and triggers scans + notifications."""

    def __init__(
        self,
        config: DepwatchConfig,
        stop_event: Optional[Callable[[], bool]] = None,
    ) -> None:
        self.config = config
        self._stop = stop_event or (lambda: False)
        self._watchers: dict[str, DependencyWatcher] = {
            path: DependencyWatcher(path) for path in config.watch_paths
        }
        self._notifier_cfg = NotifierConfig(
            min_severity=config.min_severity,
            webhook_url=config.webhook_url,
            email_to=config.email_to,
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
        )

    def run_once(self) -> None:
        """Check all watched files; scan and notify if any have changed."""
        for path, watcher in self._watchers.items():
            if watcher.check_once():
                logger.info("Change detected in %s — running scan.", path)
                self._scan_and_notify(path)
            else:
                logger.debug("No change in %s.", path)

    def run(self) -> None:
        """Block and run scans on the configured interval until stopped."""
        logger.info(
            "Scheduler started. Interval=%ds, watching %d file(s).",
            self.config.interval,
            len(self._watchers),
        )
        while not self._stop():
            self.run_once()
            time.sleep(self.config.interval)
        logger.info("Scheduler stopped.")

    def _scan_and_notify(self, path: str) -> None:
        result = scan(Path(path))
        if self.config.report_dir:
            write_report(result, path, self.config.report_dir, fmt=self.config.report_format)
        notify_log(result, self.config.min_severity)
        if self.config.webhook_url:
            notify_webhook(result, self._notifier_cfg)
        if self.config.email_to:
            notify_email(result, self._notifier_cfg)
