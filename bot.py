from __future__ import annotations

import asyncio
import contextlib

import aiohttp
import discord
from discord import guild
from discord.ext import commands

from config import config
from database.db import Database
from utils.logger import get_logger, setup_logging

setup_logging(config.log_level)
log = get_logger("core")

INITIAL_EXTENSIONS = (
    "cogs.error_handler",
    "cogs.info",
    "cogs.moderation",
    "cogs.fun",
)


class Banana(commands.Bot):
    """The Banana bot instance."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(config.prefix),
            intents=intents,
            help_command=None,  # replaced by the custom hybrid `help` command in cogs/info.py
            case_insensitive=True,
        )

        self.db = Database(config.database_path)
        self.session: aiohttp.ClientSession | None = None
        self.start_time = discord.utils.utcnow()

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()
        await self.db.connect()

        for extension in INITIAL_EXTENSIONS:
            try:
                await self.load_extension(extension)
                log.info("Loaded extension: %s", extension)
            except Exception:
                log.exception("Failed to load extension: %s", extension)

        if config.dev_guild_id:
            guild = discord.Object(id=config.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %d commands to dev guild %s", len(synced), config.dev_guild_id)
        else:
            synced = await self.tree.sync()
            log.info("Synced %d global commands", len(synced))

    async def on_ready(self) -> None:
        assert self.user is not None
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        log.info("Serving %d guild(s)", len(self.guilds))

        activity = discord.Activity(
            type=discord.ActivityType.watching, name=f"{config.prefix}help | 🍌"
        )
        await self.change_presence(activity=activity)

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()
        await self.db.close()
        await super().close()
        
    async def on_guild_join(self, guild: discord.Guild) -> None:
        log.info("Joined new guild: %s (%s)", guild.name, guild.id)

        embed = discord.Embed(
            title="🍌 Thanks for inviting Banana!",
            description=(
                f"Hey everyone! I'm **Banana**, your friendly Discord bot.\n\n"
                f"Thanks for adding me to **{guild.name}**!\n\n"
                "Use `/help` to see my commands and get started.\n\n"
                "If you need support, check out our support server."
            ),
            color=0xFFE135
        )

        embed.set_footer(text="Banana • Have a bunch of fun 🍌")

        # Send message in a server channel
        channel = None

        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages:
                channel = ch
                break

        if channel:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                log.warning("Cannot send welcome message in %s", guild.name)

        # DM the server owner
        try:
            owner = guild.owner

            if owner:
                owner_embed = discord.Embed(
                    title="🍌 Banana was added!",
                    description=(
                        f"Thanks for adding Banana to **{guild.name}**!\n\n"
                        "I'm ready to help your server.\n\n"
                        "Run `/help` to view commands."
                    ),
                    color=0xFFE135
                )

                owner_embed.set_footer(text="Banana Setup")

                await owner.send(embed=owner_embed)

        except discord.Forbidden:
            log.info("Couldn't DM owner of %s (DMs disabled)", guild.name)
        except Exception:
            log.exception("Failed to DM guild owner")


async def main() -> None:
    config.validate()
    bot = Banana()
    async with bot:
        await bot.start(config.token)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())