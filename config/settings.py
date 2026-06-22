"""Centralized, type-safe configuration loaded from environment / .env file."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Application settings. Override any value via environment variables."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Target ------------------------------------------------------------
    base_url: str = Field(
        default="https://books.toscrape.com",
        description="Public sandbox built specifically for scraping practice.",
    )
    max_pages: int = Field(
        default=5, ge=1, le=50, description="Catalogue pages to crawl."
    )

    # --- Browser -----------------------------------------------------------
    headless: bool = True
    nav_timeout_ms: int = 30_000
    slow_mo_ms: int = 0  # increase to watch the bot run in headed mode

    # --- Resilience --------------------------------------------------------
    max_retries: int = 3
    retry_backoff_s: float = 2.0

    # --- Output ------------------------------------------------------------
    output_dir: Path = PROJECT_ROOT / "output"
    logs_dir: Path = PROJECT_ROOT / "logs"

    # --- Notifications (optional) -----------------------------------------
    webhook_url: str | None = Field(
        default=None,
        description="Slack/Teams incoming webhook. Empty = console summary only.",
    )

    def ensure_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
