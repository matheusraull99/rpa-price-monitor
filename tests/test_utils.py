"""Unit tests for the pure parsing helpers — fast and network-free."""
import pytest

from pricewatch.core.utils import parse_price, rating_to_int


@pytest.mark.parametrize(
    "raw, expected",
    [("£51.77", 51.77), ("$1,299.00", 1299.00), ("13.10 GBP", 13.10), ("0", 0.0)],
)
def test_parse_price_ok(raw, expected):
    assert parse_price(raw) == pytest.approx(expected)


def test_parse_price_invalid():
    with pytest.raises(ValueError):
        parse_price("sold out")


@pytest.mark.parametrize(
    "cls, expected",
    [
        ("star-rating Three", 3),
        ("star-rating Five", 5),
        ("STAR-RATING one", 1),
        ("star-rating Unknown", 0),
    ],
)
def test_rating_to_int(cls, expected):
    assert rating_to_int(cls) == expected
