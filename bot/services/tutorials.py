from __future__ import annotations

import re
from dataclasses import dataclass

from loguru import logger
from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.tl.functions.messages import ForwardMessagesRequest

_PRIVATE_LINK = re.compile(r"^https?://t\.me/c/(\d+)/(\d+)$")


@dataclass(frozen=True)
class TutorialPost:
    key: str
    label: str
    channel_id: int
    message_id: int


TUTORIALS: dict[str, TutorialPost] = {}


def parse_private_post_link(url: str) -> tuple[int, int]:
    match = _PRIVATE_LINK.match((url or "").strip())
    if not match:
        raise ValueError(f"Invalid private post link: {url!r}")
    channel_id = int(f"-100{match.group(1)}")
    return channel_id, int(match.group(2))


async def init_tutorials(bot: TelegramClient, links: dict[str, tuple[str, str]]) -> None:
    TUTORIALS.clear()
    for key, (label, url) in links.items():
        if not url:
            logger.warning("Tutorial link missing for {}", key)
            continue
        channel_id, msg_id = parse_private_post_link(url)
        entity = await bot.get_entity(channel_id)
        msg = await bot.get_messages(entity, ids=msg_id)
        if not msg:
            raise ValueError(f"Tutorial message not found: {key} ({url})")
        TUTORIALS[key] = TutorialPost(key, label, channel_id, msg_id)
        logger.info("Tutorial ready: {} -> {}:{}", key, channel_id, msg_id)


async def send_tutorial(bot: TelegramClient, event, key: str) -> None:
    post = TUTORIALS.get(key)
    if not post:
        await event.respond("⚠️ This tutorial is not configured yet. Please try again later.")
        return
    try:
        await bot(
            ForwardMessagesRequest(
                from_peer=post.channel_id,
                id=[post.message_id],
                to_peer=event.chat_id,
                drop_author=True,
            )
        )
    except RPCError:
        logger.exception("Tutorial forward failed: {}", key)
        await event.respond("⚠️ Could not load this tutorial. Please try again later.")
