import unittest
from unittest.mock import patch
from types import SimpleNamespace
from types import ModuleType
import sys

if "PySide6" not in sys.modules:
    qtwidgets = ModuleType("PySide6.QtWidgets")

    class _QFileDialog:
        @staticmethod
        def getOpenFileName(*args, **kwargs):
            return ("", "")

    qtwidgets.QFileDialog = _QFileDialog
    pyside6 = ModuleType("PySide6")
    pyside6.QtWidgets = qtwidgets
    sys.modules["PySide6"] = pyside6
    sys.modules["PySide6.QtWidgets"] = qtwidgets

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["pandas"] = SimpleNamespace(
            notna=lambda value: value is not None,
            read_csv=None,
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
    @patch("app.ui.doc_from_excel_mixin.pd.read_csv")
    @patch("app.ui.doc_from_excel_mixin.QFileDialog.getOpenFileName")
    def test_export_doc_from_excel_cancel_does_nothing(self, get_file_name, read_csv):
        get_file_name.return_value = ("", "")
        window = _FakeWindow()

        window.exportDocFromExcel()

        read_csv.assert_not_called()
        self.assertEqual(window.opened_payloads, [])

    @patch("app.ui.doc_from_excel_mixin.pd.read_csv")
    @patch("app.ui.doc_from_excel_mixin.QFileDialog.getOpenFileName")
    def test_export_doc_from_excel_reads_rows_and_skips_header(self, get_file_name, read_csv):
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


if __name__ == "__main__":
    unittest.main()
