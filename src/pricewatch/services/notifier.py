"""Sends a run summary to the console and, optionally, a chat webhook."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from config.settings import settings

from ..core.logger import get_logger

log = get_logger(__name__)


class Notifier:
    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or settings.webhook_url

    def notify(self, count: int, report_path: Path) -> None:
        message = (
            f"✅ PriceWatch RPA finished — {count} products captured.\n"
            f"Report: {report_path.name}"
        )
        log.info(message.replace("\n", " | "))
        if self.webhook_url:
            self._post(message)

    def _post(self, text: str) -> None:
        try:
            payload = json.dumps({"text": text}).encode()
            req = urllib.request.Request(
                self.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                log.info(f"Webhook delivered (HTTP {resp.status})")
        except Exception as exc:  # never let a notification failure break the run
            log.warning(f"Webhook delivery failed: {exc}")
