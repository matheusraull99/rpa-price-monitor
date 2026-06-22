"""CLI entrypoint:  python -m pricewatch.main --pages 5 --headed"""
from __future__ import annotations

import argparse
import sys

from config.settings import settings

from .bot import PriceWatchBot
from .core.logger import get_logger

log = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pricewatch",
        description="RPA bot that monitors product prices and exports an Excel report.",
    )
    p.add_argument("--pages", type=int, default=settings.max_pages,
                   help="Number of catalogue pages to crawl.")
    p.add_argument("--headed", action="store_true",
                   help="Run with a visible browser window (debugging).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.headed:
        settings.headless = False
    try:
        PriceWatchBot().run(max_pages=args.pages)
        return 0
    except Exception as exc:
        log.exception(f"Run failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
