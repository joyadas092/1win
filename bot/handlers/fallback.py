from __future__ import annotations

import re

from telethon import TelegramClient, events

from bot.config import settings
from bot.handlers.admin import is_awaiting_admin_input
from bot.handlers.base import ensure_user, reject_if_maintenance
from bot.handlers.bind import is_awaiting_bind
from bot.keyboards import main_keyboard
from bot.utils.flood import is_flooding, is_ignored, punish_spammer
from bot.utils.telegram import is_livegram_message

_FALLBACK_TEXT = (
    "🤑 **WIN Big with this bot!**\n\n"
    "Get 100% working Aviator AI signals.\n"
    "Tap /start to begin now."
)
_KNOWN_MESSAGE = re.compile(
    "|".join([
        r"^/start(?:\s+.+)?$",
        r"^/bind(?:\s+\d+)?$",
        r"^/editid(?:\s+\d+)?$",
        r"^/AI_signal$",
        r"^/Quick_signal$",
        r"^/strategy$",
        r"^(?:ℹ️ How It Works|🧠 AI Signal|⚡ Quick Signal|💯 100% Win)$",
        r"^/tutorial$",
        r"^/What_is_Aviator$",
        r"^/How_to_follow_Signals$",
        r"^/Deposit$",
        r"^/Withdraw$",
        r"^📚 All Tutorials$",
        r"^(?:✈️ What is Aviator|📡 Follow Signals|💳 Deposit|💸 Withdraw)$",
        r"^/(?:profile|stats)$",
        r"^/my_ID$",
        r"^🆔 My ID$",
        r"^/referral$",
        r"^/totals$",
        r"^/admin$",
        r"^/broadcast(?:\s+.+)?$",
        r"^✏️ Edit ID$",
        r"^/cancel$",
    ]),
    re.IGNORECASE,
)
# _KNOWN_MESSAGE = re.compile(
#     "|".join(
#         [
#             r"^/start(?:\s+.+)?$",
#             r"^/bind(?:\s+\d+)?$",
#             r"^/editid(?:\s+\d+)?$",
#             r"(?i)^/AI_signal$",
#             r"(?i)^/Quick_signal$",
#             r"(?i)^/strategy$",
#             r"^(?:ℹ️ How It Works|🧠 AI Signal|⚡ Quick Signal|💯 100% Win)$",
#             r"(?i)^/tutorial$",
#             r"(?i)^/What_is_Aviator$",
#             r"(?i)^/How_to_follow_Signals$",
#             r"(?i)^/Deposit$",
#             r"(?i)^/Withdraw$",
#             r"^📚 All Tutorials$",
#             r"^(?:✈️ What is Aviator|📡 Follow Signals|💳 Deposit|💸 Withdraw)$",
#             r"^/(?:profile|stats)$",
#             r"(?i)^/my_ID$",
#             r"^🆔 My ID$",
#             r"^/referral$",
#             r"^/totals$",
#             r"^/admin$",
#             r"^/broadcast(?:\s+.+)?$",
#             r"^✏️ Edit ID$",
#             r"^/cancel$",
#         ]
#     )
# )


def register_fallback_handlers(bot: TelegramClient) -> None:
    @bot.on(events.NewMessage())
    async def _unknown_message(event: events.NewMessage.Event) -> None:
        if not event.is_private or not event.sender_id:
            return
        if settings.is_admin(event.sender_id):
            return
        if await reject_if_maintenance(event):
            return
        if is_awaiting_bind(event.sender_id) or is_awaiting_admin_input(event.sender_id):
            return

        text = (event.raw_text or "").strip()
        if is_livegram_message(text):
            return
        if text.startswith("/"):
            return
        if text and _KNOWN_MESSAGE.fullmatch(text):
            return

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

        await ensure_user(event)
        await event.respond(_FALLBACK_TEXT)
