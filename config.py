from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int | None = None) -> int | None:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Config:
    # Core
    token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    prefix: str = field(default_factory=lambda: os.getenv("PREFIX", "b!"))
    owner_id: int | None = field(default_factory=lambda: _get_int("OWNER_ID"))
    dev_guild_id: int | None = field(default_factory=lambda: _get_int("DEV_GUILD_ID"))

    # Branding / about command
    developer: str = field(default_factory=lambda: os.getenv("DEVELOPER", "Unknown"))
    website: str = field(default_factory=lambda: os.getenv("WEBSITE", ""))
    support_server: str = field(default_factory=lambda: os.getenv("SUPPORT_SERVER", ""))
    version: str = field(default_factory=lambda: os.getenv("BOT_VERSION", "1.0.0"))

    # Database
    database_path: str = field(
        default_factory=lambda: os.getenv("DATABASE_PATH", "data/banana.db")
    )

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Welcome message (sent to a server when the bot is added)
    welcome_channel_name: str = field(
        default_factory=lambda: os.getenv("WELCOME_CHANNEL_NAME", "general")
    )
    welcome_message: str = field(
        default_factory=lambda: os.getenv(
            "WELCOME_MESSAGE",
            "Thanks for adding me to **{guild}**! 🍌\n"
            "Use `{prefix}help` or `/help` to see what I can do.",
        )
    )

    # Theme
    color: int = 0xF4D03F  # Banana yellow
    error_color: int = 0xE74C3C
    success_color: int = 0x2ECC71

    def validate(self) -> None:
        if not self.token:
            raise RuntimeError(
                "BOT_TOKEN is missing."
            )


config = Config()