from __future__ import annotations

import asyncio
import os
import sys

from loguru import logger
from telethon import TelegramClient
from telethon.sessions import StringSession

from bot.config import settings
from bot.database import connect as db_connect
from bot.database import disconnect as db_disconnect
from bot.handlers import register_all_handlers
from bot.services import register_log_monitor
from bot.services.tutorials import init_tutorials


def _setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    )
    logger.add(
        "logs/bot.log",
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        level="DEBUG",
        enqueue=True,
    )


def _make_bot_client() -> TelegramClient:
    return TelegramClient(StringSession(), settings.api_id, settings.api_hash)


async def main() -> None:
    _setup_logging()
    try:
        settings.validate()
    except ValueError as exc:
        logger.critical("Config validation failed:\n{}", exc)
        sys.exit(1)

    logger.info("Starting membership bot")
    await db_connect()

    bot = _make_bot_client()

    try:
        await bot.start(bot_token=settings.bot_token)
        bot_me = await bot.get_me()
        logger.info("Bot started: @{} ({})", bot_me.username, bot_me.id)

        register_all_handlers(bot)
        await init_tutorials(
            bot,
            {
                "what_is_aviator": ("✈️ What is Aviator", settings.tutorial_what_is_aviator),
                "how_to_follow_signals": ("📡 How to Follow Signals", settings.tutorial_how_to_follow_signals),
                "deposit": ("💳 Deposit", settings.tutorial_deposit),
                "withdraw": ("💸 Withdraw", settings.tutorial_withdraw),
            },
        )
        register_log_monitor(bot)

        logger.info("Bot is running. Press Ctrl+C to stop.")
        await bot.run_until_disconnected()
    finally:
        await bot.disconnect()
        await db_disconnect()
        logger.info("Bot stopped cleanly")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
