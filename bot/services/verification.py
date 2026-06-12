from __future__ import annotations

from typing import Any

from bot.config import settings
from bot.database import PlatformAccountRepo, UserRepo
from bot.models import PlatformAccount, User


async def apply_platform_verification(telegram_id: int, platform_id: str) -> dict[str, Any]:
    record = await PlatformAccountRepo.get(platform_id)
    if not record:
        return {"found": False, "is_registered": False, "has_deposited": False}

    await UserRepo.update_fields(
        telegram_id,
        is_registered=record.is_registered,
        is_deposited=record.has_deposited,
        deposit_amount=record.total_deposit,
    )
    return {
        "found": True,
        "is_registered": record.is_registered,
        "has_deposited": record.has_deposited,
        "registered_at": record.registered_at,
        "last_deposit_at": record.last_deposit_at,
        "total_deposit": record.total_deposit,
    }


def signal_access_message(user: User, record: PlatformAccount | None) -> str | None:
    if not user.platform_id:
        return (
            "🔒 **1WIN ID required**\n\n"
            "Link your Player ID first with /bind command before requesting signals."
        )
    if not record:
        return (
            "🔒 **Not verified yet**\n\n"
            f"1WIN ID `{user.platform_id}` is not in our records yet.\n"
            f"First Register with {settings.affiliate_url} and promo code `{settings.promo_code}`\n"
            "then complete a deposit, then bind your Player ID with /bind command and try again."
        )
    if not record.is_registered:
        return (
            "🔒 **Registration not found**\n\n"
            f"1WIN ID `{user.platform_id}` has no registration record yet."
        )
    if not record.has_deposited:
        return (
            "🔒 **Deposit not found**\n\n"
            f"1WIN ID `{user.platform_id}` is registered but has no deposit record yet."
        )
    return None


def strategy_access_message(user: User, record: PlatformAccount | None) -> str | None:
    blocked = signal_access_message(user, record)
    if not blocked:
        return None
    return (
        "🔒 **This is a Members Only Strategy**\n\n"
        "Sign up with Below link to unlock the **100% working method**.\n\n"
        f"🎁 Promo code: `{settings.promo_code}`\n"
        f"🔗 Register here: {settings.affiliate_url}\n\n"
        "After registering and depositing, bind your Player ID with /bind command."
    )
