"""Page object encapsulating the catalogue listing and its locators."""
from __future__ import annotations

from playwright.sync_api import Locator

from ..core.logger import get_logger
from ..core.retry import resilient
from ..core.utils import parse_price, rating_to_int
from ..models.product import Product
from .base_page import BasePage

log = get_logger(__name__)


class CatalogPage(BasePage):
    """All knowledge about *where* things are on the page lives here."""

    PRODUCT_CARD = "article.product_pod"
    NEXT_BUTTON = "li.next > a"

    @resilient
    def open_page(self, page_number: int) -> None:
        self.goto(f"catalogue/page-{page_number}.html")
        self.page.wait_for_selector(self.PRODUCT_CARD)

    def has_next(self) -> bool:
        return self.page.locator(self.NEXT_BUTTON).count() > 0

    def parse_products(self) -> list[Product]:
        cards = self.page.locator(self.PRODUCT_CARD)
        total = cards.count()
        log.debug(f"Found {total} product cards on the page")
        products: list[Product] = []
        for i in range(total):
            card = cards.nth(i)
            product = self._parse_card(card)
            if product:
                products.append(product)
        return products

    def _parse_card(self, card: Locator) -> Product | None:
        try:
            link = card.locator("h3 > a")
            title = link.get_attribute("title") or link.inner_text()
            href = link.get_attribute("href") or ""
            price_raw = card.locator("p.price_color").inner_text()
            rating_cls = card.locator("p.star-rating").get_attribute("class") or ""
            in_stock = "in stock" in card.locator(
                "p.availability"
            ).inner_text().strip().lower()

            return Product(
                title=title.strip(),
                price=parse_price(price_raw),
                rating=rating_to_int(rating_cls),
                in_stock=in_stock,
                url=f"{self.base_url}/catalogue/{href.lstrip('./')}",
            )
        except Exception as exc:  # one bad card must not kill the whole run
            log.warning(f"Skipping unparseable card: {exc}")
            return None
