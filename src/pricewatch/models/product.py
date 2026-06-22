"""Domain model for a scraped product, with validation."""
from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, HttpUrl


class Product(BaseModel):
    """A single catalogue item captured by the bot."""

    title: str = Field(..., min_length=1)
    price: float = Field(..., ge=0)
    currency: str = "GBP"
    rating: int = Field(..., ge=0, le=5)
    in_stock: bool = True
    url: HttpUrl
    captured_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    def as_row(self) -> list:
        """Flatten to a spreadsheet row (order matches report headers)."""
        return [
            self.title,
            self.price,
            self.currency,
            self.rating,
            "Yes" if self.in_stock else "No",
            str(self.url),
            self.captured_at.strftime("%Y-%m-%d %H:%M:%S"),
        ]
