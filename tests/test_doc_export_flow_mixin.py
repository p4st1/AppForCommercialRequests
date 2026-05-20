import sys
import unittest
from types import ModuleType
from unittest.mock import patch

from config import Config


pyside6 = sys.modules.get("PySide6")
if pyside6 is None:
    pyside6 = ModuleType("PySide6")
    sys.modules["PySide6"] = pyside6

qtwidgets = sys.modules.get("PySide6.QtWidgets")
if qtwidgets is None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    sys.modules["PySide6.QtWidgets"] = qtwidgets

if not hasattr(qtwidgets, "QMessageBox"):
    class _QMessageBox:
        @staticmethod
        def warning(*args, **kwargs):
            return 0

        @staticmethod
        def critical(*args, **kwargs):
            return 0

        @staticmethod
        def information(*args, **kwargs):
            return 0

    qtwidgets.QMessageBox = _QMessageBox

pyside6.QtWidgets = qtwidgets


class _FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)


class _FakeNumLine:
    def __init__(self):
        self.value = ""

    def setText(self, text):
        self.value = text


class _FakeRadio:
    def __init__(self):
        self.checked = False
        self.enabled = True

    def setChecked(self, value):
        self.checked = bool(value)

    def setEnabled(self, value):
        self.enabled = bool(value)


class _FakeCreateDocUi:
    def __init__(self):
        self.numLine = _FakeNumLine()


class _FakeCreateDocWindow:
    instances = []

    def __init__(self, parent, tableData=None):
        self.parent = parent
        self.tableData = tableData
        self.ui = _FakeCreateDocUi()
        self.windowClosed = _FakeSignal()
        self.documentCreated = _FakeSignal()
        self.googleDocxFormatRadio = _FakeRadio()
        self.docxFormatRadio = _FakeRadio()
        self.pdfFormatRadio = _FakeRadio()
        self.shown = False
        self.__class__.instances.append(self)

    def show(self):
        self.shown = True


create_document_module = ModuleType("createDocument")
create_document_module.mainWindow = _FakeCreateDocWindow
sys.modules["createDocument"] = create_document_module

from app.ui.doc_export_flow_mixin import DocExportFlowMixin


class _FakeRequestNumberLine:
    def __init__(self, value):
        self._value = value

    def text(self):
        return self._value


class _FakeTableWidget:
    def __init__(self):
        self.row_count_values = []

    def setRowCount(self, value):
        self.row_count_values.append(value)


class _FakeTabWidget:
    def __init__(self, web_tab):
        self._web_tab = web_tab
        self.indices = []

    def indexOf(self, tab):
        if tab is self._web_tab:
            return 1
        return -1

    def setCurrentIndex(self, index):
        self.indices.append(index)


class _FakeMainUi:
    def __init__(self):
        self.requestNumberLine = _FakeRequestNumberLine("  42  ")
        self.KpTable = _FakeTableWidget()
        self.webTab = object()
        self.tabWidget = _FakeTabWidget(self.webTab)


class _FakeMainWindow(DocExportFlowMixin):
    def __init__(self):
        self.ui = _FakeMainUi()
        self.error_calls = []
        self.table_data = []
        self.mixed_currencies = False
        self.history_updates = 0
        self.close_calls = 0
        self.load_trades_calls = 0
        self.export_trade_calls = []
        self.finish_loading_messages = []
        self.auth_status_values = []
        self.all_trades = []
        self.pending_submission_metadata_calls = []

    def error(self, title, message):
        self.error_calls.append((title, message))

    def _has_mixed_currencies(self):
        return self.mixed_currencies

    def getTableData(self):
        return list(self.table_data)

    def updateHistoryTable(self):
        self.history_updates += 1

    def closeTable(self, *args, **kwargs):
        self.close_calls += 1

    def _ensure_platform_tab(self):
        return None

    def load_trades(self):
        self.load_trades_calls += 1

    def export_trade(self, lot_id):
        self.export_trade_calls.append(lot_id)

    def _set_pending_submission_export_metadata(self, trade, *, submission_context=None):
        self.pending_submission_metadata_calls.append((trade, submission_context))

    def _finish_trades_loading(self, status_message):
        self.finish_loading_messages.append(status_message)

    def _set_auth_status(self, *, is_auth):
        self.auth_status_values.append(is_auth)


def _has_bound_callback(callbacks, owner, method_name):
    for callback in callbacks:
        if getattr(callback, "__self__", None) is owner and getattr(
            getattr(callback, "__func__", None),
            "__name__",
            "",
        ) == method_name:
            return True
    return False


class DocExportFlowMixinTests(unittest.TestCase):
    def setUp(self):
        self._old_is_table_opened = Config.isTableOpened
        self._old_close_table = Config.settings.get("closeTable")
        _FakeCreateDocWindow.instances.clear()

    def tearDown(self):
        Config.isTableOpened = self._old_is_table_opened
        Config.settings["closeTable"] = self._old_close_table

    def test_open_create_doc_window_sets_number_and_hooks_callbacks(self):
        Config.settings["closeTable"] = True
        window = _FakeMainWindow()

        payload = (2, [["row-1"], ["row-2"]])
        window.openCreateDocWindow(payload)

        self.assertEqual(len(_FakeCreateDocWindow.instances), 1)
        created_window = _FakeCreateDocWindow.instances[0]
        self.assertIs(created_window.parent, window)
        self.assertEqual(created_window.tableData, payload)
        self.assertEqual(created_window.ui.numLine.value, "42")
        self.assertTrue(created_window.shown)
        self.assertTrue(
            _has_bound_callback(created_window.windowClosed.callbacks, window, "updateHistoryTable")
        )
        self.assertTrue(_has_bound_callback(created_window.windowClosed.callbacks, window, "closeTable"))
        self.assertEqual(window.ui.KpTable.row_count_values, [0])

    def test_open_create_doc_window_can_force_google_docx_and_connect_callback(self):
        Config.settings["closeTable"] = False
        window = _FakeMainWindow()
        callback = lambda payload: payload

        window.openCreateDocWindow(
            (1, [["row"]]),
            force_google_docx=True,
            on_document_created=callback,
        )

        created_window = _FakeCreateDocWindow.instances[0]
        self.assertTrue(created_window.googleDocxFormatRadio.checked)
        self.assertFalse(created_window.docxFormatRadio.enabled)
        self.assertFalse(created_window.pdfFormatRadio.enabled)
        self.assertEqual(created_window.documentCreated.callbacks, [callback])

    @patch("app.ui.doc_export_flow_mixin.Tool.write_log")
    def test_export_docs_requires_loaded_table(self, write_log):
        Config.isTableOpened = False
        window = _FakeMainWindow()

        window.exportDocs()

        write_log.assert_not_called()
        self.assertEqual(len(_FakeCreateDocWindow.instances), 0)
        self.assertEqual(window.error_calls, [("Ошибка", "Загрузите КП поставщика")])

    @patch("app.ui.doc_export_flow_mixin.Tool.write_log")
    def test_export_docs_blocks_mixed_currency(self, write_log):
        Config.isTableOpened = True
        window = _FakeMainWindow()
        window.mixed_currencies = True

        window.exportDocs()

        write_log.assert_not_called()
        self.assertEqual(len(_FakeCreateDocWindow.instances), 0)
        self.assertEqual(
            window.error_calls,
            [("Ошибка", "Создание КП в DOCX для таблицы со смешанной валютой не поддерживается.")],
        )

    @patch("app.ui.doc_export_flow_mixin.Tool.write_log")
    def test_export_docs_happy_path_opens_create_doc_window(self, write_log):
        Config.isTableOpened = True
        Config.settings["closeTable"] = False
        window = _FakeMainWindow()
        window.table_data = [["1"], ["2"]]

        window.exportDocs()

        self.assertEqual(write_log.call_args_list[0].args, ("CREATING DOCX",))
        self.assertEqual(write_log.call_args_list[1].args, ("CREATING DOCX...",))
        self.assertEqual(len(_FakeCreateDocWindow.instances), 1)
        created_window = _FakeCreateDocWindow.instances[0]
        self.assertEqual(created_window.tableData, (2, [["1"], ["2"]]))
        self.assertEqual(window.error_calls, [])

    def test_run_web_pipeline_switches_tab_and_starts_loading(self):
        window = _FakeMainWindow()

        window.run_web_pipeline("A-100")

        self.assertEqual(window.ui.tabWidget.indices, [1])
        self.assertEqual(window.load_trades_calls, 1)
        self.assertEqual(window._web_pipeline_trade_number, "A-100")

    def test_on_trades_loaded_continues_pipeline_and_exports_lot(self):
        window = _FakeMainWindow()
        context = {
            "customer": "ООО Тест",
            "producer": "Завод",
            "offer_validity_period": "01.06.2026",
            "delivery_order": "",
            "payment_terms": "",
            "payment_condition": "",
            "supplier_status": "Посредник",
            "warranty": "12 мес.",
        }
        window.run_web_pipeline("A-100", submission_context=context)
        window.all_trades = [
            {"registeredNumber": "ZZ-1", "lots": [{"id": 10}]},
            {"registeredNumber": "A-100", "lots": [{"id": 77}]},
        ]

        window.on_trades_loaded(window.all_trades)

        self.assertEqual(window.export_trade_calls, [77])
        self.assertEqual(window._web_pipeline_trade_number, "")
        self.assertEqual(
            window.pending_submission_metadata_calls,
            [(window.all_trades[1], context)],
        )

    def test_run_web_pipeline_adds_default_offer_validity_to_context(self):
        window = _FakeMainWindow()

        window.run_web_pipeline("A-100", submission_context={"customer": "ООО Тест"})

        context = window._web_pipeline_submission_context
        self.assertEqual(context["customer"], "ООО Тест")
        self.assertRegex(context["offer_validity_period"], r"^\d{2}\.\d{2}\.\d{4}$")
        self.assertEqual(context["supplier_status"], "")
        self.assertEqual(context["warranty"], "")

    @patch("app.ui.doc_export_flow_mixin.QMessageBox.warning")
    def test_on_trades_loaded_shows_warning_when_trade_not_found(self, warning):
        window = _FakeMainWindow()
        window.run_web_pipeline("A-404")
        window.all_trades = [{"registeredNumber": "A-100", "lots": [{"id": 77}]}]

        window.on_trades_loaded(window.all_trades)

        warning.assert_called_once()
        self.assertEqual(window.export_trade_calls, [])
        self.assertEqual(window._web_pipeline_trade_number, "")

    @patch("app.ui.doc_export_flow_mixin.QMessageBox.critical")
    def test_on_error_with_pipeline_shows_critical_and_finishes_loading(self, critical):
        window = _FakeMainWindow()
        window._web_pipeline_trade_number = "A-500"

        window.on_error("401 Unauthorized")

        critical.assert_called_once()
        self.assertEqual(window._web_pipeline_trade_number, "")
        self.assertEqual(window.finish_loading_messages, ["Ошибка загрузки заявок"])
        self.assertEqual(window.auth_status_values, [False])


if __name__ == "__main__":
    unittest.main()
