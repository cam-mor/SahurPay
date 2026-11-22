from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TypeVar

from app import (
    PaymentSession,
    Person,
    Product,
    Receipt,
    ReceiptItem,
    Store,
    calculate_balances,
    calculate_settlements,
    ensure_unique_people,
    filter_sessions,
    parse_money,
    parse_positive_integer,
    parse_session_date,
)
from storage import SessionRepository, SessionStorageError


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
            return Person(value.strip() or fallback)

        people.append(
            prompt_until_valid(
                f"Name for person {index + 1} [{default}]: ",
                parse_name,
                input_fn,
                output_fn,
            )
        )
    try:
        return ensure_unique_people(people)
    except ValueError:
        output_fn("Error: Person names must be unique. Please enter them again.")
        return read_people(input_fn, output_fn)


def read_store(input_fn: Input, output_fn: Output) -> Store:
    return prompt_until_valid(
        "Store name: ",
        lambda value: Store(value.strip()),
        input_fn,
        output_fn,
    )


def read_session_date(
    input_fn: Input, output_fn: Output, default: date | None = None
) -> date:
    default_date = default or date.today()

    def parse_date_or_default(value: str) -> date:
        return default_date if not value.strip() else parse_session_date(value)

    return prompt_until_valid(
        f"Session date [{default_date.isoformat()}]: ",
        parse_date_or_default,
        input_fn,
        output_fn,
    )


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


def read_payer(
    people: tuple[Person, ...],
    input_fn: Input,
    output_fn: Output,
) -> Person | None:
    output_fn("Who paid this store? (blank if unknown)")
    for index, person in enumerate(people, start=1):
        output_fn(f"  {index}. {person.name}")

    def parse_payer(value: str) -> Person | None:
        if not value.strip():
            return None
        try:
            index = int(value)
        except ValueError as error:
            raise ValueError("Enter a person number or leave blank.") from error
        if index < 1 or index > len(people):
            raise ValueError("Choose a number from the people list.")
        return people[index - 1]

    return prompt_until_valid(
        "Payer (blank if unknown): ",
        parse_payer,
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
        items.append(ReceiptItem(Product(name, quantity, unit_price), participants))


def read_receipts(
    people: tuple[Person, ...], input_fn: Input, output_fn: Output
) -> tuple[Receipt, ...]:
    receipts: list[Receipt] = []
    output_fn("Enter stores. Leave the store name blank when finished.")
    while True:
        name = input_fn("Store name: ").strip()
        if not name:
            if receipts:
                return tuple(receipts)
            output_fn("Error: Enter at least one store.")
            continue
        store = Store(name)
        payer = read_payer(people, input_fn, output_fn)
        items = read_items(people, input_fn, output_fn)
        receipts.append(Receipt(store, people, items, payer))


def format_money(amount: Decimal) -> str:
    return f"${amount:.2f}"


def print_receipt(receipt: Receipt, output_fn: Output) -> None:
    output_fn(f"Store: {receipt.store.name}")
    if receipt.payer is not None:
        output_fn(f"Payer: {receipt.payer.name}")
    else:
        output_fn("Payer: unknown")
    for item in receipt.items:
        product = item.product
        output_fn(
            f"- {product.name}: {product.quantity} x "
            f"{format_money(product.unit_price)} = {format_money(product.total)}"
        )
        for name, amount in item.allocation.items():
            output_fn(f"    {name}: {format_money(amount)}")
    output_fn(f"Store total: {format_money(receipt.total)}")


def print_session(session: PaymentSession, output_fn: Output) -> None:
    output_fn("")
    output_fn("=== Payment Session ===")
    output_fn(f"Date: {session.session_date.isoformat()}")
    output_fn(f"Stores: {len(session.receipts)}")
    output_fn("")
    for index, receipt in enumerate(session.receipts, start=1):
        output_fn(f"--- Store {index} ---")
        print_receipt(receipt, output_fn)
        output_fn("")
    output_fn(f"Session total: {format_money(session.total)}")
    output_fn("")
    output_fn("=== Amounts Owed Across Session ===")
    for name, amount in session.person_totals().items():
        output_fn(f"{name}: {format_money(amount)}")


def create_session(input_fn: Input, output_fn: Output) -> PaymentSession:
    people = read_people(input_fn, output_fn)
    session_date = read_session_date(input_fn, output_fn)
    receipts = read_receipts(people, input_fn, output_fn)
    return PaymentSession(session_date, people, receipts)


def choose_session(
    sessions: tuple[PaymentSession, ...], input_fn: Input, output_fn: Output
) -> PaymentSession | None:
    if not sessions:
        output_fn("No saved payment sessions.")
        return None
    output_fn("Saved payment sessions:")
    for index, session in enumerate(sessions, start=1):
        output_fn(
            f"  {index}. {session.session_date.isoformat()} - "
            f"{len(session.receipts)} store(s) - {format_money(session.total)}"
        )

    def parse_index(value: str) -> PaymentSession | None:
        if not value.strip():
            return None
        try:
            index = int(value)
        except ValueError as error:
            raise ValueError("Enter a session number.") from error
        if index < 1 or index > len(sessions):
            raise ValueError("Choose a number from the saved sessions list.")
        return sessions[index - 1]

    return prompt_until_valid(
        "Session number (blank to return): ",
        parse_index,
        input_fn,
        output_fn,
    )


def confirm_session_deletion(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> bool:
    output_fn(
        f"Delete the {session.session_date.isoformat()} session "
        f"with {len(session.receipts)} store(s)?"
    )
    answer = input_fn("Are you sure? (y/N): ").strip().lower()
    if answer not in {"y", "yes"}:
        output_fn("Deletion cancelled.")
        return False
    return True


def search_sessions(
    sessions: tuple[PaymentSession, ...],
    input_fn: Input,
    output_fn: Output,
) -> None:
    query = input_fn("Search text (blank for all): ").strip()
    person_name = input_fn("Person filter (blank for all): ").strip() or None

    def parse_optional_date(value: str) -> date | None:
        return parse_session_date(value) if value.strip() else None

    start_date = prompt_until_valid(
        "Start date YYYY-MM-DD (blank for no start): ",
        parse_optional_date,
        input_fn,
        output_fn,
    )
    end_date = prompt_until_valid(
        "End date YYYY-MM-DD (blank for no end): ",
        parse_optional_date,
        input_fn,
        output_fn,
    )
    matches = filter_sessions(
        sessions,
        query=query,
        person_name=person_name,
        start_date=start_date,
        end_date=end_date,
    )
    output_fn("")
    output_fn(f"=== Session Search ({len(matches)} result(s)) ===")
    for session in matches:
        stores = ", ".join(receipt.store.name for receipt in session.receipts)
        output_fn(
            f"{session.session_date.isoformat()} | "
            f"{stores} | {format_money(session.total)}"
        )


def print_settlements(
    sessions: tuple[PaymentSession, ...],
    output_fn: Output,
) -> None:
    balances = calculate_balances(sessions)
    output_fn("")
    output_fn("=== Net Balances ===")
    if not balances:
        output_fn("No people recorded.")
        return
    for name, amount in balances.items():
        if amount > 0:
            output_fn(f"{name}: owed {format_money(amount)}")
        elif amount < 0:
            output_fn(f"{name}: owes {format_money(-amount)}")
        else:
            output_fn(f"{name}: settled")

    settlements = calculate_settlements(sessions)
    output_fn("")
    output_fn("=== Suggested Settlements ===")
    if not settlements:
        output_fn("No transfers needed.")
        return
    for settlement in settlements:
        output_fn(
            f"{settlement.from_person.name} pays "
            f"{settlement.to_person.name} "
            f"{format_money(settlement.amount)}"
        )


def backup_menu(
    repository: SessionRepository,
    input_fn: Input,
    output_fn: Output,
) -> tuple[PaymentSession, ...] | None:
    output_fn("")
    output_fn("=== Backup and Restore ===")
    output_fn("1. Export backup")
    output_fn("2. Import and replace")
    output_fn("3. Cancel")
    choice = input_fn("Choose an option: ").strip()
    if choice == "1":
        path_text = input_fn(
            "Export path [sahurpay-backup.json]: "
        ).strip()
        path = Path(path_text or "sahurpay-backup.json")
        try:
            repository.export_backup(path)
        except SessionStorageError as error:
            output_fn(f"Storage error: {error}")
            return None
        output_fn(f"Backup exported to {path}.")
        return None
    if choice == "2":
        path_text = input_fn("Backup path: ").strip()
        if not path_text:
            output_fn("Import cancelled.")
            return None
        try:
            imported = repository.import_backup(Path(path_text))
        except SessionStorageError as error:
            output_fn(f"Storage error: {error}")
            return None
        answer = input_fn(
            f"Replace all saved sessions with {len(imported)} imported session(s)? (y/N): "
        ).strip().lower()
        if answer not in {"y", "yes"}:
            output_fn("Import cancelled.")
            return None
        try:
            repository.save(imported)
        except SessionStorageError as error:
            output_fn(f"Storage error: {error}")
            return None
        output_fn("Backup imported.")
        return imported
    return None


def choose_store_index(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> int | None:
    output_fn("Stores in this session:")
    for index, receipt in enumerate(session.receipts, start=1):
        output_fn(f"  {index}. {receipt.store.name}")

    def parse_index(value: str) -> int | None:
        if not value.strip():
            return None
        try:
            index = int(value)
        except ValueError as error:
            raise ValueError("Enter a store number.") from error
        if index < 1 or index > len(session.receipts):
            raise ValueError("Choose a number from the stores list.")
        return index - 1

    return prompt_until_valid(
        "Store number (blank to return): ",
        parse_index,
        input_fn,
        output_fn,
    )


def choose_item_index(
    receipt: Receipt, input_fn: Input, output_fn: Output
) -> int | None:
    output_fn(f"Items at {receipt.store.name}:")
    for index, item in enumerate(receipt.items, start=1):
        output_fn(
            f"  {index}. {item.product.name} - "
            f"{item.product.quantity} x {format_money(item.product.unit_price)}"
        )

    def parse_index(value: str) -> int | None:
        if not value.strip():
            return None
        try:
            index = int(value)
        except ValueError as error:
            raise ValueError("Enter an item number.") from error
        if index < 1 or index > len(receipt.items):
            raise ValueError("Choose a number from the items list.")
        return index - 1

    return prompt_until_valid(
        "Item number (blank to return): ",
        parse_index,
        input_fn,
        output_fn,
    )


def change_date(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> PaymentSession:
    new_date = read_session_date(input_fn, output_fn, session.session_date)
    return session.with_date(new_date)


def change_item_price(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> PaymentSession:
    receipt_index = choose_store_index(session, input_fn, output_fn)
    if receipt_index is None:
        return session
    receipt = session.receipts[receipt_index]
    item_index = choose_item_index(receipt, input_fn, output_fn)
    if item_index is None:
        return session
    item = receipt.items[item_index]
    new_price = prompt_until_valid(
        f"New unit price for {item.product.name} "
        f"[{format_money(item.product.unit_price)}]: ",
        parse_money,
        input_fn,
        output_fn,
    )
    return session.with_item_price(receipt_index, item_index, new_price)


def change_responsible_people(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> PaymentSession:
    receipt_index = choose_store_index(session, input_fn, output_fn)
    if receipt_index is None:
        return session
    receipt = session.receipts[receipt_index]
    item_index = choose_item_index(receipt, input_fn, output_fn)
    if item_index is None:
        return session
    item = receipt.items[item_index]
    current_names = ", ".join(person.name for person in item.participants)
    output_fn(f"Currently responsible: {current_names}")
    participants = read_participants(session.people, input_fn, output_fn)
    return session.with_item_participants(
        receipt_index,
        item_index,
        participants,
    )


def change_store_name(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> PaymentSession:
    receipt_index = choose_store_index(session, input_fn, output_fn)
    if receipt_index is None:
        return session
    receipt = session.receipts[receipt_index]

    def parse_name(value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Store name cannot be empty.")
        return name

    name = prompt_until_valid(
        f"New store name [{receipt.store.name}]: ",
        parse_name,
        input_fn,
        output_fn,
    )
    return session.with_store_name(receipt_index, name)


def change_item_name(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> PaymentSession:
    receipt_index = choose_store_index(session, input_fn, output_fn)
    if receipt_index is None:
        return session
    receipt = session.receipts[receipt_index]
    item_index = choose_item_index(receipt, input_fn, output_fn)
    if item_index is None:
        return session
    item = receipt.items[item_index]

    def parse_name(value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Product name cannot be empty.")
        return name

    name = prompt_until_valid(
        f"New product name [{item.product.name}]: ",
        parse_name,
        input_fn,
        output_fn,
    )
    return session.with_item_name(receipt_index, item_index, name)


def change_item_quantity(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> PaymentSession:
    receipt_index = choose_store_index(session, input_fn, output_fn)
    if receipt_index is None:
        return session
    receipt = session.receipts[receipt_index]
    item_index = choose_item_index(receipt, input_fn, output_fn)
    if item_index is None:
        return session
    item = receipt.items[item_index]
    quantity = prompt_until_valid(
        f"New quantity for {item.product.name} [{item.product.quantity}]: ",
        parse_positive_integer,
        input_fn,
        output_fn,
    )
    return session.with_item_quantity(receipt_index, item_index, quantity)


def delete_item(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> PaymentSession:
    receipt_index = choose_store_index(session, input_fn, output_fn)
    if receipt_index is None:
        return session
    receipt = session.receipts[receipt_index]
    item_index = choose_item_index(receipt, input_fn, output_fn)
    if item_index is None:
        return session
    item = receipt.items[item_index]
    answer = input_fn(
        f"Delete {item.product.name}? (y/N): "
    ).strip().lower()
    if answer not in {"y", "yes"}:
        output_fn("Deletion cancelled.")
        return session
    try:
        return session.without_item(receipt_index, item_index)
    except ValueError as error:
        output_fn(f"Error: {error}")
        return session


def delete_store(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> PaymentSession:
    receipt_index = choose_store_index(session, input_fn, output_fn)
    if receipt_index is None:
        return session
    store_name = session.receipts[receipt_index].store.name
    answer = input_fn(
        f"Delete the {store_name} store receipt? (y/N): "
    ).strip().lower()
    if answer not in {"y", "yes"}:
        output_fn("Deletion cancelled.")
        return session
    try:
        return session.without_store(receipt_index)
    except ValueError as error:
        output_fn(f"Error: {error}")
        return session


def change_payer(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> PaymentSession:
    receipt_index = choose_store_index(session, input_fn, output_fn)
    if receipt_index is None:
        return session
    payer = read_payer(session.people, input_fn, output_fn)
    return session.with_payer(receipt_index, payer)


ChangeHandler = Callable[[PaymentSession, Input, Output], PaymentSession]
CHANGE_HANDLERS: dict[str, tuple[str, ChangeHandler]] = {
    "1": ("Change session date", change_date),
    "2": ("Change item price", change_item_price),
    "3": ("Change responsible people", change_responsible_people),
    "4": ("Change store name", change_store_name),
    "5": ("Change product name", change_item_name),
    "6": ("Change product quantity", change_item_quantity),
    "7": ("Delete product", delete_item),
    "8": ("Delete store", delete_store),
    "9": ("Change payer", change_payer),
}


def changes_menu(
    session: PaymentSession, input_fn: Input, output_fn: Output
) -> tuple[PaymentSession, bool]:
    current = session
    changed = False
    while True:
        output_fn("")
        output_fn("=== Changes ===")
        for number, (label, _) in CHANGE_HANDLERS.items():
            output_fn(f"{number}. {label}")
        return_option = str(max(int(number) for number in CHANGE_HANDLERS) + 1)
        output_fn(f"{return_option}. Return to main menu")
        choice = input_fn("Choose a change: ").strip()
        if choice == return_option:
            return current, changed
        handler_entry = CHANGE_HANDLERS.get(choice)
        if handler_entry is None:
            output_fn("Error: Choose one of the listed changes.")
            continue
        updated = handler_entry[1](current, input_fn, output_fn)
        changed = changed or updated != current
        current = updated


def run(
    input_fn: Input = input,
    output_fn: Output = print,
    repository: SessionRepository | None = None,
) -> PaymentSession | None:
    repository = repository or SessionRepository()
    try:
        sessions = list(repository.load())
    except SessionStorageError as error:
        output_fn(f"Storage error: {error}")
        return None

    output_fn("SahurPay")
    output_fn("Track payment sessions across multiple stores.")
    while True:
        output_fn("")
        output_fn("1. Log a new payment session")
        output_fn("2. View saved sessions")
        output_fn("3. Changes")
        output_fn("4. Delete a session")
        output_fn("5. Search sessions")
        output_fn("6. View settlements")
        output_fn("7. Backup and restore")
        output_fn("8. Exit")
        choice = input_fn("Choose an option: ").strip()

        if choice == "1":
            session = create_session(input_fn, output_fn)
            sessions.append(session)
            try:
                repository.save(sessions)
            except SessionStorageError as error:
                output_fn(f"Storage error: {error}")
                sessions.pop()
                continue
            output_fn("Payment session saved.")
            print_session(session, output_fn)
            continue

        if choice == "2":
            selected = choose_session(tuple(sessions), input_fn, output_fn)
            if selected is not None:
                print_session(selected, output_fn)
            continue

        if choice == "3":
            selected = choose_session(tuple(sessions), input_fn, output_fn)
            if selected is None:
                continue
            updated, changed = changes_menu(selected, input_fn, output_fn)
            if not changed:
                continue
            selected_index = sessions.index(selected)
            sessions[selected_index] = updated
            try:
                repository.save(sessions)
            except SessionStorageError as error:
                output_fn(f"Storage error: {error}")
                sessions[selected_index] = selected
                continue
            output_fn("Changes saved.")
            continue

        if choice == "4":
            selected = choose_session(tuple(sessions), input_fn, output_fn)
            if selected is None:
                continue
            if not confirm_session_deletion(selected, input_fn, output_fn):
                continue
            selected_index = sessions.index(selected)
            sessions.pop(selected_index)
            try:
                repository.save(sessions)
            except SessionStorageError as error:
                output_fn(f"Storage error: {error}")
                sessions.insert(selected_index, selected)
                continue
            output_fn("Session deleted.")
            continue

        if choice == "5":
            search_sessions(tuple(sessions), input_fn, output_fn)
            continue

        if choice == "6":
            print_settlements(tuple(sessions), output_fn)
            continue

        if choice == "7":
            imported = backup_menu(repository, input_fn, output_fn)
            if imported is not None:
                sessions = list(imported)
            continue

        if choice == "8":
            output_fn("Goodbye.")
            return sessions[-1] if sessions else None

        output_fn("Error: Choose 1, 2, 3, 4, 5, 6, 7, or 8.")


if __name__ == "__main__":
    run()
