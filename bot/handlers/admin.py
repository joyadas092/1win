from __future__ import annotations

import asyncio
import csv
import io
from datetime import datetime

from loguru import logger
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message

from bot.config import settings
from bot.database import DepositRepo, PlatformAccountRepo, UserRepo
from bot.handlers.base import admin_required
from bot.keyboards import admin_keyboard
from bot.utils import format_dt
from bot.utils.telegram import safe_edit_message

_awaiting_broadcast: set[int] = set()
_awaiting_search: set[int] = set()


def is_awaiting_admin_input(user_id: int) -> bool:
    return user_id in _awaiting_broadcast or user_id in _awaiting_search


def register_admin_handlers(bot: TelegramClient) -> None:
    @bot.on(events.NewMessage(pattern=r"^/admin$"))
    async def _admin(event: events.NewMessage.Event) -> None:
        if not admin_required(event.sender_id):
            return
        await event.respond(await _dashboard_text(), buttons=admin_keyboard())

    @bot.on(events.CallbackQuery(data=b"admin_stats"))
    async def _admin_stats_cb(event: events.CallbackQuery.Event) -> None:
        if not admin_required(event.sender_id):
            await event.answer("Unauthorized", alert=True)
            return
        await event.edit(await _stats_text(), buttons=admin_keyboard())

    @bot.on(events.CallbackQuery(data=b"admin_users"))
    async def _admin_users(event: events.CallbackQuery.Event) -> None:
        if not admin_required(event.sender_id):
            await event.answer("Unauthorized", alert=True)
            return
        recent = await UserRepo.recent(10)
        lines = ["👥 **Last 10 Users**\n"]
        for user in recent:
            verified = "✅" if user.is_verified else "❌"
            lines.append(
                f"`{user.telegram_id}` @{user.username or 'N/A'} - {verified} - {format_dt(user.joined_at)}"
            )
        await event.edit("\n".join(lines), buttons=admin_keyboard())

    @bot.on(events.CallbackQuery(data=b"admin_broadcast"))
    async def _admin_broadcast_prompt(event: events.CallbackQuery.Event) -> None:
        if not admin_required(event.sender_id):
            await event.answer("Unauthorized", alert=True)
            return
        _awaiting_broadcast.add(event.sender_id)
        await event.answer("Send your broadcast message now.", alert=True)
        await event.respond(
            "📢 **Broadcast Mode**\n\n"
            "Send any **text**, **photo**, **video**, or **post** to broadcast.\n"
            "You can also reply to a message with `/broadcast`.\n\n"
            "Send `/cancel` to exit broadcast mode."
        )

    @bot.on(events.NewMessage(pattern=r"^/broadcast(?:\s+(.+))?$"))
    async def _broadcast_cmd(event: events.NewMessage.Event) -> None:
        if not admin_required(event.sender_id):
            return
        _awaiting_broadcast.discard(event.sender_id)

        if event.is_reply:
            source = await event.get_reply_message()
            if source:
                await _do_broadcast(event, bot, source_message=source)
                return

        message = event.pattern_match.group(1)
        if message:
            await _do_broadcast(event, bot, text=message)
            return

        _awaiting_broadcast.add(event.sender_id)
        await event.respond(
            "📢 **Broadcast Mode**\n\n"
            "Send the message or post to broadcast, or use:\n"
            "• `/broadcast your text here`\n"
            "• Reply to any post with `/broadcast`\n\n"
            "Send /cancel to exit."
        )

    @bot.on(events.NewMessage())
    async def _capture_broadcast(event: events.NewMessage.Event) -> None:
        if not event.is_private or event.sender_id not in _awaiting_broadcast:
            return
        text = (event.raw_text or "").strip()
        if text.lower() == "/cancel":
            _awaiting_broadcast.discard(event.sender_id)
            await event.respond("❌ Broadcast cancelled.")
            return
        if text.startswith("/"):
            return
        _awaiting_broadcast.discard(event.sender_id)
        await _do_broadcast(event, bot, source_message=event.message)

    @bot.on(events.CallbackQuery(data=b"admin_search"))
    async def _admin_search_prompt(event: events.CallbackQuery.Event) -> None:
        if not admin_required(event.sender_id):
            await event.answer("Unauthorized", alert=True)
            return
        _awaiting_search.add(event.sender_id)
        await event.answer("Send username, name, or 1WIN ID.", alert=True)

    @bot.on(events.NewMessage())
    async def _capture_search(event: events.NewMessage.Event) -> None:
        if not event.is_private or event.sender_id not in _awaiting_search:
            return
        _awaiting_search.discard(event.sender_id)
        query = (event.raw_text or "").strip()
        results = await UserRepo.search(query)
        if not results:
            await event.respond(f"No users found for `{query}`.")
            return
        lines = [f"🔍 **Search `{query}`** - {len(results)} result(s)\n"]
        for user in results:
            lines.append(
                f"`{user.telegram_id}` @{user.username or 'N/A'}\n"
                f"🆔 1WIN ID: `{user.platform_id or 'N/A'}` | reg:{int(user.is_registered)} dep:{int(user.is_deposited)}"
            )
        await event.respond("\n".join(lines))

    @bot.on(events.CallbackQuery(data=b"admin_export"))
    async def _admin_export(event: events.CallbackQuery.Event) -> None:
        if not admin_required(event.sender_id):
            await event.answer("Unauthorized", alert=True)
            return
        await event.answer("📤 Generating export...", alert=False)
        users = await UserRepo.export_all()
        output = io.StringIO()
        if users:
            writer = csv.DictWriter(output, fieldnames=list(users[0].keys()))
            writer.writeheader()
            writer.writerows(users)
        content = io.BytesIO(output.getvalue().encode("utf-8"))
        content.name = f"users_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        await bot.send_file(event.sender_id, content, caption=f"📤 User export - {len(users)} records")

    @bot.on(events.CallbackQuery(data=b"admin_maintenance"))
    async def _admin_maintenance(event: events.CallbackQuery.Event) -> None:
        if not admin_required(event.sender_id):
            await event.answer("Unauthorized", alert=True)
            return
        current = settings.maintenance_mode
        object.__setattr__(settings, "maintenance_mode", not current)
        state = "enabled" if not current else "disabled"
        await event.answer(f"🛠 Maintenance mode {state}.", alert=True)
        logger.info("Maintenance mode toggled to {}", not current)

    @bot.on(events.CallbackQuery(data=b"admin_close"))
    async def _admin_close(event: events.CallbackQuery.Event) -> None:
        if admin_required(event.sender_id):
            await event.delete()


async def _dashboard_text() -> str:
    total = await UserRepo.count()
    registered = await UserRepo.count_registered()
    deposited = await UserRepo.count_deposited()
    verified = await UserRepo.count_verified()
    platform_total = await PlatformAccountRepo.count()
    requests = await UserRepo.total_requests()
    return (
        "🛠 **Admin Dashboard**\n\n"
        f"👥 Telegram Users: **{total}**\n"
        f"🆔 Platform Records: **{platform_total}**\n"
        f"✅ Registered Users: **{registered}**\n"
        f"💰 Deposited Users: **{deposited}**\n"
        f"✔️ Verified Users: **{verified}**\n"
        f"📨 Signal Requests: **{requests}**"
    )


async def _stats_text() -> str:
    total = await UserRepo.count()
    registered = await UserRepo.count_registered()
    deposited = await UserRepo.count_deposited()
    verified = await UserRepo.count_verified()
    requests = await UserRepo.total_requests()
    dep_total = await DepositRepo.total_amount()
    dep_count = await DepositRepo.count()
    platform_total = await PlatformAccountRepo.count()
    return (
        "📊 **Bot Statistics**\n\n"
        f"👥 Users: **{total}**\n"
        f"🆔 Platform records: **{platform_total}**\n"
        f"✅ Registered: **{registered}** ({_pct(registered, total)})\n"
        f"💰 Deposited: **{deposited}** ({_pct(deposited, total)})\n"
        f"✔️ Verified: **{verified}** ({_pct(verified, total)})\n"
        f"📨 Requests: **{requests}**\n"
        f"💵 Deposits: **{dep_count} x INR {dep_total:.2f}**"
    )


def _pct(part: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{part / total * 100:.1f}%"


async def _do_broadcast(
    event,
    bot: TelegramClient,
    *,
    text: str | None = None,
    source_message: Message | None = None,
) -> None:
    if not text and not source_message:
        await event.respond("❌ Broadcast message cannot be empty.")
        return
    if text and not text.strip():
        await event.respond("❌ Broadcast message cannot be empty.")
        return

    user_ids = await UserRepo.all_active_ids()
    total = len(user_ids)
    if total == 0:
        await event.respond("❌ No active users found to broadcast to.")
        return

    success = 0
    failed = 0
    status_msg = await event.respond(_broadcast_progress_text(0, total, success, failed))

    for index, user_id in enumerate(user_ids, start=1):
        try:
            if source_message is not None:
                await bot.forward_messages(user_id, source_message, drop_author=True)
            else:
                await bot.send_message(user_id, text)
            success += 1
        except Exception as exc:
            logger.warning("Broadcast failed for {}: {}", user_id, exc)
            failed += 1

        if index % 5 == 0 or index == total:
            await safe_edit_message(
                status_msg,
                _broadcast_progress_text(index, total, success, failed, done=index == total),
            )
        await asyncio.sleep(0.05)

    logger.info("Broadcast complete: success={} failed={} total={}", success, failed, total)


def _broadcast_progress_text(
    processed: int,
    total: int,
    success: int,
    failed: int,
    *,
    done: bool = False,
) -> str:
    percent = (processed / total * 100) if total else 0
    if done:
        return (
            "✅ **Broadcast Complete**\n\n"
            f"📊 Progress: **{processed}/{total}** (100%)\n"
            f"✅ Sent: **{success}**\n"
            f"❌ Failed: **{failed}**"
        )
    return (
        "📢 **Broadcast in progress...**\n\n"
        f"📊 Progress: **{processed}/{total}** ({percent:.1f}%)\n"
        f"✅ Sent: **{success}**\n"
        f"❌ Failed: **{failed}**"
    )
