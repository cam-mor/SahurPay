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
    parse_money,
    parse_session_date,
)
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


if __name__ == "__main__":
    unittest.main()
