import unittest
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


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

    class _QSettings:
        def __init__(self, *_args, **_kwargs):
            pass

        def value(self, _key, default=None):
            return default

        def setValue(self, *_args, **_kwargs):
            pass

    class _QTimer:
        def __init__(self, *_args, **_kwargs):
            self.timeout = _Signal()

        def setSingleShot(self, *_args, **_kwargs):
            pass

        def isActive(self):
            return False

    qtcore.QSettings = getattr(qtcore, "QSettings", _QSettings)
    qtcore.QThread = getattr(qtcore, "QThread", _QThread)
    qtcore.Signal = getattr(qtcore, "Signal", _Signal)
    qtcore.QTimer = getattr(qtcore, "QTimer", _QTimer)
    qtcore.Qt = getattr(qtcore, "Qt", type("Qt", (), {})())
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

    qtgui.QAction = getattr(qtgui, "QAction", _QAction)
    qtgui.QColor = getattr(qtgui, "QColor", _QColor)
    pyside6.QtGui = qtgui

    qtuitools = sys.modules.get("PySide6.QtUiTools")
    if qtuitools is None:
        qtuitools = ModuleType("PySide6.QtUiTools")
        sys.modules["PySide6.QtUiTools"] = qtuitools

    class _QUiLoader:
        pass

    qtuitools.QUiLoader = getattr(qtuitools, "QUiLoader", _QUiLoader)
    pyside6.QtUiTools = qtuitools

    qtwidgets = sys.modules.get("PySide6.QtWidgets")
    if qtwidgets is None:
        qtwidgets = ModuleType("PySide6.QtWidgets")
        sys.modules["PySide6.QtWidgets"] = qtwidgets

    class _Widget:
        pass

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

    class _QFileDialog:
        @staticmethod
        def getOpenFileName(*_args, **_kwargs):
            return ("", "")

    class _QInputDialog:
        @staticmethod
        def getText(*_args, **_kwargs):
            return ("", False)

    for name, value in {
        "QAbstractItemView": _Widget,
        "QCheckBox": _Widget,
        "QDoubleSpinBox": _Widget,
        "QFileDialog": _QFileDialog,
        "QHeaderView": _Widget,
        "QHBoxLayout": _Widget,
        "QInputDialog": _QInputDialog,
        "QLabel": _Widget,
        "QListWidget": _Widget,
        "QListWidgetItem": _Widget,
        "QMessageBox": _QMessageBox,
        "QPushButton": _Widget,
        "QSpinBox": _Widget,
        "QTableWidget": _Widget,
        "QTableWidgetItem": _Widget,
        "QTabWidget": _Widget,
        "QWidget": _Widget,
    }.items():
        setattr(qtwidgets, name, getattr(qtwidgets, name, value))
    pyside6.QtWidgets = qtwidgets


_ensure_pyside_stubs()

try:
    import requests  # noqa: F401
except ModuleNotFoundError:
    sys.modules["requests"] = ModuleType("requests")

from ui_mixins.export_mixin import ExportMixin


class _FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)


class _FakeButton:
    def __init__(self, text="", _parent=None):
        self._text = text
        self.object_name = ""
        self.properties = {}
        self.stylesheet = ""
        self.clicked = _FakeSignal()

    def setObjectName(self, name):
        self.object_name = name

    def setProperty(self, name, value):
        self.properties[name] = value

    def setStyleSheet(self, stylesheet):
        self.stylesheet = stylesheet

    def style(self):
        return None

    def update(self):
        pass

    def text(self):
        return self._text

    def setText(self, text):
        self._text = text

    def setEnabled(self, _enabled):
        pass


class _FakeHBoxLayout:
    def __init__(self):
        self.widgets = []

    def indexOf(self, widget):
        try:
            return self.widgets.index(widget)
        except ValueError:
            return -1

    def count(self):
        return len(self.widgets)

    def insertWidget(self, index, widget):
        self.widgets.insert(index, widget)


class _FakeExportWorker:
    created = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.finished = _FakeSignal()
        self.error = _FakeSignal()
        self.started = False
        _FakeExportWorker.created.append(self)

    def start(self):
        self.started = True

    def isRunning(self):
        return False


class _FakeOffersTable:
    def __init__(self, row):
        self._row = row

    def currentRow(self):
        return self._row


class _FakeExportWindow(ExportMixin):
    def __init__(self):
        self._export_trade_worker = None
        self._pending_retrade_bid_id = None
        self._pending_retrade_context = {}
        self.current_retrade = ""
        self.current_retrade_context = {}
        self.current_retrade_excel_path = ""
        self.current_retrade_bid_id = None
        self.current_retrade_trade_id = None
        self.current_retrade_lot_id = None
        self._active_export_workflow = ""
        self._generate_retrade_after_export = False
        self.calculations_file_path = "/tmp/calc.xlsx"
        self.loading_states = []

    def _build_export_download_path(self, identifier):
        return f"/tmp/trade_{identifier}.xlsx"

    def _set_export_loading_state(self, *, is_loading):
        self.loading_states.append(is_loading)


class RetradeContextTests(unittest.TestCase):
    def setUp(self):
        _FakeExportWorker.created.clear()

    def test_build_current_retrade_context_uses_selected_offer_number(self):
        window = _FakeExportWindow()

        context = window._build_current_retrade_context(
            retrade={
                "id": 999,
                "number": "RT-1",
                "title": "Переторжка 1",
                "status": "Активна",
            },
            offer={
                "bid_id": 7001,
                "number": "740370",
                "bidder_title": "ООО Альфа",
                "price": "100",
            },
            trade_id=999,
            lot_id=55,
            bid_id=7001,
        )
        window._set_current_retrade_context(context)

        self.assertEqual(window.current_retrade, "740370")
        self.assertEqual(window.current_retrade_bid_id, 7001)
        self.assertEqual(window.current_retrade_trade_id, 999)
        self.assertEqual(window.current_retrade_lot_id, 55)
        self.assertEqual(window.current_retrade_context["retrade_number"], "RT-1")

    def test_import_bid_prefers_current_retrade_context_over_selection(self):
        window = _FakeExportWindow()
        window.table_retrade_offers = _FakeOffersTable(0)
        window.retrade_offers = [{"bid_id": 7002, "number": "OTHER"}]
        window._set_current_retrade_context(
            {
                "number": "740370",
                "bid_id": 7001,
                "trade_id": 999,
                "lot_id": 55,
            }
        )

        self.assertEqual(window._get_retrade_bid_id_for_import(), 7001)

    def test_start_retrade_export_sets_current_and_pending_context(self):
        window = _FakeExportWindow()
        window.current_retrade_excel_path = "/tmp/old_retrade.xlsx"
        context = {
            "number": "740370",
            "bid_id": 7001,
            "trade_id": 999,
            "lot_id": 55,
        }

        with patch("ui_mixins.export_mixin.ExportTradeWorker", _FakeExportWorker):
            window._start_export_worker(
                trade_id=999,
                lot_id=55,
                bid_id=7001,
                is_retrade=True,
                retrade_context=context,
            )

        self.assertEqual(window.current_retrade, "740370")
        self.assertEqual(window.current_retrade_excel_path, "")
        self.assertEqual(window.current_retrade_bid_id, 7001)
        self.assertEqual(window._pending_retrade_bid_id, 7001)
        self.assertEqual(window._pending_retrade_context, context)
        self.assertEqual(window._active_export_workflow, "retrade")
        self.assertEqual(len(_FakeExportWorker.created), 1)
        self.assertTrue(_FakeExportWorker.created[0].started)
        self.assertEqual(_FakeExportWorker.created[0].kwargs["bid_id"], 7001)

    def test_attached_retrade_context_can_drive_reexport(self):
        window = _FakeExportWindow()
        context = {
            "number": "740370",
            "bid_id": 7001,
            "trade_id": 999,
            "lot_id": 55,
        }
        window._set_current_retrade_context(context)

        attached_context = window._get_attached_retrade_export_context()

        self.assertEqual(attached_context["bid_id"], 7001)
        self.assertEqual(attached_context["trade_id"], 999)
        self.assertEqual(attached_context["lot_id"], 55)

    def test_export_selected_retrade_prefers_attached_context(self):
        window = _FakeExportWindow()
        window._set_current_retrade_context(
            {
                "number": "740370",
                "bid_id": 7001,
                "trade_id": 999,
                "lot_id": 55,
            }
        )

        with patch("ui_mixins.export_mixin.ExportTradeWorker", _FakeExportWorker):
            window.export_selected_retrade()

        self.assertEqual(len(_FakeExportWorker.created), 1)
        self.assertEqual(_FakeExportWorker.created[0].kwargs["trade_id"], 999)
        self.assertEqual(_FakeExportWorker.created[0].kwargs["lot_id"], 55)
        self.assertEqual(_FakeExportWorker.created[0].kwargs["bid_id"], 7001)

    def test_generate_button_reexports_attached_retrade_first(self):
        window = _FakeExportWindow()
        window._set_current_retrade_context(
            {
                "number": "740370",
                "bid_id": 7001,
                "trade_id": 999,
                "lot_id": 55,
            }
        )

        with patch("ui_mixins.export_mixin.ExportTradeWorker", _FakeExportWorker):
            window._on_generate_retrade_calculation_clicked()

        self.assertTrue(window._generate_retrade_after_export)
        self.assertEqual(len(_FakeExportWorker.created), 1)
        self.assertEqual(_FakeExportWorker.created[0].kwargs["trade_id"], 999)
        self.assertEqual(_FakeExportWorker.created[0].kwargs["lot_id"], 55)
        self.assertEqual(_FakeExportWorker.created[0].kwargs["bid_id"], 7001)

    def test_mark_current_retrade_table_exported_now_stores_timestamp(self):
        window = _FakeExportWindow()
        window._set_current_retrade_context(
            {
                "number": "740370",
                "bid_id": 7001,
                "trade_id": 999,
                "lot_id": 55,
            }
        )

        window._mark_current_retrade_table_exported_now()

        self.assertTrue(window.current_retrade_last_export_at)
        self.assertEqual(
            window.current_retrade_context["last_export_at"],
            window.current_retrade_last_export_at,
        )

    def test_retrade_main_controls_only_add_update_proposal_button(self):
        class _Window(ExportMixin):
            def __init__(self):
                self.retrade_controls_layout = _FakeHBoxLayout()
                self.label_auto_trade_status = object()
                self.retrade_controls_layout.widgets.append(self.label_auto_trade_status)
                self.retrade_tab = object()
                self.ui = SimpleNamespace()

            def on_import_clicked(self):
                pass

        window = _Window()

        with (
            patch("ui_mixins.export_mixin.QHBoxLayout", _FakeHBoxLayout),
            patch("ui_mixins.export_mixin.QPushButton", _FakeButton),
        ):
            window._ensure_retrade_main_table_controls()

        self.assertFalse(hasattr(window, "save_button"))
        self.assertEqual(window.import_button.text(), "Обновить предложение")
        self.assertEqual(window.import_button.object_name, "import_button")
        self.assertEqual(window.import_button.properties.get("variant"), "primary")
        self.assertEqual(window.import_button.stylesheet, "")
        self.assertEqual(
            window.retrade_controls_layout.widgets,
            [window.import_button, window.label_auto_trade_status],
        )


if __name__ == "__main__":
    unittest.main()
