"""Context manager that owns the Playwright browser lifecycle."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from config.settings import settings
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from .logger import get_logger

log = get_logger(__name__)


@contextmanager
def browser_session() -> Iterator[Page]:
    """Yield a ready-to-use Page, guaranteeing clean teardown even on error."""
    log.info(
        f"Launching Chromium (headless={settings.headless}, "
        f"slow_mo={settings.slow_mo_ms}ms)"
    )
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(
            headless=settings.headless,
            slow_mo=settings.slow_mo_ms,
        )
        context: BrowserContext = browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent=(
                "Mozilla/5.0 (PriceWatch-RPA; +https://github.com/) "
                "Playwright/Chromium"
            ),
            locale="en-GB",
        )
        context.set_default_timeout(settings.nav_timeout_ms)
        page = context.new_page()
        try:
            yield page
        finally:
            log.info("Closing browser session")
            context.close()
            browser.close()
