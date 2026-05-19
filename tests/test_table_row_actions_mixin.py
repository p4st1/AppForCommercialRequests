import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.ui.table_row_actions_mixin import TableRowActionsMixin
from config import Config


class _FakeIndex:
    def __init__(self, row, col):
        self._row = row
        self._col = col

    def row(self):
        return self._row

    def column(self):
        return self._col


class _FakeSelectionModel:
    def __init__(self, indexes):
        self._indexes = list(indexes)

    def selectedIndexes(self):
        return list(self._indexes)

    def selectedRows(self):
        return []


class _FakeItem:
    def __init__(self, text=""):
        self._text = str(text)

    def text(self):
        return self._text

    def setText(self, value):
        self._text = str(value)


class _FakeTable:
    def __init__(self, *, rows=1, cols=15, selected_indexes=None):
        self._rows = rows
        self._cols = cols
        self._selected_indexes = list(selected_indexes or [])
        self.items = {}
        self.current_row = -1
        self.current_col = -1

    def rowCount(self):
        return self._rows

    def columnCount(self):
        return self._cols

    def selectionModel(self):
        return _FakeSelectionModel(self._selected_indexes)

    def currentRow(self):
        return self.current_row

    def currentColumn(self):
        return self.current_col

    def item(self, row, col):
        return self.items.get((row, col))


class _FakeSignalBlocker:
    def __init__(self, _target):
        pass


class _FakeStatusBar:
    def __init__(self):
        self.messages = []

    def showMessage(self, message, timeout=0):
        self.messages.append((message, timeout))


class _FakeWindow(TableRowActionsMixin):
    EDITABLE_COLUMNS = {0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 13, 14}
    BASE_EDITABLE_COLUMNS = {0, 1, 2, 3, 4, 5, 14}
    FORMULA_EDITABLE_COLUMNS = {8, 9, 10, 11, 13}

    def __init__(self, table):
        self.ui = SimpleNamespace(KpTable=table)
        self.rows = table.rowCount()
        self.tableData = {
            "amount": [2],
            "currency": ["₽"],
            "unitPrice": [100],
            "totalPrice": [200],
            "termDelivery": [5],
            "logistic": [200],
        }
        self.formulaExpressions = {col: ["formula"] for col in self.FORMULA_EDITABLE_COLUMNS}
        self.mixedCurrencyWarningShown = True
        self.undo_count = 0
        self.filters_applied = 0
        self.total_updates = 0
        self.status_bar = _FakeStatusBar()

    def _set_table_item(self, row, col, text, editable):
        item = self.ui.KpTable.item(row, col)
        if item is None:
            item = _FakeItem()
            self.ui.KpTable.items[(row, col)] = item
        item.setText(text)

    def _push_undo_state(self):
        self.undo_count += 1

    def _apply_table_filters(self):
        self.filters_applied += 1

    def _update_total_tab_table(self):
        self.total_updates += 1

    def statusBar(self):
        return self.status_bar


class TableRowActionsMixinTests(unittest.TestCase):
    def setUp(self):
        self._previous_is_table_opened = Config.isTableOpened
        Config.isTableOpened = True

    def tearDown(self):
        Config.isTableOpened = self._previous_is_table_opened

    @patch("app.ui.table_row_actions_mixin.resize_table_to_contents", lambda _table: None)
    @patch("app.ui.table_row_actions_mixin.QSignalBlocker", _FakeSignalBlocker)
    def test_clear_selected_cells_blanks_base_editable_cells(self):
        table = _FakeTable(
            selected_indexes=[
                _FakeIndex(0, 1),
                _FakeIndex(0, 3),
            ]
        )
        table.items[(0, 1)] = _FakeItem("Позиция")
        table.items[(0, 3)] = _FakeItem("шт")
        window = _FakeWindow(table)

        window._clear_selected_cells()

        self.assertEqual(table.item(0, 1).text(), "")
        self.assertEqual(table.item(0, 3).text(), "")
        self.assertEqual(window.undo_count, 1)
        self.assertEqual(window.filters_applied, 1)
        self.assertEqual(window.total_updates, 1)
        self.assertEqual(window.status_bar.messages[-1][0], "Очищено ячеек: 2")

    @patch("app.ui.table_row_actions_mixin.resize_table_to_contents", lambda _table: None)
    @patch("app.ui.table_row_actions_mixin.QSignalBlocker", _FakeSignalBlocker)
    def test_clear_selected_cells_ignores_formula_columns(self):
        table = _FakeTable(selected_indexes=[_FakeIndex(0, 8)])
        table.items[(0, 8)] = _FakeItem("250 ₽")
        window = _FakeWindow(table)

        window._clear_selected_cells()

        self.assertEqual(table.item(0, 8).text(), "250 ₽")
        self.assertEqual(window.undo_count, 0)
        self.assertEqual(window.status_bar.messages[-1][0], "Выберите редактируемые ячейки для очистки")

    @patch("app.ui.table_row_actions_mixin.resize_table_to_contents", lambda _table: None)
    @patch("app.ui.table_row_actions_mixin.QSignalBlocker", _FakeSignalBlocker)
    def test_clear_price_cell_resets_dependent_total_cells(self):
        table = _FakeTable(selected_indexes=[_FakeIndex(0, 5)])
        table.items[(0, 5)] = _FakeItem("100 ₽")
        table.items[(0, 6)] = _FakeItem("200 ₽")
        table.items[(0, 7)] = _FakeItem("220 ₽")
        window = _FakeWindow(table)

        window._clear_selected_cells()

        self.assertEqual(table.item(0, 5).text(), "")
        self.assertEqual(table.item(0, 6).text(), "")
        self.assertEqual(table.item(0, 7).text(), "")
        self.assertEqual(window.tableData["unitPrice"][0], 0)
        self.assertEqual(window.tableData["totalPrice"][0], 0)


if __name__ == "__main__":
    unittest.main()
