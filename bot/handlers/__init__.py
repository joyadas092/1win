from __future__ import annotations

from telethon import TelegramClient

from .admin import register_admin_handlers
from .bind import register_bind_handlers
from .fallback import register_fallback_handlers
from .start import register_start_handlers
from .stats import register_stats_handlers
from .tracking import register_tracking_handlers
from .tutorials import register_tutorial_handlers


def register_all_handlers(bot: TelegramClient) -> None:
    register_tracking_handlers(bot)
    register_start_handlers(bot)
    register_bind_handlers(bot)
    register_tutorial_handlers(bot)
    register_stats_handlers(bot)
    register_admin_handlers(bot)
    register_fallback_handlers(bot)
