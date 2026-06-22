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
from ..models.product import Product

log = get_logger(__name__)

HEADERS = ["Title", "Price", "Currency", "Rating", "In Stock", "URL", "Captured At"]


class ReportBuilder:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def build(self, products: list[Product]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"price_report_{stamp}.xlsx"

        wb = xlsxwriter.Workbook(str(path), {"in_memory": True})
        fmts = self._formats(wb)
        self._sheet_data(wb, fmts, products)
        self._sheet_summary(wb, fmts, products)
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
        }

    # ---- "Data" sheet ----------------------------------------------------
    def _sheet_data(self, wb, fmts, products: list[Product]) -> None:
        ws = wb.add_worksheet("Data")
        rows = [p.as_row() for p in products]
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
                        **({"format": fmts["currency"]} if h == "Price" else {}),
                    }
                    for h in HEADERS
                ],
            },
        )

        widths = [38, 9, 10, 8, 10, 60, 21]
        for col, width in enumerate(widths):
            ws.set_column(col, col, width)
        ws.freeze_panes(1, 0)

    # ---- "Summary" sheet -------------------------------------------------
    def _sheet_summary(self, wb, fmts, products: list[Product]) -> None:
        ws = wb.add_worksheet("Summary")
        prices = [p.price for p in products] or [0]

        ws.write_row(0, 0, ["Metric", "Value"], fmts["header"])
        kpis = {
            "Generated at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Products captured": len(products),
            "In stock": sum(p.in_stock for p in products),
            "Average price": round(mean(prices), 2),
            "Min price": min(prices),
            "Max price": max(prices),
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
        ws.insert_chart("D9", chart)
