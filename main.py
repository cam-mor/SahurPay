from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import TypeVar

from app import (
    Person,
    Product,
    Receipt,
    ReceiptItem,
    Store,
    ensure_unique_people,
    parse_money,
    parse_positive_integer,
)


Input = Callable[[str], str]
Output = Callable[[str], None]
DEFAULT_PEOPLE = ("A", "B", "C")
T = TypeVar("T")


def prompt_until_valid(
    prompt: str,
    parser: Callable[[str], T],
    input_fn: Input,
    output_fn: Output,
) -> T:
    while True:
        try:
            return parser(input_fn(prompt))
        except ValueError as error:
            output_fn(f"Error: {error}")


def read_people(input_fn: Input, output_fn: Output) -> tuple[Person, ...]:
    def parse_count(value: str) -> int:
        if not value.strip():
            return len(DEFAULT_PEOPLE)
        return parse_positive_integer(value)

    count = prompt_until_valid(
        "Number of people [3]: ", parse_count, input_fn, output_fn
    )
    people: list[Person] = []
    for index in range(count):
        default = (
            DEFAULT_PEOPLE[index]
            if index < len(DEFAULT_PEOPLE)
            else f"Person {index + 1}"
        )

        def parse_name(value: str, fallback: str = default) -> Person:
            name = value.strip() or fallback
            return Person(name)

        person = prompt_until_valid(
            f"Name for person {index + 1} [{default}]: ",
            parse_name,
            input_fn,
            output_fn,
        )
        people.append(person)
    try:
        return ensure_unique_people(people)
    except ValueError:
        output_fn("Error: Person names must be unique. Please enter them again.")
        return read_people(input_fn, output_fn)


def read_store(input_fn: Input, output_fn: Output) -> Store:
    def parse_store(value: str) -> Store:
        return Store(value.strip())

    return prompt_until_valid("Store name: ", parse_store, input_fn, output_fn)


def read_participants(
    people: tuple[Person, ...], input_fn: Input, output_fn: Output
) -> tuple[Person, ...]:
    output_fn("Choose who shares this product by number (for example: 1,3).")
    for index, person in enumerate(people, start=1):
        output_fn(f"  {index}. {person.name}")

    def parse_selection(value: str) -> tuple[Person, ...]:
        selected_indexes = [part.strip() for part in value.split(",")]
        if not value.strip() or any(not part for part in selected_indexes):
            raise ValueError("Select at least one person.")
        try:
            indexes = [int(part) for part in selected_indexes]
        except ValueError as error:
            raise ValueError("Use comma-separated person numbers.") from error
        if len(indexes) != len(set(indexes)):
            raise ValueError("Do not select a person more than once.")
        if any(index < 1 or index > len(people) for index in indexes):
            raise ValueError("Choose only numbers shown in the people list.")
        return tuple(people[index - 1] for index in indexes)

    return prompt_until_valid(
        "People responsible [1,2,3]: ",
        parse_selection,
        input_fn,
        output_fn,
    )


def read_items(
    people: tuple[Person, ...], input_fn: Input, output_fn: Output
) -> tuple[ReceiptItem, ...]:
    items: list[ReceiptItem] = []
    output_fn("Enter products. Leave the product name blank when finished.")
    while True:
        name = input_fn("Product name: ").strip()
        if not name:
            if items:
                return tuple(items)
            output_fn("Error: Enter at least one product.")
            continue

        quantity = prompt_until_valid(
            "Quantity: ", parse_positive_integer, input_fn, output_fn
        )
        unit_price = prompt_until_valid(
            "Unit price: ", parse_money, input_fn, output_fn
        )
        participants = read_participants(people, input_fn, output_fn)
        items.append(
            ReceiptItem(
                Product(name, quantity, unit_price), participants
            )
        )


def format_money(amount: Decimal) -> str:
    return f"${amount:.2f}"


def print_receipt(receipt: Receipt, output_fn: Output) -> None:
    output_fn("")
    output_fn("=== Receipt Summary ===")
    output_fn(f"Store: {receipt.store.name}")
    output_fn("")
    for item in receipt.items:
        product = item.product
        output_fn(
            f"- {product.name}: {product.quantity} x "
            f"{format_money(product.unit_price)} = {format_money(product.total)}"
        )
        for name, amount in item.allocation.items():
            output_fn(f"    {name}: {format_money(amount)}")
    output_fn("")
    output_fn(f"Receipt total: {format_money(receipt.total)}")
    output_fn("")
    output_fn("=== Amounts Owed ===")
    for name, amount in receipt.person_totals().items():
        output_fn(f"{name}: {format_money(amount)}")


def run(input_fn: Input = input, output_fn: Output = print) -> Receipt:
    output_fn("SahurPay")
    output_fn("Track a receipt and split each product among your group.")
    people = read_people(input_fn, output_fn)
    store = read_store(input_fn, output_fn)
    items = read_items(people, input_fn, output_fn)
    receipt = Receipt(store, people, items)
    print_receipt(receipt, output_fn)
    return receipt


if __name__ == "__main__":
    run()
