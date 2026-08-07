from __future__ import annotations

import asyncio
import math

import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import error_embed
from utils.helpers import DurationError
from utils.logger import get_logger

log = get_logger("errors")

COOLDOWN_TITLE = "Slow down!"


def _cooldown_embed(seconds: int) -> discord.Embed:
    return error_embed(
        f"This command is on cooldown. Try again in **{seconds}s**.",
        title=COOLDOWN_TITLE,
    )


async def _run_cooldown_countdown(message: discord.Message, retry_after: float) -> None:
    """Live-edits a cooldown message down to 0 in whole seconds (OwO-style:
    3s → 2s → 1s, no decimals), then deletes the message once it hits 0."""
    remaining = math.ceil(retry_after)

    try:
        while remaining > 0:
            await asyncio.sleep(1)
            remaining -= 1
            if remaining <= 0:
                break
            await message.edit(embed=_cooldown_embed(remaining))
        await message.delete()
    except discord.HTTPException:
        pass


class ErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Hybrid commands raised via the app command tree route through
        # here too, so we only need to register this one listener plus
        # a thin tree.on_error passthrough set up in setup().
        bot.tree.on_error = self.on_app_command_error

    async def _respond(
        self, ctx: commands.Context, embed: discord.Embed, *, retry_after: float | None = None
    ) -> None:
        try:
            if ctx.interaction is not None and ctx.interaction.response.is_done():
                message = await ctx.send(embed=embed, ephemeral=True)
            else:
                message = await ctx.send(embed=embed)
        except discord.HTTPException:
            return

        if retry_after is not None and message is not None:
            self.bot.loop.create_task(_run_cooldown_countdown(message, retry_after))

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        error = getattr(error, "original", error)
        retry_after: float | None = None

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            embed = _cooldown_embed(math.ceil(retry_after))
        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(p.replace("_", " ").title() for p in error.missing_permissions)
            embed = error_embed(f"You need the **{perms}** permission to do that.")
        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(p.replace("_", " ").title() for p in error.missing_permissions)
            embed = error_embed(f"I need the **{perms}** permission to do that.")
        elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            embed = error_embed(str(error) or "Invalid or missing argument.", title="Invalid usage")
        elif isinstance(error, DurationError):
            embed = error_embed(str(error), title="Invalid duration")
        elif isinstance(error, commands.NoPrivateMessage):
            embed = error_embed("This command can only be used in a server.")
        elif isinstance(error, commands.CheckFailure):
            embed = error_embed("You aren't allowed to use this command.")
        else:
            log.error(
                "Unhandled error in command '%s': %s",
                ctx.command,
                error,
                exc_info=error,
            )
            embed = error_embed("Something went wrong while running that command.")

        await self._respond(ctx, embed, retry_after=retry_after)

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        # Hybrid commands funnel through on_command_error above; this
        # exists to catch pure app-command errors (e.g. context menus,
        # or failures before a Context could be constructed).
        original = getattr(error, "original", error)
        embed = error_embed("Something went wrong while running that command.")
        retry_after: float | None = None

        if isinstance(original, app_commands.CommandOnCooldown):
            retry_after = original.retry_after
            embed = _cooldown_embed(math.ceil(retry_after))
        elif isinstance(original, app_commands.MissingPermissions):
            embed = error_embed("You aren't allowed to use this command.")
        elif isinstance(original, app_commands.BotMissingPermissions):
            embed = error_embed("I'm missing permissions needed to do that.")
        else:
            log.error("Unhandled app command error: %s", original, exc_info=original)

        try:
            if interaction.response.is_done():
                message = await interaction.followup.send(embed=embed, ephemeral=True, wait=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                message = await interaction.original_response()
        except discord.HTTPException:
            return

        if retry_after is not None and message is not None:
            self.bot.loop.create_task(_run_cooldown_countdown(message, retry_after))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ErrorHandler(bot))
