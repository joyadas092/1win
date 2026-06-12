from __future__ import annotations

from telethon import events

from bot.database import PlatformAccountRepo, UserRepo
from bot.keyboards import main_keyboard
from bot.services import (
    STRATEGY_IMAGE,
    STRATEGY_TEXT,
    generate_personal_signal,
    generate_quick_signal,
    signal_access_message,
    strategy_access_message,
)
from bot.utils.telegram import send_transient_steps


async def send_quick_signal(event, user) -> None:
    record = await PlatformAccountRepo.get(user.platform_id) if user.platform_id else None
    blocked = signal_access_message(user, record)
    if blocked:
        await event.respond(blocked)
        return

    await UserRepo.increment(user.telegram_id, requests_count=1)
    await event.respond(generate_quick_signal())


async def send_ai_signal(event, user) -> None:
    record = await PlatformAccountRepo.get(user.platform_id) if user.platform_id else None
    blocked = signal_access_message(user, record)
    if blocked:
        await event.respond(blocked)
        return

    await UserRepo.increment(user.telegram_id, requests_count=1)
    await send_transient_steps(
        event,
        ["📡 Fetching Recent Aviator 🚀data...","Please wait " ,"🔍 Analysing With GPT AI...", "🎯 Sending best signal..."],
    )
    await event.respond(generate_personal_signal(user.platform_id))


async def send_strategy(event, user) -> None:
    record = await PlatformAccountRepo.get(user.platform_id) if user.platform_id else None
    blocked = strategy_access_message(user, record)
    if blocked:
        await event.respond(blocked, buttons=main_keyboard())
        return

    if STRATEGY_IMAGE.is_file():
        await event.respond(file=STRATEGY_IMAGE, message=STRATEGY_TEXT)
        return
    await event.respond(STRATEGY_TEXT)
