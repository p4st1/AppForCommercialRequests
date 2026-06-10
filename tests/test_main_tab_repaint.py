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


class _FakeOrderTabWidget:
    def __init__(self, tabs, current_widget=None):
        self._tabs = [
            {
                "widget": widget,
                "text": text,
                "icon": None,
                "enabled": True,
                "visible": True,
                "tooltip": "",
                "whats_this": "",
                "data": None,
            }
            for widget, text in tabs
        ]
        self._current_widget = current_widget

    def count(self):
        return len(self._tabs)

    def currentWidget(self):
        return self._current_widget

    def setCurrentWidget(self, widget):
        self._current_widget = widget

    def indexOf(self, widget):
        for index, tab in enumerate(self._tabs):
            if tab["widget"] is widget:
                return index
        return -1

    def removeTab(self, index):
        self._tabs.pop(index)

    def insertTab(self, index, widget, icon, text):
        self._tabs.insert(
            index,
            {
                "widget": widget,
                "text": text,
                "icon": icon,
                "enabled": True,
                "visible": True,
                "tooltip": "",
                "whats_this": "",
                "data": None,
            },
        )
        return index

    def tabIcon(self, index):
        return self._tabs[index]["icon"]

    def isTabEnabled(self, index):
        return self._tabs[index]["enabled"]

    def setTabEnabled(self, index, enabled):
        self._tabs[index]["enabled"] = enabled

    def isTabVisible(self, index):
        return self._tabs[index]["visible"]

    def setTabVisible(self, index, visible):
        self._tabs[index]["visible"] = visible

    def tabToolTip(self, index):
        return self._tabs[index]["tooltip"]

    def setTabToolTip(self, index, tooltip):
        self._tabs[index]["tooltip"] = tooltip

    def tabWhatsThis(self, index):
        return self._tabs[index]["whats_this"]

    def setTabWhatsThis(self, index, whats_this):
        self._tabs[index]["whats_this"] = whats_this

    def tabData(self, index):
        return self._tabs[index]["data"]

    def setTabData(self, index, data):
        self._tabs[index]["data"] = data

    def tab_titles(self):
        return [tab["text"] for tab in self._tabs]

    def tab_widgets(self):
        return [tab["widget"] for tab in self._tabs]


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

    def test_apply_main_tab_order_removes_total_tab_and_orders_workflow_tabs(self):
        self._ensure_real_pyside6()
        from main import mainWindow

        full_tab = object()
        updates_tab = object()
        history_tab = object()
        platform_tab = object()
        retrade_tab = object()
        submission_tab = object()
        total_tab = object()
        tabs = _FakeOrderTabWidget(
            [
                (retrade_tab, "Переторжка"),
                (total_tab, "Итого"),
                (full_tab, "Полная таблица"),
                (updates_tab, "Обновления"),
                (history_tab, "История"),
                (platform_tab, "Прием заявок"),
                (submission_tab, "Подача заявки"),
            ],
            current_widget=full_tab,
        )
        window = SimpleNamespace(
            ui=SimpleNamespace(
                tabWidget=tabs,
                tab=full_tab,
                tab_2=updates_tab,
                tab_3=total_tab,
                webTab=platform_tab,
                historyTab=history_tab,
            ),
            retrade_tab=retrade_tab,
            submission_tab=submission_tab,
            MAIN_TAB_ORDER=mainWindow.MAIN_TAB_ORDER,
        )
        window._main_tab_widget = mainWindow._main_tab_widget.__get__(window)

        mainWindow._apply_main_tab_order(window)

        self.assertEqual(
            tabs.tab_titles(),
            [
                "Подготовка КП",
                "Загрузка с ЭТП",
                "Подача заявки",
                "Переторжка",
                "История",
                "Обновления",
            ],
        )
        self.assertNotIn(total_tab, tabs.tab_widgets())
        self.assertIs(tabs.currentWidget(), full_tab)


if __name__ == "__main__":
    unittest.main()
