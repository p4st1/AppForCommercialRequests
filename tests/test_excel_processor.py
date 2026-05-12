import os
import tempfile
import unittest

import pandas as pd

from services.excel_processor import ExcelProcessor, RowCountMismatchError


class ExcelProcessorTests(unittest.TestCase):
    def setUp(self):
        self.processor = ExcelProcessor()

    def _create_excel(self, rows: list[dict]) -> str:
        fd, path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        pd.DataFrame(rows).to_excel(path, index=False)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        return path

    def test_can_fill_exported_excel_checks_required_columns(self):
        valid_path = self._create_excel(
            [
                {
                    ExcelProcessor.PRICE_COLUMN: 0,
                    ExcelProcessor.MANUFACTURER_COLUMN: "old",
                    ExcelProcessor.TECH_COLUMN: "old",
                }
            ]
        )
        invalid_path = self._create_excel(
            [
                {
                    "Случайная колонка": "old",
                }
            ]
        )

        self.assertTrue(self.processor.can_fill_exported_excel(valid_path))
        self.assertFalse(self.processor.can_fill_exported_excel(invalid_path))

    def test_fill_exported_excel_transfers_rows(self):
        path = self._create_excel(
            [
                {
                    "Наименование": "Насос",
                    "Ед. изм.": "шт",
                    "Кол-во": 2,
                    ExcelProcessor.PRICE_COLUMN: None,
                    "Сумма, RUB (без учета НДС)": 0,
                    "Срок поставки": None,
                    ExcelProcessor.MANUFACTURER_COLUMN: None,
                    ExcelProcessor.TECH_COLUMN: None,
                    "Условия гарантий качества": "12 мес.",
                },
                {
                    "Наименование": "Клапан",
                    "Ед. изм.": "шт",
                    "Кол-во": 1,
                    ExcelProcessor.PRICE_COLUMN: None,
                    "Сумма, RUB (без учета НДС)": 0,
                    "Срок поставки": None,
                    ExcelProcessor.MANUFACTURER_COLUMN: None,
                    ExcelProcessor.TECH_COLUMN: None,
                    "Условия гарантий качества": "24 мес.",
                },
            ]
        )

        self.processor.fill_exported_excel(
            path,
            [
                {
                    "price": 12345,
                    "total": 24690,
                    "delivery_time": "30 дней",
                    "manufacturer": "ООО Ромашка",
                    "tech_characteristics": "IP65",
                },
                {
                    "price": 200,
                    "total": 200,
                    "delivery_time": "10 дней",
                    "manufacturer": "АО Лотос",
                    "tech_characteristics": "220V",
                },
            ],
        )

        result = pd.read_excel(path)
        self.assertEqual(result.at[0, "Наименование"], "Насос")
        self.assertEqual(result.at[0, "Ед. изм."], "шт")
        self.assertEqual(result.at[0, "Кол-во"], 2)
        self.assertEqual(result.at[0, ExcelProcessor.PRICE_COLUMN], 12345)
        self.assertEqual(result.at[0, "Сумма, RUB (без учета НДС)"], 24690)
        self.assertEqual(result.at[0, "Срок поставки"], "30 дней")
        self.assertEqual(result.at[0, ExcelProcessor.MANUFACTURER_COLUMN], "ООО Ромашка")
        self.assertEqual(result.at[0, ExcelProcessor.TECH_COLUMN], "ООО Ромашка")
        self.assertEqual(result.at[0, "Условия гарантий качества"], "12 мес.")
        self.assertEqual(result.at[1, ExcelProcessor.PRICE_COLUMN], 200)
        self.assertEqual(result.at[1, "Сумма, RUB (без учета НДС)"], 200)
        self.assertEqual(result.at[1, "Срок поставки"], "10 дней")
        self.assertEqual(result.at[1, ExcelProcessor.MANUFACTURER_COLUMN], "АО Лотос")
        self.assertEqual(result.at[1, ExcelProcessor.TECH_COLUMN], "АО Лотос")

    def test_fill_exported_excel_uses_real_name_not_alternative_name(self):
        path = self._create_excel(
            [
                {
                    "Наименование": None,
                    "Ед. изм.": "шт",
                    "Альтернативное наименование": None,
                    ExcelProcessor.PRICE_COLUMN: None,
                }
            ]
        )

        self.processor.fill_exported_excel(
            path,
            [
                {
                    "name": "Насос",
                    "price": 12345,
                }
            ],
        )

        result = pd.read_excel(path)
        self.assertEqual(result.at[0, "Наименование"], "Насос")
        self.assertTrue(pd.isna(result.at[0, "Альтернативное наименование"]))

    def test_fill_exported_excel_accepts_sale_price_source_key(self):
        path = self._create_excel([{"Наименование": "Позиция", ExcelProcessor.PRICE_COLUMN: None}])

        self.processor.fill_exported_excel(
            path,
            [{"Цена реализации за ед. без НДС": 777}],
        )

        result = pd.read_excel(path)
        self.assertEqual(result.at[0, ExcelProcessor.PRICE_COLUMN], 777)

    def test_fill_exported_excel_does_not_overwrite_existing_cells(self):
        path = self._create_excel(
            [
                {
                    ExcelProcessor.PRICE_COLUMN: 100,
                    "Сумма, RUB (без учета НДС)": 300,
                    "Срок поставки": "old срок",
                    ExcelProcessor.MANUFACTURER_COLUMN: "old manufacturer",
                    ExcelProcessor.TECH_COLUMN: "old tech",
                }
            ]
        )

        self.processor.fill_exported_excel(
            path,
            [
                {
                    "price": 999,
                    "total": 999,
                    "delivery_time": "new срок",
                    "manufacturer": "new manufacturer",
                }
            ],
        )

        result = pd.read_excel(path)
        self.assertEqual(result.at[0, ExcelProcessor.PRICE_COLUMN], 100)
        self.assertEqual(result.at[0, "Сумма, RUB (без учета НДС)"], 300)
        self.assertEqual(result.at[0, "Срок поставки"], "old срок")
        self.assertEqual(result.at[0, ExcelProcessor.MANUFACTURER_COLUMN], "old manufacturer")
        self.assertEqual(result.at[0, ExcelProcessor.TECH_COLUMN], "old tech")

    def test_fill_exported_excel_uses_manufacturer_for_tech_fallback(self):
        path = self._create_excel(
            [
                {
                    ExcelProcessor.PRICE_COLUMN: 0,
                    ExcelProcessor.MANUFACTURER_COLUMN: None,
                    ExcelProcessor.TECH_COLUMN: None,
                }
            ]
        )

        self.processor.fill_exported_excel(
            path,
            [
                {
                    "price": 1500,
                    "manufacturer": "ООО Ромашка",
                    "tech_characteristics": "IP65",
                }
            ],
        )

        result = pd.read_excel(path)
        self.assertEqual(result.at[0, ExcelProcessor.TECH_COLUMN], "ООО Ромашка")

    def test_fill_exported_excel_raises_when_column_is_missing(self):
        path = self._create_excel(
            [
                {
                    "Случайная колонка": "old",
                }
            ]
        )

        with self.assertRaises(Exception) as context:
            self.processor.fill_exported_excel(path, [{"price": 1, "manufacturer": "A"}])

        self.assertIn("Не найдена колонка", str(context.exception))

    def test_fill_exported_excel_raises_when_row_count_mismatch(self):
        path = self._create_excel(
            [
                {
                    ExcelProcessor.PRICE_COLUMN: 0,
                    ExcelProcessor.MANUFACTURER_COLUMN: "old",
                    ExcelProcessor.TECH_COLUMN: "old",
                }
            ]
        )

        with self.assertRaises(RowCountMismatchError) as context:
            self.processor.fill_exported_excel(
                path,
                [
                    {"price": 1, "manufacturer": "A"},
                    {"price": 2, "manufacturer": "B"},
                ],
            )

        self.assertIn("Количество строк не совпадает", str(context.exception))
        self.assertEqual(context.exception.excel_rows, 1)
        self.assertEqual(context.exception.source_rows, 2)

    def test_fill_exported_excel_can_copy_overlapping_rows_when_counts_differ(self):
        path = self._create_excel(
            [
                {
                    ExcelProcessor.PRICE_COLUMN: 0,
                    ExcelProcessor.MANUFACTURER_COLUMN: None,
                    ExcelProcessor.TECH_COLUMN: None,
                },
                {
                    ExcelProcessor.PRICE_COLUMN: 0,
                    ExcelProcessor.MANUFACTURER_COLUMN: "old-2",
                    ExcelProcessor.TECH_COLUMN: "old-2",
                },
            ]
        )

        self.processor.fill_exported_excel(
            path,
            [{"price": 999, "manufacturer": "ООО Ромашка", "tech_characteristics": "IP65"}],
            strict_row_count=False,
        )

        result = pd.read_excel(path)
        self.assertEqual(result.at[0, ExcelProcessor.PRICE_COLUMN], 999)
        self.assertEqual(result.at[0, ExcelProcessor.MANUFACTURER_COLUMN], "ООО Ромашка")
        self.assertEqual(result.at[0, ExcelProcessor.TECH_COLUMN], "ООО Ромашка")
        self.assertEqual(result.at[1, ExcelProcessor.MANUFACTURER_COLUMN], "old-2")

    def test_fill_exported_csv_uses_semicolon_delimiter(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as file:
            file.write(
                f"{ExcelProcessor.PRICE_COLUMN};{ExcelProcessor.MANUFACTURER_COLUMN};"
                f"{ExcelProcessor.TECH_COLUMN}\n"
                "0;;\n"
            )
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))

        self.processor.fill_exported_excel(
            path,
            [{"price": 123, "manufacturer": "ООО Ромашка"}],
        )

        result = pd.read_csv(path, sep=";")
        self.assertEqual(result.at[0, ExcelProcessor.PRICE_COLUMN], 123)
        self.assertEqual(result.at[0, ExcelProcessor.MANUFACTURER_COLUMN], "ООО Ромашка")
        self.assertEqual(result.at[0, ExcelProcessor.TECH_COLUMN], "ООО Ромашка")


if __name__ == "__main__":
    unittest.main()
