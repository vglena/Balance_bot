# Balance_bot

A personal AI assistant that helps manage daily life — work, home, school pickups, and family routines. Operates via Telegram, powered by GPT-4o-mini.

## Features

- Daily and weekly planning
- Real-time day adaptation ("what do I do now?", "I have a 30-minute gap")
- School pickup logistics with automatic schedule awareness
- Family afternoon decisions (park vs home, energy-aware)
- Work prioritization with deep-focus protection
- Home task management

## Architecture

```
/agent          ← main agent brain (read first)
/agents         ← specialized sub-agents by domain
/skills         ← reusable capabilities
/directives     ← SOPs and operational protocols
/memory         ← single source of truth (persistent context)
/context        ← daily variable state
/execution      ← deterministic scripts and checklists
/app            ← Telegram bot interface
```

## Setup

### Requirements

- Python 3.10+
- A Telegram bot token (from [@BotFather](https://t.me/botfather))
- An OpenAI-compatible API key

### Installation

```bash
cd app/telegram_bot
pip install -r requirements.txt
```

### Configuration

Copy `app/telegram_bot/config.example.env` to `.env` at the workspace root and fill in your values:

```
BOT_NAME=balance_bot
BOT_API=your_telegram_bot_token
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key
LLM_MODEL=gpt-4o-mini
AUTHORIZED_TELEGRAM_USER_ID=your_telegram_user_id
```

### Run

```bash
python app/telegram_bot/bot.py
```

## Usage

Send natural language messages to the bot:

- `"generate today's plan"`
- `"plan tomorrow"`
- `"what do I do now?"`
- `"I have a 30-minute gap"`
- `"park or home after pickup?"`
- `"I'm tired"`
- `/start` — show welcome message

## Security

- Only the user defined in `AUTHORIZED_TELEGRAM_USER_ID` can interact with the bot
- The `.env` file is excluded from version control via `.gitignore`
- No credentials are logged

## License

Private use.
