import os
import unittest

from app.ui.table_autosize import refresh_table_viewport, resize_table_to_contents, table_update_guard


class _FakeItem:
    def __init__(self, text):
        self._text = str(text)

    def text(self):
        return self._text


class _FakeMetrics:
    @staticmethod
    def horizontalAdvance(text):
        return len(str(text)) * 8


class _FakeViewport:
    def __init__(self):
        self.updates = True
        self.update_calls = 0

    def updatesEnabled(self):
        return self.updates

    def setUpdatesEnabled(self, value):
        self.updates = bool(value)

    def update(self):
        self.update_calls += 1


class _FakeTable:
    def __init__(self, rows=10, cols=3):
        self._rows = rows
        self._cols = cols
        self._viewport = _FakeViewport()
        self.items = {
            (row, col): _FakeItem(f"value {row} {col}")
            for row in range(rows)
            for col in range(cols)
        }
        self.full_column_resize_calls = 0
        self.full_row_resize_calls = 0
        self.row_resize_calls = []
        self.layout_calls = 0
        self.geometry_update_calls = 0
        self.update_calls = 0
        self.row_heights = {}
        self.column_widths = {}
        self.updates = True
        self.sorting = True

    def rowCount(self):
        return self._rows

    def columnCount(self):
        return self._cols

    def item(self, row, col):
        return self.items.get((row, col))

    def horizontalHeaderItem(self, col):
        return _FakeItem(f"header {col}")

    def setColumnWidth(self, col, width):
        self.column_widths[col] = width

    def setRowHeight(self, row, height):
        self.row_heights[row] = height

    def resizeColumnsToContents(self):
        self.full_column_resize_calls += 1

    def resizeRowsToContents(self):
        self.full_row_resize_calls += 1

    def resizeRowToContents(self, row):
        self.row_resize_calls.append(row)

    def doItemsLayout(self):
        self.layout_calls += 1

    def updateGeometries(self):
        self.geometry_update_calls += 1

    def update(self):
        self.update_calls += 1

    def setWordWrap(self, _value):
        pass

    def verticalHeader(self):
        return None

    def horizontalHeader(self):
        return None

    def fontMetrics(self):
        return _FakeMetrics()

    def viewport(self):
        return self._viewport

    def updatesEnabled(self):
        return self.updates

    def setUpdatesEnabled(self, value):
        self.updates = bool(value)
        if not self.updates:
            self._viewport.setUpdatesEnabled(False)

    def isSortingEnabled(self):
        return self.sorting

    def setSortingEnabled(self, value):
        self.sorting = bool(value)


class TableAutosizeTests(unittest.TestCase):
    def test_small_table_uses_full_resize(self):
        table = _FakeTable(rows=4, cols=2)

        resize_table_to_contents(table, full_resize_row_limit=5)

        self.assertEqual(table.full_column_resize_calls, 1)
        self.assertEqual(table.full_row_resize_calls, 0)
        self.assertEqual(table.row_resize_calls, [])
        self.assertEqual(len(table.row_heights), 4)
        self.assertGreaterEqual(table.layout_calls, 1)
        self.assertGreaterEqual(table.geometry_update_calls, 1)
        self.assertGreaterEqual(table.update_calls, 1)

    def test_large_table_uses_sampled_resize(self):
        table = _FakeTable(rows=12, cols=3)

        resize_table_to_contents(table, full_resize_row_limit=5, text_columns={1: 300})

        self.assertEqual(table.full_column_resize_calls, 0)
        self.assertEqual(table.full_row_resize_calls, 0)
        self.assertEqual(table.row_resize_calls, [])
        self.assertEqual(len(table.row_heights), 12)
        self.assertEqual(table.column_widths[1], 300)
        self.assertIn(0, table.column_widths)

    def test_table_update_guard_restores_state(self):
        table = _FakeTable()

        with table_update_guard(table):
            self.assertFalse(table.updates)
            self.assertFalse(table.sorting)
            self.assertFalse(table.viewport().updates)

        self.assertTrue(table.updates)
        self.assertTrue(table.sorting)
        self.assertTrue(table.viewport().updates)
        self.assertGreaterEqual(table.viewport().update_calls, 1)

    def test_table_update_guard_restores_real_qt_viewport_updates(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication, QTableWidget
        except Exception as exc:
            self.skipTest(f"PySide6 is not available: {exc}")

        app = QApplication.instance() or QApplication([])
        table = QTableWidget()
        table.setRowCount(1)
        table.setColumnCount(1)
        table.show()
        app.processEvents()

        try:
            self.assertTrue(table.updatesEnabled())
            self.assertTrue(table.viewport().updatesEnabled())

            with table_update_guard(table):
                self.assertFalse(table.updatesEnabled())
                self.assertFalse(table.viewport().updatesEnabled())

            self.assertTrue(table.updatesEnabled())
            self.assertTrue(table.viewport().updatesEnabled())
        finally:
            table.close()

    def test_refresh_table_viewport_recovers_updates_after_tab_switch(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication, QLabel, QTabWidget, QTableWidget, QTableWidgetItem
        except Exception as exc:
            self.skipTest(f"PySide6 is not available: {exc}")

        app = QApplication.instance() or QApplication([])
        tabs = QTabWidget()
        table = QTableWidget()
        table.setColumnCount(2)
        table.setRowCount(1)
        table.setItem(0, 0, QTableWidgetItem("VISIBLE"))
        table.setItem(0, 1, QTableWidgetItem("TEXT"))
        tabs.addTab(table, "Полная таблица")
        tabs.addTab(QLabel("other"), "Другая вкладка")
        tabs.resize(640, 240)
        tabs.show()
        app.processEvents()

        try:
            tabs.setCurrentIndex(1)
            app.processEvents()
            table.setUpdatesEnabled(False)
            table.viewport().setUpdatesEnabled(False)

            tabs.setCurrentIndex(0)
            refresh_table_viewport(table, force_updates_enabled=True)
            app.processEvents()

            self.assertTrue(table.isVisible())
            self.assertTrue(table.updatesEnabled())
            self.assertTrue(table.viewport().updatesEnabled())
            self.assertEqual(table.item(0, 0).text(), "VISIBLE")
            self.assertTrue(table.visualItemRect(table.item(0, 0)).isValid())
        finally:
            tabs.close()


if __name__ == "__main__":
    unittest.main()
