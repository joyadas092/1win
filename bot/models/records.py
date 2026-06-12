from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any


@dataclass
class User:
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    platform_id: str | None = None
    is_registered: bool = False
    is_deposited: bool = False
    deposit_amount: float = 0.0
    joined_at: str = ""
    requests_count: int = 0
    referral_by: int | None = None
    referral_count: int = 0
    status: str = "active"

    @property
    def is_verified(self) -> bool:
        return self.is_registered and self.is_deposited

    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> "User":
        doc = dict(doc)
        doc.pop("_id", None)
        allowed = {field.name for field in fields(cls)}
        return cls(**{key: value for key, value in doc.items() if key in allowed})

    def to_doc(self) -> dict[str, Any]:
        doc = {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "is_registered": self.is_registered,
            "is_deposited": self.is_deposited,
            "deposit_amount": float(self.deposit_amount),
            "joined_at": self.joined_at,
            "requests_count": int(self.requests_count),
            "referral_by": self.referral_by,
            "referral_count": int(self.referral_count),
            "status": self.status,
        }
        if self.platform_id is not None:
            doc["platform_id"] = self.platform_id
        return doc


@dataclass
class PlatformAccount:
    platform_id: str
    is_registered: bool = False
    registered_at: str | None = None
    has_deposited: bool = False
    last_deposit_at: str | None = None
    last_deposit_amount: float = 0.0
    total_deposit: float = 0.0
    updated_at: str = ""

    @property
    def is_verified(self) -> bool:
        return self.is_registered and self.has_deposited

    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> "PlatformAccount":
        doc = dict(doc)
        doc.pop("_id", None)
        return cls(**doc)

    def to_doc(self) -> dict[str, Any]:
        return {
            "platform_id": self.platform_id,
            "is_registered": self.is_registered,
            "registered_at": self.registered_at,
            "has_deposited": self.has_deposited,
            "last_deposit_at": self.last_deposit_at,
            "last_deposit_amount": float(self.last_deposit_amount),
            "total_deposit": float(self.total_deposit),
            "updated_at": self.updated_at,
        }


@dataclass
class Deposit:
    platform_id: str
    amount: float
    is_first_deposit: bool = False
    created_at: str = ""

    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> "Deposit":
        doc = dict(doc)
        doc.pop("_id", None)
        return cls(**doc)

    def to_doc(self) -> dict[str, Any]:
        return {
            "platform_id": self.platform_id,
            "amount": float(self.amount),
            "is_first_deposit": self.is_first_deposit,
            "created_at": self.created_at,
        }

