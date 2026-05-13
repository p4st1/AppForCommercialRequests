import unittest

from app.ui.number_format_mixin import NumberFormatMixin


class NumberFormatMixinTests(unittest.TestCase):
    def test_fmt_number_formats_integer_without_decimal(self):
        self.assertEqual(NumberFormatMixin._fmt_number(10.0), "10")
        self.assertEqual(NumberFormatMixin._fmt_number(0), "0")

    def test_fmt_number_trims_trailing_zeroes(self):
        self.assertEqual(NumberFormatMixin._fmt_number(1.230000), "1.23")
        self.assertEqual(NumberFormatMixin._fmt_number(1.23456789), "1.234568")

    def test_round_money_uses_half_up_rounding(self):
        self.assertEqual(NumberFormatMixin._round_money("2.345"), 2.35)
        self.assertEqual(NumberFormatMixin._round_money("2.344"), 2.34)
        self.assertEqual(NumberFormatMixin._round_money(0), 0.0)


if __name__ == "__main__":
    unittest.main()
