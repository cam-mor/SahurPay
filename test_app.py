import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from app import (
    PaymentSession,
    Person,
    Product,
    Receipt,
    ReceiptItem,
    Store,
    calculate_balances,
    calculate_settlements,
    filter_sessions,
    parse_money,
    parse_session_date,
)
from main import changes_menu, run
from storage import SessionRepository


class ReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.a = Person("A")
        self.b = Person("B")
        self.c = Person("C")

    def test_product_total_includes_quantity(self) -> None:
        product = Product("Coffee", 3, Decimal("2.50"))

        self.assertEqual(product.total, Decimal("7.50"))

    def test_equal_split_assigns_remainder_deterministically(self) -> None:
        item = ReceiptItem(
            Product("Shared item", 1, Decimal("10.00")),
            (self.a, self.b, self.c),
        )

        self.assertEqual(
            item.allocation,
            {
                "A": Decimal("3.34"),
                "B": Decimal("3.33"),
                "C": Decimal("3.33"),
            },
        )

    def test_receipt_total_and_person_totals_reconcile(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b, self.c),
            (
                ReceiptItem(Product("Everyone", 1, Decimal("10.00")), (self.a, self.b, self.c)),
                ReceiptItem(Product("For C", 2, Decimal("1.25")), (self.c,)),
                ReceiptItem(Product("For A and B", 1, Decimal("5.00")), (self.a, self.b)),
            ),
        )

        self.assertEqual(receipt.total, Decimal("17.50"))
        self.assertEqual(
            receipt.person_totals(),
            {
                "A": Decimal("5.84"),
                "B": Decimal("5.83"),
                "C": Decimal("5.83"),
            },
        )
        self.assertEqual(sum(receipt.person_totals().values()), receipt.total)

    def test_invalid_money_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_money("-1.00")

        with self.assertRaises(ValueError):
            parse_money("not money")

    def test_empty_participants_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ReceiptItem(Product("Item", 1, Decimal("1.00")), ())

    def test_session_aggregates_multiple_stores(self) -> None:
        first_store = Receipt(
            Store("Market"),
            (self.a, self.b, self.c),
            (ReceiptItem(Product("Bread", 1, Decimal("6.00")), (self.a, self.b)),),
        )
        second_store = Receipt(
            Store("Pharmacy"),
            (self.a, self.b, self.c),
            (ReceiptItem(Product("Soap", 2, Decimal("2.50")), (self.c,)),),
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b, self.c),
            (first_store, second_store),
        )

        self.assertEqual(session.total, Decimal("11.00"))
        self.assertEqual(
            session.person_totals(),
            {
                "A": Decimal("3.00"),
                "B": Decimal("3.00"),
                "C": Decimal("5.00"),
            },
        )

    def test_session_date_parser_requires_iso_date(self) -> None:
        self.assertEqual(parse_session_date("2026-11-09"), date(2026, 11, 9))
        with self.assertRaises(ValueError):
            parse_session_date("11/09/2026")

    def test_session_repository_round_trip(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b, self.c),
            (
                ReceiptItem(
                    Product("Shared item", 1, Decimal("10.00")),
                    (self.a, self.b, self.c),
                ),
            ),
        )
        original = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b, self.c),
            (receipt,),
            session_id="test-session",
        )

        with TemporaryDirectory() as directory:
            repository = SessionRepository(Path(directory) / "data" / "sessions.json")
            repository.save((original,))
            loaded = repository.load()

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].session_id, "test-session")
        self.assertEqual(loaded[0].session_date, original.session_date)
        self.assertEqual(loaded[0].total, original.total)
        self.assertEqual(loaded[0].person_totals(), original.person_totals())
        self.assertEqual(loaded[0].receipts[0].store.name, "Corner Store")

    def test_changing_item_price_recalculates_session_totals(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b, self.c),
            (
                ReceiptItem(
                    Product("Shared item", 2, Decimal("10.00")),
                    (self.a, self.b),
                ),
            ),
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b, self.c),
            (receipt,),
            session_id="editable-session",
        )

        updated = session.with_item_price(0, 0, Decimal("7.50"))

        self.assertEqual(updated.total, Decimal("15.00"))
        self.assertEqual(
            updated.person_totals(),
            {
                "A": Decimal("7.50"),
                "B": Decimal("7.50"),
                "C": Decimal("0.00"),
            },
        )
        self.assertEqual(session.total, Decimal("20.00"))

    def test_changes_menu_can_change_date_and_price(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b, self.c),
            (
                ReceiptItem(
                    Product("Shared item", 1, Decimal("10.00")),
                    (self.a, self.b, self.c),
                ),
            ),
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b, self.c),
            (receipt,),
            session_id="menu-session",
        )
        inputs = iter(["1", "2026-11-10", "2", "1", "1", "6.00", "16"])
        output: list[str] = []

        updated, changed = changes_menu(
            session, lambda _: next(inputs), output.append
        )

        self.assertTrue(changed)
        self.assertEqual(updated.session_date, date(2026, 11, 10))
        self.assertEqual(updated.total, Decimal("6.00"))
        self.assertIn("=== Changes ===", output)

    def test_changing_responsible_people_recalculates_totals(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b, self.c),
            (
                ReceiptItem(
                    Product("Shared item", 1, Decimal("10.00")),
                    (self.a, self.b),
                ),
            ),
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b, self.c),
            (receipt,),
            session_id="responsible-session",
        )

        updated = session.with_item_participants(
            0,
            0,
            (self.a, self.c),
        )

        self.assertEqual(
            updated.person_totals(),
            {
                "A": Decimal("5.00"),
                "B": Decimal("0.00"),
                "C": Decimal("5.00"),
            },
        )
        self.assertEqual(sum(updated.person_totals().values()), updated.total)

    def test_changes_menu_can_change_responsible_people(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b, self.c),
            (
                ReceiptItem(
                    Product("Shared item", 1, Decimal("10.00")),
                    (self.a, self.b),
                ),
            ),
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b, self.c),
            (receipt,),
            session_id="responsible-menu-session",
        )
        inputs = iter(["3", "1", "1", "1,3", "16"])
        output: list[str] = []

        updated, changed = changes_menu(
            session, lambda _: next(inputs), output.append
        )

        self.assertTrue(changed)
        self.assertEqual(
            updated.receipts[0].items[0].participants,
            (self.a, self.c),
        )
        self.assertIn("Currently responsible: A, B", output)

    def test_run_can_delete_and_cancel_session_deletion(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b, self.c),
            (
                ReceiptItem(
                    Product("Shared item", 1, Decimal("10.00")),
                    (self.a, self.b, self.c),
                ),
            ),
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b, self.c),
            (receipt,),
            session_id="delete-session",
        )

        with TemporaryDirectory() as directory:
            repository = SessionRepository(
                Path(directory) / "data" / "sessions.json"
            )
            repository.save((session,))

            cancel_inputs = iter(["4", "1", "n", "9"])
            run(
                input_fn=lambda _: next(cancel_inputs),
                output_fn=lambda _: None,
                repository=repository,
            )
            self.assertEqual(len(repository.load()), 1)

            delete_inputs = iter(["4", "1", "yes", "9"])
            run(
                input_fn=lambda _: next(delete_inputs),
                output_fn=lambda _: None,
                repository=repository,
            )
            self.assertEqual(repository.load(), ())

    def test_category_and_note_fields_round_trip(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b),
            (
                ReceiptItem(
                    Product(
                        "Milk",
                        2,
                        Decimal("2.50"),
                        "Groceries",
                        "Whole milk",
                    ),
                    (self.a, self.b),
                ),
            ),
            payer=self.a,
            category="Food",
            note="Weekly shop",
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b),
            (receipt,),
            session_id="category-session",
            category="Household",
            note="Roommate grocery run",
        )

        with TemporaryDirectory() as directory:
            repository = SessionRepository(
                Path(directory) / "data" / "sessions.json"
            )
            repository.save((session,))
            loaded = repository.load()

        self.assertEqual(loaded[0].category, "Household")
        self.assertEqual(loaded[0].note, "Roommate grocery run")
        self.assertEqual(loaded[0].receipts[0].category, "Food")
        self.assertEqual(loaded[0].receipts[0].note, "Weekly shop")
        product = loaded[0].receipts[0].items[0].product
        self.assertEqual(product.category, "Groceries")
        self.assertEqual(product.note, "Whole milk")

    def test_filter_search_includes_categories_and_notes(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b),
            (
                ReceiptItem(
                    Product(
                        "Milk",
                        1,
                        Decimal("3.00"),
                        "Groceries",
                        "Whole milk",
                    ),
                    (self.a,),
                ),
            ),
            category="Food",
            note="Weekly shop",
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b),
            (receipt,),
            session_id="search-category",
            category="Household",
            note="Roommate run",
        )

        self.assertEqual(
            len(filter_sessions((session,), query="groceries")),
            1,
        )
        self.assertEqual(
            len(filter_sessions((session,), query="roommate")),
            1,
        )
        self.assertEqual(
            len(filter_sessions((session,), query="weekly")),
            1,
        )

    def test_run_can_undo_category_edit_and_session_deletion(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b),
            (
                ReceiptItem(
                    Product("Milk", 1, Decimal("3.00")),
                    (self.a, self.b),
                ),
            ),
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b),
            (receipt,),
            session_id="undo-session",
        )

        with TemporaryDirectory() as directory:
            repository = SessionRepository(
                Path(directory) / "data" / "sessions.json"
            )
            repository.save((session,))

            inputs = iter([
                "3", "1", "10", "Groceries", "16",
                "8",
                "4", "1", "yes",
                "8",
                "9",
            ])
            run(
                input_fn=lambda _: next(inputs),
                output_fn=lambda _: None,
                repository=repository,
            )
            restored = repository.load()
            self.assertEqual(len(restored), 1)
            self.assertEqual(restored[0].category, "")

    def test_entity_edit_helpers_update_store_product_quantity_and_delete_item(self) -> None:
        receipt = Receipt(
            Store("Old Store"),
            (self.a, self.b, self.c),
            (
                ReceiptItem(Product("Old item", 1, Decimal("3.00")), (self.a,)),
                ReceiptItem(Product("Keep item", 2, Decimal("2.50")), (self.b,)),
            ),
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b, self.c),
            (receipt,),
            session_id="entity-edit",
        )

        updated = session.with_store_name(0, "New Store")
        updated = updated.with_item_name(0, 0, "New item")
        updated = updated.with_item_quantity(0, 0, 4)
        updated = updated.without_item(0, 1)

        self.assertEqual(updated.receipts[0].store.name, "New Store")
        self.assertEqual(updated.receipts[0].items[0].product.name, "New item")
        self.assertEqual(updated.receipts[0].items[0].product.quantity, 4)
        self.assertEqual(updated.total, Decimal("12.00"))

    def test_delete_store_preserves_remaining_store_receipts(self) -> None:
        first = Receipt(
            Store("Market"),
            (self.a, self.b),
            (ReceiptItem(Product("Bread", 1, Decimal("4.00")), (self.a,)),),
        )
        second = Receipt(
            Store("Pharmacy"),
            (self.a, self.b),
            (ReceiptItem(Product("Soap", 1, Decimal("5.00")), (self.b,)),),
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b),
            (first, second),
            session_id="store-delete",
        )

        updated = session.without_store(0)

        self.assertEqual(len(updated.receipts), 1)
        self.assertEqual(updated.receipts[0].store.name, "Pharmacy")
        self.assertEqual(updated.total, Decimal("5.00"))

    def test_settlements_use_payer_and_responsible_shares(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b, self.c),
            (
                ReceiptItem(
                    Product("Shared item", 1, Decimal("30.00")),
                    (self.a, self.b, self.c),
                ),
            ),
            payer=self.a,
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b, self.c),
            (receipt,),
            session_id="settlement",
        )

        balances = calculate_balances((session,))
        settlements = calculate_settlements((session,))

        self.assertEqual(
            balances,
            {
                "A": Decimal("20.00"),
                "B": Decimal("-10.00"),
                "C": Decimal("-10.00"),
            },
        )
        self.assertEqual(len(settlements), 2)
        self.assertEqual(settlements[0].from_person.name, "B")
        self.assertEqual(settlements[0].to_person.name, "A")
        self.assertEqual(settlements[0].amount, Decimal("10.00"))
        self.assertEqual(settlements[1].from_person.name, "C")
        self.assertEqual(settlements[1].to_person.name, "A")

    def test_filter_sessions_by_store_person_and_date(self) -> None:
        market = Receipt(
            Store("Market"),
            (self.a, self.b, self.c),
            (ReceiptItem(Product("Bread", 1, Decimal("4.00")), (self.a,)),),
        )
        pharmacy = Receipt(
            Store("Pharmacy"),
            (self.a, self.b, self.c),
            (ReceiptItem(Product("Soap", 1, Decimal("5.00")), (self.c,)),),
        )
        sessions = (
            PaymentSession(
                date(2026, 11, 8),
                (self.a, self.b, self.c),
                (market,),
                session_id="market-session",
            ),
            PaymentSession(
                date(2026, 11, 9),
                (self.a, self.b, self.c),
                (pharmacy,),
                session_id="pharmacy-session",
            ),
        )

        market_matches = filter_sessions(
            sessions,
            query="market",
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 8),
        )
        person_matches = filter_sessions(sessions, person_name="C")

        self.assertEqual(len(market_matches), 1)
        self.assertEqual(market_matches[0].session_id, "market-session")
        self.assertEqual(len(person_matches), 2)

    def test_backup_export_and_import_preserve_payer_and_entities(self) -> None:
        receipt = Receipt(
            Store("Corner Store"),
            (self.a, self.b, self.c),
            (
                ReceiptItem(
                    Product("Shared item", 2, Decimal("5.00")),
                    (self.a, self.b),
                ),
            ),
            payer=self.a,
        )
        session = PaymentSession(
            date(2026, 11, 9),
            (self.a, self.b, self.c),
            (receipt,),
            session_id="backup-session",
        )

        with TemporaryDirectory() as directory:
            source = SessionRepository(
                Path(directory) / "data" / "sessions.json"
            )
            backup_path = Path(directory) / "backup.json"
            source.save((session,))
            source.export_backup(backup_path)
            imported = source.import_backup(backup_path)

        self.assertEqual(len(imported), 1)
        self.assertEqual(imported[0].session_id, "backup-session")
        self.assertEqual(imported[0].receipts[0].payer.name, "A")
        self.assertEqual(imported[0].total, Decimal("10.00"))


if __name__ == "__main__":
    unittest.main()
