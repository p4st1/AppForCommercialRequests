import sys
import unittest
from types import ModuleType
from unittest.mock import patch

from config import Config


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


class _FakeMainUi:
    def __init__(self):
        self.requestNumberLine = _FakeRequestNumberLine("  42  ")
        self.KpTable = _FakeTableWidget()


class _FakeMainWindow(DocExportFlowMixin):
    def __init__(self):
        self.ui = _FakeMainUi()
        self.error_calls = []
        self.table_data = []
        self.mixed_currencies = False
        self.history_updates = 0
        self.close_calls = 0

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


if __name__ == "__main__":
    unittest.main()
