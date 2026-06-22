"""Structured logging via loguru: pretty console + rotating JSON file."""
from __future__ import annotations

import sys
from functools import lru_cache

from config.settings import settings
from loguru import logger

_CONSOLE_FMT = (
    "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{extra[ctx]}</cyan> | <level>{message}</level>"
)


@lru_cache(maxsize=1)
def _configure() -> None:
    settings.ensure_dirs()
    logger.remove()
    logger.configure(extra={"ctx": "app"})
    logger.add(sys.stderr, format=_CONSOLE_FMT, level="INFO", colorize=True)
    logger.add(
        settings.logs_dir / "pricewatch_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="14 days",
        serialize=True,  # machine-readable JSON lines for log aggregators
        level="DEBUG",
        enqueue=True,
    )


def get_logger(ctx: str):
    """Return a logger bound to a short context label (usually the module name)."""
    _configure()
    short = ctx.split(".")[-1]
    return logger.bind(ctx=short)
