import sys
import unittest
from types import ModuleType
from types import SimpleNamespace


pyside6 = sys.modules.get("PySide6")
if pyside6 is None:
    pyside6 = ModuleType("PySide6")
    sys.modules["PySide6"] = pyside6

qtcore = sys.modules.get("PySide6.QtCore")
if qtcore is None:
    qtcore = ModuleType("PySide6.QtCore")
    sys.modules["PySide6.QtCore"] = qtcore
if not hasattr(qtcore, "Qt"):
    class _ContextMenuPolicy:
        CustomContextMenu = 1

    class _Qt:
        ContextMenuPolicy = _ContextMenuPolicy

    qtcore.Qt = _Qt
pyside6.QtCore = qtcore

qtwidgets = sys.modules.get("PySide6.QtWidgets")
if qtwidgets is None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    sys.modules["PySide6.QtWidgets"] = qtwidgets
if not hasattr(qtwidgets, "QInputDialog"):
    class _QInputDialog:
        @staticmethod
        def getText(*_args, **_kwargs):
            return "", False

    qtwidgets.QInputDialog = _QInputDialog
if not hasattr(qtwidgets, "QMenu"):
    class _QMenu:
        pass

    qtwidgets.QMenu = _QMenu
pyside6.QtWidgets = qtwidgets

from app.ui.table_filter_mixin import TableFilterMixin


class _FakeTable:
    def __init__(self, rows=3):
        self._rows = rows
        self.hidden = {row: True for row in range(rows)}

    def rowCount(self):
        return self._rows

    def columnCount(self):
        return 0

    def setRowHidden(self, row, hidden):
        self.hidden[row] = bool(hidden)


class _FakeWindow(TableFilterMixin):
    def __init__(self, table):
        self.ui = SimpleNamespace(KpTable=table)
        self.columnFilters = {}
        self.quickSearchText = ""
        self._table_filter_all_visible = True
        self._table_filter_row_count = table.rowCount()


class TableFilterMixinTests(unittest.TestCase):
    def test_apply_table_filters_always_unhides_rows_without_active_filters(self):
        table = _FakeTable(rows=3)
        window = _FakeWindow(table)

        window._apply_table_filters()

        self.assertEqual(table.hidden, {0: False, 1: False, 2: False})


if __name__ == "__main__":
    unittest.main()
