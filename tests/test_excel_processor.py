import os
import tempfile
import unittest

import pandas as pd

from services.excel_processor import ExcelProcessor


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
                    ExcelProcessor.PRICE_COLUMN: 0,
                    ExcelProcessor.MANUFACTURER_COLUMN: "old",
                }
            ]
        )

        self.assertTrue(self.processor.can_fill_exported_excel(valid_path))
        self.assertFalse(self.processor.can_fill_exported_excel(invalid_path))

    def test_fill_exported_excel_transfers_rows(self):
        path = self._create_excel(
            [
                {
                    ExcelProcessor.PRICE_COLUMN: 0,
                    ExcelProcessor.MANUFACTURER_COLUMN: "old",
                    ExcelProcessor.TECH_COLUMN: "old",
                },
                {
                    ExcelProcessor.PRICE_COLUMN: 0,
                    ExcelProcessor.MANUFACTURER_COLUMN: "old",
                    ExcelProcessor.TECH_COLUMN: "old",
                },
            ]
        )

        self.processor.fill_exported_excel(
            path,
            [
                {
                    "price": 12345,
                    "manufacturer": "ООО Ромашка",
                    "tech_characteristics": "IP65",
                },
                {
                    "price": 200,
                    "manufacturer": "АО Лотос",
                    "tech_characteristics": "220V",
                },
            ],
        )

        result = pd.read_excel(path)
        self.assertEqual(result.at[0, ExcelProcessor.PRICE_COLUMN], 12345)
        self.assertEqual(result.at[0, ExcelProcessor.MANUFACTURER_COLUMN], "ООО Ромашка")
        self.assertEqual(result.at[0, ExcelProcessor.TECH_COLUMN], "IP65")
        self.assertEqual(result.at[1, ExcelProcessor.PRICE_COLUMN], 200)
        self.assertEqual(result.at[1, ExcelProcessor.MANUFACTURER_COLUMN], "АО Лотос")
        self.assertEqual(result.at[1, ExcelProcessor.TECH_COLUMN], "220V")

    def test_fill_exported_excel_uses_manufacturer_for_tech_fallback(self):
        path = self._create_excel(
            [
                {
                    ExcelProcessor.PRICE_COLUMN: 0,
                    ExcelProcessor.MANUFACTURER_COLUMN: "old",
                    ExcelProcessor.TECH_COLUMN: "old",
                }
            ]
        )

        self.processor.fill_exported_excel(
            path,
            [{"price": 1500, "manufacturer": "ООО Ромашка"}],
        )

        result = pd.read_excel(path)
        self.assertEqual(result.at[0, ExcelProcessor.TECH_COLUMN], "ООО Ромашка")

    def test_fill_exported_excel_raises_when_column_is_missing(self):
        path = self._create_excel(
            [
                {
                    ExcelProcessor.PRICE_COLUMN: 0,
                    ExcelProcessor.MANUFACTURER_COLUMN: "old",
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

        with self.assertRaises(Exception) as context:
            self.processor.fill_exported_excel(
                path,
                [
                    {"price": 1, "manufacturer": "A"},
                    {"price": 2, "manufacturer": "B"},
                ],
            )

        self.assertIn("Количество строк не совпадает", str(context.exception))


if __name__ == "__main__":
    unittest.main()
