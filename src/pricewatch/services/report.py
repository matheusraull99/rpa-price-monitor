"""Builds a polished, broadly-compatible Excel workbook from scraped products.

Uses XlsxWriter, which always emits a shared-strings table (xl/sharedStrings.xml),
so the file renders correctly in Excel, LibreOffice, Google Sheets *and* lightweight
browser-based viewers that expect that table to exist.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from statistics import mean

import xlsxwriter

from ..core.logger import get_logger
from ..models.change import TREND_LABELS, ProductDelta, compute_changes
from ..models.product import Product

log = get_logger(__name__)

HEADERS = [
    "Title", "Price", "Currency", "Rating", "In Stock", "URL", "Captured At",
    "Prev Price", "Δ", "Δ %", "Trend",
]


class ReportBuilder:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def build(
        self,
        products: list[Product],
        changes: list[ProductDelta] | None = None,
    ) -> Path:
        # When no history is supplied (e.g. tests), treat every item as new.
        if changes is None:
            changes = compute_changes(products, {})

        self.output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"price_report_{stamp}.xlsx"

        wb = xlsxwriter.Workbook(str(path), {"in_memory": True})
        fmts = self._formats(wb)
        self._sheet_data(wb, fmts, changes)
        self._sheet_changes(wb, fmts, changes)
        self._sheet_summary(wb, fmts, changes)
        wb.close()

        log.success(f"Report saved -> {path}")
        return path

    # ---- shared cell formats --------------------------------------------
    @staticmethod
    def _formats(wb: xlsxwriter.Workbook) -> dict:
        return {
            "header": wb.add_format(
                {
                    "bold": True,
                    "font_color": "#FFFFFF",
                    "bg_color": "#1F4E78",
                    "align": "center",
                    "valign": "vcenter",
                    "border": 1,
                }
            ),
            "currency": wb.add_format({"num_format": "#,##0.00"}),
            "cell": wb.add_format({"border": 1}),
            "kpi_val": wb.add_format({"border": 1, "align": "right"}),
            # price went up -> red ; down -> green ; new/same -> neutral
            "up": wb.add_format({"font_color": "#C00000", "bold": True}),
            "down": wb.add_format({"font_color": "#1E7A34", "bold": True}),
            "neutral": wb.add_format({"font_color": "#808080"}),
        }

    @staticmethod
    def _trend_fmt(fmts: dict, trend: str):
        return {"up": fmts["up"], "down": fmts["down"]}.get(trend, fmts["neutral"])

    # ---- "Data" sheet ----------------------------------------------------
    def _sheet_data(self, wb, fmts, changes: list[ProductDelta]) -> None:
        ws = wb.add_worksheet("Data")
        rows = [
            [
                *c.product.as_row(),
                c.previous_price if c.previous_price is not None else "",
                c.delta if c.delta is not None else "",
                c.pct if c.pct is not None else "",
                TREND_LABELS[c.trend],
            ]
            for c in changes
        ]
        last_row = len(rows)  # header is row 0, data rows start at 1

        ws.add_table(
            0,
            0,
            last_row,
            len(HEADERS) - 1,
            {
                "data": rows,
                "style": "Table Style Medium 2",
                "columns": [
                    {
                        "header": h,
                        "header_format": fmts["header"],
                        **(
                            {"format": fmts["currency"]}
                            if h in ("Price", "Prev Price")
                            else {}
                        ),
                    }
                    for h in HEADERS
                ],
            },
        )

        widths = [38, 9, 10, 8, 10, 60, 21, 11, 9, 8, 9]
        for col, width in enumerate(widths):
            ws.set_column(col, col, width)
        ws.freeze_panes(1, 0)

    # ---- "Changes" sheet -------------------------------------------------
    def _sheet_changes(self, wb, fmts, changes: list[ProductDelta]) -> None:
        """Only the products whose price moved, biggest swings first."""
        ws = wb.add_worksheet("Changes")
        moved = sorted(
            (c for c in changes if c.trend in ("up", "down")),
            key=lambda c: abs(c.delta or 0),
            reverse=True,
        )

        cols = ["Title", "Previous", "Current", "Δ", "Δ %", "Trend"]
        ws.write_row(0, 0, cols, fmts["header"])

        if not moved:
            ws.write(1, 0, "No price changes vs. previous run.", fmts["neutral"])
        else:
            for r, c in enumerate(moved, start=1):
                tf = self._trend_fmt(fmts, c.trend)
                ws.write(r, 0, c.product.title, fmts["cell"])
                ws.write_number(r, 1, c.previous_price, fmts["currency"])
                ws.write_number(r, 2, c.product.price, fmts["currency"])
                ws.write_number(r, 3, c.delta, tf)
                ws.write_number(r, 4, c.pct, tf)
                ws.write(r, 5, TREND_LABELS[c.trend], tf)

        for col, width in enumerate([38, 11, 11, 9, 8, 9]):
            ws.set_column(col, col, width)
        ws.freeze_panes(1, 0)

    # ---- "Summary" sheet -------------------------------------------------
    def _sheet_summary(self, wb, fmts, changes: list[ProductDelta]) -> None:
        ws = wb.add_worksheet("Summary")
        products = [c.product for c in changes]
        prices = [p.price for p in products] or [0]

        ws.write_row(0, 0, ["Metric", "Value"], fmts["header"])
        kpis = {
            "Generated at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Products captured": len(products),
            "In stock": sum(p.in_stock for p in products),
            "Average price": round(mean(prices), 2),
            "Min price": min(prices),
            "Max price": max(prices),
            "Price increases": sum(c.trend == "up" for c in changes),
            "Price decreases": sum(c.trend == "down" for c in changes),
            "New products": sum(c.trend == "new" for c in changes),
            "Unchanged": sum(c.trend == "same" for c in changes),
        }
        for r, (key, val) in enumerate(kpis.items(), start=1):
            ws.write(r, 0, key, fmts["cell"])
            ws.write(r, 1, val, fmts["kpi_val"])

        # Average price per rating (feeds the chart)
        ws.write_row(0, 3, ["Rating", "Avg Price"], fmts["header"])
        for r, rating in enumerate(range(1, 6), start=1):
            subset = [p.price for p in products if p.rating == rating]
            ws.write(r, 3, f"{rating} stars", fmts["cell"])
            ws.write(r, 4, round(mean(subset), 2) if subset else 0, fmts["kpi_val"])

        chart = wb.add_chart({"type": "column"})
        chart.add_series(
            {
                "name": "Avg price by rating",
                "categories": ["Summary", 1, 3, 5, 3],
                "values": ["Summary", 1, 4, 5, 4],
                "fill": {"color": "#1F4E78"},
            }
        )
        chart.set_title({"name": "Average price by rating"})
        chart.set_x_axis({"name": "Rating"})
        chart.set_y_axis({"name": "Price"})
        chart.set_legend({"none": True})
        chart.set_size({"width": 460, "height": 300})
        ws.set_column(0, 0, 18)
        ws.insert_chart("D13", chart)
