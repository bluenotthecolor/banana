from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

from config import config
from utils.embeds import base_embed, error_embed
from utils.helpers import key_permissions
from utils.logger import get_logger

log = get_logger("info")

GuildChannel = Union[
    discord.TextChannel,
    discord.VoiceChannel,
    discord.StageChannel,
    discord.ForumChannel,
    discord.CategoryChannel,
    discord.Thread,
]


def _discord_timestamp(dt: datetime, style: str = "F") -> str:
    return f"<t:{int(dt.timestamp())}:{style}>"


class Info(commands.Cog):
    """General information commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── about ───────────────────────────────────────────────────

    @commands.hybrid_command(name="about", description="Shows Banana's information.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def about(self, ctx: commands.Context) -> None:
        server_count = len(self.bot.guilds)
        user_count = sum(g.member_count or 0 for g in self.bot.guilds)

        embed = base_embed(
            title="🍌 About Banana",
            description=(
                f"A fast, friendly, banana-themed Discord bot, owned by **{config.developer}**. "
                f"Currently serving **{server_count}** servers and **{user_count}** users, "
                f"running on discord.py **{discord.__version__}**."
            ),
        )

        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        view = discord.ui.View()
        if self.bot.user:
            invite_url = (
                f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}"
                "&permissions=1099780064470&scope=bot%20applications.commands"
            )
            view.add_item(discord.ui.Button(label="Invite Me", url=invite_url, emoji="🍌"))
        if config.website:
            view.add_item(discord.ui.Button(label="Website", url=config.website))
        if config.support_server:
            view.add_item(discord.ui.Button(label="Support Server", url=config.support_server))

        await ctx.send(embed=embed, view=view if view.children else None)

    # ── help ────────────────────────────────────────────────────

    @commands.hybrid_command(name="help", description="Shows all commands, or details about one.")
    @app_commands.describe(command="Optional command name to get details for.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def help(self, ctx: commands.Context, command: Optional[str] = None) -> None:
        if command:
            cmd = self.bot.get_command(command)
            if cmd is None or cmd.hidden:
                await ctx.send(embed=error_embed(f"No command called **{command}** found."))
                return

            usage = f"{config.prefix}{cmd.qualified_name} {cmd.signature}".strip()
            embed = base_embed(title=f"🍌 Help — {cmd.qualified_name}")
            embed.add_field(
                name="Description",
                value=cmd.description or cmd.short_doc or "No description.",
                inline=False,
            )
            embed.add_field(name="Prefix usage", value=f"`{usage}`", inline=False)
            embed.add_field(name="Slash usage", value=f"`/{cmd.qualified_name}`", inline=False)
            await ctx.send(embed=embed)
            return

        embed = base_embed(
            title="🍌 Banana Help",
            description=(
                f"Prefix: `{config.prefix}` — every command also works as a `/slash` command.\n"
                f"Use `{config.prefix}help <command>` or `/help command:<command>` for details."
            ),
        )
        for cog_name, cog in sorted(self.bot.cogs.items()):
            cog_commands = sorted(
                (c for c in cog.get_commands() if not c.hidden), key=lambda c: c.name
            )
            if not cog_commands:
                continue
            embed.add_field(
                name=cog_name,
                value=", ".join(f"`{c.name}`" for c in cog_commands),
                inline=False,
            )
        await ctx.send(embed=embed)

    # ── ping ────────────────────────────────────────────────────

    @commands.hybrid_command(name="ping", description="Shows API, websocket, and database latency.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx: commands.Context) -> None:
        start = time.perf_counter()
        message = await ctx.send(embed=base_embed(title="🍌 Peeling the ping..."))
        api_latency = (time.perf_counter() - start) * 1000

        db_latency: Optional[float] = None
        if hasattr(self.bot, "db"):
            try:
                db_latency = await self.bot.db.ping()
            except Exception:  # noqa: BLE001
                db_latency = None

        embed = base_embed(title="🍌 Bananapong!")
        embed.add_field(name="Websocket", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="API", value=f"{api_latency:.0f}ms", inline=True)
        embed.add_field(
            name="Database",
            value=f"{db_latency:.1f}ms" if db_latency is not None else "N/A",
            inline=True,
        )
        await message.edit(embed=embed)

    # ── userinfo ────────────────────────────────────────────────

    @commands.hybrid_command(name="userinfo", description="Shows information about a user.")
    @app_commands.describe(member="The member to look up (defaults to you).")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def userinfo(
        self, ctx: commands.Context, member: Optional[discord.Member] = None
    ) -> None:
        member = member or ctx.author  # type: ignore[assignment]
        assert isinstance(member, discord.Member)

        roles = [f"@{r.name}" for r in reversed(member.roles) if r.name != "@everyone"]
        perms = key_permissions(member)

        embed = base_embed(title=f"👤 {member}")
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Created", value=_discord_timestamp(member.created_at), inline=True)
        if member.joined_at:
            embed.add_field(name="Joined", value=_discord_timestamp(member.joined_at), inline=True)
        embed.add_field(
            name=f"Roles [{len(roles)}]",
            value=", ".join(roles) if roles else "None",
            inline=False,
        )
        embed.add_field(
            name="Key Permissions",
            value=", ".join(perms) if perms else "None",
            inline=False,
        )
        await ctx.send(embed=embed)

    # ── serverinfo ──────────────────────────────────────────────

    @commands.hybrid_command(name="serverinfo", description="Shows information about this server.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context) -> None:
        guild = ctx.guild
        assert guild is not None

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)

        embed = base_embed(title=f"🏠 {guild.name}")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="Owner", value=f"@{guild.owner.display_name}" if guild.owner else "Unknown")
        embed.add_field(name="ID", value=str(guild.id))
        embed.add_field(name="Members", value=str(guild.member_count))
        embed.add_field(name="Created", value=_discord_timestamp(guild.created_at), inline=True)
        embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier} ({guild.premium_subscription_count} boosts)")
        embed.add_field(
            name="Verification Level", value=str(guild.verification_level).title()
        )
        embed.add_field(
            name="Channels",
            value=f"{text_channels} text • {voice_channels} voice",
        )
        embed.add_field(name="Roles", value=str(len(guild.roles)))
        embed.add_field(name="Emojis", value=str(len(guild.emojis)))
        await ctx.send(embed=embed)

    # ── channelinfo ─────────────────────────────────────────────

    @commands.hybrid_command(name="channelinfo", description="Shows information about a channel.")
    @app_commands.describe(channel="The channel to look up (defaults to this one).")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def channelinfo(
        self, ctx: commands.Context, channel: Optional[GuildChannel] = None
    ) -> None:
        target = channel or ctx.channel
        if not hasattr(target, "id"):
            await ctx.send(embed=error_embed("That's not a valid server channel."))
            return

        embed = base_embed(title=f"# {getattr(target, 'name', 'channel')}")
        embed.add_field(name="ID", value=str(target.id))
        embed.add_field(name="Type", value=str(target.type).replace("_", " ").title())
        category = getattr(target, "category", None)
        embed.add_field(name="Category", value=category.name if category else "None")

        topic = getattr(target, "topic", None)
        embed.add_field(name="Topic", value=topic or "None", inline=False)

        created_at = getattr(target, "created_at", None)
        if created_at:
            embed.add_field(name="Created", value=_discord_timestamp(created_at), inline=True)

        nsfw = getattr(target, "nsfw", None)
        if nsfw is not None:
            embed.add_field(name="NSFW", value="Yes" if nsfw else "No")

        slowmode = getattr(target, "slowmode_delay", None)
        if slowmode is not None:
            embed.add_field(name="Slowmode", value=f"{slowmode}s" if slowmode else "Off")

        await ctx.send(embed=embed)

    # ── roleinfo ────────────────────────────────────────────────

    @commands.hybrid_command(name="roleinfo", description="Shows information about a role.")
    @app_commands.describe(role="The role to look up.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def roleinfo(self, ctx: commands.Context, role: discord.Role) -> None:
        embed = base_embed(title=f"🎭 {role.name}", color=role.color.value or config.color)
        embed.add_field(name="ID", value=str(role.id))
        embed.add_field(name="Color", value=str(role.color))
        embed.add_field(name="Position", value=str(role.position))
        embed.add_field(name="Members", value=str(len(role.members)))
        embed.add_field(name="Created", value=_discord_timestamp(role.created_at), inline=True)

        perms = [p.replace("_", " ").title() for p, v in role.permissions if v]
        embed.add_field(
            name="Permissions",
            value=", ".join(perms[:15]) + ("..." if len(perms) > 15 else "") if perms else "None",
            inline=False,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Info(bot))