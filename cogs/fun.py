from __future__ import annotations

import random

from discord import app_commands
from discord.ext import commands

from assets.banana_data import BANANA_FACTS

from utils.embeds import base_embed, error_embed
from utils.logger import get_logger

log = get_logger("fun")

CAT_API_URL = "https://api.thecatapi.com/v1/images/search"
DADJOKE_API_URL = "https://icanhazdadjoke.com/"
URBAN_API_URL = "https://api.urbandictionary.com/v0/define"

BANANA_EMOJI = "<:banana:1535364444522287124>"


class Fun(commands.Cog):
    """Lighthearted, non-essential commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @property
    def session(self):
        return self.bot.session

    # ── banana (group) ─────────────────────────────────────────

    @commands.hybrid_group(
        name="banana",
        description="Sends Banana's custom emoji, or use 'fact' for a random banana fact.",
        invoke_without_command=True,
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def banana(self, ctx: commands.Context) -> None:
        """Bare `b!banana` (prefix only) falls back to sending the banana emoji."""
        await ctx.send(BANANA_EMOJI)

    @banana.command(name="fact", description="Sends a random banana fact.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def banana_fact(self, ctx: commands.Context) -> None:
        embed = base_embed(title="🍌 Banana Fact", description=random.choice(BANANA_FACTS))
        await ctx.send(embed=embed)

    # ── cat ─────────────────────────────────────────────────────

    @commands.hybrid_command(name="cat", description="Sends a random cat image.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def cat(self, ctx: commands.Context) -> None:
        try:
            async with self.session.get(CAT_API_URL, timeout=10) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"status {resp.status}")
                data = await resp.json()
            image_url = data[0]["url"]
        except Exception as exc:  # noqa: BLE001
            log.warning("Cat API failed: %s", exc)
            await ctx.send(embed=error_embed("Couldn't fetch a cat right now. Try again shortly."))
            return

        embed = base_embed(title="🐱 Meow!")
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)

    # ── dadjoke ─────────────────────────────────────────────────

    @commands.hybrid_command(name="dadjoke", description="Sends a random dad joke.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dadjoke(self, ctx: commands.Context) -> None:
        headers = {"Accept": "application/json", "User-Agent": "Banana Discord Bot"}
        try:
            async with self.session.get(DADJOKE_API_URL, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"status {resp.status}")
                data = await resp.json()
            joke = data["joke"]
        except Exception as exc:  # noqa: BLE001
            log.warning("Dad joke API failed: %s", exc)
            await ctx.send(embed=error_embed("Couldn't fetch a joke right now. Try again shortly."))
            return

        embed = base_embed(title="😂 Dad Joke", description=joke)
        await ctx.send(embed=embed)

    # ── urban ───────────────────────────────────────────────────

    @commands.hybrid_command(name="urban", description="Searches Urban Dictionary for a word.")
    @app_commands.describe(word="The word or phrase to look up.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def urban(self, ctx: commands.Context, *, word: str) -> None:
        try:
            async with self.session.get(
                URBAN_API_URL, params={"term": word}, timeout=10
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"status {resp.status}")
                data = await resp.json()
        except Exception as exc:  # noqa: BLE001
            log.warning("Urban Dictionary API failed: %s", exc)
            await ctx.send(embed=error_embed("Couldn't reach Urban Dictionary right now."))
            return

        results = data.get("list") or []
        if not results:
            await ctx.send(embed=error_embed(f"No definitions found for **{word}**."))
            return

        top = max(results, key=lambda d: d.get("thumbs_up", 0) - d.get("thumbs_down", 0))

        def _trim(text: str, limit: int = 1000) -> str:
            text = text.replace("[", "").replace("]", "")
            return text if len(text) <= limit else text[: limit - 3] + "..."

        embed = base_embed(title=f"📖 {top['word']}")
        embed.add_field(name="Definition", value=_trim(top["definition"]), inline=False)
        if top.get("example"):
            embed.add_field(name="Example", value=_trim(top["example"]), inline=False)
        embed.add_field(name="👍 Thumbs Up", value=str(top.get("thumbs_up", 0)), inline=True)
        embed.add_field(name="👎 Thumbs Down", value=str(top.get("thumbs_down", 0)), inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))