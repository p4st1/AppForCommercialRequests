import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


pyside6 = sys.modules.get("PySide6")
if pyside6 is None:
    pyside6 = ModuleType("PySide6")
    sys.modules["PySide6"] = pyside6

qtcore = sys.modules.get("PySide6.QtCore")
if qtcore is None:
    qtcore = ModuleType("PySide6.QtCore")
    sys.modules["PySide6.QtCore"] = qtcore
pyside6.QtCore = qtcore

qtwidgets = sys.modules.get("PySide6.QtWidgets")
if qtwidgets is None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    sys.modules["PySide6.QtWidgets"] = qtwidgets
pyside6.QtWidgets = qtwidgets

if not hasattr(qtcore, "Qt"):
    qtcore.Qt = SimpleNamespace()
if not hasattr(qtwidgets, "QTableWidgetItem"):
    class _PlaceholderItem:
        def __init__(self):
            pass

    qtwidgets.QTableWidgetItem = _PlaceholderItem

from app.ui.table_item_mixin import TableItemMixin


class _FakeItemFlag:
    ItemIsSelectable = 1
    ItemIsEnabled = 2
    ItemIsEditable = 4


class _FakeQt:
    ItemFlag = _FakeItemFlag


class _FakeItem:
    def __init__(self):
        self.text_value = ""
        self.flags_value = 0

    def setText(self, value):
        self.text_value = value

    def flags(self):
        return self.flags_value

    def setFlags(self, value):
        self.flags_value = value


class _FakeTable:
    def __init__(self):
        self.items = {}
        self.set_calls = []

    def item(self, row, col):
        return self.items.get((row, col))

    def setItem(self, row, col, item):
        self.items[(row, col)] = item
        self.set_calls.append((row, col, item))


class _FakeWindow(TableItemMixin):
    def __init__(self):
        self.ui = SimpleNamespace(KpTable=_FakeTable())


class TableItemMixinTests(unittest.TestCase):
    @patch("app.ui.table_item_mixin.Qt", _FakeQt)
    @patch("app.ui.table_item_mixin.QTableWidgetItem", _FakeItem)
    def test_set_table_item_creates_item_and_sets_editable_flags(self):
        window = _FakeWindow()

        window._set_table_item(2, 3, 123, editable=True)

        self.assertEqual(len(window.ui.KpTable.set_calls), 1)
        item = window.ui.KpTable.item(2, 3)
        self.assertIsNotNone(item)
        self.assertEqual(item.text_value, "123")
        self.assertEqual(item.flags_value, 7)

    @patch("app.ui.table_item_mixin.Qt", _FakeQt)
    @patch("app.ui.table_item_mixin.QTableWidgetItem", _FakeItem)
    def test_set_table_item_removes_editable_flag_for_readonly(self):
        window = _FakeWindow()
        existing_item = _FakeItem()
        existing_item.flags_value = 7
        window.ui.KpTable.setItem(0, 0, existing_item)

        window._set_table_item(0, 0, "readonly", editable=False)

        self.assertEqual(len(window.ui.KpTable.set_calls), 1)
        item = window.ui.KpTable.item(0, 0)
        self.assertIs(item, existing_item)
        self.assertEqual(item.text_value, "readonly")
        self.assertEqual(item.flags_value, 3)


if __name__ == "__main__":
    unittest.main()
