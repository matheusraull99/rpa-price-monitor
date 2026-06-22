"""High-level orchestration: wire the browser, scraper, report and notifier."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from config.settings import settings

from .core.browser import browser_session
from .core.logger import get_logger
from .services.history import HistoryStore
from .services.notifier import Notifier
from .services.report import ReportBuilder
from .services.scraper import Scraper

log = get_logger(__name__)


class PriceWatchBot:
    """The RPA process, expressed as a single readable workflow."""

    def __init__(self) -> None:
        settings.ensure_dirs()
        self.report_builder = ReportBuilder(settings.output_dir)
        self.notifier = Notifier()

    def run(self, max_pages: int | None = None) -> Path:
        max_pages = max_pages or settings.max_pages
        started = datetime.now()
        log.info(f"=== PriceWatch RPA started (target: {settings.base_url}) ===")

        with browser_session() as page:
            try:
                products = Scraper(page).collect(max_pages)
            except Exception:
                self._capture_failure(page)
                raise

        if not products:
            log.warning("No products collected — skipping report generation.")
            raise RuntimeError("Run produced zero products.")

        with HistoryStore(settings.db_path) as history:
            changes = history.diff_and_record(products)

        report_path = self.report_builder.build(products, changes)
        self.notifier.notify(len(products), report_path)

        elapsed = (datetime.now() - started).total_seconds()
        log.success(f"=== Finished in {elapsed:.1f}s ===")
        return report_path

    def _capture_failure(self, page) -> None:
        """Save a screenshot for post-mortem debugging — a hallmark of good RPA."""
        try:
            shot = settings.logs_dir / f"failure_{datetime.now():%Y%m%d_%H%M%S}.png"
            page.screenshot(path=str(shot), full_page=True)
            log.error(f"Failure screenshot saved -> {shot}")
        except Exception as exc:
            log.error(f"Could not capture failure screenshot: {exc}")
