import unittest

import pandas as pd

from ui_mixins.export_mixin import ExportMixin


class RetradeCalculationsParserTests(unittest.TestCase):
    def test_parse_uses_first_non_empty_row_as_headers(self):
        dataframe = pd.DataFrame(
            [
                ["", "", ""],
                [None, None, None],
                ["№", "Наименование", "Цена"],
                ["1", "Позиция 1", 100],
                ["2", "Позиция 2", 250],
                ["", "", ""],
            ]
        )

        parsed = ExportMixin._parse_retrade_calculations(dataframe)

        self.assertEqual(
            parsed["headers"],
            ["№", "Наименование", "Цена"],
        )
        self.assertEqual(
            parsed["rows"],
            [["1", "Позиция 1", "100"], ["2", "Позиция 2", "250"]],
        )

    def test_parse_skips_fully_empty_rows_and_keeps_all_data_rows(self):
        dataframe = pd.DataFrame(
            [
                ["Код", "Описание", "Значение"],
                [1, "Строка 1", 10],
                ["", "", ""],
                [None, None, None],
                [2, "Строка 2", 20],
                [3, "Итого: 30", 30],
            ]
        )

        parsed = ExportMixin._parse_retrade_calculations(dataframe)

        self.assertEqual(parsed["headers"], ["Код", "Описание", "Значение"])
        self.assertEqual(
            parsed["rows"],
            [
                ["1", "Строка 1", "10"],
                ["2", "Строка 2", "20"],
                ["3", "Итого: 30", "30"],
            ],
        )

    def test_parse_returns_empty_structure_for_empty_file(self):
        dataframe = pd.DataFrame([[None, None], ["", ""]])
        parsed = ExportMixin._parse_retrade_calculations(dataframe)
        self.assertEqual(parsed, {"headers": [], "rows": []})


if __name__ == "__main__":
    unittest.main()
