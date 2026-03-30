import unittest

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


if __name__ == "__main__":
    unittest.main()
