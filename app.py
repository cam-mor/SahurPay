from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_UP
from typing import Iterable
from uuid import uuid4


MONEY_QUANTUM = Decimal("0.01")


def quantize_money(value: Decimal | str | int) -> Decimal:
    """Convert a value to a two-decimal currency amount."""
    amount = value if isinstance(value, Decimal) else Decimal(str(value))
    return amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Person:
    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Person names cannot be empty.")


@dataclass(frozen=True)
class Store:
    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Store names cannot be empty.")


@dataclass(frozen=True)
class Product:
    name: str
    quantity: int
    unit_price: Decimal

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Product names cannot be empty.")
        if isinstance(self.quantity, bool) or self.quantity <= 0:
            raise ValueError("Product quantity must be greater than zero.")
        unit_price = quantize_money(self.unit_price)
        if unit_price < 0:
            raise ValueError("Product price cannot be negative.")
        object.__setattr__(self, "unit_price", unit_price)

    @property
    def total(self) -> Decimal:
        return quantize_money(self.unit_price * self.quantity)

    def with_unit_price(self, unit_price: Decimal) -> Product:
        return Product(self.name, self.quantity, unit_price)


@dataclass(frozen=True)
class ReceiptItem:
    product: Product
    participants: tuple[Person, ...]

    def __post_init__(self) -> None:
        if not self.participants:
            raise ValueError("Each product must have at least one participant.")
        names = [person.name for person in self.participants]
        if len(names) != len(set(names)):
            raise ValueError("A participant cannot be selected more than once.")

    @property
    def allocation(self) -> dict[str, Decimal]:
        """Return equal cent-accurate shares for this product."""
        share = (self.product.total / len(self.participants)).quantize(
            MONEY_QUANTUM, rounding=ROUND_DOWN
        )
        remainder = int(
            (self.product.total - share * len(self.participants)) * 100
        )
        return {
            person.name: quantize_money(
                share + (MONEY_QUANTUM if index < remainder else Decimal("0"))
            )
            for index, person in enumerate(self.participants)
        }


@dataclass(frozen=True)
class Receipt:
    store: Store
    people: tuple[Person, ...]
    items: tuple[ReceiptItem, ...]

    def __post_init__(self) -> None:
        names = [person.name for person in self.people]
        if len(names) != len(set(names)):
            raise ValueError("Person names must be unique.")
        known_names = set(names)
        for item in self.items:
            if any(person.name not in known_names for person in item.participants):
                raise ValueError("Every participant must belong to the receipt group.")

    @property
    def total(self) -> Decimal:
        return quantize_money(sum(item.product.total for item in self.items))

    def person_totals(self) -> dict[str, Decimal]:
        totals = {person.name: Decimal("0.00") for person in self.people}
        for item in self.items:
            for name, amount in item.allocation.items():
                totals[name] += amount
        return {name: quantize_money(amount) for name, amount in totals.items()}

    def with_item_price(self, item_index: int, unit_price: Decimal) -> Receipt:
        if item_index < 0 or item_index >= len(self.items):
            raise IndexError("Receipt item index is out of range.")
        updated_items = list(self.items)
        item = updated_items[item_index]
        updated_items[item_index] = ReceiptItem(
            item.product.with_unit_price(unit_price),
            item.participants,
        )
        return Receipt(self.store, self.people, tuple(updated_items))


@dataclass(frozen=True)
class PaymentSession:
    session_date: date
    people: tuple[Person, ...]
    receipts: tuple[Receipt, ...]
    session_id: str = ""

    def __post_init__(self) -> None:
        people = ensure_unique_people(self.people)
        if not people:
            raise ValueError("A payment session must have at least one person.")
        if not self.receipts:
            raise ValueError("A payment session must have at least one store.")
        session_id = self.session_id or uuid4().hex
        if not session_id.strip():
            raise ValueError("A payment session must have an ID.")
        people_names = tuple(person.name for person in people)
        for receipt in self.receipts:
            if tuple(person.name for person in receipt.people) != people_names:
                raise ValueError("All stores in a session must use the same people.")
        object.__setattr__(self, "people", people)
        object.__setattr__(self, "session_id", session_id)

    @property
    def total(self) -> Decimal:
        return quantize_money(sum(receipt.total for receipt in self.receipts))

    def person_totals(self) -> dict[str, Decimal]:
        totals = {person.name: Decimal("0.00") for person in self.people}
        for receipt in self.receipts:
            for name, amount in receipt.person_totals().items():
                totals[name] += amount
        return {name: quantize_money(amount) for name, amount in totals.items()}

    def with_date(self, session_date: date) -> PaymentSession:
        return PaymentSession(
            session_date=session_date,
            people=self.people,
            receipts=self.receipts,
            session_id=self.session_id,
        )

    def with_item_price(
        self, receipt_index: int, item_index: int, unit_price: Decimal
    ) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        updated_receipts[receipt_index] = updated_receipts[
            receipt_index
        ].with_item_price(item_index, unit_price)
        return PaymentSession(
            session_date=self.session_date,
            people=self.people,
            receipts=tuple(updated_receipts),
            session_id=self.session_id,
        )


def parse_money(value: str) -> Decimal:
    """Parse a non-negative decimal currency value."""
    try:
        amount = Decimal(value.strip())
    except InvalidOperation as error:
        raise ValueError("Enter a valid price, such as 12.50.") from error
    if not amount.is_finite() or amount < 0:
        raise ValueError("Price must be a non-negative number.")
    return quantize_money(amount)


def parse_positive_integer(value: str) -> int:
    try:
        number = int(value.strip())
    except ValueError as error:
        raise ValueError("Enter a whole number greater than zero.") from error
    if number <= 0:
        raise ValueError("Enter a whole number greater than zero.")
    return number


def parse_session_date(value: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError as error:
        raise ValueError("Enter a date in YYYY-MM-DD format.") from error


def ensure_unique_people(people: Iterable[Person]) -> tuple[Person, ...]:
    result = tuple(people)
    names = [person.name for person in result]
    if len(names) != len(set(names)):
        raise ValueError("Person names must be unique.")
    return result
