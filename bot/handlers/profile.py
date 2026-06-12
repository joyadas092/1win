from __future__ import annotations

from bot.utils import format_dt


def profile_text(user) -> str:
    return (
        "🆔 **My 1WIN ID**\n\n"
        f"👤 Telegram ID: `{user.telegram_id}`\n"
        f"🔖 Username: @{user.username or 'N/A'}\n"
        f"🆔 1WIN ID: `{user.platform_id or 'not linked'}`\n\n"
        f"📝 Registration: {_status(user.is_registered)}\n"
        f"💰 Deposit: {_status(user.is_deposited)}\n"
        f"💵 Total deposits: **INR {user.deposit_amount:.2f}**\n"
        f"📨 Signal requests: **{user.requests_count}**\n"
        f"📅 Joined: {format_dt(user.joined_at)}"
    )


def _status(value: bool) -> str:
    return "Verified ✅" if value else "Not found ❌"
