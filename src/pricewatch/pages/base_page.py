"""Base class shared by all page objects."""
from __future__ import annotations

from playwright.sync_api import Page

from ..core.logger import get_logger

log = get_logger(__name__)


class BasePage:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    def goto(self, path: str = "") -> None:
        url = f"{self.base_url}/{path.lstrip('/')}" if path else self.base_url
        log.debug(f"Navigating to {url}")
        self.page.goto(url, wait_until="domcontentloaded")
