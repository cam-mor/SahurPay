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
    category: str = ""
    note: str = ""

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
        return Product(
            self.name,
            self.quantity,
            unit_price,
            self.category,
            self.note,
        )

    def with_name(self, name: str) -> Product:
        return Product(
            name,
            self.quantity,
            self.unit_price,
            self.category,
            self.note,
        )

    def with_quantity(self, quantity: int) -> Product:
        return Product(
            self.name,
            quantity,
            self.unit_price,
            self.category,
            self.note,
        )

    def with_category(self, category: str) -> Product:
        return Product(
            self.name,
            self.quantity,
            self.unit_price,
            category,
            self.note,
        )

    def with_note(self, note: str) -> Product:
        return Product(
            self.name,
            self.quantity,
            self.unit_price,
            self.category,
            note,
        )


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
    payer: Person | None = None
    category: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        names = [person.name for person in self.people]
        if len(names) != len(set(names)):
            raise ValueError("Person names must be unique.")
        known_names = set(names)
        if self.payer is not None and self.payer.name not in known_names:
            raise ValueError("The payer must belong to the receipt group.")
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
        return Receipt(
            self.store,
            self.people,
            tuple(updated_items),
            self.payer,
            self.category,
            self.note,
        )

    def with_item_participants(
        self, item_index: int, participants: tuple[Person, ...]
    ) -> Receipt:
        if item_index < 0 or item_index >= len(self.items):
            raise IndexError("Receipt item index is out of range.")
        updated_items = list(self.items)
        item = updated_items[item_index]
        updated_items[item_index] = ReceiptItem(item.product, participants)
        return Receipt(
            self.store,
            self.people,
            tuple(updated_items),
            self.payer,
            self.category,
            self.note,
        )

    def with_store_name(self, name: str) -> Receipt:
        return Receipt(
            Store(name),
            self.people,
            self.items,
            self.payer,
            self.category,
            self.note,
        )

    def with_item_name(self, item_index: int, name: str) -> Receipt:
        if item_index < 0 or item_index >= len(self.items):
            raise IndexError("Receipt item index is out of range.")
        updated_items = list(self.items)
        item = updated_items[item_index]
        updated_items[item_index] = ReceiptItem(
            item.product.with_name(name),
            item.participants,
        )
        return Receipt(
            self.store,
            self.people,
            tuple(updated_items),
            self.payer,
            self.category,
            self.note,
        )

    def with_item_quantity(self, item_index: int, quantity: int) -> Receipt:
        if item_index < 0 or item_index >= len(self.items):
            raise IndexError("Receipt item index is out of range.")
        updated_items = list(self.items)
        item = updated_items[item_index]
        updated_items[item_index] = ReceiptItem(
            item.product.with_quantity(quantity),
            item.participants,
        )
        return Receipt(
            self.store,
            self.people,
            tuple(updated_items),
            self.payer,
            self.category,
            self.note,
        )

    def without_item(self, item_index: int) -> Receipt:
        if item_index < 0 or item_index >= len(self.items):
            raise IndexError("Receipt item index is out of range.")
        updated_items = list(self.items)
        updated_items.pop(item_index)
        if not updated_items:
            raise ValueError("A store receipt must keep at least one item.")
        return Receipt(
            self.store,
            self.people,
            tuple(updated_items),
            self.payer,
            self.category,
            self.note,
        )

    def with_payer(self, payer: Person | None) -> Receipt:
        return Receipt(
            self.store,
            self.people,
            self.items,
            payer,
            self.category,
            self.note,
        )

    def with_category(self, category: str) -> Receipt:
        return Receipt(
            self.store,
            self.people,
            self.items,
            self.payer,
            category,
            self.note,
        )

    def with_note(self, note: str) -> Receipt:
        return Receipt(
            self.store,
            self.people,
            self.items,
            self.payer,
            self.category,
            note,
        )


@dataclass(frozen=True)
class PaymentSession:
    session_date: date
    people: tuple[Person, ...]
    receipts: tuple[Receipt, ...]
    session_id: str = ""
    category: str = ""
    note: str = ""

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
            category=self.category,
            note=self.note,
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
            category=self.category,
            note=self.note,
        )

    def with_item_participants(
        self,
        receipt_index: int,
        item_index: int,
        participants: tuple[Person, ...],
    ) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        updated_receipts[receipt_index] = updated_receipts[
            receipt_index
        ].with_item_participants(item_index, participants)
        return PaymentSession(
            session_date=self.session_date,
            people=self.people,
            receipts=tuple(updated_receipts),
            session_id=self.session_id,
            category=self.category,
            note=self.note,
        )

    def with_store_name(self, receipt_index: int, name: str) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        updated_receipts[receipt_index] = updated_receipts[
            receipt_index
        ].with_store_name(name)
        return PaymentSession(
            self.session_date,
            self.people,
            tuple(updated_receipts),
            self.session_id,
            self.category,
            self.note,
        )

    def with_item_name(
        self, receipt_index: int, item_index: int, name: str
    ) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        updated_receipts[receipt_index] = updated_receipts[
            receipt_index
        ].with_item_name(item_index, name)
        return PaymentSession(
            self.session_date,
            self.people,
            tuple(updated_receipts),
            self.session_id,
            self.category,
            self.note,
        )

    def with_item_quantity(
        self, receipt_index: int, item_index: int, quantity: int
    ) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        updated_receipts[receipt_index] = updated_receipts[
            receipt_index
        ].with_item_quantity(item_index, quantity)
        return PaymentSession(
            self.session_date,
            self.people,
            tuple(updated_receipts),
            self.session_id,
            self.category,
            self.note,
        )

    def without_item(
        self, receipt_index: int, item_index: int
    ) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        updated_receipts[receipt_index] = updated_receipts[
            receipt_index
        ].without_item(item_index)
        return PaymentSession(
            self.session_date,
            self.people,
            tuple(updated_receipts),
            self.session_id,
            self.category,
            self.note,
        )

    def without_store(self, receipt_index: int) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        updated_receipts.pop(receipt_index)
        if not updated_receipts:
            raise ValueError("A payment session must keep at least one store.")
        return PaymentSession(
            self.session_date,
            self.people,
            tuple(updated_receipts),
            self.session_id,
            self.category,
            self.note,
        )

    def with_payer(
        self, receipt_index: int, payer: Person | None
    ) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        updated_receipts[receipt_index] = updated_receipts[
            receipt_index
        ].with_payer(payer)
        return PaymentSession(
            self.session_date,
            self.people,
            tuple(updated_receipts),
            self.session_id,
            self.category,
            self.note,
        )

    def with_category(self, category: str) -> PaymentSession:
        return PaymentSession(
            self.session_date,
            self.people,
            self.receipts,
            self.session_id,
            category,
            self.note,
        )

    def with_note(self, note: str) -> PaymentSession:
        return PaymentSession(
            self.session_date,
            self.people,
            self.receipts,
            self.session_id,
            self.category,
            note,
        )

    def with_store_category(
        self, receipt_index: int, category: str
    ) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        updated_receipts[receipt_index] = updated_receipts[
            receipt_index
        ].with_category(category)
        return PaymentSession(
            self.session_date,
            self.people,
            tuple(updated_receipts),
            self.session_id,
            self.category,
            self.note,
        )

    def with_store_note(
        self, receipt_index: int, note: str
    ) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        updated_receipts[receipt_index] = updated_receipts[
            receipt_index
        ].with_note(note)
        return PaymentSession(
            self.session_date,
            self.people,
            tuple(updated_receipts),
            self.session_id,
            self.category,
            self.note,
        )

    def with_item_category(
        self, receipt_index: int, item_index: int, category: str
    ) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        receipt = updated_receipts[receipt_index]
        if item_index < 0 or item_index >= len(receipt.items):
            raise IndexError("Receipt item index is out of range.")
        updated_items = list(receipt.items)
        item = updated_items[item_index]
        updated_items[item_index] = ReceiptItem(
            item.product.with_category(category),
            item.participants,
        )
        updated_receipts[receipt_index] = Receipt(
            receipt.store,
            receipt.people,
            tuple(updated_items),
            receipt.payer,
            receipt.category,
            receipt.note,
        )
        return PaymentSession(
            self.session_date,
            self.people,
            tuple(updated_receipts),
            self.session_id,
            self.category,
            self.note,
        )

    def with_item_note(
        self, receipt_index: int, item_index: int, note: str
    ) -> PaymentSession:
        if receipt_index < 0 or receipt_index >= len(self.receipts):
            raise IndexError("Store receipt index is out of range.")
        updated_receipts = list(self.receipts)
        receipt = updated_receipts[receipt_index]
        if item_index < 0 or item_index >= len(receipt.items):
            raise IndexError("Receipt item index is out of range.")
        updated_items = list(receipt.items)
        item = updated_items[item_index]
        updated_items[item_index] = ReceiptItem(
            item.product.with_note(note),
            item.participants,
        )
        updated_receipts[receipt_index] = Receipt(
            receipt.store,
            receipt.people,
            tuple(updated_items),
            receipt.payer,
            receipt.category,
            receipt.note,
        )
        return PaymentSession(
            self.session_date,
            self.people,
            tuple(updated_receipts),
            self.session_id,
            self.category,
            self.note,
        )


@dataclass(frozen=True)
class Settlement:
    from_person: Person
    to_person: Person
    amount: Decimal


def calculate_balances(
    sessions: Iterable[PaymentSession],
) -> dict[str, Decimal]:
    session_list = tuple(sessions)
    people: dict[str, Person] = {}
    for session in session_list:
        for person in session.people:
            people.setdefault(person.name, person)
    balances = {name: Decimal("0.00") for name in people}

    for session in session_list:
        for receipt in session.receipts:
            if receipt.payer is not None:
                balances[receipt.payer.name] = quantize_money(
                    balances[receipt.payer.name] + receipt.total
                )
            for name, amount in receipt.person_totals().items():
                balances[name] = quantize_money(balances[name] - amount)
    return balances


def calculate_settlements(
    sessions: Iterable[PaymentSession],
) -> tuple[Settlement, ...]:
    session_list = tuple(sessions)
    balances = calculate_balances(session_list)
    named_people: dict[str, Person] = {}
    for session in session_list:
        for person in session.people:
            named_people.setdefault(person.name, person)

    creditors = [
        [name, quantize_money(amount)]
        for name, amount in balances.items()
        if amount > 0
    ]
    debtors = [
        [name, quantize_money(-amount)]
        for name, amount in balances.items()
        if amount < 0
    ]
    settlements: list[Settlement] = []
    debtor_index = 0
    creditor_index = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor_name, debt = debtors[debtor_index]
        creditor_name, credit = creditors[creditor_index]
        amount = min(debt, credit)
        if amount > 0:
            settlements.append(
                Settlement(
                    named_people[debtor_name],
                    named_people[creditor_name],
                    quantize_money(amount),
                )
            )
        debt = quantize_money(debt - amount)
        credit = quantize_money(credit - amount)
        debtors[debtor_index][1] = debt
        creditors[creditor_index][1] = credit
        if debt == 0:
            debtor_index += 1
        if credit == 0:
            creditor_index += 1
    return tuple(settlements)


def filter_sessions(
    sessions: Iterable[PaymentSession],
    query: str = "",
    person_name: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[PaymentSession, ...]:
    needle = query.strip().casefold()
    result: list[PaymentSession] = []
    for session in sessions:
        if start_date is not None and session.session_date < start_date:
            continue
        if end_date is not None and session.session_date > end_date:
            continue
        if person_name:
            if not any(
                person.name.casefold() == person_name.strip().casefold()
                for person in session.people
            ):
                continue
        if needle:
            searchable: list[str] = [session.session_id]
            searchable.extend([session.category, session.note])
            for person in session.people:
                searchable.append(person.name)
            for receipt in session.receipts:
                searchable.append(receipt.store.name)
                searchable.extend([receipt.category, receipt.note])
                if receipt.payer is not None:
                    searchable.append(receipt.payer.name)
                for item in receipt.items:
                    searchable.append(item.product.name)
                    searchable.extend([item.product.category, item.product.note])
            if not any(needle in value.casefold() for value in searchable):
                continue
        result.append(session)
    return tuple(sorted(result, key=lambda session: session.session_date, reverse=True))


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
