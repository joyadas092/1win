from __future__ import annotations

from telethon import TelegramClient, events

from bot.config import settings
from bot.database import UserRepo
from bot.handlers.base import ensure_user, reject_if_maintenance
from bot.handlers.bind import send_bind_prompt
from bot.handlers.profile import profile_text
from bot.keyboards import main_keyboard


def register_stats_handlers(bot: TelegramClient) -> None:
    @bot.on(events.NewMessage(pattern=r"^/(profile|stats)$"))
    async def _profile_cmd(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        user = await ensure_user(event)
        await _respond_my_id(event, user)

    @bot.on(events.NewMessage(pattern=r"(?i)^/my_ID$"))
    async def _my_id_cmd(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        user = await ensure_user(event)
        await _respond_my_id(event, user)

    @bot.on(events.CallbackQuery(data=b"profile"))
    async def _profile_cb(event: events.CallbackQuery.Event) -> None:
        if await reject_if_maintenance(event):
            return
        user = await ensure_user(event)
        await event.edit(profile_text(user), buttons=main_keyboard())

    @bot.on(events.NewMessage(pattern=r"^🆔 My ID$"))
    async def _my_id_button(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        user = await ensure_user(event)
        await _respond_my_id(event, user)

    @bot.on(events.NewMessage(pattern=r"^/referral$"))
    async def _referral(event: events.NewMessage.Event) -> None:
        user = await ensure_user(event)
        me = await bot.get_me()
        await event.respond(
            f"🔗 **Your Referral Link**\n\n"
            f"https://t.me/{me.username}?start=ref_{user.telegram_id}\n\n"
            f"👥 Referrals: **{user.referral_count}**"
        )

    @bot.on(events.NewMessage(pattern=r"^/totals$"))
    async def _totals(event: events.NewMessage.Event) -> None:
        if not settings.is_admin(event.sender_id):
            return
        from bot.database import DepositRepo, PlatformAccountRepo

        users = await UserRepo.count()
        registered = await UserRepo.count_registered()
        deposited = await UserRepo.count_deposited()
        platform_total = await PlatformAccountRepo.count()
        dep_amount = await DepositRepo.total_amount()
        await event.respond(
            "📊 **Totals**\n\n"
            f"👥 Telegram users: **{users}**\n"
            f"🆔 Platform records: **{platform_total}**\n"
            f"✅ Verified users: **{registered}**\n"
            f"💰 Deposited users: **{deposited}**\n"
            f"💵 Deposit amount: **INR {dep_amount:.2f}**"
        )


async def _respond_my_id(event, user) -> None:
    if user.platform_id:
        await event.respond(profile_text(user), buttons=main_keyboard())
        return
    await send_bind_prompt(event)
