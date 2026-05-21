import importlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class _FakeHeader:
    def __init__(self):
        self.visible = False

    def setVisible(self, value):
        self.visible = bool(value)


class _FakeViewport:
    def __init__(self):
        self.updates = False
        self.update_calls = 0

    def setUpdatesEnabled(self, value):
        self.updates = bool(value)

    def update(self):
        self.update_calls += 1


class _FakeTable:
    def __init__(self):
        self.visible = False
        self.updates = False
        self.layout_calls = 0
        self.geometry_calls = 0
        self.update_calls = 0
        self.header = _FakeHeader()
        self._viewport = _FakeViewport()

    def setVisible(self, value):
        self.visible = bool(value)

    def horizontalHeader(self):
        return self.header

    def setUpdatesEnabled(self, value):
        self.updates = bool(value)

    def viewport(self):
        return self._viewport

    def doItemsLayout(self):
        self.layout_calls += 1

    def updateGeometries(self):
        self.geometry_calls += 1

    def update(self):
        self.update_calls += 1


class _FakePanelWidget:
    def __init__(self):
        self.visible = True

    def setVisible(self, value):
        self.visible = bool(value)


class _FakeTabWidget:
    def __init__(self, current_widget):
        self._current_widget = current_widget

    def currentWidget(self):
        return self._current_widget


class MainTabRepaintTests(unittest.TestCase):
    @staticmethod
    def _ensure_real_pyside6():
        try:
            qtwidgets = importlib.import_module("PySide6.QtWidgets")
            if hasattr(qtwidgets, "QMainWindow"):
                return
        except Exception:
            pass

        for module_name in list(sys.modules):
            if module_name == "PySide6" or module_name.startswith("PySide6."):
                sys.modules.pop(module_name, None)

        try:
            qtwidgets = importlib.import_module("PySide6.QtWidgets")
        except Exception as exc:
            raise unittest.SkipTest(f"PySide6 is not available: {exc}") from exc
        if not hasattr(qtwidgets, "QMainWindow"):
            raise unittest.SkipTest("Real PySide6.QtWidgets is not available")

    def test_total_tab_switch_restores_summary_table_painting(self):
        self._ensure_real_pyside6()
        from main import mainWindow

        total_tab = object()
        full_tab = object()
        summary_table = _FakeTable()
        full_table = _FakeTable()
        panel_widget = _FakePanelWidget()
        window = SimpleNamespace(
            ui=SimpleNamespace(
                tab=full_tab,
                tab_3=total_tab,
                tabWidget=_FakeTabWidget(total_tab),
                KpTable=full_table,
                tableWidget_3=summary_table,
            ),
            _full_table_panel_widgets=[panel_widget],
        )
        window._restore_table_painting = lambda table: mainWindow._restore_table_painting(
            window,
            table,
        )
        window._restore_total_table_painting = lambda: mainWindow._restore_total_table_painting(window)
        window._restore_full_table_painting = lambda: mainWindow._restore_full_table_painting(window)

        with patch("main.QTimer.singleShot", side_effect=lambda _msec, callback: callback()):
            mainWindow._on_main_tab_changed(window, 0)

        self.assertFalse(panel_widget.visible)
        self.assertTrue(summary_table.visible)
        self.assertTrue(summary_table.updates)
        self.assertTrue(summary_table.viewport().updates)
        self.assertTrue(summary_table.header.visible)
        self.assertGreaterEqual(summary_table.layout_calls, 1)
        self.assertGreaterEqual(summary_table.geometry_calls, 1)
        self.assertGreaterEqual(summary_table.viewport().update_calls, 1)
        self.assertFalse(full_table.visible)


if __name__ == "__main__":
    unittest.main()
