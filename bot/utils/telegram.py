from __future__ import annotations

import asyncio
import re

from loguru import logger
from telethon import Button, TelegramClient
from telethon.errors import MessageIdInvalidError, MessageNotModifiedError
from telethon.tl.custom.message import Message

_LIVEGRAM_PATTERN = re.compile(r"@?LivegramBot", re.IGNORECASE)


def is_livegram_message(text: str | None) -> bool:
    return bool(text and _LIVEGRAM_PATTERN.search(text))


async def safe_edit_message(
    message: Message,
    text: str,
    *,
    buttons: list[list[Button]] | None = None,
) -> Message:
    try:
        return await message.edit(text, buttons=buttons)
    except MessageNotModifiedError:
        return message
    except MessageIdInvalidError:
        return await message.respond(text, buttons=buttons)


async def send_transient_steps(event, steps: list[str], delay_seconds: float = 3.0) -> None:
    for step in steps:
        msg = await event.respond(step)
        await asyncio.sleep(delay_seconds)
        try:
            await msg.delete()
        except Exception:
            pass


async def delete_livegram_message(message: Message) -> bool:
    text = message.text or message.message or ""
    if not is_livegram_message(text):
        return False
    try:
        await message.delete()
        return True
    except Exception as exc:
        logger.debug("Could not delete Livegram message {}: {}", message.id, exc)
        return False


async def purge_livegram_messages(
    bot: TelegramClient,
    chat_id: int,
    *,
    limit: int = 15,
    delay_seconds: float = 1.5,
) -> int:
    """Scan recent chat messages and delete any Livegram promo messages."""
    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)

    deleted = 0
    try:
        async for message in bot.iter_messages(chat_id, limit=limit):
            if await delete_livegram_message(message):
                deleted += 1
    except Exception as exc:
        logger.debug("Livegram purge failed for chat {}: {}", chat_id, exc)
    return deleted
