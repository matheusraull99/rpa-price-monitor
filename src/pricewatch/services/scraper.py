"""Orchestrates pagination across the catalogue and collects products."""
from __future__ import annotations

from config.settings import settings
from playwright.sync_api import Page

from ..core.logger import get_logger
from ..models.product import Product
from ..pages.catalog_page import CatalogPage

log = get_logger(__name__)


class Scraper:
    def __init__(self, page: Page) -> None:
        self.catalog = CatalogPage(page, settings.base_url)

    def collect(self, max_pages: int) -> list[Product]:
        """Walk up to `max_pages` listing pages, stopping early if none left."""
        all_products: list[Product] = []
        for page_no in range(1, max_pages + 1):
            log.info(f"Scraping catalogue page {page_no}/{max_pages}")
            self.catalog.open_page(page_no)
            batch = self.catalog.parse_products()
            log.info(f"  -> {len(batch)} products extracted")
            all_products.extend(batch)
            if not self.catalog.has_next():
                log.info("No further pages; finishing crawl early.")
                break
        log.success(f"Collected {len(all_products)} products in total")
        return all_products
