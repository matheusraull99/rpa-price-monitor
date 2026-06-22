"""Price-variation domain logic — pure and fully unit-testable (no DB, no network).

Compares the products captured in the current run against the prices recorded
in the previous run, classifying each item as up / down / same / new.
"""
from __future__ import annotations

from dataclasses import dataclass

from .product import Product

# Trend labels rendered in the report (kept here so report + tests agree).
TREND_LABELS = {
    "up": "▲ up",
    "down": "▼ down",
    "same": "– same",
    "new": "new",
}


@dataclass(frozen=True)
class ProductDelta:
    """A product paired with how its price moved since the previous run."""

    product: Product
    previous_price: float | None

    @property
    def trend(self) -> str:
        if self.previous_price is None:
            return "new"
        if self.product.price > self.previous_price:
            return "up"
        if self.product.price < self.previous_price:
            return "down"
        return "same"

    @property
    def delta(self) -> float | None:
        """Absolute change vs. the previous run (None when the item is new)."""
        if self.previous_price is None:
            return None
        return round(self.product.price - self.previous_price, 2)

    @property
    def pct(self) -> float | None:
        """Percentage change vs. the previous run (None when new or prev == 0)."""
        if not self.previous_price:  # None or 0.0
            return None
        return round(
            (self.product.price - self.previous_price) / self.previous_price * 100, 2
        )


def compute_changes(
    products: list[Product], previous: dict[str, float]
) -> list[ProductDelta]:
    """Pair each product with its previous price (keyed by URL), preserving order."""
    return [ProductDelta(p, previous.get(str(p.url))) for p in products]
