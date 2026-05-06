import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

from docx import Document
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter


def _ensure_pyside_stubs() -> None:
    pyside6 = sys.modules.get("PySide6")
    if pyside6 is None:
        pyside6 = ModuleType("PySide6")
        sys.modules["PySide6"] = pyside6

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

    class _QThread:
        def __init__(self, *_args, **_kwargs):
            pass

        def start(self):
            run = getattr(self, "run", None)
            if callable(run):
                run()

    class _QSettings:
        _values = {}

        def __init__(self, *_args, **_kwargs):
            pass

        def value(self, key, default=None, type=None):
            value = self._values.get(key, default)
            if type is not None and value is not None:
                try:
                    return type(value)
                except Exception:
                    return default
            return value

        def setValue(self, key, value):
            self._values[key] = value

    class _QTimer:
        def __init__(self, *_args, **_kwargs):
            self.timeout = _Signal()

        def setInterval(self, *_args, **_kwargs):
            pass

        def start(self, *_args, **_kwargs):
            pass

        def stop(self):
            pass

    qtcore.QSettings = getattr(qtcore, "QSettings", _QSettings)
    qtcore.QThread = getattr(qtcore, "QThread", _QThread)
    qtcore.Signal = getattr(qtcore, "Signal", _Signal)
    qtcore.QTimer = getattr(qtcore, "QTimer", _QTimer)

    qt = getattr(qtcore, "Qt", type("Qt", (), {})())
    for nested_name, values in {
        "ItemDataRole": {"EditRole": 2, "UserRole": 32, "BackgroundRole": 8},
        "AlignmentFlag": {
            "AlignLeft": 1,
            "AlignRight": 2,
            "AlignVCenter": 4,
            "AlignCenter": 8,
        },
        "PenStyle": {"SolidLine": 1},
        "ItemFlag": {
            "ItemIsEditable": 1,
            "ItemIsUserCheckable": 2,
            "ItemIsEnabled": 4,
        },
        "CheckState": {"Unchecked": 0, "Checked": 2},
    }.items():
        nested = getattr(qt, nested_name, type(nested_name, (), {})())
        for attr, value in values.items():
            setattr(nested, attr, getattr(nested, attr, value))
        setattr(qt, nested_name, nested)
    qtcore.Qt = qt
    pyside6.QtCore = qtcore

    qtgui = sys.modules.get("PySide6.QtGui")
    if qtgui is None:
        qtgui = ModuleType("PySide6.QtGui")
        sys.modules["PySide6.QtGui"] = qtgui

    class _QAction:
        def __init__(self, *_args, **_kwargs):
            self.triggered = _Signal()

    class _QColor:
        def __init__(self, *_args, **_kwargs):
            pass

        def isValid(self):
            return True

    qtgui.QAction = getattr(qtgui, "QAction", _QAction)
    qtgui.QColor = getattr(qtgui, "QColor", _QColor)
    pyside6.QtGui = qtgui

    qtuitools = sys.modules.get("PySide6.QtUiTools")
    if qtuitools is None:
        qtuitools = ModuleType("PySide6.QtUiTools")
        sys.modules["PySide6.QtUiTools"] = qtuitools
    if not hasattr(qtuitools, "loadUiType"):
        qtuitools.loadUiType = lambda *_args, **_kwargs: (object, object)
    pyside6.QtUiTools = qtuitools

    qtwidgets = sys.modules.get("PySide6.QtWidgets")
    if qtwidgets is None:
        qtwidgets = ModuleType("PySide6.QtWidgets")
        sys.modules["PySide6.QtWidgets"] = qtwidgets

    class _Widget:
        def __init__(self, *_args, **_kwargs):
            pass

    class _QFileDialog:
        @staticmethod
        def getOpenFileName(*_args, **_kwargs):
            return ("", "")

    class _QMessageBox:
        @staticmethod
        def warning(*_args, **_kwargs):
            return 0

        @staticmethod
        def critical(*_args, **_kwargs):
            return 0

        @staticmethod
        def information(*_args, **_kwargs):
            return 0

    class _QAbstractItemView:
        SelectionBehavior = type("SelectionBehavior", (), {"SelectRows": 1})
        EditTrigger = type("EditTrigger", (), {"NoEditTriggers": 0})

    class _QHeaderView:
        ResizeMode = type(
            "ResizeMode",
            (),
            {"Interactive": 1, "ResizeToContents": 2, "Stretch": 3},
        )

    class _QTableWidgetItem:
        def __init__(self, text=""):
            self._text = str(text)
            self._data = {}
            self._flags = 0

        def text(self):
            return self._text

        def setText(self, text):
            self._text = str(text)

        def data(self, role):
            return self._data.get(role)

        def setData(self, role, value):
            self._data[role] = value

        def flags(self):
            return self._flags

        def setFlags(self, flags):
            self._flags = flags

        def setTextAlignment(self, *_args, **_kwargs):
            pass

        def setCheckState(self, *_args, **_kwargs):
            pass

        def setBackground(self, *_args, **_kwargs):
            pass

    for name, value in {
        "QAbstractItemView": _QAbstractItemView,
        "QCheckBox": _Widget,
        "QDoubleSpinBox": _Widget,
        "QFileDialog": _QFileDialog,
        "QHeaderView": _QHeaderView,
        "QHBoxLayout": _Widget,
        "QLabel": _Widget,
        "QListWidget": _Widget,
        "QListWidgetItem": _Widget,
        "QMessageBox": _QMessageBox,
        "QPushButton": _Widget,
        "QSpinBox": _Widget,
        "QTableWidget": _Widget,
        "QTableWidgetItem": _QTableWidgetItem,
        "QTabWidget": _Widget,
        "QWidget": _Widget,
    }.items():
        if not hasattr(qtwidgets, name):
            setattr(qtwidgets, name, value)
    pyside6.QtWidgets = qtwidgets


_ensure_pyside_stubs()

from ui_mixins.export_mixin import ExportMixin


class _FakeItem:
    def __init__(self, text):
        self._text = text

    def text(self):
        return str(self._text)


class _FakeRetradeTable:
    def __init__(self, headers, rows):
        self._headers = [_FakeItem(header) for header in headers]
        self._rows = [
            [None if value is None else _FakeItem(value) for value in row]
            for row in rows
        ]

    def columnCount(self):
        return len(self._headers)

    def rowCount(self):
        return len(self._rows)

    def horizontalHeaderItem(self, column):
        if column < 0 or column >= len(self._headers):
            return None
        return self._headers[column]

    def item(self, row, column):
        if row < 0 or row >= len(self._rows):
            return None
        row_values = self._rows[row]
        if column < 0 or column >= len(row_values):
            return None
        return row_values[column]


class _FakeEditableItem:
    def __init__(self, value):
        self._value = value

    def data(self, _role):
        return self._value

    def text(self):
        return "" if self._value is None else str(self._value)


class _FakeEditableTable:
    def __init__(self, rows, headers=None):
        self._headers = [_FakeItem(header) for header in (headers or [])]
        self._rows = [
            [None if value is None else _FakeEditableItem(value) for value in row]
            for row in rows
        ]

    def rowCount(self):
        return len(self._rows)

    def columnCount(self):
        return max([len(self._headers), *(len(row) for row in self._rows)], default=0)

    def horizontalHeaderItem(self, column):
        if column < 0 or column >= len(self._headers):
            return None
        return self._headers[column]

    def item(self, row, column):
        if row < 0 or row >= len(self._rows):
            return None
        row_values = self._rows[row]
        if column < 0 or column >= len(row_values):
            return None
        return row_values[column]


class RetradeCalculationsParserTests(unittest.TestCase):
    def test_parse_uses_first_non_empty_row_as_headers(self):
        parsed = ExportMixin._parse_retrade_calculations(
            [
                [{"value": "", "currency": None}, {"value": None, "currency": None}],
                [{"value": "№", "currency": None}, {"value": "Цена", "currency": None}],
                [{"value": 1, "currency": None}, {"value": 1000, "currency": "RUB"}],
                [{"value": 2, "currency": None}, {"value": 5, "currency": None}],
            ]
        )
        self.assertEqual(
            parsed["headers"],
            ["№", "Цена"],
        )
        self.assertEqual(
            parsed["rows"],
            [
                [
                    {"value": 1, "currency": None},
                    {"value": 1000, "currency": "RUB"},
                ],
                [
                    {"value": 2, "currency": None},
                    {"value": 5, "currency": None},
                ],
            ],
        )
        self.assertIsNone(parsed["total_without_vat"])
        self.assertIsNone(parsed["total_without_vat_currency"])
        self.assertEqual(parsed["totals"], {"price": 0.0, "logistic": 0.0, "customs": 0.0})
        self.assertEqual(
            parsed["totals_currency"],
            {"price": None, "logistic": None, "customs": None},
        )

    def test_parse_skips_fully_empty_rows_and_keeps_all_data_rows(self):
        parsed = ExportMixin._parse_retrade_calculations(
            [
                [{"value": "Код", "currency": None}, {"value": "Значение", "currency": None}],
                [{"value": "", "currency": None}, {"value": None, "currency": None}],
                [{"value": 2, "currency": None}, {"value": 20, "currency": "USD"}],
                [{"value": 3, "currency": None}, {"value": "30 руб", "currency": "RUB"}],
            ]
        )
        self.assertEqual(parsed["headers"], ["Код", "Значение"])
        self.assertEqual(
            parsed["rows"],
            [
                [
                    {"value": 2, "currency": None},
                    {"value": 20, "currency": "USD"},
                ],
                [
                    {"value": 3, "currency": None},
                    {"value": "30 руб", "currency": "RUB"},
                ],
            ],
        )
        self.assertIsNone(parsed["total_without_vat"])
        self.assertIsNone(parsed["total_without_vat_currency"])
        self.assertEqual(parsed["totals"], {"price": 0.0, "logistic": 0.0, "customs": 0.0})
        self.assertEqual(
            parsed["totals_currency"],
            {"price": None, "logistic": None, "customs": None},
        )

    def test_parse_returns_empty_structure_for_empty_file(self):
        parsed = ExportMixin._parse_retrade_calculations(
            [
                [{"value": None, "currency": None}],
                [{"value": "", "currency": None}],
            ]
        )
        self.assertEqual(
            parsed,
            {
                "headers": [],
                "rows": [],
                "total_without_vat": None,
                "total_without_vat_currency": None,
                "totals": {"price": 0.0, "logistic": 0.0, "customs": 0.0},
                "totals_currency": {"price": None, "logistic": None, "customs": None},
            },
        )

    def test_parse_extracts_total_without_vat_and_removes_service_row(self):
        parsed = ExportMixin._parse_retrade_calculations(
            [
                [{"value": "Наименование", "currency": None}, {"value": "Сумма", "currency": None}],
                [{"value": 1, "currency": None}, {"value": 1250000, "currency": "RUB"}],
                [{"value": "Итого без НДС", "currency": None}, {"value": 1250000, "currency": "RUB"}],
            ]
        )
        self.assertEqual(
            parsed["headers"],
            ["Наименование"],
        )
        self.assertEqual(
            parsed["rows"],
            [[{"value": 1, "currency": None}]],
        )
        self.assertEqual(parsed["total_without_vat"], 1250000)
        self.assertEqual(parsed["total_without_vat_currency"], "RUB")
        self.assertEqual(parsed["totals"], {"price": 0.0, "logistic": 0.0, "customs": 0.0})
        self.assertEqual(
            parsed["totals_currency"],
            {"price": None, "logistic": None, "customs": None},
        )

    def test_parse_keeps_only_position_rows_by_first_cell(self):
        parsed = ExportMixin._parse_retrade_calculations(
            [
                [{"value": "№", "currency": None}, {"value": "Сумма", "currency": None}],
                [{"value": 1, "currency": None}, {"value": 1000, "currency": "RUB"}],
                [{"value": "2", "currency": None}, {"value": 2000, "currency": "RUB"}],
                [{"value": "Прибыль", "currency": None}, {"value": 500, "currency": "RUB"}],
                [{"value": "Итого", "currency": None}, {"value": 3000, "currency": "RUB"}],
            ]
        )
        self.assertEqual(
            parsed["headers"],
            ["№"],
        )
        self.assertEqual(
            parsed["rows"],
            [
                [{"value": 1, "currency": None}],
                [{"value": "2", "currency": None}],
            ],
        )
        self.assertIsNone(parsed["total_without_vat"])
        self.assertIsNone(parsed["total_without_vat_currency"])
        self.assertEqual(parsed["totals"], {"price": 0.0, "logistic": 0.0, "customs": 0.0})
        self.assertEqual(
            parsed["totals_currency"],
            {"price": None, "logistic": None, "customs": None},
        )

    def test_parse_filters_service_columns_and_calculates_price_total(self):
        parsed = ExportMixin._parse_retrade_calculations(
            [
                [
                    {"value": "№", "currency": None},
                    {"value": "Цена за ед. без НДС", "currency": None},
                    {"value": "Сумма", "currency": None},
                    {"value": "Прибыль", "currency": None},
                ],
                [
                    {"value": 1, "currency": None},
                    {"value": 1000, "currency": "RUB"},
                    {"value": 3000, "currency": "RUB"},
                    {"value": 100, "currency": "RUB"},
                ],
                [
                    {"value": "2", "currency": None},
                    {"value": 2500.5, "currency": "RUB"},
                    {"value": 7501.5, "currency": "RUB"},
                    {"value": 250, "currency": "RUB"},
                ],
                [
                    {"value": "Итого", "currency": None},
                    {"value": None, "currency": None},
                    {"value": 10501.5, "currency": "RUB"},
                    {"value": 350, "currency": "RUB"},
                ],
            ]
        )
        self.assertEqual(parsed["headers"], ["№", "Цена за ед. без НДС"])
        self.assertEqual(
            parsed["rows"],
            [
                [
                    {"value": 1, "currency": None},
                    {"value": 1000, "currency": "RUB"},
                ],
                [
                    {"value": "2", "currency": None},
                    {"value": 2500.5, "currency": "RUB"},
                ],
            ],
        )
        self.assertEqual(parsed["totals"]["price"], 3500.5)
        self.assertEqual(parsed["totals"]["logistic"], 0.0)
        self.assertEqual(parsed["totals"]["customs"], 0.0)
        self.assertEqual(parsed["totals_currency"]["price"], "RUB")
        self.assertIsNone(parsed["totals_currency"]["logistic"])
        self.assertIsNone(parsed["totals_currency"]["customs"])

    def test_parse_calculates_logistic_and_customs_totals(self):
        parsed = ExportMixin._parse_retrade_calculations(
            [
                [
                    {"value": "№", "currency": None},
                    {"value": "Цена за ед. без НДС", "currency": None},
                    {"value": "Логистика", "currency": None},
                    {"value": "Таможня", "currency": None},
                ],
                [
                    {"value": 1, "currency": None},
                    {"value": 1000, "currency": "RUB"},
                    {"value": 100, "currency": "RUB"},
                    {"value": 50, "currency": "RUB"},
                ],
                [
                    {"value": 2, "currency": None},
                    {"value": 2000, "currency": "RUB"},
                    {"value": 200, "currency": "RUB"},
                    {"value": 80, "currency": "RUB"},
                ],
            ]
        )

        self.assertEqual(parsed["totals"], {"price": 3000.0, "logistic": 300.0, "customs": 130.0})
        self.assertEqual(
            parsed["totals_currency"],
            {"price": "RUB", "logistic": "RUB", "customs": "RUB"},
        )

    def test_detect_currency_from_number_format(self):
        self.assertEqual(ExportMixin._detect_currency(1000, '#,##0.00 "₽"'), "RUB")
        self.assertEqual(ExportMixin._detect_currency(1000, '#,##0.00 "$"'), "USD")
        self.assertEqual(ExportMixin._detect_currency(1000, '#,##0.00 "EUR"'), "EUR")

    def test_detect_currency_from_string_fallback(self):
        self.assertEqual(ExportMixin._detect_currency("1000 руб", "General"), "RUB")
        self.assertEqual(ExportMixin._detect_currency("1 000,00 ₽", "General"), "RUB")
        self.assertEqual(ExportMixin._detect_currency("Total $100", "General"), "USD")
        self.assertEqual(ExportMixin._detect_currency("Amount 50 eur", "General"), "EUR")

    def test_format_number_ru(self):
        self.assertEqual(ExportMixin._format_number_ru(100000), "100 000,00")
        self.assertEqual(ExportMixin._format_number_ru(1500.5), "1 500,50")
        self.assertEqual(ExportMixin._format_number_ru(100), "100,00")

    def test_format_cell_displays_currency_suffix(self):
        self.assertEqual(
            ExportMixin._format_retrade_calculations_cell_for_display(
                {"value": 100000, "currency": "RUB"}
            ),
            "100 000,00 ₽",
        )
        self.assertEqual(
            ExportMixin._format_retrade_calculations_cell_for_display(
                {"value": 5000, "currency": "USD"}
            ),
            "5 000,00 $",
        )
        self.assertEqual(
            ExportMixin._format_retrade_calculations_cell_for_display(
                {"value": 1234.5, "currency": "EUR"}
            ),
            "1 234,50 €",
        )

    def test_format_cell_returns_non_numeric_as_is(self):
        self.assertEqual(
            ExportMixin._format_retrade_calculations_cell_for_display(
                {"value": "N/A", "currency": "RUB"}
            ),
            "N/A",
        )

    def test_parse_number_accepts_currency_and_decimal_comma(self):
        self.assertEqual(ExportMixin.parse_number("30 033,85 ₽"), 30033.85)
        self.assertEqual(ExportMixin.parse_number("1,25"), 1.25)
        self.assertEqual(ExportMixin.parse_number(None), 0.0)

    def test_extract_delivery_time_text(self):
        self.assertEqual(
            ExportMixin._extract_delivery_time_text("Срок поставки: 40 дней"),
            "40 дней",
        )
        self.assertEqual(
            ExportMixin._extract_delivery_time_text("до 45 календарных дней"),
            "45 календарных дней",
        )

    def test_extract_kp_data_from_document(self):
        document = Document()
        table = document.add_table(rows=3, cols=3)
        table.rows[0].cells[0].text = "Наименование"
        table.rows[0].cells[1].text = "Срок поставки"
        table.rows[0].cells[2].text = "Цена"
        table.rows[1].cells[0].text = "Позиция 1"
        table.rows[1].cells[1].text = "40 дней"
        table.rows[2].cells[0].text = "Позиция 2"
        table.rows[2].cells[1].text = "45 дней"
        document.add_paragraph("Производитель - CAT;")

        data = ExportMixin._extract_kp_data_from_document(document)

        self.assertEqual(data["delivery_times"], ["40 дней", "45 дней"])
        self.assertEqual(data["manufacturer"], "CAT")

    def test_load_kp_docx_data_reads_saved_file(self):
        document = Document()
        table = document.add_table(rows=2, cols=2)
        table.rows[0].cells[0].text = "Позиция"
        table.rows[0].cells[1].text = "Срок поставки"
        table.rows[1].cells[0].text = "Позиция 1"
        table.rows[1].cells[1].text = "30 дней"
        document.add_paragraph("Производитель: Atlas Copco;")

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "kp.docx"
            document.save(file_path)

            data = ExportMixin._load_kp_docx_data(str(file_path))

        self.assertEqual(data["delivery_times"], ["30 дней"])
        self.assertEqual(data["manufacturer"], "Atlas Copco")

    def test_write_retrade_table_to_worksheet_preserves_formulas_and_blanks(self):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(["A", "B", "C"])
        worksheet.cell(row=2, column=1).value = "old"
        worksheet.cell(row=2, column=2).value = "=SUM(A2:A3)"
        worksheet.cell(row=2, column=3).value = "keep"
        worksheet.cell(row=3, column=1).value = "old text"
        worksheet.cell(row=3, column=2).value = "keep blank"

        table = _FakeEditableTable(
            [
                [10, 20, ""],
                ["new text", None, "=A1"],
            ]
        )

        mixin = ExportMixin()
        written_count = mixin._write_retrade_table_to_worksheet(
            worksheet,
            table,
        )

        self.assertEqual(written_count, 2)
        self.assertEqual(worksheet.cell(row=2, column=1).value, 10.0)
        self.assertEqual(worksheet.cell(row=2, column=2).value, "=SUM(A2:A3)")
        self.assertEqual(worksheet.cell(row=2, column=3).value, "keep")
        self.assertEqual(worksheet.cell(row=3, column=1).value, "new text")
        self.assertEqual(worksheet.cell(row=3, column=2).value, "keep blank")
        self.assertIsNone(worksheet.cell(row=3, column=3).value)

    def test_write_retrade_table_to_worksheet_saves_money_text_as_number(self):
        workbook = Workbook()
        worksheet = workbook.active
        headers = ["Предлагаемая цена за ед.", "Кол-во", "Сумма, CNY"]
        worksheet.append(headers)
        table = _FakeEditableTable(
            [["100 000,00", "2", "200 000,00"]],
            headers=headers,
        )

        mixin = ExportMixin()
        written_count = mixin._write_retrade_table_to_worksheet(
            worksheet,
            table,
        )

        self.assertEqual(written_count, 3)
        self.assertEqual(worksheet.cell(row=2, column=1).value, 100000.0)
        self.assertEqual(worksheet.cell(row=2, column=2).value, 2.0)
        self.assertEqual(worksheet.cell(row=2, column=3).value, 200000.0)
        self.assertEqual(
            worksheet.cell(row=2, column=1).number_format,
            mixin._currency_format("¥"),
        )
        self.assertEqual(worksheet.cell(row=2, column=2).number_format, "General")
        self.assertEqual(
            worksheet.cell(row=2, column=3).number_format,
            mixin._currency_format("¥"),
        )

    def test_write_retrade_table_to_worksheet_formats_money_formulas(self):
        workbook = Workbook()
        worksheet = workbook.active
        headers = ["Предлагаемая цена за ед.", "Кол-во", "Сумма, USD"]
        worksheet.append(headers)
        worksheet.cell(row=2, column=1).value = "=A3"
        worksheet.cell(row=2, column=3).value = "=A2*B2"
        table = _FakeEditableTable(
            [["100 000,00", "2", "200 000,00"]],
            headers=headers,
        )

        mixin = ExportMixin()
        written_count = mixin._write_retrade_table_to_worksheet(
            worksheet,
            table,
        )

        self.assertEqual(written_count, 1)
        self.assertEqual(worksheet.cell(row=2, column=1).value, "=A3")
        self.assertEqual(worksheet.cell(row=2, column=3).value, "=A2*B2")
        self.assertEqual(
            worksheet.cell(row=2, column=1).number_format,
            mixin._currency_format("$"),
        )
        self.assertEqual(
            worksheet.cell(row=2, column=3).number_format,
            mixin._currency_format("$"),
        )

    def test_collect_missing_retrade_required_cells(self):
        headers = [
            "Наименование",
            "Срок поставки",
            "Производитель",
            "Технические характеристики",
            "Условия гарантий качества",
        ]
        table = _FakeEditableTable(
            [
                ["Позиция 1", "30 дней", "Atlas Copco", "Описание", "6 мес"],
                ["Позиция 2", "", "Atlas Copco", "", "6 мес"],
                ["", "", "", "", ""],
            ],
            headers=headers,
        )

        missing = ExportMixin._collect_missing_retrade_required_cells(table)

        self.assertEqual(
            missing,
            [
                {"row": 1, "column": 1, "label": "Срок поставки"},
                {"row": 1, "column": 3, "label": "Технические характеристики"},
            ],
        )

    def test_retrade_main_row_has_position_ignores_default_manual_fields(self):
        headers = [
            "Наименование",
            "Срок поставки",
            "Производитель",
            "Условия гарантий качества",
        ]
        table = _FakeEditableTable(
            [
                ["Позиция 1", "", "", "6 мес"],
                ["", "", "", "6 мес"],
            ],
            headers=headers,
        )
        columns = ExportMixin._get_retrade_main_columns(headers)
        position_columns = ExportMixin._retrade_main_position_columns(
            headers,
            columns,
        )

        self.assertTrue(
            ExportMixin._retrade_main_row_has_position(table, 0, position_columns)
        )
        self.assertFalse(
            ExportMixin._retrade_main_row_has_position(table, 1, position_columns)
        )

    def test_format_missing_retrade_required_cells_message(self):
        message = ExportMixin._format_missing_retrade_required_cells_message(
            [
                {"row": 1, "column": 1, "label": "Срок поставки"},
                {"row": 1, "column": 2, "label": "Производитель"},
            ]
        )

        self.assertIn("строка 2: Срок поставки", message)
        self.assertIn("строка 2: Производитель", message)
        self.assertIn("Пропустить", message)

    def test_recalculate_retrade_main_row_values_updates_total(self):
        headers = ["Предлагаемая цена за ед.", "Кол-во", "Сумма"]
        columns = ExportMixin._get_retrade_main_columns(headers)

        row = ExportMixin._recalculate_retrade_main_row_values(
            ["100 000,00", "2", None],
            columns,
        )

        self.assertEqual(row, ["100 000,00", "2", 200000.0])
        self.assertEqual(ExportMixin.format_money(row[2]), "200 000,00")

    def test_format_rating_always_uses_two_decimals(self):
        mixin = ExportMixin()

        self.assertEqual(mixin.format_rating("1,234"), "1.23")
        self.assertEqual(
            mixin._format_calculations_display_value(
                "1,2",
                col_index=3,
                header="Рейтинг",
                price_columns=set(),
                rating_columns={3},
            ),
            "1.20",
        )

    def test_calculate_updated_position_prices_uses_corrected_rating(self):
        updates, sale_price_col = ExportMixin._calculate_updated_position_prices(
            [
                "№",
                "Цена за ед. без НДС",
                "Скорректированный рейтинг",
                "Цена реализации за ед. без НДС",
            ],
            [
                [
                    {"value": 1, "currency": None},
                    {"value": "30 033,85 ₽", "currency": "RUB"},
                    {"value": "1,25", "currency": None},
                    {"value": None, "currency": "RUB"},
                ],
                [
                    {"value": 2, "currency": None},
                    {"value": "", "currency": None},
                    {"value": "1,10", "currency": None},
                    {"value": None, "currency": None},
                ],
            ],
        )

        self.assertEqual(sale_price_col, 3)
        self.assertEqual(
            updates,
            [{"row": 0, "value": 37542.31, "currency": "RUB"}],
        )

    def test_calculate_updated_position_prices_prefers_excel_j_and_s(self):
        headers = [f"Колонка {index}" for index in range(1, 20)]
        headers[5] = "Цена за ед. без НДС"
        headers[9] = "Колонка J"
        headers[10] = "Цена реализации за ед. без НДС"
        headers[18] = "Скорректированный рейтинг"
        row = [{"value": None, "currency": None} for _ in headers]
        row[5] = {"value": 999, "currency": "RUB"}
        row[9] = {"value": 100, "currency": "RUB"}
        row[18] = {"value": "1,25", "currency": None}

        updates, sale_price_col = ExportMixin._calculate_updated_position_prices(
            headers,
            [row],
        )

        self.assertEqual(sale_price_col, 10)
        self.assertEqual(updates, [{"row": 0, "value": 125.0, "currency": "RUB"}])

    def test_calculate_updated_position_prices_uses_excel_columns_with_offset(self):
        headers = [""] + [f"Колонка {index}" for index in range(1, 20)]
        headers[6] = "Цена за ед. без НДС"
        headers[11] = "Цена реализации за ед. без НДС"
        headers[19] = "Скорректированный рейтинг"
        row = [{"value": None, "currency": None} for _ in headers]
        row[6] = {"value": 999, "currency": "RUB"}
        row[10] = {"value": 100, "currency": "RUB"}
        row[19] = {"value": "1,25", "currency": None}

        updates, sale_price_col = ExportMixin._calculate_updated_position_prices(
            headers,
            [row],
            column_offset=1,
        )

        self.assertEqual(sale_price_col, 11)
        self.assertEqual(updates, [{"row": 0, "value": 125.0, "currency": "RUB"}])

    def test_calculate_updated_position_prices_detects_currency_from_display_text(self):
        headers = [f"Колонка {index}" for index in range(1, 20)]
        headers[9] = "Цена за ед. без НДС"
        headers[10] = "Цена реализации за ед. без НДС"
        headers[18] = "Скорректированный рейтинг"
        row = [{"value": None, "currency": None} for _ in headers]
        row[9] = {"value": "100,00 ₽", "currency": None}
        row[18] = {"value": "1,25", "currency": None}

        updates, sale_price_col = ExportMixin._calculate_updated_position_prices(
            headers,
            [row],
        )

        self.assertEqual(sale_price_col, 10)
        self.assertEqual(updates, [{"row": 0, "value": 125.0, "currency": "RUB"}])

    def test_calculate_updated_position_prices_requires_columns(self):
        with self.assertRaises(ValueError) as context:
            ExportMixin._calculate_updated_position_prices(["№"], [])

        message = str(context.exception)
        self.assertIn("Цена за ед. без НДС", message)
        self.assertIn("Скорректированный рейтинг", message)

    def test_formula_update_row_indices_do_not_require_rating_value(self):
        row_indices = ExportMixin._formula_update_row_indices(
            [
                "№",
                "Цена за ед. без НДС",
                "Скорректированный рейтинг",
                "Цена реализации за ед. без НДС",
            ],
            [
                [
                    {"value": 1, "currency": None},
                    {"value": 81, "currency": "RUB"},
                    {"value": None, "currency": None},
                    {"value": None, "currency": "RUB"},
                ],
                [
                    {"value": 2, "currency": None},
                    {"value": "", "currency": None},
                    {"value": None, "currency": None},
                    {"value": None, "currency": "RUB"},
                ],
            ],
        )

        self.assertEqual(row_indices, [0])

    def test_write_realization_price_formulas_to_sheet(self):
        workbook = Workbook()
        worksheet = workbook.active
        headers = [f"Колонка {index}" for index in range(1, 20)]
        headers[5] = "Цена за ед. без НДС"
        headers[9] = "Колонка J"
        headers[10] = "Цена реализации за ед. без НДС"
        headers[18] = "Скорректированный рейтинг"
        worksheet.append(headers)
        worksheet.append([None for _ in headers])
        worksheet.append([None for _ in headers])
        worksheet.append([None for _ in headers])
        worksheet.cell(row=2, column=10).number_format = '#,##0.00 "₽"'

        formulas = ExportMixin._write_realization_price_formulas_to_sheet(
            worksheet,
            [0, 2],
        )

        self.assertEqual(
            formulas,
            {
                0: "=ROUND(J2*S2, 2)",
                2: "=ROUND(J4*S4, 2)",
            },
        )
        self.assertEqual(worksheet.cell(row=2, column=11).value, "=ROUND(J2*S2, 2)")
        self.assertEqual(
            worksheet.cell(row=2, column=11).number_format,
            ExportMixin._currency_format("₽"),
        )
        self.assertIsNone(worksheet.cell(row=3, column=11).value)
        self.assertEqual(worksheet.cell(row=4, column=11).value, "=ROUND(J4*S4, 2)")
        self.assertEqual(
            worksheet.cell(row=4, column=11).number_format,
            ExportMixin._currency_format(None),
        )

    def test_write_update_position_formulas_to_current_file_saves_workbook(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "calc.xlsx"
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "Рассчеты"
            headers = [f"Колонка {index}" for index in range(1, 20)]
            headers[9] = "Цена за ед. без НДС"
            headers[10] = "Цена реализации за ед. без НДС"
            headers[18] = "Скорректированный рейтинг"
            worksheet.append(headers)
            worksheet.append([None for _ in headers])
            worksheet.append([None for _ in headers])
            workbook.save(file_path)

            mixin = ExportMixin()
            mixin.calculations_file_path = str(file_path)
            mixin.current_calculations_sheet_name = "Рассчеты"

            formulas = mixin._write_update_position_formulas_to_current_calculations_file(
                [0, 1]
            )

            self.assertEqual(
                formulas,
                {
                    0: "=ROUND(J2*S2, 2)",
                    1: "=ROUND(J3*S3, 2)",
                },
            )

            result_workbook = load_workbook(file_path, data_only=False)
            try:
                result_sheet = result_workbook["Рассчеты"]
                self.assertEqual(
                    result_sheet.cell(row=2, column=11).value,
                    "=ROUND(J2*S2, 2)",
                )
                self.assertEqual(
                    result_sheet.cell(row=3, column=11).value,
                    "=ROUND(J3*S3, 2)",
                )
                self.assertEqual(result_workbook.calculation.calcMode, "auto")
                self.assertTrue(result_workbook.calculation.fullCalcOnLoad)
                self.assertTrue(result_workbook.calculation.forceFullCalc)
            finally:
                result_workbook.close()

    def test_extract_best_prices_uses_header_and_parses_currency(self):
        table = _FakeRetradeTable(
            ["Наименование", "Лучшая цена за ед."],
            [
                ["Двигатель", "102 188,50 ¥"],
                ["Насос", ""],
                ["Клапан", "нет цены"],
            ],
        )

        self.assertEqual(
            ExportMixin._extract_retrade_best_prices(table),
            [102188.5, None, None],
        )

    def test_extract_ratings_and_best_prices_uses_headers(self):
        table = _FakeRetradeTable(
            ["Наименование", "Рейтинг", "Лучшая цена за ед."],
            [
                ["Двигатель", "1,25", "102 188,50 ₽"],
                ["Насос", "", ""],
                ["Клапан", "нет рейтинга", "нет цены"],
            ],
        )

        self.assertEqual(
            ExportMixin._extract_retrade_ratings_and_best_prices(table),
            ([1.25, None, None], [102188.5, None, None]),
        )

    def test_next_retrade_sheet_title_uses_next_number(self):
        workbook = Workbook()
        workbook.active.title = "Sheet"
        workbook.create_sheet("Переторжка 1")
        workbook.create_sheet("Переторжка 2")

        self.assertEqual(
            ExportMixin._next_retrade_sheet_title(workbook),
            "Переторжка 3",
        )

    def test_write_best_prices_to_calculations_file_creates_updated_sheet(self):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Расчет"
        headers = [f"Колонка {index}" for index in range(1, 16)]
        headers[9] = "Цена за ед."
        headers[10] = "Цена реализации за ед. без НДС"
        first_row = [None for _ in headers]
        first_row[0] = "Двигатель"
        first_row[9] = 100
        second_row = [None for _ in headers]
        second_row[0] = "Насос"
        second_row[9] = 200
        worksheet.append(headers)
        worksheet.append(first_row)
        worksheet.append(second_row)

        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        temp_file.close()
        file_path = temp_file.name

        try:
            workbook.save(file_path)
            workbook.close()

            sheet_title = ExportMixin._write_best_prices_to_calculations_file(
                file_path,
                [102188.5, None, 3000.0],
                ratings=[1.25, None, 2.0],
                min_margin=1.15,
                delta_percent=2,
            )

            result_workbook = load_workbook(file_path, data_only=False)
            try:
                self.assertEqual(sheet_title, "Переторжка 1")
                self.assertIn(sheet_title, result_workbook.sheetnames)
                result_sheet = result_workbook[sheet_title]
                real_rating_col_index = 16
                best_price_col_index = 17
                formula_col_index = 18
                corrected_rating_col_index = 19
                realization_price_col_index = 11

                self.assertEqual(
                    result_sheet.cell(row=1, column=real_rating_col_index).value,
                    "Рейтинг (таблица)",
                )
                self.assertEqual(
                    result_sheet.cell(row=1, column=best_price_col_index).value,
                    "Лучшая цена за ед.",
                )
                self.assertEqual(
                    result_sheet.cell(row=1, column=formula_col_index).value,
                    "Рейтинг",
                )
                self.assertEqual(
                    result_sheet.cell(
                        row=1,
                        column=corrected_rating_col_index,
                    ).value,
                    "Скорректированный рейтинг",
                )
                self.assertEqual(
                    result_sheet.cell(row=2, column=best_price_col_index).value,
                    102188.5,
                )
                self.assertIsNone(
                    result_sheet.cell(row=3, column=best_price_col_index).value
                )
                self.assertEqual(
                    result_sheet.cell(row=4, column=best_price_col_index).value,
                    3000,
                )
                self.assertEqual(
                    result_sheet.cell(row=2, column=real_rating_col_index).value,
                    1.25,
                )
                self.assertIsNone(
                    result_sheet.cell(row=3, column=real_rating_col_index).value
                )
                self.assertEqual(
                    result_sheet.cell(row=4, column=real_rating_col_index).value,
                    2,
                )
                self.assertEqual(
                    result_sheet.cell(row=2, column=formula_col_index).value,
                    "=Q2/J2",
                )
                self.assertEqual(
                    result_sheet.cell(row=3, column=formula_col_index).value,
                    "=Q3/J3",
                )
                self.assertEqual(
                    result_sheet.cell(row=4, column=formula_col_index).value,
                    "=Q4/J4",
                )
                self.assertEqual(
                    result_sheet.cell(row=2, column=corrected_rating_col_index).value,
                    "=IF(R2-0.02<1.15,1.15,R2-0.02)",
                )
                self.assertEqual(
                    result_sheet.cell(row=3, column=corrected_rating_col_index).value,
                    "=IF(R3-0.02<1.15,1.15,R3-0.02)",
                )
                self.assertEqual(
                    result_sheet.cell(row=4, column=corrected_rating_col_index).value,
                    "=IF(R4-0.02<1.15,1.15,R4-0.02)",
                )
                self.assertEqual(
                    result_sheet.cell(row=2, column=realization_price_col_index).value,
                    "=ROUND(J2*S2, 2)",
                )
                self.assertEqual(
                    result_sheet.cell(row=3, column=realization_price_col_index).value,
                    "=ROUND(J3*S3, 2)",
                )
                self.assertEqual(
                    result_sheet.cell(row=4, column=realization_price_col_index).value,
                    "=ROUND(J4*S4, 2)",
                )
                self.assertEqual(
                    result_sheet.column_dimensions[get_column_letter(formula_col_index)].width,
                    18,
                )
                self.assertEqual(
                    result_sheet.column_dimensions[
                        get_column_letter(corrected_rating_col_index)
                    ].width,
                    26,
                )
                self.assertEqual(
                    result_sheet.column_dimensions[get_column_letter(best_price_col_index)].width,
                    18,
                )
                self.assertEqual(
                    result_sheet.column_dimensions[get_column_letter(real_rating_col_index)].width,
                    18,
                )
            finally:
                result_workbook.close()
        finally:
            workbook.close()
            Path(file_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
