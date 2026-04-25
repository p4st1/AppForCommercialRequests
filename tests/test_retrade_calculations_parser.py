import unittest

from ui_mixins.export_mixin import ExportMixin


class RetradeCalculationsParserTests(unittest.TestCase):
    def test_parse_uses_first_non_empty_row_as_headers(self):
        parsed = ExportMixin._parse_retrade_calculations(
            [
                [{"value": "", "currency": None}, {"value": None, "currency": None}],
                [{"value": "№", "currency": None}, {"value": "Цена", "currency": None}],
                [{"value": 1, "currency": None}, {"value": 1000, "currency": "RUB"}],
                [{"value": 2, "currency": None}, {"value": 5, "currency": None}],
            ]
        )
        self.assertEqual(
            parsed["headers"],
            ["№", "Цена"],
        )
        self.assertEqual(
            parsed["rows"],
            [
                [
                    {"value": 1, "currency": None},
                    {"value": 1000, "currency": "RUB"},
                ],
                [
                    {"value": 2, "currency": None},
                    {"value": 5, "currency": None},
                ],
            ],
        )

    def test_parse_skips_fully_empty_rows_and_keeps_all_data_rows(self):
        parsed = ExportMixin._parse_retrade_calculations(
            [
                [{"value": "Код", "currency": None}, {"value": "Значение", "currency": None}],
                [{"value": "", "currency": None}, {"value": None, "currency": None}],
                [{"value": 2, "currency": None}, {"value": 20, "currency": "USD"}],
                [{"value": 3, "currency": None}, {"value": "30 руб", "currency": "RUB"}],
            ]
        )
        self.assertEqual(parsed["headers"], ["Код", "Значение"])
        self.assertEqual(
            parsed["rows"],
            [
                [
                    {"value": 2, "currency": None},
                    {"value": 20, "currency": "USD"},
                ],
                [
                    {"value": 3, "currency": None},
                    {"value": "30 руб", "currency": "RUB"},
                ],
            ],
        )

    def test_parse_returns_empty_structure_for_empty_file(self):
        parsed = ExportMixin._parse_retrade_calculations(
            [
                [{"value": None, "currency": None}],
                [{"value": "", "currency": None}],
            ]
        )
        self.assertEqual(parsed, {"headers": [], "rows": []})

    def test_detect_currency_from_number_format(self):
        self.assertEqual(ExportMixin._detect_currency(1000, '#,##0.00 "₽"'), "RUB")
        self.assertEqual(ExportMixin._detect_currency(1000, '#,##0.00 "$"'), "USD")
        self.assertEqual(ExportMixin._detect_currency(1000, '#,##0.00 "EUR"'), "EUR")

    def test_detect_currency_from_string_fallback(self):
        self.assertEqual(ExportMixin._detect_currency("1000 руб", "General"), "RUB")
        self.assertEqual(ExportMixin._detect_currency("Total $100", "General"), "USD")
        self.assertEqual(ExportMixin._detect_currency("Amount 50 eur", "General"), "EUR")

    def test_format_number_ru(self):
        self.assertEqual(ExportMixin._format_number_ru(100000), "100 000,00")
        self.assertEqual(ExportMixin._format_number_ru(1500.5), "1 500,50")
        self.assertEqual(ExportMixin._format_number_ru(100), "100,00")

    def test_format_cell_displays_currency_suffix(self):
        self.assertEqual(
            ExportMixin._format_retrade_calculations_cell_for_display(
                {"value": 100000, "currency": "RUB"}
            ),
            "100 000,00 ₽",
        )
        self.assertEqual(
            ExportMixin._format_retrade_calculations_cell_for_display(
                {"value": 5000, "currency": "USD"}
            ),
            "5 000,00 $",
        )
        self.assertEqual(
            ExportMixin._format_retrade_calculations_cell_for_display(
                {"value": 1234.5, "currency": "EUR"}
            ),
            "1 234,50 €",
        )

    def test_format_cell_returns_non_numeric_as_is(self):
        self.assertEqual(
            ExportMixin._format_retrade_calculations_cell_for_display(
                {"value": "N/A", "currency": "RUB"}
            ),
            "N/A",
        )


if __name__ == "__main__":
    unittest.main()
