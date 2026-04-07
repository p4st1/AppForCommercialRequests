import sys
import unittest
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
if not hasattr(qtcore, "Qt") or not hasattr(qtcore.Qt, "ItemDataRole"):
    class _ItemDataRole:
        UserRole = 32

    class _Qt:
        ItemDataRole = _ItemDataRole

    qtcore.Qt = _Qt
pyside6.QtCore = qtcore

qtwidgets = sys.modules.get("PySide6.QtWidgets")
if qtwidgets is None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    sys.modules["PySide6.QtWidgets"] = qtwidgets
if not hasattr(qtwidgets, "QFileDialog"):
    class _QFileDialog:
        @staticmethod
        def getOpenFileName(*_args, **_kwargs):
            return ("", "")

    qtwidgets.QFileDialog = _QFileDialog
if not hasattr(qtwidgets, "QMessageBox"):
    class _QMessageBox:
        @staticmethod
        def warning(*_args, **_kwargs):
            return 0

    qtwidgets.QMessageBox = _QMessageBox
pyside6.QtWidgets = qtwidgets

from app.ui.calculation_flow_mixin import CalculationFlowMixin


class _FakeItem:
    def __init__(self, text=""):
        self._text = str(text)
        self._data = {}

    def setData(self, role, value):
        self._data[role] = value

    def data(self, role):
        return self._data.get(role)


class _FakeKpTable:
    def __init__(self):
        self._items = {}

    def item(self, row, col):
        return self._items.get((row, col))

    def set_item(self, row, col, item):
        self._items[(row, col)] = item


class _FakeComboBox:
    def __init__(self, index):
        self._index = index
        self.block_calls = []
        self.set_calls = []

    def currentIndex(self):
        return self._index

    def blockSignals(self, value):
        self.block_calls.append(bool(value))

    def setCurrentIndex(self, index):
        self._index = index
        self.set_calls.append(index)


class _FakeUi:
    def __init__(self, logistic_mode):
        self.KpTable = _FakeKpTable()
        self.logisticVar = _FakeComboBox(logistic_mode)


class _FakeCalculationService:
    def __init__(self, result=None):
        self.result = result or SimpleNamespace(
            customs_sum=10,
            unit_sale_price=20,
            real_price=30,
            total_without_vat=40,
            total_with_vat=48,
            total_delivery_days=9,
        )
        self.calls = []

    def calculate_row(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


class _FakeWindow(CalculationFlowMixin):
    FORMULA_EDITABLE_COLUMNS = {8, 9, 10, 11, 13}

    def __init__(self, logistic_mode=0):
        self.ui = _FakeUi(logistic_mode)
        self.tableData = {
            "amount": [1, 2],
            "currency": ["¥", "¥"],
            "unitPrice": [100.0, 50.0],
            "totalPrice": [100.0, 100.0],
            "termDelivery": [5, 6],
            "logistic": [110.0, 110.0],
        }
        self.rows = 2
        self.formulaExpressions = {
            8: ["F8-1", "F8-2"],
            9: ["F9-1", "F9-2"],
            10: ["F10-1", "F10-2"],
            11: ["F11-1", "F11-2"],
            13: ["F13-1", "F13-2"],
        }
        self.formulaCustom = 1.0
        self.formulaMarkup = 1.2
        self.formulaLogistic = 1.1
        self.termDeliveryDays = 10
        self.mixedCurrencyWarningShown = False
        self.calculation_service = _FakeCalculationService()
        self.set_item_calls = []
        self.apply_filters_calls = 0
        self.update_total_calls = 0
        self.init_formula_calls = 0
        self.error_calls = []

    def _init_formula_expressions(self):
        self.init_formula_calls += 1
        self.formulaExpressions = {col: [""] * self.rows for col in self.FORMULA_EDITABLE_COLUMNS}

    def _load_formula_parameters(self):
        return {"A": 1}

    def _vat_multiplier(self):
        return 1.2

    def _column_title(self, column):
        return str(column)

    def _set_table_item(self, row, col, text, editable):
        self.set_item_calls.append((row, col, str(text), editable))
        item = self.ui.KpTable.item(row, col)
        if item is None:
            item = _FakeItem(text)
            self.ui.KpTable.set_item(row, col, item)
        else:
            item._text = str(text)

    def _apply_table_filters(self):
        self.apply_filters_calls += 1

    def _update_total_tab_table(self):
        self.update_total_calls += 1

    def _round_money(self, value):
        return round(float(value), 2)

    def _fmt_number(self, value):
        text = f"{float(value):.10f}".rstrip("0").rstrip(".")
        return text or "0"

    def error(self, title, message):
        self.error_calls.append((title, message))


class _FakeEventWindow(CalculationFlowMixin):
    def __init__(self):
        self.logistic_calls = 0
        self.calculation_calls = 0
        self.error_calls = []

    def logisticCalculate(self):
        self.logistic_calls += 1

    def calculating(self):
        self.calculation_calls += 1

    def error(self, title, text):
        self.error_calls.append((title, text))


class CalculationFlowMixinTests(unittest.TestCase):
    def setUp(self):
        self._old_is_table_opened = Config.isTableOpened

    def tearDown(self):
        Config.isTableOpened = self._old_is_table_opened

    def test_logistic_var_changed_noop_when_table_closed(self):
        Config.isTableOpened = False
        window = _FakeEventWindow()

        window.logisticVarChanged(None)

        self.assertEqual(window.logistic_calls, 0)
        self.assertEqual(window.calculation_calls, 0)
        self.assertEqual(window.error_calls, [])

    @patch("app.ui.calculation_flow_mixin.QMessageBox.warning")
    @patch("app.ui.calculation_flow_mixin.Tool.formatPrice", side_effect=lambda value, currency: f"{currency}{value}")
    def test_logistic_calculate_mixed_currency_switches_mode(self, _format_price, warning):
        window = _FakeWindow(logistic_mode=1)
        window.tableData["currency"] = ["¥", "$"]
        window.tableData["totalPrice"] = [100.0, 200.0]
        window.rows = 2
        window.formulaLogistic = 1.1

        window.logisticCalculate()

        warning.assert_called_once()
        self.assertTrue(window.mixedCurrencyWarningShown)
        self.assertEqual(window.ui.logisticVar.currentIndex(), 0)
        self.assertEqual(window.ui.logisticVar.block_calls, [True, False])
        self.assertEqual(window.tableData["logistic"], [110.0, 220.0])
        user_role = qtcore.Qt.ItemDataRole.UserRole
        self.assertEqual(window.ui.KpTable.item(0, 7).data(user_role), "TotalPrice*1.1")
        self.assertEqual(window.ui.KpTable.item(1, 7).data(user_role), "TotalPrice*1.1")
        self.assertEqual(window.apply_filters_calls, 1)

    @patch("app.ui.calculation_flow_mixin.QMessageBox.warning")
    @patch("app.ui.calculation_flow_mixin.Tool.formatPrice", side_effect=lambda value, currency: f"{currency}{value}")
    def test_logistic_calculate_distribution_sets_formula(self, _format_price, warning):
        window = _FakeWindow(logistic_mode=1)
        window.tableData["currency"] = ["¥", "¥"]
        window.tableData["totalPrice"] = [100.0, 200.0]
        window.rows = 2
        window.formulaLogistic = 30.0

        window.logisticCalculate()

        warning.assert_not_called()
        self.assertEqual(window.ui.logisticVar.currentIndex(), 1)
        self.assertEqual(window.tableData["logistic"], [110.0, 220.0])
        user_role = qtcore.Qt.ItemDataRole.UserRole
        self.assertEqual(window.ui.KpTable.item(0, 7).data(user_role), "TotalPrice+30/300*TotalPrice")
        self.assertEqual(window.ui.KpTable.item(1, 7).data(user_role), "TotalPrice+30/300*TotalPrice")
        self.assertEqual(window.apply_filters_calls, 1)

    def test_calculating_returns_when_required_data_missing(self):
        window = _FakeWindow()
        window.tableData["amount"] = []
        window.tableData["logistic"] = []

        window.calculating()

        self.assertEqual(window.calculation_service.calls, [])
        self.assertEqual(window.apply_filters_calls, 0)
        self.assertEqual(window.update_total_calls, 0)

    @patch("app.ui.calculation_flow_mixin.Tool.formatPrice", side_effect=lambda value, currency: f"{currency}{value}")
    def test_calculating_populates_cells_and_updates_totals(self, _format_price):
        result = SimpleNamespace(
            customs_sum=11,
            unit_sale_price=22,
            real_price=33,
            total_without_vat=44,
            total_with_vat=52.8,
            total_delivery_days=12,
        )
        window = _FakeWindow()
        window.rows = 1
        window.tableData = {
            "amount": [2],
            "currency": ["¥"],
            "unitPrice": [10.0],
            "totalPrice": [20.0],
            "termDelivery": [3],
            "logistic": [22.0],
        }
        window.formulaExpressions = {
            8: ["F8"],
            9: ["F9"],
            10: ["F10"],
            11: ["F11"],
            13: ["F13"],
        }
        window.calculation_service = _FakeCalculationService(result=result)

        window.calculating()

        self.assertEqual(len(window.calculation_service.calls), 1)
        self.assertEqual(window.apply_filters_calls, 1)
        self.assertEqual(window.update_total_calls, 1)
        expected_columns = [8, 9, 10, 11, 12, 13]
        actual_columns = [col for _, col, _, _ in window.set_item_calls]
        self.assertEqual(actual_columns, expected_columns)


if __name__ == "__main__":
    unittest.main()
