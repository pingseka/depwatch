"""File watcher that monitors dependency files and triggers scans on change."""

import hashlib
import logging
import time
from pathlib import Path
from typing import Callable, Optional

from depwatch.scanner import ScanResult, scan_file

logger = logging.getLogger(__name__)


def _file_hash(filepath: str) -> Optional[str]:
    """Return MD5 hash of file contents, or None if file is unreadable."""
    try:
        data = Path(filepath).read_bytes()
        return hashlib.md5(data).hexdigest()
    except OSError:
        return None


class DependencyWatcher:
    """Monitors a list of dependency files and invokes a callback on changes."""

    def __init__(
        self,
        dep_files: list[str],
        on_change: Callable[[ScanResult], None],
        poll_interval: int = 60,
    ) -> None:
        self.dep_files = dep_files
        self.on_change = on_change
        self.poll_interval = poll_interval
        self._hashes: dict[str, Optional[str]] = {}
        self._running = False

    def _has_changed(self, filepath: str) -> bool:
        current = _file_hash(filepath)
        previous = self._hashes.get(filepath)
        if current != previous:
            self._hashes[filepath] = current
            return True
        return False

    def check_once(self) -> list[ScanResult]:
        """Perform a single check pass over all monitored files."""
        results = []
        for filepath in self.dep_files:
            if self._has_changed(filepath):
                logger.info("Change detected in %s — scanning.", filepath)
                result = scan_file(filepath)
                self.on_change(result)
                results.append(result)
        return results

    def start(self) -> None:
        """Start the polling loop (blocking)."""
        self._running = True
        logger.info(
            "Watching %d file(s) every %ds.", len(self.dep_files), self.poll_interval
        )
        # Seed initial hashes without triggering callbacks.
        for filepath in self.dep_files:
            self._hashes[filepath] = _file_hash(filepath)

        while self._running:
            self.check_once()
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        """Signal the polling loop to stop."""
        self._running = False
        logger.info("Watcher stopped.")
