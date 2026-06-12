from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import motor.motor_asyncio
from loguru import logger

from bot.config import settings
from bot.models import Deposit, PlatformAccount, User

_client: motor.motor_asyncio.AsyncIOMotorClient | None = None
_db: motor.motor_asyncio.AsyncIOMotorDatabase | None = None


async def connect() -> None:
    global _client, _db
    _client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_uri)
    _db = _client[settings.mongo_db]
    await _ensure_indexes()
    logger.info("MongoDB connected: {}", settings.mongo_db)


async def disconnect() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB disconnected")


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("MongoDB is not connected. Call connect() first.")
    return _db


async def _ensure_indexes() -> None:
    db = get_db()
    await db.users.create_index("telegram_id", unique=True)

    # Legacy docs stored platform_id: null, which breaks unique indexes.
    await db.users.update_many({"platform_id": None}, {"$unset": {"platform_id": ""}})
    for index_name in ("platform_id_1", "platform_id_unique"):
        try:
            await db.users.drop_index(index_name)
        except Exception:
            pass
    await db.users.create_index(
        "platform_id",
        unique=True,
        name="platform_id_unique",
        partialFilterExpression={"platform_id": {"$type": "string"}},
    )

    await db.users.create_index("status")
    await db.users.create_index("joined_at")
    await db.deposits.create_index("platform_id")
    await db.deposits.create_index("created_at")
    await db.platform_accounts.create_index("platform_id", unique=True)
    await db.platform_accounts.create_index("registered_at")
    await db.platform_accounts.create_index("last_deposit_at")


class UserRepo:
    @staticmethod
    async def get(telegram_id: int) -> User | None:
        doc = await get_db().users.find_one({"telegram_id": telegram_id})
        return User.from_doc(doc) if doc else None

    @staticmethod
    async def get_by_platform_id(platform_id: str) -> User | None:
        doc = await get_db().users.find_one({"platform_id": platform_id})
        return User.from_doc(doc) if doc else None

    @staticmethod
    async def upsert(user: User) -> None:
        await get_db().users.update_one(
            {"telegram_id": user.telegram_id},
            {"$set": user.to_doc()},
            upsert=True,
        )

    @staticmethod
    async def update_fields(telegram_id: int, **fields: Any) -> None:
        unset = {key: "" for key, value in fields.items() if value is None}
        set_fields = {key: value for key, value in fields.items() if value is not None}
        update: dict[str, Any] = {}
        if set_fields:
            update["$set"] = set_fields
        if unset:
            update["$unset"] = unset
        if update:
            await get_db().users.update_one({"telegram_id": telegram_id}, update)

    @staticmethod
    async def increment(telegram_id: int, **fields: int | float) -> None:
        await get_db().users.update_one({"telegram_id": telegram_id}, {"$inc": fields})

    @staticmethod
    async def count() -> int:
        return await get_db().users.count_documents({})

    @staticmethod
    async def count_registered() -> int:
        return await get_db().users.count_documents({"is_registered": True})

    @staticmethod
    async def count_deposited() -> int:
        return await get_db().users.count_documents({"is_deposited": True})

    @staticmethod
    async def count_verified() -> int:
        return await get_db().users.count_documents({"is_registered": True, "is_deposited": True})

    @staticmethod
    async def recent(limit: int = 10) -> list[User]:
        cursor = get_db().users.find().sort("joined_at", -1).limit(limit)
        return [User.from_doc(doc) async for doc in cursor]

    @staticmethod
    async def all_active_ids() -> list[int]:
        cursor = get_db().users.find(
            {"$or": [{"status": "active"}, {"status": {"$exists": False}}]},
            {"telegram_id": 1},
        )
        return [doc["telegram_id"] async for doc in cursor]

    @staticmethod
    async def search(query: str) -> list[User]:
        regex = {"$regex": query, "$options": "i"}
        cursor = get_db().users.find(
            {"$or": [{"username": regex}, {"first_name": regex}, {"platform_id": regex}]}
        ).limit(20)
        return [User.from_doc(doc) async for doc in cursor]

    @staticmethod
    async def platform_id_exists(platform_id: str) -> bool:
        return bool(await get_db().users.count_documents({"platform_id": platform_id}, limit=1))

    @staticmethod
    async def total_requests() -> int:
        pipeline = [{"$group": {"_id": None, "total": {"$sum": "$requests_count"}}}]
        result = await get_db().users.aggregate(pipeline).to_list(1)
        return int(result[0]["total"]) if result else 0

    @staticmethod
    async def export_all() -> list[dict[str, Any]]:
        cursor = get_db().users.find({}, {"_id": 0})
        return [doc async for doc in cursor]

class PlatformAccountRepo:
    @staticmethod
    async def get(platform_id: str) -> PlatformAccount | None:
        doc = await get_db().platform_accounts.find_one({"platform_id": platform_id})
        return PlatformAccount.from_doc(doc) if doc else None

    @staticmethod
    async def record_registration(platform_id: str, registered_at: str) -> None:
        await get_db().platform_accounts.update_one(
            {"platform_id": platform_id},
            {
                "$set": {
                    "platform_id": platform_id,
                    "is_registered": True,
                    "registered_at": registered_at,
                    "updated_at": registered_at,
                }
            },
            upsert=True,
        )

    @staticmethod
    async def record_deposit(platform_id: str, amount: float, deposited_at: str) -> None:
        await get_db().platform_accounts.update_one(
            {"platform_id": platform_id},
            {
                "$set": {
                    "platform_id": platform_id,
                    "has_deposited": True,
                    "last_deposit_at": deposited_at,
                    "last_deposit_amount": float(amount),
                    "updated_at": deposited_at,
                },
                "$inc": {"total_deposit": float(amount)},
            },
            upsert=True,
        )

    @staticmethod
    async def count() -> int:
        return await get_db().platform_accounts.count_documents({})

    @staticmethod
    async def count_registered() -> int:
        return await get_db().platform_accounts.count_documents({"is_registered": True})

    @staticmethod
    async def count_deposited() -> int:
        return await get_db().platform_accounts.count_documents({"has_deposited": True})


class DepositRepo:
    @staticmethod
    async def insert(deposit: Deposit) -> None:
        await get_db().deposits.insert_one(deposit.to_doc())

    @staticmethod
    async def recent(limit: int = 10) -> list[Deposit]:
        cursor = get_db().deposits.find().sort("created_at", -1).limit(limit)
        return [Deposit.from_doc(doc) async for doc in cursor]

    @staticmethod
    async def total_amount() -> float:
        pipeline = [{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
        result = await get_db().deposits.aggregate(pipeline).to_list(1)
        return float(result[0]["total"]) if result else 0.0

    @staticmethod
    async def count() -> int:
        return await get_db().deposits.count_documents({})

