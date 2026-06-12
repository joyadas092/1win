from __future__ import annotations

from telethon import TelegramClient, events

from bot.handlers.base import reject_if_maintenance
from bot.keyboards import tutorial_inline_keyboard
from bot.services.tutorials import send_tutorial

TUTORIAL_MENU_TEXT = (
    "📚 **Aviator Tutorials**\n\n"
    "New here? Watch these short guides before using signals:\n\n"
    "✈️ **What is Aviator** — game basics\n"
    "📡 **Follow Signals** — how to use bot signals\n"
    "💳 **Deposit** — add funds safely\n"
    "💸 **Withdraw** — cash out your winnings\n\n"
    "👇 Pick a tutorial below:"
)

_REPLY_BUTTONS: dict[str, str] = {
    "✈️ What is Aviator": "what_is_aviator",
    "📡 Follow Signals": "how_to_follow_signals",
    "💳 Deposit": "deposit",
    "💸 Withdraw": "withdraw",
}


def register_tutorial_handlers(bot: TelegramClient) -> None:
    @bot.on(events.NewMessage(pattern=r"(?i)^/tutorial$"))
    async def _tutorial_menu(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        await event.respond(TUTORIAL_MENU_TEXT, buttons=tutorial_inline_keyboard())

    @bot.on(events.NewMessage(pattern=r"(?i)^/What_is_Aviator$"))
    async def _what_is_aviator(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        await send_tutorial(bot, event, "what_is_aviator")

    @bot.on(events.NewMessage(pattern=r"(?i)^/How_to_follow_Signals$"))
    async def _how_to_follow_signals(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        await send_tutorial(bot, event, "how_to_follow_signals")

    @bot.on(events.NewMessage(pattern=r"(?i)^/Deposit$"))
    async def _deposit(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        await send_tutorial(bot, event, "deposit")

    @bot.on(events.NewMessage(pattern=r"(?i)^/Withdraw$"))
    async def _withdraw(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        await send_tutorial(bot, event, "withdraw")

    @bot.on(events.CallbackQuery(pattern=rb"tutorial:(.+)$"))
    async def _tutorial_cb(event: events.CallbackQuery.Event) -> None:
        if await reject_if_maintenance(event):
            return
        key = event.pattern_match.group(1).decode()
        await event.answer()
        if key == "menu":
            await event.respond(TUTORIAL_MENU_TEXT, buttons=tutorial_inline_keyboard())
            return
        await send_tutorial(bot, event, key)

    @bot.on(events.NewMessage(pattern=r"^📚 All Tutorials$"))
    async def _all_tutorials_reply(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        await event.respond(TUTORIAL_MENU_TEXT, buttons=tutorial_inline_keyboard())

    @bot.on(events.NewMessage(pattern=r"^(✈️ What is Aviator|📡 Follow Signals|💳 Deposit|💸 Withdraw)$"))
    async def _tutorial_reply(event: events.NewMessage.Event) -> None:
        if await reject_if_maintenance(event):
            return
        key = _REPLY_BUTTONS.get(event.raw_text or "")
        if key:
            await send_tutorial(bot, event, key)
