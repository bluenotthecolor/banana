from __future__ import annotations

from typing import Optional

import discord

from config import config

BANANA_ICON = "🍌"


def base_embed(
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[int] = None,
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color if color is not None else config.color,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text="Banana")
    return embed


def success_embed(description: str, *, title: str = "Success") -> discord.Embed:
    return base_embed(
        title=f"{BANANA_ICON} {title}",
        description=description,
        color=config.success_color,
    )


def error_embed(description: str, *, title: str = "Error") -> discord.Embed:
    return base_embed(
        title=f"⚠️ {title}",
        description=description,
        color=config.error_color,
    )


def info_embed(description: str, *, title: str = "Info") -> discord.Embed:
    return base_embed(title=f"{BANANA_ICON} {title}", description=description)
