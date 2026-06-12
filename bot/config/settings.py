from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _parse_list(env_key: str, sep: str = ",") -> list[str]:
    raw = os.getenv(env_key, "")
    return [item.strip() for item in raw.split(sep) if item.strip()]


def _parse_int_list(env_key: str) -> list[int]:
    values: list[int] = []
    for item in _parse_list(env_key):
        try:
            values.append(int(item))
        except ValueError:
            continue
    return values


@dataclass(frozen=True)
class Settings:
    api_id: int = int(os.getenv("API_ID", "0") or "0")
    api_hash: str = os.getenv("API_HASH", "")
    bot_token: str = os.getenv("BOT_TOKEN", "")

    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db: str = os.getenv("MONGO_DB", "membership_bot")

    admin_ids: list[int] = field(default_factory=lambda: _parse_int_list("ADMIN_IDS"))
    log_channel_id: int = int(os.getenv("LOG_CHANNEL_ID", "0") or "0")
    force_join_channels: list[str] = field(default_factory=lambda: _parse_list("FORCE_JOIN_CHANNELS"))

    affiliate_url: str = os.getenv("AFFILIATE_URL", "https://one-vv3184.com/?open=register&p=7qjp")
    promo_code: str = os.getenv("PROMO_CODE", "WIN1300")
    how_to_get_id_url: str = os.getenv("HOW_TO_GET_ID_URL", "https://example.com/how-to-get-1win-id")
    tutorial_what_is_aviator: str = os.getenv("TUTORIAL_WHAT_IS_AVIATOR", "")
    tutorial_how_to_follow_signals: str = os.getenv("TUTORIAL_HOW_TO_FOLLOW_SIGNALS", "")
    tutorial_deposit: str = os.getenv("TUTORIAL_DEPOSIT", "")
    tutorial_withdraw: str = os.getenv("TUTORIAL_WITHDRAW", "")
    one_win_id_min_length: int = int(os.getenv("ONE_WIN_ID_MIN_LENGTH", "8") or "8")
    one_win_id_max_length: int = int(os.getenv("ONE_WIN_ID_MAX_LENGTH", "10") or "10")
    flood_limit: int = int(os.getenv("FLOOD_LIMIT", "5") or "5")
    flood_window: int = int(os.getenv("FLOOD_WINDOW", "10") or "10")
    spam_ignore_seconds: int = int(os.getenv("SPAM_IGNORE_SECONDS", "300") or "300")
    maintenance_mode: bool = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"

    def is_admin(self, user_id: int | None) -> bool:
        return bool(user_id and user_id in self.admin_ids)

    def validate(self) -> None:
        errors: list[str] = []
        if not self.api_id:
            errors.append("API_ID is missing")
        if not self.api_hash:
            errors.append("API_HASH is missing")
        if not self.bot_token:
            errors.append("BOT_TOKEN is missing")
        if not self.log_channel_id:
            errors.append("LOG_CHANNEL_ID is missing")
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {error}" for error in errors))


settings = Settings()
