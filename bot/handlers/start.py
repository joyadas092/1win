from __future__ import annotations

import asyncio
import re
from pathlib import Path

from loguru import logger
from telethon import TelegramClient, events

from bot.config import settings
from bot.database import UserRepo
from bot.handlers.base import ensure_user, reject_if_maintenance
from bot.handlers.signals import send_ai_signal, send_quick_signal, send_strategy
from bot.keyboards import main_keyboard, main_reply_keyboard
from bot.utils.flood import is_flooding, is_ignored, punish_spammer
from bot.utils.telegram import purge_livegram_messages

_START_BANNER = Path(__file__).resolve().parent.parent / "assets" / "start_banner.png"


def register_start_handlers(bot: TelegramClient) -> None:
    @bot.on(events.NewMessage(pattern=r"^/start(?:@\w+)?(?:\s+(.+))?$"))
    async def _start(event: events.NewMessage.Event) -> None:
        if event.sender_id:
            if is_ignored(event.sender_id):
                return
            if is_flooding(event.sender_id):
                punish_spammer(event.sender_id)
                minutes = max(1, settings.spam_ignore_seconds // 60)
                await event.respond(
                    f"⚠️ **Too many messages.**\n\n"
                    f"Please slow down and try again in **{minutes} minute(s)**."
                )
                return
        if await reject_if_maintenance(event):
            return

        user = await ensure_user(event)
        payload = event.pattern_match.group(1)
        await _apply_referral(user.telegram_id, payload)

        text = (
            "👋 **Welcome to 1WIN Aviator Hack Bot**\n\n"
            "This is a 100% working AI Signal Bot that will help you to win 💸 big in 1WIN Aviator.\n\n"
            "New here? Watch 👉 /tutorial to know more.\n\n\n"
            "To Get the acceess of this Amazing Bot follow the steps below:\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 📝 Register with the button below.\n"
            f"2. 🎁 Use promo code: `{settings.promo_code}`\n"
            "3. 🆔 Then bind your 1WIN ID with /bind.\n\n"
            f"📌 Your status: {status_line(user)}"
        )
        await event.respond("🎛 **Main Menu**", buttons=main_reply_keyboard())
        if _START_BANNER.is_file():
            await event.respond(file=_START_BANNER, message=text, buttons=main_keyboard())
        else:
            await event.respond(text, buttons=main_keyboard())

        if event.chat_id:
            asyncio.create_task(purge_livegram_messages(bot, event.chat_id))

    @bot.on(events.CallbackQuery(data=b"help"))
    async def _help(event: events.CallbackQuery.Event) -> None:
        if await reject_if_maintenance(event):
            return
        await event.edit(how_it_works_text(), buttons=main_keyboard())

    @bot.on(events.NewMessage(pattern=r"(?i)^/AI_signal$"))
    async def _ai_signal_cmd(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        user = await ensure_user(event)
        await send_ai_signal(event, user)

    @bot.on(events.NewMessage(pattern=r"(?i)^/Quick_signal$"))
    async def _quick_signal_cmd(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        user = await ensure_user(event)
        await send_quick_signal(event, user)

    @bot.on(events.NewMessage(pattern=r"(?i)^/strategy$"))
    async def _strategy_cmd(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        user = await ensure_user(event)
        await send_strategy(event, user)

    @bot.on(events.NewMessage(pattern=r"^(ℹ️ How It Works|🧠 AI Signal|⚡ Quick Signal|💯 100% Win)$"))
    async def _reply_menu(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        text = event.raw_text or ""
        user = await ensure_user(event)

        if text == "ℹ️ How It Works":
            await event.respond(how_it_works_text(), buttons=main_keyboard())
            return
        if text == "⚡ Quick Signal":
            await send_quick_signal(event, user)
            return
        if text == "🧠 AI Signal":
            await send_ai_signal(event, user)
            return
        if text == "💯 100% Win":
            await send_strategy(event, user)


async def _apply_referral(telegram_id: int, payload: str | None) -> None:
    if not payload:
        return
    match = re.fullmatch(r"ref_(\d+)", payload.strip())
    if not match:
        return
    referrer_id = int(match.group(1))
    if referrer_id == telegram_id:
        return

    user = await UserRepo.get(telegram_id)
    if not user or user.referral_by:
        return
    referrer = await UserRepo.get(referrer_id)
    if not referrer:
        return

    await UserRepo.update_fields(telegram_id, referral_by=referrer_id)
    await UserRepo.increment(referrer_id, referral_count=1)
    logger.info("Referral linked: user={} referrer={}", telegram_id, referrer_id)


def status_line(user) -> str:
    if not user.platform_id:
        return "1WIN ID not linked"
    registered = "Registered ✅" if user.is_registered else "Not registered ❌"
    deposited = "Deposit ✅" if user.is_deposited else "No deposit ❌"
    return f"{registered}, {deposited}"


def how_it_works_text() -> str:
    return (
        "ℹ️ **How It Works**\n\n"
        f"1️⃣ Register on 1WIN using below link \n{settings.affiliate_url} \n with promo code `{settings.promo_code}`.\n"
        "2️⃣ Copy your numeric Player ID from your profile.\n"
        "3️⃣ Send /bind and paste your 1 WIN Player ID.\n"
        "4️⃣ The bot saves your registration and deposit details automatically.\n"
        "5️⃣ Once verified, use **🧠 AI Signal**, **⚡ Quick Signal**, or **💯 100% Win**."
    )
