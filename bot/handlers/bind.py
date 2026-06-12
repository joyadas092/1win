from __future__ import annotations

import re
from pathlib import Path

from telethon import TelegramClient, events

from bot.config import settings
from bot.database import UserRepo
from bot.handlers.base import ensure_user, reject_if_maintenance
from bot.keyboards import main_keyboard
from bot.services import apply_platform_verification
from bot.utils import format_dt
from bot.utils.telegram import safe_edit_message

_awaiting_bind: dict[int, str] = {}


def is_awaiting_bind(user_id: int) -> bool:
    return user_id in _awaiting_bind
_BIND_TUTORIAL_IMAGE = Path(__file__).resolve().parent.parent / "assets" / "player_id_tutorial.png"
_MENU_BUTTONS = {
    "🧠 AI Signal",
    "⚡ Quick Signal",
    "💯 100% Win",
    "🆔 My ID",
    "✏️ Edit ID",
    "ℹ️ How It Works",
    "🎛 Main Menu",
    "📚 All Tutorials",
    "✈️ What is Aviator",
    "📡 Follow Signals",
    "💳 Deposit",
    "💸 Withdraw",
}


def register_bind_handlers(bot: TelegramClient) -> None:
    @bot.on(events.NewMessage(pattern=r"^/bind(?:\s+(\d+))?$"))
    async def _bind_cmd(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        await ensure_user(event)
        one_win_id = event.pattern_match.group(1)
        if not one_win_id:
            _awaiting_bind[event.sender_id] = "bind"
            await send_bind_prompt(event)
            return
        await _save_1win_id(event, one_win_id, mode="bind")

    @bot.on(events.NewMessage(pattern=r"^/editid(?:\s+(\d+))?$"))
    async def _edit_id_cmd(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        one_win_id = event.pattern_match.group(1)
        if not one_win_id:
            _awaiting_bind[event.sender_id] = "edit"
            await send_bind_prompt(event, title="✏️ Enter your new 1WIN ID")
            return
        await _save_1win_id(event, one_win_id, mode="edit")

    @bot.on(events.CallbackQuery(data=b"how_to_get_id"))
    async def _how_to_get_id_cb(event: events.CallbackQuery.Event) -> None:
        if await reject_if_maintenance(event):
            return
        _awaiting_bind[event.sender_id] = "bind"
        await event.answer()
        await send_bind_prompt(event)

    @bot.on(events.CallbackQuery(data=b"edit_id"))
    async def _edit_id_cb(event: events.CallbackQuery.Event) -> None:
        if await reject_if_maintenance(event):
            return
        _awaiting_bind[event.sender_id] = "edit"
        await event.answer()
        await send_bind_prompt(event, title="✏️ Enter your new 1WIN ID")

    @bot.on(events.NewMessage(pattern=r"^✏️ Edit ID$"))
    async def _reply_edit_id(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        _awaiting_bind[event.sender_id] = "edit"
        await send_bind_prompt(event, title="✏️ Enter your new 1WIN ID")

    @bot.on(events.NewMessage())
    async def _capture_bind(event: events.NewMessage.Event) -> None:
        if not event.is_private or event.sender_id not in _awaiting_bind:
            return
        text = (event.raw_text or "").strip()
        if not text or text.startswith("/") or text in _MENU_BUTTONS:
            return
        mode = _awaiting_bind.pop(event.sender_id)
        await _save_1win_id(event, text, mode=mode)


async def send_bind_prompt(event, title: str = "🆔 Enter your 1WIN ID") -> None:
    caption = _ask_id_text(title)
    if _BIND_TUTORIAL_IMAGE.is_file():
        await event.respond(file=_BIND_TUTORIAL_IMAGE, message=caption, buttons=main_keyboard())
        return
    await event.respond(caption, buttons=main_keyboard())


async def _save_1win_id(event: events.NewMessage.Event, one_win_id: str, mode: str) -> None:
    user = await ensure_user(event)
    if not _valid_1win_id(one_win_id):
        await event.respond(
            "❌ **Invalid 1WIN ID**\n\n"
            f"Your ID must contain only numbers and be {settings.one_win_id_min_length}-"
            f"{settings.one_win_id_max_length} digits long.",
            buttons=main_keyboard(),
        )
        return

    existing = await UserRepo.get_by_platform_id(one_win_id)
    if existing and existing.telegram_id != user.telegram_id:
        await event.respond("🚫 This 1WIN ID is already linked to another Telegram account.")
        return

    reset_fields = {}
    if user.platform_id and user.platform_id != one_win_id:
        reset_fields = {"is_registered": False, "is_deposited": False, "deposit_amount": 0.0}

    await UserRepo.update_fields(user.telegram_id, platform_id=one_win_id, **reset_fields)

    status_msg = await event.respond(f"🔎 Verifying 1WIN ID `{one_win_id}` from database...")
    verification = await apply_platform_verification(user.telegram_id, one_win_id)
    refreshed = await UserRepo.get(user.telegram_id)

    action = "updated" if mode == "edit" else "linked"
    text = f"✅ **1WIN ID {action}:** `{one_win_id}`\n\n"
    if not verification["found"]:
        text += (
            "⚠️ **No records yet**\n\n"
            "This ID is not in our database yet.\n"
            "Please register using the button below and send your updated 1WIN Player ID."
        )
    else:
        text += (
            f"📝 Registration: {_yes_no(bool(refreshed and refreshed.is_registered))}\n"
            f"💰 Deposit: {_yes_no(bool(refreshed and refreshed.is_deposited))}\n"
            f"💵 Total deposits: **INR {verification.get('total_deposit', 0):.2f}**"
        )
        if verification.get("registered_at"):
            text += f"\n📅 Registered: {format_dt(verification['registered_at'])}"
        if verification.get("last_deposit_at"):
            text += f"\n🕒 Last deposit: {format_dt(verification['last_deposit_at'])}"

    await safe_edit_message(status_msg, text, buttons=main_keyboard())


def _valid_1win_id(one_win_id: str) -> bool:
    return bool(
        re.fullmatch(r"\d+", one_win_id)
        and settings.one_win_id_min_length <= len(one_win_id) <= settings.one_win_id_max_length
    )


def _ask_id_text(title: str) -> str:
    return (
        f"{title}\n\n"
        f"Please send belowyour Player ID ({settings.one_win_id_min_length}-"
        f"{settings.one_win_id_max_length} digits) only\n\n"
        "Don't have an account yet? Register first:\n\n"
        "👆 Your Player ID is located in your profile.\n"
        "Tap on the ID to copy it, then send the number here."
    )


def _yes_no(value: bool) -> str:
    return "✅ Found" if value else "❌ Not yet"
