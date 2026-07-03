import unittest
from unittest.mock import patch

from submission.submission_service import (
    SubmissionHeader,
    SubmissionPayload,
    SubmissionRow,
    SubmissionService,
)
from submission.submission_tab import SubmissionTabMixin


class _FakeSignalBlocker:
    def __init__(self, _target):
        pass


class _FakeItem:
    def __init__(self, text=""):
        self._text = str(text)

    def text(self):
        return self._text

    def setText(self, value):
        self._text = str(value)


class _FakeTable:
    def __init__(self, rows, headers=None):
        self._headers = [_FakeItem(header) for header in (headers or [])]
        self._rows = [[_FakeItem(value) for value in row] for row in rows]
        self.selection_cleared = False
        self.current_item = object()

    def rowCount(self):
        return len(self._rows)

    def columnCount(self):
        return max([len(self._headers), *(len(row) for row in self._rows)], default=0)

    def horizontalHeaderItem(self, column):
        if column < 0 or column >= len(self._headers):
            return None
        return self._headers[column]

    def item(self, row, column):
        if row < 0 or row >= len(self._rows):
            return None
        row_values = self._rows[row]
        if column < 0 or column >= len(row_values):
            return None
        return row_values[column]

    def setItem(self, row, column, item):
        while len(self._rows) <= row:
            self._rows.append([])
        while len(self._rows[row]) <= column:
            self._rows[row].append(_FakeItem(""))
        self._rows[row][column] = item

    def clearSelection(self):
        self.selection_cleared = True

    def setCurrentItem(self, item):
        self.current_item = item


class _FakeWindow(SubmissionTabMixin):
    def __init__(self, rows, headers=None):
        self.submission_service = SubmissionService()
        self.submission_table = _FakeTable(rows, headers=headers)
        self._updating_submission_table = False
        self.total_updates = 0

    def _update_submission_total(self):
        self.total_updates += 1


class SubmissionTabMixinTests(unittest.TestCase):
    def test_currency_from_table_prefers_price_cells(self):
        window = _FakeWindow(
            [["Насос", "1", "шт", "8 808,80 ¥", "8 808,80 ¥"]],
            headers=["Наименование", "Кол-во", "Ед. изм.", "Цена за ед.", "Сумма"],
        )

        self.assertEqual(window._submission_currency_from_table(), "CNY")

    def test_source_rows_for_excel_duplicates_manufacturer_to_technical_keys(self):
        payload = SubmissionPayload(
            header=SubmissionHeader(number="REQ-1", title="Заявка"),
            rows=[SubmissionRow(name="Насос", manufacturer="Atlas Copco", technical="IP65")],
        )

        rows = SubmissionTabMixin._submission_source_rows_for_excel(payload)

        self.assertEqual(rows[0]["manufacturer"], "Atlas Copco")
        self.assertEqual(rows[0]["technical"], "Atlas Copco")
        self.assertEqual(rows[0]["tech_characteristics"], "Atlas Copco")
        self.assertEqual(rows[0]["technical_characteristics"], "Atlas Copco")

    @patch("submission.submission_tab.QSignalBlocker", _FakeSignalBlocker)
    def test_row_defaults_clear_status_and_warranty_for_zero_price_rows(self):
        window = _FakeWindow(
            [
                [
                    "",
                    "32",
                    "штука",
                    "",
                    "0,00",
                    "31 авг. 2026 г.",
                    "",
                    "",
                    "посредник",
                    "6 месяцев",
                ],
                [
                    "Гидромотор",
                    "1",
                    "штука",
                    "8 808,80",
                    "8 808,80",
                    "77 дней",
                    "cat",
                    "гидромотор 3003",
                    "",
                    "",
                ],
            ]
        )

        window._apply_submission_row_defaults(
            {"supplier_status": "посредник", "warranty": "6 месяцев"}
        )

        self.assertEqual(window._submission_item_text(0, 8), "")
        self.assertEqual(window._submission_item_text(0, 9), "")
        self.assertEqual(window._submission_item_text(1, 8), "посредник")
        self.assertEqual(window._submission_item_text(1, 9), "6 месяцев")
        self.assertEqual(window.total_updates, 1)

    def test_clear_submission_table_selection_removes_current_item(self):
        window = _FakeWindow([["Насос"]])

        window._clear_submission_table_selection()

        self.assertTrue(window.submission_table.selection_cleared)
        self.assertIsNone(window.submission_table.current_item)


if __name__ == "__main__":
    unittest.main()
