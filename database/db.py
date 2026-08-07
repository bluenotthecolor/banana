from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from utils.logger import get_logger

log = get_logger("database")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS warnings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    INTEGER NOT NULL,
    user_id     INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    reason      TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_warnings_guild_user
    ON warnings (guild_id, user_id);

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    prefix   TEXT
);
"""


@dataclass(slots=True)
class Warning:
    id: int
    guild_id: int
    user_id: int
    moderator_id: int
    reason: str
    created_at: str


class Database:
    """Owns the single aiosqlite connection used by the bot."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database used before connect() was called.")
        return self._conn

    async def connect(self) -> None:
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(_SCHEMA)
        await self._conn.commit()
        log.info("Connected to SQLite database at %s", self._path)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            log.info("Database connection closed.")

    async def ping(self) -> float:
        """Round-trip a trivial query and return the latency in ms."""
        import time

        start = time.perf_counter()
        await self.conn.execute("SELECT 1")
        return (time.perf_counter() - start) * 1000

    # ── Warnings ────────────────────────────────────────────────

    async def add_warning(
        self, guild_id: int, user_id: int, moderator_id: int, reason: str
    ) -> int:
        cursor = await self.conn.execute(
            """
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (guild_id, user_id, moderator_id, reason, datetime.now(timezone.utc).isoformat()),
        )
        await self.conn.commit()
        return await self.count_warnings(guild_id, user_id) if cursor else 0

    async def count_warnings(self, guild_id: int, user_id: int) -> int:
        async with self.conn.execute(
            "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
            return int(row[0]) if row else 0

    async def get_warnings(self, guild_id: int, user_id: int) -> list[Warning]:
        async with self.conn.execute(
            """
            SELECT id, guild_id, user_id, moderator_id, reason, created_at
            FROM warnings WHERE guild_id = ? AND user_id = ?
            ORDER BY id DESC
            """,
            (guild_id, user_id),
        ) as cursor:
            rows = await cursor.fetchall()
            return [Warning(**dict(row)) for row in rows]
