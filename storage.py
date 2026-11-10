from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from app import PaymentSession, Person, Product, Receipt, ReceiptItem, Store


DEFAULT_STORAGE_PATH = Path(__file__).with_name("data") / "sessions.json"


class SessionStorageError(Exception):
    """Raised when saved payment sessions cannot be read or written."""


def _person_by_name(people: tuple[Person, ...], name: str) -> Person:
    for person in people:
        if person.name == name:
            return person
    raise ValueError(f"Unknown participant in saved session: {name}.")


def _receipt_to_dict(receipt: Receipt) -> dict[str, Any]:
    return {
        "store": receipt.store.name,
        "items": [
            {
                "name": item.product.name,
                "quantity": item.product.quantity,
                "unit_price": str(item.product.unit_price),
                "participants": [person.name for person in item.participants],
            }
            for item in receipt.items
        ],
    }


def _session_to_dict(session: PaymentSession) -> dict[str, Any]:
    return {
        "id": session.session_id,
        "date": session.session_date.isoformat(),
        "people": [person.name for person in session.people],
        "receipts": [_receipt_to_dict(receipt) for receipt in session.receipts],
    }


def _session_from_dict(raw: Any) -> PaymentSession:
    if not isinstance(raw, dict):
        raise ValueError("A saved session must be an object.")
    people = tuple(Person(name) for name in raw["people"])
    receipts: list[Receipt] = []
    for raw_receipt in raw["receipts"]:
        if not isinstance(raw_receipt, dict):
            raise ValueError("A saved store receipt must be an object.")
        items: list[ReceiptItem] = []
        for raw_item in raw_receipt["items"]:
            if not isinstance(raw_item, dict):
                raise ValueError("A saved product must be an object.")
            participants = tuple(
                _person_by_name(people, name)
                for name in raw_item["participants"]
            )
            items.append(
                ReceiptItem(
                    Product(
                        raw_item["name"],
                        raw_item["quantity"],
                        Decimal(raw_item["unit_price"]),
                    ),
                    participants,
                )
            )
        receipts.append(Receipt(Store(raw_receipt["store"]), people, tuple(items)))
    return PaymentSession(
        session_date=date.fromisoformat(raw["date"]),
        people=people,
        receipts=tuple(receipts),
        session_id=raw["id"],
    )


class SessionRepository:
    def __init__(self, path: Path | str = DEFAULT_STORAGE_PATH) -> None:
        self.path = Path(path)

    def load(self) -> tuple[PaymentSession, ...]:
        if not self.path.exists():
            return ()
        try:
            raw_data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw_data, dict):
                raise ValueError("The session file must contain an object.")
            raw_sessions = raw_data.get("sessions")
            if not isinstance(raw_sessions, list):
                raise ValueError("The session file has no sessions list.")
            return tuple(_session_from_dict(raw) for raw in raw_sessions)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise SessionStorageError(
                f"Could not read saved sessions from {self.path}: {error}"
            ) from error

    def save(self, sessions: Iterable[PaymentSession]) -> None:
        payload = {
            "version": 1,
            "sessions": [_session_to_dict(session) for session in sessions],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f"{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                json.dump(payload, file, indent=2)
                file.write("\n")
            os.replace(temporary_path, self.path)
        except OSError as error:
            raise SessionStorageError(
                f"Could not save sessions to {self.path}: {error}"
            ) from error
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
