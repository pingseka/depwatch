"""Alert notification module for depwatch."""

import json
import logging
import smtplib
import urllib.request
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Optional

from depwatch.scanner import ScanResult

logger = logging.getLogger(__name__)


@dataclass
class NotifierConfig:
    method: str  # "log", "email", "webhook"
    webhook_url: Optional[str] = None
    email_to: Optional[str] = None
    email_from: Optional[str] = None
    smtp_host: str = "localhost"
    smtp_port: int = 25


def _format_message(result: ScanResult) -> str:
    lines = ["[depwatch] Dependency alert detected:", ""]
    if result.outdated:
        lines.append(f"  Outdated packages ({len(result.outdated)}):")
        for pkg in result.outdated:
            lines.append(f"    - {pkg.name}: {pkg.current_version} -> {pkg.latest_version}")
    if result.vulnerable:
        lines.append(f"  Vulnerable packages ({len(result.vulnerable)}):")
        for pkg in result.vulnerable:
            cves = ", ".join(pkg.vulnerabilities)
            lines.append(f"    - {pkg.name} {pkg.current_version} ({cves})")
    return "\n".join(lines)


def notify_log(result: ScanResult) -> None:
    msg = _format_message(result)
    logger.warning(msg)


def notify_webhook(result: ScanResult, url: str) -> None:
    payload = json.dumps({
        "outdated": [p.name for p in result.outdated],
        "vulnerable": [p.name for p in result.vulnerable],
        "summary": _format_message(result),
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        logger.info("Webhook notified, status: %s", resp.status)


def notify_email(result: ScanResult, cfg: NotifierConfig) -> None:
    msg = MIMEText(_format_message(result))
    msg["Subject"] = "[depwatch] Dependency Alert"
    msg["From"] = cfg.email_from or "depwatch@localhost"
    msg["To"] = cfg.email_to
    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
        server.sendmail(msg["From"], [cfg.email_to], msg.as_string())
    logger.info("Email alert sent to %s", cfg.email_to)


def send_alert(result: ScanResult, cfg: NotifierConfig) -> None:
    """Dispatch an alert based on the configured notification method."""
    if not result.has_issues:
        return
    if cfg.method == "email":
        notify_email(result, cfg)
    elif cfg.method == "webhook":
        if not cfg.webhook_url:
            raise ValueError("webhook_url must be set for webhook notifications")
        notify_webhook(result, cfg.webhook_url)
    else:
        notify_log(result)
