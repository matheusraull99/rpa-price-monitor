"""Persists every capture to SQLite and derives price variation between runs.

Each run appends one row per product. Before recording the current run we read
the most recent price per URL (i.e. the *previous* run) so we can classify how
each price moved. SQLite keeps the whole project self-contained — no server.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from ..core.logger import get_logger
from ..models.change import ProductDelta, compute_changes
from ..models.product import Product

log = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS price_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    url         TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    price       REAL    NOT NULL,
    currency    TEXT    NOT NULL,
    rating      INTEGER NOT NULL,
    in_stock    INTEGER NOT NULL,
    captured_at TEXT    NOT NULL
);
"""
_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_url_captured "
    "ON price_history (url, captured_at);"
)


class HistoryStore:
    """Lightweight SQLite-backed history of captured prices."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute(_SCHEMA)
        self._conn.execute(_INDEX)
        self._conn.commit()

    # ---- reads -----------------------------------------------------------
    def latest_prices(self) -> dict[str, float]:
        """Most recent recorded price per URL across all prior runs."""
        rows = self._conn.execute(
            """
            SELECT url, price FROM price_history AS ph
            WHERE captured_at = (
                SELECT MAX(captured_at) FROM price_history WHERE url = ph.url
            )
            """
        ).fetchall()
        return {url: price for url, price in rows}

    # ---- writes ----------------------------------------------------------
    def save(self, products: list[Product]) -> None:
        self._conn.executemany(
            """
            INSERT INTO price_history
                (url, title, price, currency, rating, in_stock, captured_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(p.url),
                    p.title,
                    p.price,
                    p.currency,
                    p.rating,
                    int(p.in_stock),
                    p.captured_at.strftime("%Y-%m-%d %H:%M:%S"),
                )
                for p in products
            ],
        )
        self._conn.commit()

    # ---- orchestration ---------------------------------------------------
    def diff_and_record(self, products: list[Product]) -> list[ProductDelta]:
        """Compare against the previous run, then persist the current one."""
        previous = self.latest_prices()
        changes = compute_changes(products, previous)
        self.save(products)

        moved = sum(c.trend in ("up", "down") for c in changes)
        fresh = sum(c.trend == "new" for c in changes)
        log.info(
            f"History: {len(products)} recorded "
            f"({moved} changed, {fresh} new vs. previous run)"
        )
        return changes

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> HistoryStore:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
