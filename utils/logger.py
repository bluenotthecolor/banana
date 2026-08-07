from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

_LEVEL_COLORS = {
    logging.DEBUG: "\x1b[38;20m",
    logging.INFO: "\x1b[36;20m",
    logging.WARNING: "\x1b[33;20m",
    logging.ERROR: "\x1b[31;20m",
    logging.CRITICAL: "\x1b[31;1m",
}
_RESET = "\x1b[0m"


class _ConsoleFormatter(logging.Formatter):
    """Adds color to level names when writing to a real terminal."""

    _FMT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    _DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, "")
        base = logging.Formatter(self._FMT, self._DATE_FMT)
        formatted = base.format(record)
        if color and sys.stdout.isatty():
            return f"{color}{formatted}{_RESET}"
        return formatted


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger. Safe to call once at startup."""
    _LOG_DIR.mkdir(exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(_ConsoleFormatter())
    root.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        _LOG_DIR / "banana.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(file_handler)

    # Quiet down noisy third-party loggers.
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logging.getLogger("discord.client").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"banana.{name}")
