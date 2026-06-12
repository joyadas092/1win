from __future__ import annotations

import time
from collections import defaultdict, deque

from bot.config import settings

_hits: dict[int, deque[float]] = defaultdict(deque)
_ignored_until: dict[int, float] = {}


def is_flooding(user_id: int) -> bool:
    now = time.monotonic()
    window_start = now - settings.flood_window
    hits = _hits[user_id]
    while hits and hits[0] < window_start:
        hits.popleft()
    hits.append(now)
    return len(hits) > settings.flood_limit


def is_ignored(user_id: int) -> bool:
    until = _ignored_until.get(user_id)
    if until is None:
        return False
    if time.monotonic() >= until:
        _ignored_until.pop(user_id, None)
        return False
    return True


def punish_spammer(user_id: int) -> None:
    _ignored_until[user_id] = time.monotonic() + settings.spam_ignore_seconds
    _hits.pop(user_id, None)

