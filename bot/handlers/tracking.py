from __future__ import annotations

from loguru import logger
from telethon import TelegramClient, events

from bot.handlers.base import ensure_user
from bot.utils.telegram import delete_livegram_message, is_livegram_message


def register_tracking_handlers(bot: TelegramClient) -> None:
    """Persist every real user and remove Livegram promo messages."""

    @bot.on(events.NewMessage())
    async def _track_private_user(event: events.NewMessage.Event) -> None:
        if not event.is_private or not event.sender_id:
            return

        text = event.raw_text or ""
        if is_livegram_message(text):
            await delete_livegram_message(event.message)
            raise events.StopPropagation

        sender = await event.get_sender()
        if getattr(sender, "bot", False):
            return

        try:
            await ensure_user(event)
        except Exception as exc:
            logger.warning("Failed to track user {}: {}", event.sender_id, exc)

    @bot.on(events.CallbackQuery())
    async def _track_callback_user(event: events.CallbackQuery.Event) -> None:
        if not event.is_private or not event.sender_id:
            return

        sender = await event.get_sender()
        if getattr(sender, "bot", False):
            return

        try:
            await ensure_user(event)
        except Exception as exc:
            logger.warning("Failed to track callback user {}: {}", event.sender_id, exc)
