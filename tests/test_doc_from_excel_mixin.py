import unittest
from unittest.mock import patch
from types import SimpleNamespace
from types import ModuleType
import sys

if "PySide6" not in sys.modules:
    pyside6 = ModuleType("PySide6")
    sys.modules["PySide6"] = pyside6

pyside6 = sys.modules["PySide6"]

qtcore = sys.modules.get("PySide6.QtCore")
if qtcore is None:
    qtcore = ModuleType("PySide6.QtCore")
    sys.modules["PySide6.QtCore"] = qtcore


class _Signal:
    def __init__(self, *_args, **_kwargs):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args, **kwargs):
        for callback in list(self._callbacks):
            callback(*args, **kwargs)


class _QSignalBlocker:
    def __init__(self, *_args, **_kwargs):
        pass


class _QThread:
    def __init__(self, *_args, **_kwargs):
        pass

    def isRunning(self):
        return False

    def start(self):
        run = getattr(self, "run", None)
        if callable(run):
            run()


qtcore.QSignalBlocker = getattr(qtcore, "QSignalBlocker", _QSignalBlocker)
qtcore.QThread = getattr(qtcore, "QThread", _QThread)
qtcore.Signal = getattr(qtcore, "Signal", _Signal)
qtcore.Qt = getattr(qtcore, "Qt", type("Qt", (), {})())
pyside6.QtCore = qtcore

qtgui = sys.modules.get("PySide6.QtGui")
if qtgui is None:
    qtgui = ModuleType("PySide6.QtGui")
    sys.modules["PySide6.QtGui"] = qtgui


class _QColor:
    def __init__(self, *_args, **_kwargs):
        pass


qtgui.QColor = getattr(qtgui, "QColor", _QColor)
pyside6.QtGui = qtgui

qtwidgets = sys.modules.get("PySide6.QtWidgets")
if qtwidgets is None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    sys.modules["PySide6.QtWidgets"] = qtwidgets

pyside6.QtWidgets = qtwidgets


class _Widget:
    def __init__(self, *_args, **_kwargs):
        pass


for name in (
    "QAbstractItemView",
    "QGridLayout",
    "QHeaderView",
    "QHBoxLayout",
    "QLabel",
    "QLineEdit",
    "QPushButton",
    "QTableWidget",
    "QTableWidgetItem",
    "QTabWidget",
    "QVBoxLayout",
    "QWidget",
):
    setattr(qtwidgets, name, getattr(qtwidgets, name, _Widget))

if not hasattr(qtwidgets, "QFileDialog"):
    class _QFileDialog:
        @staticmethod
        def getOpenFileName(*args, **kwargs):
            return ("", "")

    qtwidgets.QFileDialog = _QFileDialog

if not hasattr(qtwidgets, "QInputDialog"):
    class _QInputDialog:
        @staticmethod
        def getText(*args, **kwargs):
            return ("", False)

    qtwidgets.QInputDialog = _QInputDialog

if not hasattr(qtwidgets, "QMessageBox"):
    class _QMessageBox:
        class ButtonRole:
            AcceptRole = 0
            ActionRole = 1
            RejectRole = 2
            YesRole = 3

        class StandardButton:
            Yes = 1
            No = 2

        @staticmethod
        def warning(*args, **kwargs):
            return 0

        @staticmethod
        def information(*args, **kwargs):
            return 0

        @staticmethod
        def critical(*args, **kwargs):
            return 0

        @staticmethod
        def question(*args, **kwargs):
            return _QMessageBox.StandardButton.No

        def __init__(self, *args, **kwargs):
            self._clicked_button = None

        def setWindowTitle(self, *args, **kwargs):
            pass

        def setText(self, *args, **kwargs):
            pass

        def addButton(self, *args, **kwargs):
            button = object()
            if self._clicked_button is None:
                self._clicked_button = button
            return button

        def exec(self):
            return 0

        def clickedButton(self):
            return self._clicked_button

    qtwidgets.QMessageBox = _QMessageBox

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["pandas"] = SimpleNamespace(
            notna=lambda value: value is not None,
            read_csv=None,
            read_excel=None,
        )

from app.ui.doc_from_excel_mixin import DocFromExcelMixin


class _FakeWindow(DocFromExcelMixin):
    def __init__(self):
        self.opened_payloads = []

    def openCreateDocWindow(self, payload):
        self.opened_payloads.append(payload)


class _FakeValues:
    def __init__(self, rows):
        self._rows = rows

    def tolist(self):
        return self._rows


class _FakeDataFrame:
    def __init__(self, rows):
        self._rows = rows

    def dropna(self, how="all"):
        return self

    @property
    def values(self):
        return _FakeValues(self._rows)


class DocFromExcelMixinTests(unittest.TestCase):
    @patch.object(
        DocFromExcelMixin,
        "_choose_doc_from_calculations_source",
        return_value="",
    )
    @patch("app.ui.doc_from_excel_mixin.pd.read_csv")
    @patch("app.ui.doc_from_excel_mixin.QFileDialog.getOpenFileName")
    def test_export_doc_from_excel_cancel_source_does_nothing(
        self,
        get_file_name,
        read_csv,
        _choose_source,
    ):
        window = _FakeWindow()

        window.exportDocFromExcel()

        get_file_name.assert_not_called()
        read_csv.assert_not_called()
        self.assertEqual(window.opened_payloads, [])

    @patch.object(
        DocFromExcelMixin,
        "_choose_doc_from_calculations_source",
        return_value=DocFromExcelMixin.DOC_FROM_CALCULATIONS_SOURCE_LOCAL,
    )
    @patch("app.ui.doc_from_excel_mixin.pd.read_csv")
    @patch("app.ui.doc_from_excel_mixin.QFileDialog.getOpenFileName")
    def test_export_doc_from_excel_cancel_file_does_nothing(
        self,
        get_file_name,
        read_csv,
        _choose_source,
    ):
        get_file_name.return_value = ("", "")
        window = _FakeWindow()

        window.exportDocFromExcel()

        read_csv.assert_not_called()
        self.assertEqual(window.opened_payloads, [])

    @patch.object(
        DocFromExcelMixin,
        "_choose_doc_from_calculations_source",
        return_value=DocFromExcelMixin.DOC_FROM_CALCULATIONS_SOURCE_LOCAL,
    )
    @patch("app.ui.doc_from_excel_mixin.pd.read_csv")
    @patch("app.ui.doc_from_excel_mixin.QFileDialog.getOpenFileName")
    def test_export_doc_from_excel_reads_csv_rows_and_skips_header(
        self,
        get_file_name,
        read_csv,
        _choose_source,
    ):
        get_file_name.return_value = ("/tmp/input.csv", "")
        read_csv.return_value = _FakeDataFrame(
            [
                [
                    "№",
                    "Наименование",
                    "Каталожный товар",
                    "Ед. изм.",
                    "Кол-во",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "Цена за ед. без НДС",
                    "Итого без НДС",
                    "Итого с НДС",
                    "Срок поставки",
                ],
                [1, "Насос", "SKU1", "шт", 2, "", "", "", "", "", "10", "20", "24", "5 дней"],
                [2, "Клапан", "SKU2", "шт", 1, "", "", "", "", "", "5", "5", "6", "3 дня"],
                [None, "", "", "", "", "", "", "", "", "", "", "", "", ""],
            ]
        )
        window = _FakeWindow()

        window.exportDocFromExcel()

        read_csv.assert_called_once_with("/tmp/input.csv", header=None, sep=";")
        self.assertEqual(len(window.opened_payloads), 1)
        self.assertEqual(
            window.opened_payloads[0],
            (
                2,
                [
                    [1, "Насос", "SKU1", "шт", 2, "10", "20", "24", "5 дней"],
                    [2, "Клапан", "SKU2", "шт", 1, "5", "5", "6", "3 дня"],
                ],
            ),
        )

    @patch.object(
        DocFromExcelMixin,
        "_choose_doc_from_calculations_source",
        return_value=DocFromExcelMixin.DOC_FROM_CALCULATIONS_SOURCE_LOCAL,
    )
    @patch("app.ui.doc_from_excel_mixin.pd.read_excel")
    @patch("app.ui.doc_from_excel_mixin.QFileDialog.getOpenFileName")
    def test_export_doc_from_excel_reads_excel_from_pc(
        self,
        get_file_name,
        read_excel,
        _choose_source,
    ):
        get_file_name.return_value = ("/tmp/input.xlsx", "")
        read_excel.return_value = _FakeDataFrame(
            [
                ["№", "Наименование", "Каталожный товар", "Ед. изм.", "Кол-во", "", "", "", "", "", "Цена", "Итого", "Итого НДС", "Срок"],
                [1, "Насос", "SKU1", "шт", 2, "", "", "", "", "", "10", "20", "24", "5 дней"],
            ]
        )
        window = _FakeWindow()

        window.exportDocFromExcel()

        read_excel.assert_called_once_with("/tmp/input.xlsx", header=None)
        self.assertEqual(
            window.opened_payloads[0],
            (1, [[1, "Насос", "SKU1", "шт", 2, "10", "20", "24", "5 дней"]]),
        )

    @patch.object(
        DocFromExcelMixin,
        "_choose_doc_from_calculations_source",
        return_value=DocFromExcelMixin.DOC_FROM_CALCULATIONS_SOURCE_GOOGLE,
    )
    @patch("app.ui.doc_from_excel_mixin.pd.read_excel")
    @patch("app.ui.doc_from_excel_mixin.GoogleDriveService")
    @patch("app.ui.doc_from_excel_mixin.QInputDialog.getText")
    def test_export_doc_from_excel_downloads_google_sheet(
        self,
        get_text,
        google_drive_service,
        read_excel,
        _choose_source,
    ):
        get_text.return_value = ("https://docs.google.com/spreadsheets/d/sheet-id/edit", True)
        google_drive_service.return_value.download_excel.return_value = SimpleNamespace(
            local_path="/tmp/google.xlsx",
        )
        read_excel.return_value = _FakeDataFrame(
            [
                ["№", "Наименование", "Каталожный товар", "Ед. изм.", "Кол-во", "", "", "", "", "", "Цена", "Итого", "Итого НДС", "Срок"],
                [1, "Клапан", "SKU2", "шт", 1, "", "", "", "", "", "5", "5", "6", "3 дня"],
            ]
        )
        window = _FakeWindow()

        window.exportDocFromExcel()

        google_drive_service.return_value.download_excel.assert_called_once_with(
            "https://docs.google.com/spreadsheets/d/sheet-id/edit",
        )
        read_excel.assert_called_once_with("/tmp/google.xlsx", header=None)
        self.assertEqual(
            window.opened_payloads[0],
            (1, [[1, "Клапан", "SKU2", "шт", 1, "5", "5", "6", "3 дня"]]),
        )


if __name__ == "__main__":
    unittest.main()
