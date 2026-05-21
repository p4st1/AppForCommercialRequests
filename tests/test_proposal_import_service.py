import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.proposal_import_service import ProposalImportService


class _IatAccessor:
    def __init__(self, rows):
        self._rows = rows

    def __getitem__(self, key):
        row, col = key
        return self._rows[row][col]


class _FakeTable:
    def __init__(self, rows):
        max_cols = max(len(row) for row in rows) if rows else 0
        self._rows = []
        for row in rows:
            padded = list(row) + [""] * (max_cols - len(row))
            self._rows.append(padded)
        self.index = list(range(len(self._rows)))
        self.columns = list(range(max_cols))
        self.iat = _IatAccessor(self._rows)


class ProposalImportServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = ProposalImportService()

    def test_normalize_header(self):
        self.assertEqual(self.service.normalize_header(" Цена за ед. без НДС "), "ценазаедбезндс")
        self.assertEqual(self.service.normalize_header("Кол-во"), "колво")

    def test_detect_columns_finds_header_row_and_mapping(self):
        df = _FakeTable(
            [
                ["шапка", "", ""],
                ["№", "Наименование", "Каталожный номер", "Ед.", "Кол-во", "Цена", "Срок"],
            ]
        )

        header_row, mapping = self.service.detect_columns(df)

        self.assertEqual(header_row, 1)
        self.assertEqual(mapping["number"], 0)
        self.assertEqual(mapping["name"], 1)
        self.assertEqual(mapping["sku"], 2)
        self.assertEqual(mapping["unit"], 3)
        self.assertEqual(mapping["qty"], 4)
        self.assertEqual(mapping["price"], 5)
        self.assertEqual(mapping["term"], 6)

    def test_parse_source_rows_returns_rows_and_warnings(self):
        df = _FakeTable(
            [
                ["№", "Наименование", "Каталожный номер", "Ед.", "Кол-во", "Цена", "Срок"],
                ["1", "Насос", "SKU-1", "шт", "2", "¥10,5", "15 дней"],
                ["2", "Клапан", "SKU-2", "шт", "x", "¥7,0", "20 дней"],
            ]
        )

        rows, warnings = self.service.parse_source_rows(df)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["number"], "1")
        self.assertEqual(rows[0]["name"], "Насос")
        self.assertEqual(rows[0]["qty"], 2)
        self.assertEqual(rows[0]["currency"], "¥")
        self.assertEqual(rows[0]["unitPrice"], 10.5)
        self.assertEqual(rows[0]["supplierTermDays"], 15)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Кол-во", warnings[0])

    def test_parse_source_rows_treats_dash_price_as_zero(self):
        df = _FakeTable(
            [
                ["№", "Наименование", "Каталожный номер", "Ед.", "Кол-во", "Цена", "Срок"],
                ["1", "Ось 1234568", "1234568", "шт.", "1", " -   ₽ ", "20 дней"],
            ]
        )

        rows, warnings = self.service.parse_source_rows(df)

        self.assertEqual(warnings, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["currency"], "₽")
        self.assertEqual(rows[0]["unitPrice"], 0)
        self.assertEqual(rows[0]["supplierTermDays"], 20)

    def test_parse_source_rows_uses_column_currency_for_plain_dash_price(self):
        df = _FakeTable(
            [
                ["№", "Наименование", "Каталожный номер", "Ед.", "Кол-во", "Цена", "Срок"],
                ["1", "Ось 1234568", "1234568", "шт.", "1", "-", "20 дней"],
                ["2", "Ось 1234569", "1234569", "шт.", "1", "100 ₽", "21 дней"],
            ]
        )

        rows, warnings = self.service.parse_source_rows(df)

        self.assertEqual(warnings, [])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["currency"], "₽")
        self.assertEqual(rows[0]["unitPrice"], 0)
        self.assertEqual(rows[1]["unitPrice"], 100)

    def test_parse_source_rows_raises_when_no_valid_rows(self):
        df = _FakeTable(
            [
                ["№", "Наименование", "Каталожный номер", "Ед.", "Кол-во", "Цена", "Срок"],
                ["1", "", "SKU-1", "шт", "", "", ""],
            ]
        )

        with self.assertRaises(ValueError) as context:
            self.service.parse_source_rows(df)

        self.assertIn("не найдено ни одной валидной строки", str(context.exception))

    def test_read_source_table_reads_csv_without_pandas(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.csv"
            path.write_text(
                "№;Наименование;Каталожный номер;Ед.;Кол-во;Цена;Срок\n"
                "1;Насос;SKU-1;шт;2;¥10,5;15 дней\n",
                encoding="utf-8",
            )

            rows, warnings = self.service.load_source_rows(path)

        self.assertEqual(warnings, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Насос")
        self.assertEqual(rows[0]["unitPrice"], 10.5)

    def test_read_source_table_reads_xlsx_in_streaming_mode(self):
        from openpyxl import Workbook

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(["№", "Наименование", "Каталожный номер", "Ед.", "Кол-во", "Цена", "Срок"])
            sheet.append(["1", "Клапан", "SKU-2", "шт", "3", "100 ₽", "20 дней"])
            workbook.save(path)

            rows, warnings = self.service.load_source_rows(path)

        self.assertEqual(warnings, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Клапан")
        self.assertEqual(rows[0]["qty"], 3)

    def test_load_source_rows_falls_back_to_pandas_reader(self):
        df = _FakeTable(
            [
                ["№", "Наименование", "Каталожный номер", "Ед.", "Кол-во", "Цена", "Срок"],
                ["1", "Насос", "SKU-1", "шт", "2", "100 ₽", "15 дней"],
            ]
        )

        with (
            patch.object(self.service, "read_source_table", side_effect=ValueError("fast failed")),
            patch.object(self.service, "_read_source_table_with_pandas", return_value=df) as fallback,
        ):
            rows, warnings = self.service.load_source_rows("/tmp/input.csv")

        fallback.assert_called_once_with("/tmp/input.csv")
        self.assertEqual(warnings, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Насос")


if __name__ == "__main__":
    unittest.main()
