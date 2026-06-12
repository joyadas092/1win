from __future__ import annotations

import re
from typing import Any

from loguru import logger
from telethon import TelegramClient, events

from bot.config import settings
from bot.database import DepositRepo, PlatformAccountRepo, UserRepo
from bot.models import Deposit
from bot.utils import utcnow_str

RE_REGISTER = re.compile(r"\bNew-User-Registered-(\d+)\b", re.IGNORECASE)
RE_DEPOSIT = re.compile(r"\bUser-(\d+)-Deposited-([0-9]+(?:\.[0-9]{1,2})?)(?:-(Firsttime))?\b", re.IGNORECASE)


def parse_log_message(text: str) -> dict[str, Any] | None:
    if match := RE_REGISTER.search(text):
        return {"type": "registration", "platform_id": match.group(1)}

    if match := RE_DEPOSIT.search(text):
        return {
            "type": "deposit",
            "platform_id": match.group(1),
            "amount": float(match.group(2)),
            "is_first": bool(match.group(3)),
        }

    return None


def register_log_monitor(bot_client: TelegramClient) -> None:
    @bot_client.on(events.NewMessage(chats=settings.log_channel_id))
    async def _handle(event: events.NewMessage.Event) -> None:
        parsed = parse_log_message(event.raw_text or "")
        if not parsed:
            return

        platform_id = parsed["platform_id"]
        now = utcnow_str()

        if parsed["type"] == "registration":
            await PlatformAccountRepo.record_registration(platform_id, now)
            logger.info("Platform registration saved: 1WIN ID={}", platform_id)

            user = await UserRepo.get_by_platform_id(platform_id)
            if not user or user.is_registered:
                return

            await UserRepo.update_fields(user.telegram_id, is_registered=True)
            await _safe_notify(
                bot_client,
                user.telegram_id,
                f"✅ **Registration Confirmed**\n\n🆔 1WIN ID: `{platform_id}`",
            )
            return

        await PlatformAccountRepo.record_deposit(platform_id, parsed["amount"], now)
        await DepositRepo.insert(
            Deposit(
                platform_id=platform_id,
                amount=parsed["amount"],
                is_first_deposit=parsed["is_first"],
                created_at=now,
            )
        )
        logger.info("Platform deposit saved: 1WIN ID={} amount={}", platform_id, parsed["amount"])

        user = await UserRepo.get_by_platform_id(platform_id)
        if not user:
            return

        record = await PlatformAccountRepo.get(platform_id)
        await UserRepo.update_fields(
            user.telegram_id,
            is_deposited=True,
            deposit_amount=record.total_deposit if record else user.deposit_amount + parsed["amount"],
        )
        message = (
            f"💰 **Deposit Recorded**\n\n"
            f"🆔 1WIN ID: `{platform_id}`\n"
            f"💵 Amount: **INR {parsed['amount']:.2f}**"
        )
        if parsed["is_first"]:
            message += "\n\n✅ First deposit verified. You can now use signals."
        await _safe_notify(bot_client, user.telegram_id, message)

    logger.info("Log monitor registered for channel {}", settings.log_channel_id)


async def _safe_notify(bot: TelegramClient, telegram_id: int, message: str) -> None:
    try:
        await bot.send_message(telegram_id, message)
    except Exception as exc:
        logger.error("Failed to notify user {}: {}", telegram_id, exc)
