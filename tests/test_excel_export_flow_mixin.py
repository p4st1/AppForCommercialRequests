import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from config import Config

if "PySide6.QtCore" not in sys.modules:
    qtcore = ModuleType("PySide6.QtCore")

    class _ItemDataRole:
        UserRole = 32

    class _Qt:
        ItemDataRole = _ItemDataRole

    qtcore.Qt = _Qt
    sys.modules["PySide6.QtCore"] = qtcore

    pyside6 = sys.modules.get("PySide6")
    if pyside6 is None:
        pyside6 = ModuleType("PySide6")
        sys.modules["PySide6"] = pyside6
    pyside6.QtCore = qtcore

pyside6 = sys.modules.get("PySide6")
if pyside6 is None:
    pyside6 = ModuleType("PySide6")
    sys.modules["PySide6"] = pyside6

if "PySide6.QtWidgets" not in sys.modules:
    qtwidgets = ModuleType("PySide6.QtWidgets")

    class _QMessageBox:
        @staticmethod
        def information(*args, **kwargs):
            return 0

    qtwidgets.QMessageBox = _QMessageBox
    sys.modules["PySide6.QtWidgets"] = qtwidgets
    pyside6.QtWidgets = qtwidgets

if "create" not in sys.modules:
    create_module = ModuleType("create")
    create_module.createExcelFile = lambda payload: SimpleNamespace(success=False, error_message="", output_path="")
    sys.modules["create"] = create_module

from app.ui.excel_export_flow_mixin import ExcelExportFlowMixin


class _FakeItem:
    def __init__(self, text="", user_role_data=""):
        self._text = text
        self._user_role_data = user_role_data

    def text(self):
        return str(self._text)

    def data(self, _role):
        return self._user_role_data


class _FakeTableWidget:
    def __init__(self, rows):
        self._rows = rows

    def rowCount(self):
        return len(self._rows)

    def columnCount(self):
        return max((len(row) for row in self._rows), default=0)

    def item(self, row, col):
        if row < 0 or row >= len(self._rows):
            return None
        row_items = self._rows[row]
        if col < 0 or col >= len(row_items):
            return None
        return row_items[col]


class _FakeLineEdit:
    def __init__(self, value):
        self._value = value

    def text(self):
        return self._value


class _FakeComboBox:
    def __init__(self, index):
        self._index = index

    def currentIndex(self):
        return self._index


class _FakeUi:
    def __init__(self, table_rows):
        self.KpTable = _FakeTableWidget(table_rows)
        self.requestNumberLine = _FakeLineEdit("  REQ-1  ")
        self.logisticVar = _FakeComboBox(1)


class _FakeHistoryService:
    def __init__(self):
        self.record_calls = []
        self.saved = False

    def record_excel_export(self, **kwargs):
        self.record_calls.append(kwargs)

    def save(self):
        self.saved = True


class _FakeWindow(ExcelExportFlowMixin):
    FORMULA_EDITABLE_COLUMNS = {8, 9, 10, 11, 13}

    def __init__(self, table_rows):
        self.ui = _FakeUi(table_rows)
        self.history_service = _FakeHistoryService()
        self.formulaExpressions = {
            8: ["c8-r1", "c8-r2"],
            9: ["c9-r1", "c9-r2"],
            10: ["c10-r1", "c10-r2"],
            11: ["c11-r1", "c11-r2"],
            13: ["c13-r1", "c13-r2"],
        }
        self.mixed_currencies = False
        self.parse_result = {
            "logistic": 1.1,
            "custom": 1.2,
            "markup": 1.3,
            "termDelivery": 5,
        }
        self.error_calls = []
        self.updated_history = 0
        self.total_result = (321.5, "¥")

    def error(self, title, text):
        self.error_calls.append((title, text))

    def _has_mixed_currencies(self):
        return self.mixed_currencies

    def _parse_input_parameters(self, show_error=True):
        return self.parse_result

    def _vat_multiplier(self):
        return 1.2

    def _load_formula_parameters(self):
        return {"X": 10}

    def _table_column_total(self, _col):
        return self.total_result

    def updateHistoryTable(self):
        self.updated_history += 1


class ExcelExportFlowMixinTests(unittest.TestCase):
    def setUp(self):
        self._old_is_table_opened = Config.isTableOpened

    def tearDown(self):
        Config.isTableOpened = self._old_is_table_opened

    def _build_window(self):
        table_rows = [
            [
                _FakeItem("1"),
                _FakeItem("Насос"),
                _FakeItem("SKU1"),
                _FakeItem("шт"),
                _FakeItem("2"),
                _FakeItem("10"),
                _FakeItem("20"),
                _FakeItem("22", {"formula": "TotalPrice*1.1"}),
                _FakeItem("x"),
            ],
            [
                _FakeItem("2"),
                _FakeItem("Клапан"),
                _FakeItem("SKU2"),
                _FakeItem("шт"),
                _FakeItem("1"),
                _FakeItem("5"),
                _FakeItem("5"),
                _FakeItem("5.5", "ManualFormula"),
                None,
            ],
        ]
        return _FakeWindow(table_rows)

    @patch("app.ui.excel_export_flow_mixin.exportExcelFile")
    def test_export_excel_requires_loaded_table(self, export_excel_file):
        Config.isTableOpened = False
        window = self._build_window()

        window.exportExcel()

        export_excel_file.assert_not_called()
        self.assertEqual(window.error_calls, [("Ошибка", "Загрузите КП поставщика")])

    @patch("app.ui.excel_export_flow_mixin.exportExcelFile")
    def test_export_excel_blocks_mixed_currency(self, export_excel_file):
        Config.isTableOpened = True
        window = self._build_window()
        window.mixed_currencies = True

        window.exportExcel()

        export_excel_file.assert_not_called()
        self.assertEqual(
            window.error_calls,
            [("Ошибка", "Создание Excel для таблицы со смешанной валютой не поддерживается.")],
        )

    @patch("app.ui.excel_export_flow_mixin.exportExcelFile")
    def test_export_excel_stops_when_parse_fails(self, export_excel_file):
        Config.isTableOpened = True
        window = self._build_window()
        window.parse_result = None

        window.exportExcel()

        export_excel_file.assert_not_called()
        self.assertEqual(window.error_calls, [])

    @patch("app.ui.excel_export_flow_mixin.exportExcelFile")
    def test_export_excel_reports_export_error(self, export_excel_file):
        Config.isTableOpened = True
        window = self._build_window()
        export_excel_file.return_value = SimpleNamespace(success=False, error_message="Broken file")

        window.exportExcel()

        self.assertEqual(window.error_calls, [("Ошибка", "Broken file")])
        self.assertEqual(window.history_service.record_calls, [])
        self.assertFalse(window.history_service.saved)
        self.assertEqual(window.updated_history, 0)

    @patch("app.ui.excel_export_flow_mixin.QMessageBox.information")
    @patch("app.ui.excel_export_flow_mixin.exportExcelFile")
    def test_export_excel_happy_path_records_history(self, export_excel_file, information):
        Config.isTableOpened = True
        window = self._build_window()
        export_excel_file.return_value = SimpleNamespace(success=True, output_path="/tmp/out.xlsx")

        window.exportExcel()

        export_excel_file.assert_called_once()
        payload = export_excel_file.call_args.args[0]
        self.assertEqual(payload["request_number"], "REQ-1")
        self.assertEqual(payload["logistic_mode"], 1)
        self.assertEqual(payload["logistic_value"], 1.1)
        self.assertEqual(payload["custom_value"], 1.2)
        self.assertEqual(payload["markup_value"], 1.3)
        self.assertEqual(payload["term_delivery"], 5)
        self.assertEqual(payload["vat_multiplier"], 1.2)
        self.assertEqual(payload["named_parameters"], {"X": 10})
        self.assertEqual(payload["logistic_formulas"], ["TotalPrice*1.1", "ManualFormula"])
        self.assertEqual(payload["table_rows"][1][8], "")
        self.assertEqual(payload["formula_expressions"][8], ["c8-r1", "c8-r2"])
        self.assertEqual(payload["formula_expressions"][13], ["c13-r1", "c13-r2"])

        self.assertEqual(len(window.history_service.record_calls), 1)
        self.assertEqual(
            window.history_service.record_calls[0],
            {
                "items_count": 2,
                "total_amount": 321.5,
                "currency": "¥",
                "file_path": "/tmp/out.xlsx",
            },
        )
        self.assertTrue(window.history_service.saved)
        self.assertEqual(window.updated_history, 1)
        self.assertEqual(window.error_calls, [])
        information.assert_called_once_with(
            window,
            "Сохранение расчетов",
            "Расчеты успешно сохранены.\n/tmp/out.xlsx",
        )


if __name__ == "__main__":
    unittest.main()
