import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from config import Config


pyside6 = sys.modules.get("PySide6")
if pyside6 is None:
    pyside6 = ModuleType("PySide6")
    sys.modules["PySide6"] = pyside6

qtcore = sys.modules.get("PySide6.QtCore")
if qtcore is None:
    qtcore = ModuleType("PySide6.QtCore")
    sys.modules["PySide6.QtCore"] = qtcore
if not hasattr(qtcore, "QSignalBlocker"):
    class _QSignalBlocker:
        def __init__(self, _obj):
            pass

    qtcore.QSignalBlocker = _QSignalBlocker
pyside6.QtCore = qtcore

qtwidgets = sys.modules.get("PySide6.QtWidgets")
if qtwidgets is None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    sys.modules["PySide6.QtWidgets"] = qtwidgets
if not hasattr(qtwidgets, "QFileDialog"):
    class _QFileDialog:
        @staticmethod
        def getOpenFileName(*args, **kwargs):
            return ("", "")

    qtwidgets.QFileDialog = _QFileDialog
if not hasattr(qtwidgets, "QMessageBox"):
    class _QMessageBox:
        @staticmethod
        def warning(*args, **kwargs):
            return 0

    qtwidgets.QMessageBox = _QMessageBox
pyside6.QtWidgets = qtwidgets

from app.ui.table_import_flow_mixin import TableImportFlowMixin


class _FakeKpTable:
    def __init__(self):
        self.row_counts = []
        self.resize_calls = 0

    def setRowCount(self, value):
        self.row_counts.append(value)

    def resizeColumnsToContents(self):
        self.resize_calls += 1


class _FakeTabWidget:
    def __init__(self):
        self.indices = []

    def setCurrentIndex(self, index):
        self.indices.append(index)


class _FakeUi:
    def __init__(self):
        self.KpTable = _FakeKpTable()
        self.tabWidget = _FakeTabWidget()


class _FakeProposalImportService:
    def __init__(self, rows=None, warnings=None, error=None):
        self.rows = rows or []
        self.warnings = warnings or []
        self.error = error
        self.calls = []

    def load_source_rows(self, filename):
        self.calls.append(filename)
        if self.error is not None:
            raise self.error
        return self.rows, self.warnings


class _FakeWindow(TableImportFlowMixin):
    def __init__(self):
        self.ui = _FakeUi()
        self.proposal_import_service = _FakeProposalImportService()
        self.tableData = {}
        self.rows = 0
        self.mixedCurrencyWarningShown = True
        self.error_calls = []
        self.close_calls = 0
        self.set_item_calls = []
        self.init_formula_calls = 0
        self.clear_undo_calls = 0
        self.logistic_calls = 0
        self.calculating_calls = 0
        self.apply_filters_calls = 0
        self.save_calls = 0
        self.parse_result = {
            "custom": 1.0,
            "markup": 1.0,
            "logistic": 1.0,
            "termDelivery": 0,
        }

    def error(self, title, message):
        self.error_calls.append((title, message))

    def _parse_input_parameters(self, show_error=True):
        return self.parse_result

    def closeTable(self):
        self.close_calls += 1

    def _round_money(self, value):
        return round(float(value), 2)

    def _set_table_item(self, row, col, text, editable):
        self.set_item_calls.append((row, col, str(text), editable))

    def _init_formula_expressions(self):
        self.init_formula_calls += 1

    def _clear_undo_history(self):
        self.clear_undo_calls += 1

    def logisticCalculate(self):
        self.logistic_calls += 1

    def calculating(self):
        self.calculating_calls += 1

    def _apply_table_filters(self):
        self.apply_filters_calls += 1

    def saveConfig(self):
        self.save_calls += 1


class TableImportFlowMixinTests(unittest.TestCase):
    def setUp(self):
        self._old_is_table_opened = Config.isTableOpened
        self._old_config = Config.config.copy()

    def tearDown(self):
        Config.isTableOpened = self._old_is_table_opened
        Config.config.clear()
        Config.config.update(self._old_config)

    @patch("app.ui.table_import_flow_mixin.QFileDialog.getOpenFileName", return_value=("", ""))
    def test_open_table_cancel_does_nothing(self, _get_open_file_name):
        window = _FakeWindow()

        window.openTable()

        self.assertEqual(window.error_calls, [])
        self.assertEqual(window.close_calls, 0)
        self.assertEqual(window.proposal_import_service.calls, [])

    @patch("app.ui.table_import_flow_mixin.Path.exists", return_value=False)
    def test_open_table_shows_error_when_file_missing(self, _exists):
        window = _FakeWindow()

        window.openTable(file="/tmp/missing.csv")

        self.assertEqual(window.error_calls, [("Ошибка", "Файл не найден: /tmp/missing.csv")])
        self.assertEqual(window.close_calls, 0)
        self.assertEqual(window.proposal_import_service.calls, [])

    @patch("app.ui.table_import_flow_mixin.Path.exists", return_value=True)
    def test_open_table_stops_when_input_params_invalid(self, _exists):
        window = _FakeWindow()
        window.parse_result = None

        window.openTable(file="/tmp/input.csv")

        self.assertEqual(window.error_calls, [])
        self.assertEqual(window.close_calls, 0)
        self.assertEqual(window.proposal_import_service.calls, [])

    @patch("app.ui.table_import_flow_mixin.Path.exists", return_value=True)
    def test_open_table_reports_import_error(self, _exists):
        window = _FakeWindow()
        window.proposal_import_service = _FakeProposalImportService(error=RuntimeError("broken file"))

        window.openTable(file="/tmp/input.csv")

        self.assertEqual(window.close_calls, 1)
        self.assertEqual(window.error_calls, [("Ошибка", "Невозможно прочитать таблицу\nbroken file")])
        self.assertEqual(window.proposal_import_service.calls, ["/tmp/input.csv"])

    @patch("app.ui.table_import_flow_mixin.QMessageBox.warning")
    @patch("app.ui.table_import_flow_mixin.Tool.formatPrice", side_effect=lambda value, currency: f"{currency}{value}")
    @patch("app.ui.table_import_flow_mixin.Path.exists", return_value=True)
    def test_open_table_success_updates_state_and_shows_warnings(
        self,
        _exists,
        _format_price,
        warning,
    ):
        window = _FakeWindow()
        window.proposal_import_service = _FakeProposalImportService(
            rows=[
                {
                    "number": 1,
                    "name": "Насос",
                    "sku": "SKU1",
                    "unit": "шт",
                    "qty": 2,
                    "unitPrice": 10,
                    "currency": "¥",
                    "supplierTermDays": 5,
                },
            ],
            warnings=["warn-1", "warn-2"],
        )

        Config.isTableOpened = False
        Config.config["lastTable"] = ""

        window.openTable(file="/tmp/input.csv")

        self.assertEqual(window.proposal_import_service.calls, ["/tmp/input.csv"])
        self.assertEqual(window.ui.KpTable.row_counts, [1])
        self.assertEqual(window.rows, 1)
        self.assertEqual(window.tableData["amount"], [2])
        self.assertEqual(window.tableData["currency"], ["¥"])
        self.assertEqual(window.tableData["unitPrice"], [10])
        self.assertEqual(window.tableData["totalPrice"], [20.0])
        self.assertEqual(window.tableData["termDelivery"], [5])
        self.assertEqual(window.close_calls, 1)
        self.assertEqual(window.init_formula_calls, 1)
        self.assertEqual(window.clear_undo_calls, 1)
        self.assertEqual(window.logistic_calls, 1)
        self.assertEqual(window.calculating_calls, 1)
        self.assertEqual(window.ui.KpTable.resize_calls, 1)
        self.assertEqual(window.apply_filters_calls, 1)
        self.assertEqual(window.save_calls, 1)
        self.assertFalse(window.mixedCurrencyWarningShown)
        self.assertEqual(Config.config["lastTable"], "/tmp/input.csv")
        self.assertTrue(Config.isTableOpened)
        self.assertEqual(window.ui.tabWidget.indices, [1])
        self.assertEqual(len(window.set_item_calls), 8)
        warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
