from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from telethon import TelegramClient

from bot.database import NotificationRepo


def setup_scheduler(bot: TelegramClient) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(_complete_due_notifications, "interval", seconds=30, args=[bot], id="due_notifications")
    scheduler.start()
    logger.info("Scheduler started")
    return scheduler


async def _complete_due_notifications(bot: TelegramClient) -> None:
    due = await NotificationRepo.get_pending_expired()
    for notif_id, notif in due:
        if notif.message_id:
            try:
                await bot.send_message(notif.telegram_id, "Scheduled reminder completed.")
            except Exception as exc:
                logger.warning("Unable to send scheduled reminder {}: {}", notif_id, exc)
        await NotificationRepo.mark_completed(notif_id)

