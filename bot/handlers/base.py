from __future__ import annotations

from telethon import events

from bot.config import settings
from bot.database import UserRepo
from bot.models import User
from bot.utils import utcnow_str


def admin_required(user_id: int | None) -> bool:
    return settings.is_admin(user_id)


async def ensure_user(event: events.common.EventBuilder) -> User:
    sender = await event.get_sender()
    telegram_id = int(sender.id)
    existing = await UserRepo.get(telegram_id)
    if existing:
        updates = {}
        if existing.username != sender.username:
            updates["username"] = sender.username
            existing.username = sender.username
        if existing.first_name != sender.first_name:
            updates["first_name"] = sender.first_name
            existing.first_name = sender.first_name
        if updates:
            await UserRepo.update_fields(telegram_id, **updates)
        return existing

    user = User(
        telegram_id=telegram_id,
        username=sender.username,
        first_name=sender.first_name,
        joined_at=utcnow_str(),
    )
    await UserRepo.upsert(user)
    return user


async def reject_if_maintenance(event: events.common.EventBuilder) -> bool:
    if settings.maintenance_mode and not settings.is_admin(event.sender_id):
        await event.respond("🛠 **Maintenance Mode**\n\nPlease try again later.")
        return True
    return False
