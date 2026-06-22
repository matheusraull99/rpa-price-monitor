"""Validation tests for the Product domain model."""
import pytest
from pydantic import ValidationError

from pricewatch.models.product import Product

VALID = dict(
    title="Clean Code",
    price=42.5,
    rating=5,
    in_stock=True,
    url="https://books.toscrape.com/catalogue/clean-code_1/index.html",
)


def test_product_valid():
    p = Product(**VALID)
    assert p.currency == "GBP"
    assert p.as_row()[0] == "Clean Code"
    assert p.as_row()[4] == "Yes"


@pytest.mark.parametrize("field, bad", [("rating", 9), ("price", -1), ("title", "")])
def test_product_rejects_bad_values(field, bad):
    data = VALID | {field: bad}
    with pytest.raises(ValidationError):
        Product(**data)
