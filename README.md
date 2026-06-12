# Telegram Membership Bot

Async Telegram bot for 1WIN affiliate onboarding, 1WIN ID binding, registration/deposit verification from a log channel, user stats, daily check-ins, referrals, admin broadcast, and CSV export.

This version intentionally does not include gambling prediction or signal-generation logic.

## Features

- Telethon bot client for user and admin commands
- Single in-memory Telethon bot client for user commands and log monitoring
- Motor/MongoDB repositories for users, deposits, and notifications
- Registration and deposit parsing from log messages
- 1WIN ID binding/editing with duplicate protection
- Old log message scan after a user binds their 1WIN ID
- Admin dashboard, search, export, maintenance toggle, and broadcast
- Referral links and leaderboard
- Docker and Docker Compose support

## Project Structure

```text
1win/
  bot/
    config/        environment settings
    database/      MongoDB connection and repositories
    handlers/      user/admin command handlers
    keyboards/     inline keyboard builders
    models/        dataclass records
    scheduler/     APScheduler setup
    services/      log channel monitor
    utils/         helper functions
  main.py          local launcher
  requirements.txt
  Dockerfile
  docker-compose.yml
  .env.example
```

## Configuration

Copy `.env.example` to `.env` and fill the required values:

```env
API_ID=12345678
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
ADMIN_IDS=123456789
LOG_CHANNEL_ID=-1001234567890
MONGO_URI=mongodb://localhost:27017
MONGO_DB=membership_bot
AFFILIATE_URL=https://example.com/register
PROMO_CODE=WIN1300
HOW_TO_GET_ID_URL=https://example.com/how-to-get-1win-id-video
ONE_WIN_ID_MIN_LENGTH=8
ONE_WIN_ID_MAX_LENGTH=10
LOG_HISTORY_SCAN_LIMIT=5000
```

## Run Locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m bot.main
```

MongoDB must be running before the bot starts.

## Run With Docker

```bash
docker compose up --build
```

No phone login is needed. Add the bot to the log channel and give it permission to read channel posts.

## Commands

User commands:

- `/start` - onboarding and menu
- `/bind <1win_id>` - link a numeric 1WIN ID
- `/editid <1win_id>` - change linked 1WIN ID
- `/profile` or `/stats` - account status
- `/bonus` - daily premium check-in
- `/leaderboard` - top check-ins
- `/referral` - personal referral link

Admin commands:

- `/admin` - dashboard
- `/broadcast <message>` - broadcast to active users
- `/totals` - plain text totals

## Log Channel Formats

The log monitor parses these messages:

```text
New-User-Registered-365951234
User-365951234-Deposited-3.77-Firsttime
User-365951234-Deposited-5.00
```

The numeric 1WIN ID must already be linked by a Telegram user via `/bind`.

When a user binds or edits their 1WIN ID, the bot scans recent log channel history using `LOG_HISTORY_SCAN_LIMIT` and updates verified/deposited status if old matching messages already exist.
