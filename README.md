# 🍌 Banana

A production-ready Discord bot built with **discord.py 2.4+**, supporting both
**slash commands** and **prefix commands** from the same underlying logic
(via discord.py's hybrid commands), with SQLite persistence, structured
logging, and a consistent banana-yellow (`#F4D03F`) embed theme.

## Features

- **Hybrid commands** — every command works as both `/command` and `b!command`
  with zero duplicated logic.
- **Modular Cogs** — `info`, `moderation`, `fun`, and a global `error_handler`.
- **SQLite via aiosqlite** — async, swappable for Postgres/MySQL later by only
  editing `database/db.py`.
- **Structured logging** — colorized console output + rotating file logs in
  `logs/banana.log`.
- **Permission checks & cooldowns** on every moderation and utility command.
- **Global error handling** for both prefix and slash invocation paths.

## Folder structure

```
banana-bot/
├── bot.py                 # Entry point
├── config.py               # Environment-driven configuration
├── requirements.txt
├── .env.example
├── cogs/
│   ├── error_handler.py    # Global error handling
│   ├── info.py              # about, ping, userinfo, serverinfo, channelinfo, roleinfo
│   ├── moderation.py        # ban, kick, mute, unmute, warn, purge, lock, unlock, nickname
│   └── fun.py                # banana, cat, dadjoke, urban
├── database/
│   └── db.py                # Async SQLite manager
├── utils/
│   ├── embeds.py             # Banana-yellow themed embed builders
│   ├── helpers.py            # Duration parsing, hierarchy checks, etc.
│   └── logger.py             # Logging setup
├── assets/
│   └── banana_data.py        # Banana facts + image list
└── data/                      # SQLite database file lives here
```

## Setup

1. **Install Python 3.12+** and create a virtual environment:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Fill in `BOT_TOKEN` at minimum. Set `DEV_GUILD_ID` to your test server's ID
   for instant slash-command sync while developing (global sync can take up
   to an hour to propagate).

4. **Enable required intents** in the [Discord Developer Portal](https://discord.com/developers/applications)
   for your bot: **Server Members Intent** and **Message Content Intent**.

5. **Run the bot:**
   ```bash
   python bot.py
   ```

## Required bot permissions

For full functionality, invite the bot with at least:
`Ban Members`, `Kick Members`, `Moderate Members`, `Manage Messages`,
`Manage Channels`, `Manage Nicknames`, `Read Message History`, `Send Messages`,
`Embed Links`, `Add Reactions`.

## Extending the bot

- **Add a command:** add a new `@commands.hybrid_command()` method to the
  relevant cog (or create a new cog and drop it in `cogs/`, then add it to
  `INITIAL_EXTENSIONS` in `bot.py`).
- **Swap the database:** `database/db.py` is the only file that talks to
  SQLite — replace its internals with an async driver for your database of
  choice and the rest of the bot is unaffected.
- **Change the theme color:** edit `config.color` in `config.py`.

## Notes

- `mute` accepts durations like `10m`, `30m`, `1h`, `6h`, `12h`, `1d`, `7d`
  (max 28 days, Discord's timeout ceiling).
- `warn` persists warnings per-guild/per-user in SQLite and reports the
  running total on each new warning.
- `banana` ships with a small predefined image list — swap in local files
  from an `assets/images/` folder and use `discord.File` if you'd rather not
  depend on external image URLs.
