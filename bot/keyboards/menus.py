from __future__ import annotations

from telethon import Button

from bot.config import settings


def tutorial_inline_keyboard() -> list[list[Button]]:
    return [
        [Button.inline("✈️ What is Aviator?", b"tutorial:what_is_aviator")],
        [Button.inline("📡 How to Follow Signals", b"tutorial:how_to_follow_signals")],
        [Button.inline("💳 How to Deposit", b"tutorial:deposit")],
        [Button.inline("💸 How to Withdraw", b"tutorial:withdraw")],
    ]


def tutorial_reply_keyboard() -> list[list[Button]]:
    return [
        [Button.text("✈️ What is Aviator", resize=True), Button.text("📡 Follow Signals", resize=True)],
        [Button.text("💳 Deposit", resize=True), Button.text("💸 Withdraw", resize=True)],
        [Button.text("📚 All Tutorials", resize=True)],
    ]


def main_keyboard() -> list[list[Button]]:
    return [
        [Button.url("📝 Register on 1WIN", settings.affiliate_url)],
        [Button.inline("🎥 How to Get 1WIN ID", b"how_to_get_id")],
        [Button.inline("🆔 My 1WIN ID", b"profile"), Button.inline("✏️ Edit ID", b"edit_id")],
        [Button.inline("📚 Tutorials", b"tutorial:menu")],
        [Button.inline("ℹ️ How It Works", b"help")],
    ]


def main_reply_keyboard() -> list[list[Button]]:
    return [
        [Button.text("🧠 AI Signal", resize=True), Button.text("⚡ Quick Signal", resize=True)],
        [Button.text("💯 100% Win", resize=True), Button.text("🆔 My ID", resize=True)],
        [Button.text("✏️ Edit ID", resize=True), Button.text("ℹ️ How It Works", resize=True)],
        [Button.text("✈️ What is Aviator", resize=True), Button.text("📡 Follow Signals", resize=True)],
        [Button.text("💳 Deposit", resize=True), Button.text("💸 Withdraw", resize=True)],
        [Button.text("📚 All Tutorials", resize=True)],
    ]


def admin_keyboard() -> list[list[Button]]:
    return [
        [Button.inline("📊 Statistics", b"admin_stats"), Button.inline("👥 Users", b"admin_users")],
        [Button.inline("📢 Broadcast", b"admin_broadcast"), Button.inline("🔍 Search User", b"admin_search")],
        [Button.inline("📤 Export Users", b"admin_export"), Button.inline("🛠 Maintenance", b"admin_maintenance")],
        [Button.inline("❌ Close", b"admin_close")],
    ]
