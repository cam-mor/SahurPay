import unittest
from decimal import Decimal

from app import Person, Product, Receipt, ReceiptItem, Store, parse_money


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


if __name__ == "__main__":
    unittest.main()
