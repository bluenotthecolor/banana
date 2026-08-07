<p align="center">
  <img src="banana.png" width="200" alt="Banana">
</p>

<h1 align="center">Banana</h1>

## Setup

### Requirements

- Python 3.10+
- A Discord bot token

### 1. Clone the repository

```bash
git clone https://github.com/bluenotthecolor/banana.git
cd banana
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file

Create a file named `.env` in the project folder.

Add:

```env
DISCORD_TOKEN=your_bot_token
```

Replace `your_bot_token` with your Discord bot token.

### 4. Enable Discord intents

Go to the Discord Developer Portal and enable:

- Server Members Intent
- Message Content Intent
- Presence Intent

### 5. Run Banana

```bash
python bot.py
```

If everything is configured correctly, Banana will start and connect to Discord.

## Updating

To update your installation:

```bash
git pull
pip install -r requirements.txt
```

## Links

### Invite Banana

[Invite Bot](https://discord.com/oauth2/authorize?client_id=1535349953420070962&permissions=1099780064470&scope=bot%20applications.commands)

### Support Server

[Join Support Server](https://discord.gg/ucTZH4qEgT)
