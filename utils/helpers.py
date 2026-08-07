from __future__ import annotations

import re
from datetime import timedelta
from typing import Optional

import discord

_DURATION_RE = re.compile(r"^(\d+)\s*([smhd])$", re.IGNORECASE)

_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}

# discord.py's timeout ceiling is 28 days.
MAX_TIMEOUT = timedelta(days=28)


class DurationError(ValueError):
    """Raised when a duration string can't be parsed."""


def parse_duration(raw: str) -> timedelta:
    """
    Parse strings like '10m', '1h', '7d' into a timedelta.

    Accepted units: s (seconds), m (minutes), h (hours), d (days).
    """
    match = _DURATION_RE.match(raw.strip())
    if not match:
        raise DurationError(
            f"`{raw}` isn't a valid duration. Try formats like `10m`, `1h`, `6h`, `1d`, `7d`."
        )

    amount, unit = match.groups()
    seconds = int(amount) * _UNIT_SECONDS[unit.lower()]
    delta = timedelta(seconds=seconds)

    if delta.total_seconds() <= 0:
        raise DurationError("Duration must be greater than zero.")
    if delta > MAX_TIMEOUT:
        raise DurationError("Duration can't exceed 28 days (Discord's timeout limit).")

    return delta


def format_timedelta(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds and not days:
        parts.append(f"{seconds}s")
    return " ".join(parts) if parts else "0s"


_KEY_PERMISSIONS = (
    "administrator",
    "manage_guild",
    "manage_roles",
    "manage_channels",
    "manage_messages",
    "kick_members",
    "ban_members",
    "moderate_members",
    "mention_everyone",
    "manage_nicknames",
    "manage_webhooks",
    "manage_emojis",
)


def key_permissions(member: discord.Member) -> list[str]:
    """Return a short list of the member's notable permissions."""
    perms = member.guild_permissions
    return [
        perm.replace("_", " ").title()
        for perm in _KEY_PERMISSIONS
        if getattr(perms, perm, False)
    ]


def check_hierarchy(actor: discord.Member, target: discord.Member) -> Optional[str]:
    """
    Return an error message if `actor` should not be able to act on
    `target` (role hierarchy / self / owner protections), else None.
    """
    guild = actor.guild

    if target == actor:
        return "You can't target yourself."
    if target == guild.me:
        return "I can't target myself."
    if target.id == guild.owner_id:
        return "You can't target the server owner."
    if actor.id != guild.owner_id and target.top_role >= actor.top_role:
        return "You can't target someone with an equal or higher role than you."
    if target.top_role >= guild.me.top_role:
        return "I don't have a high enough role to do that."
    return None
