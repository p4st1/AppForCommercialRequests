import unittest

from tools import DatabaseTools as Tool


class NumberParsingTests(unittest.TestCase):
    def test_parse_float_accepts_decimal_comma_with_three_digits(self):
        self.assertEqual(Tool.parse_float("0,425", "Цена"), 0.425)

    def test_parse_float_accepts_mixed_separators(self):
        self.assertEqual(Tool.parse_float("1,000.50", "Цена"), 1000.5)
        self.assertEqual(Tool.parse_float("1.000,50", "Цена"), 1000.5)

    def test_parse_int_accepts_thousand_separator_comma(self):
        self.assertEqual(Tool.parse_int("1,000", "Кол-во", allow_zero=False), 1000)

    def test_parse_int_rejects_non_integer(self):
        with self.assertRaises(ValueError):
            Tool.parse_int("10,5", "Кол-во", allow_zero=False)

    def test_valid_num_accepts_decimal_comma(self):
        self.assertEqual(Tool.validNum("1,25"), 1.25)

    def test_num2text_keeps_tenths_place(self):
        self.assertEqual(Tool.num2text("1042,9"), "1 042,90")

    def test_parse_price_accepts_currency_codes(self):
        self.assertEqual(Tool.parsePrice("100 RUB"), ("₽", "100"))
        self.assertEqual(Tool.parsePrice("USD100"), ("$", "100"))
        self.assertEqual(Tool.parsePrice("100 EUR"), ("€", "100"))
        self.assertEqual(Tool.parsePrice("CNY 100"), ("¥", "100"))
        self.assertEqual(Tool.parsePrice("100 CYN"), ("¥", "100"))
        self.assertEqual(Tool.parsePrice("￥584,15"), ("¥", "584,15"))

    def test_format_price_accepts_currency_codes(self):
        self.assertEqual(Tool.formatPrice("100", "RUB"), "100,00₽")
        self.assertEqual(Tool.formatPrice("100", "USD"), "$100,00")
        self.assertEqual(Tool.formatPrice("100", "EUR"), "€100,00")
        self.assertEqual(Tool.formatPrice("100", "CYN"), "¥100,00")
        self.assertEqual(Tool.formatPrice("100", "￥"), "¥100,00")


if __name__ == "__main__":
    unittest.main()
