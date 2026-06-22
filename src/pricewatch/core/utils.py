"""Pure, side-effect-free parsing helpers (fully unit-testable, no network)."""
from __future__ import annotations

import re

_PRICE_RE = re.compile(r"[-+]?\d*\.?\d+")
_RATING_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
}


def parse_price(raw: str) -> float:
    """'£51.77' -> 51.77 ; raises ValueError when no number is present."""
    match = _PRICE_RE.search(raw.replace(",", ""))
    if not match:
        raise ValueError(f"No numeric price found in {raw!r}")
    return float(match.group())


def rating_to_int(class_attr: str) -> int:
    """'star-rating Three' -> 3 ; unknown words map to 0."""
    for token in class_attr.lower().split():
        if token in _RATING_WORDS:
            return _RATING_WORDS[token]
    return 0
