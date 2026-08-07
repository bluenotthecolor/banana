from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from flask import ctx

from utils.embeds import base_embed, error_embed, success_embed
from utils.helpers import DurationError, check_hierarchy, format_timedelta, parse_duration
from utils.logger import get_logger

log = get_logger("moderation")


async def _try_dm(member: discord.Member, embed: discord.Embed) -> bool:
    try:
        await member.send(embed=embed)
        return True
    except discord.HTTPException:
        return False


class Moderation(commands.Cog):
    """Server moderation tools."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── ban ─────────────────────────────────────────────────────

    @commands.hybrid_command(name="ban", description="Bans a member from the server.")
    @app_commands.describe(member="The member to ban.", reason="Reason for the ban.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        assert isinstance(ctx.author, discord.Member)
        if (err := check_hierarchy(ctx.author, member)) is not None:
            await ctx.send(embed=error_embed(err))
            return

        dm_embed = base_embed(
            title="You've been banned",
            description=f"You were banned from **{ctx.guild.name}**.",
        )
        dm_embed.add_field(name="Reason", value=reason)
        dm_sent = await _try_dm(member, dm_embed)

        await ctx.guild.ban(member, reason=f"{ctx.author} ({ctx.author.id}): {reason}")
        log.info("BAN | %s banned %s | reason=%s | guild=%s", ctx.author, member, reason, ctx.guild.id)

        embed = success_embed(
            f"**{member}** has been banned.\n**Reason:** {reason}"
            + ("" if dm_sent else "\n*(Couldn't DM the user.)*"),
            title="Member Banned",
        )
        await ctx.send(embed=embed)

    # ── kick ────────────────────────────────────────────────────

    @commands.hybrid_command(name="kick", description="Kicks a member from the server.")
    @app_commands.describe(member="The member to kick.", reason="Reason for the kick.")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        assert isinstance(ctx.author, discord.Member)
        if (err := check_hierarchy(ctx.author, member)) is not None:
            await ctx.send(embed=error_embed(err))
            return

        dm_embed = base_embed(
            title="You've been kicked",
            description=f"You were kicked from **{ctx.guild.name}**.",
        )
        dm_embed.add_field(name="Reason", value=reason)
        dm_sent = await _try_dm(member, dm_embed)

        await ctx.guild.kick(member, reason=f"{ctx.author} ({ctx.author.id}): {reason}")
        log.info("KICK | %s kicked %s | reason=%s | guild=%s", ctx.author, member, reason, ctx.guild.id)

        embed = success_embed(
            f"**{member}** has been kicked.\n**Reason:** {reason}"
            + ("" if dm_sent else "\n*(Couldn't DM the user.)*"),
            title="Member Kicked",
        )
        await ctx.send(embed=embed)

    # ── mute / unmute ───────────────────────────────────────────

    @commands.hybrid_command(name="mute", description="Times out a member for a set duration.")
    @app_commands.describe(
        member="The member to mute.",
        duration="Duration, e.g. 10m, 30m, 1h, 6h, 12h, 1d, 7d.",
        reason="Reason for the mute.",
    )
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str = "10m",
        *,
        reason: str = "No reason provided",
    ) -> None:
        assert isinstance(ctx.author, discord.Member)
        if (err := check_hierarchy(ctx.author, member)) is not None:
            await ctx.send(embed=error_embed(err))
            return

        try:
            delta = parse_duration(duration)
        except DurationError as exc:
            await ctx.send(embed=error_embed(str(exc), title="Invalid duration"))
            return

        await member.timeout(delta, reason=f"{ctx.author} ({ctx.author.id}): {reason}")
        log.info(
            "MUTE | %s muted %s for %s | reason=%s | guild=%s",
            ctx.author, member, format_timedelta(delta), reason, ctx.guild.id,
        )

        embed = success_embed(
            f"**{member}** has been muted for **{format_timedelta(delta)}**.\n**Reason:** {reason}",
            title="Member Muted",
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="unmute", description="Removes a member's timeout.")
    @app_commands.describe(member="The member to unmute.", reason="Reason for the unmute.")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def unmute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        if member.timed_out_until is None:
            await ctx.send(embed=error_embed(f"**{member}** isn't currently muted."))
            return

        await member.timeout(None, reason=f"{ctx.author} ({ctx.author.id}): {reason}")
        log.info("UNMUTE | %s unmuted %s | reason=%s | guild=%s", ctx.author, member, reason, ctx.guild.id)

        embed = success_embed(f"**{member}** has been unmuted.\n**Reason:** {reason}", title="Member Unmuted")
        await ctx.send(embed=embed)

    # ── warn ────────────────────────────────────────────────────

    @commands.hybrid_command(name="warn", description="Warns a member and logs it.")
    @app_commands.describe(member="The member to warn.", reason="Reason for the warning.")
    @commands.has_permissions(moderate_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def warn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        assert isinstance(ctx.author, discord.Member)
        if (err := check_hierarchy(ctx.author, member)) is not None:
            await ctx.send(embed=error_embed(err))
            return

        count = await self.bot.db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        log.info("WARN | %s warned %s (total=%s) | reason=%s | guild=%s", ctx.author, member, count, reason, ctx.guild.id)

        dm_embed = base_embed(
            title="You've been warned",
            description=f"You were warned in **{ctx.guild.name}**.",
        )
        dm_embed.add_field(name="Reason", value=reason)
        await _try_dm(member, dm_embed)

        embed = success_embed(
            f"**{member}** has been warned.\n**Reason:** {reason}\n**Total warnings:** {count}",
            title="Member Warned",
        )
        await ctx.send(embed=embed)

    # ── warnings ────────────────────────────────────────────────

    @commands.hybrid_command(name="warnings", description="Shows a member's warning history.")
    @app_commands.describe(member="The member to look up.")
    @commands.has_permissions(moderate_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def warnings(
        self,
        ctx: commands.Context,
        member: discord.Member,
    ) -> None:
        if member == ctx.guild.me:
            embed = base_embed(
                title="Nice Try",
                description="BANANA !!!",
            )
            await ctx.send(embed=embed)
            return

        entries = await self.bot.db.get_warnings(ctx.guild.id, member.id)

        if not entries:
            embed = base_embed(
                title="No Warnings",
                description=f"**{member}** has no warnings on record.",
            )
            await ctx.send(embed=embed)
            return

        embed = base_embed(
            title=f"Warnings for {member}",
            description=f"**Total:** {len(entries)}",
        )

        for i, entry in enumerate(entries[:25], start=1):
            moderator = f"<@{entry.moderator_id}>"

            # created_at is stored as an ISO 8601 string (UTC).
            when = ""
            try:
                dt = datetime.fromisoformat(entry.created_at)
                when = f" • <t:{int(dt.timestamp())}:R>"
            except ValueError:
                pass

            embed.add_field(
                name=f"#{i} — by {moderator}{when}",
                value=entry.reason,
                inline=False,
            )

        if len(entries) > 25:
            embed.set_footer(text=f"Showing 25 of {len(entries)} warnings.")

        log.info(
            "WARNINGS | %s viewed %s's warnings (total=%s) | guild=%s",
            ctx.author, member, len(entries), ctx.guild.id,
        )
        await ctx.send(embed=embed)

    # ── purge ───────────────────────────────────────────────────

    @commands.hybrid_command(
        name="purge",
        description="Deletes a number of recent messages."
    )
    @app_commands.describe(
        amount="Number of messages to delete (1-100).",
        member="Only delete messages from this member.",
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.guild_only()
    async def purge(
        self,
        ctx: commands.Context,
        amount: int,
        member: Optional[discord.Member] = None,
    ) -> None:
        assert isinstance(ctx.channel, discord.TextChannel)

        if ctx.interaction is not None:
            await ctx.defer(ephemeral=True)

        if amount < 1 or amount > 100:
            embed = error_embed(
                "Amount must be between **1 and 100**."
            )

            if ctx.interaction is not None:
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed, delete_after=5)

            return

        found = 0

        def check(msg: discord.Message) -> bool:
            nonlocal found

            if ctx.interaction is None and msg.id == ctx.message.id:
                return False

            if member is not None and msg.author.id != member.id:
                return False

            if found >= amount:
                return False

            found += 1
            return True

        deleted = await ctx.channel.purge(
            limit=100,
            check=check,
            bulk=True,
        )

        log.info(
            "PURGE | %s deleted %s messages%s | guild=%s",
            ctx.author,
            len(deleted),
            f" from {member}" if member else "",
            ctx.guild.id,
        )

        embed = success_embed(
            f"Deleted **{len(deleted)}** messages.",
            title="Messages Purged",
        )

        if ctx.interaction is not None:
            await ctx.send(
                embed=embed,
                ephemeral=True,
            )
        else:
            await ctx.send(
                embed=embed,
                delete_after=5,
            )
            
    # ── lock / unlock ───────────────────────────────────────────

    @commands.hybrid_command(name="lock", description="Prevents @everyone from sending messages here.")
    @app_commands.describe(channel="The channel to lock (defaults to this one).")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def lock(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None
    ) -> None:
        target = channel or ctx.channel
        assert isinstance(target, discord.TextChannel)

        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await target.set_permissions(
            ctx.guild.default_role, overwrite=overwrite, reason=f"Locked by {ctx.author}"
        )
        log.info("LOCK | %s locked #%s | guild=%s", ctx.author, target.name, ctx.guild.id)

        embed = success_embed(f"🔒 {target.mention} has been locked.", title="Channel Locked")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="unlock", description="Restores @everyone's ability to send messages here.")
    @app_commands.describe(channel="The channel to unlock (defaults to this one).")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def unlock(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None
    ) -> None:
        target = channel or ctx.channel
        assert isinstance(target, discord.TextChannel)

        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await target.set_permissions(
            ctx.guild.default_role, overwrite=overwrite, reason=f"Unlocked by {ctx.author}"
        )
        log.info("UNLOCK | %s unlocked #%s | guild=%s", ctx.author, target.name, ctx.guild.id)

        embed = success_embed(f"🔓 {target.mention} has been unlocked.", title="Channel Unlocked")
        await ctx.send(embed=embed)

    # ── nickname ────────────────────────────────────────────────

    @commands.hybrid_command(name="nickname", description="Changes a member's nickname.")
    @app_commands.describe(member="The member to rename.", nickname="New nickname (leave blank to reset).")
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def nickname(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        nickname: Optional[str] = None,
    ) -> None:
        assert isinstance(ctx.author, discord.Member)
        if (err := check_hierarchy(ctx.author, member)) is not None:
            await ctx.send(embed=error_embed(err))
            return

        old_nick = member.display_name
        await member.edit(nick=nickname, reason=f"Changed by {ctx.author}")
        log.info(
            "NICKNAME | %s changed %s's nickname to %s | guild=%s",
            ctx.author, member, nickname or "(reset)", ctx.guild.id,
        )

        embed = success_embed(
            f"**{old_nick}**'s nickname is now **{member.nick or member.name}**.",
            title="Nickname Changed",
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))