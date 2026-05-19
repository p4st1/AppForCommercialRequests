import sys
import unittest
from types import ModuleType


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

    class _QTimer:
        def __init__(self, *_args, **_kwargs):
            self.timeout = _Signal()

        def setSingleShot(self, *_args, **_kwargs):
            pass

        def start(self, *_args, **_kwargs):
            pass

    qt = getattr(qtcore, "Qt", type("Qt", (), {})())
    qtcore.Qt = qt
    qtcore.QSignalBlocker = getattr(qtcore, "QSignalBlocker", _QSignalBlocker)
    qtcore.QThread = getattr(qtcore, "QThread", _QThread)
    qtcore.QTimer = getattr(qtcore, "QTimer", _QTimer)
    qtcore.Signal = getattr(qtcore, "Signal", _Signal)
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

    class _Widget:
        def __init__(self, *_args, **_kwargs):
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

    for name in (
        "QAbstractItemView",
        "QCheckBox",
        "QHBoxLayout",
        "QHeaderView",
        "QLabel",
        "QLineEdit",
        "QPushButton",
        "QTableWidget",
        "QTableWidgetItem",
        "QVBoxLayout",
        "QWidget",
    ):
        setattr(qtwidgets, name, getattr(qtwidgets, name, _Widget))
    qtwidgets.QMessageBox = getattr(qtwidgets, "QMessageBox", _QMessageBox)
    pyside6.QtWidgets = qtwidgets


_ensure_pyside_stubs()

try:
    import requests  # noqa: F401
except ModuleNotFoundError:
    requests = ModuleType("requests")
    requests.Session = object
    sys.modules["requests"] = requests

from ui_mixins.platform_mixin import PlatformMixin


class PlatformMixinSearchTests(unittest.TestCase):
    def test_short_search_text_requires_minimum_length(self):
        self.assertTrue(PlatformMixin._is_search_text_too_short("1"))
        self.assertTrue(PlatformMixin._is_search_text_too_short("12"))
        self.assertFalse(PlatformMixin._is_search_text_too_short(""))
        self.assertFalse(PlatformMixin._is_search_text_too_short("125"))

    def test_filter_trades_matches_registered_number_case_insensitive(self):
        trades = [
            {
                "id": 1,
                "title": "Запасные части",
                "registeredNumber": "125570-ТТ",
                "bidSubmissionEndDate": "2026-05-20T10:00:00",
            },
            {
                "id": 2,
                "title": "Другая заявка",
                "registeredNumber": "999999-ТТ",
                "bidSubmissionEndDate": "2026-05-20T10:00:00",
            },
        ]

        filtered = PlatformMixin._filter_trades(
            trades,
            active_only=False,
            search_text="125570-тт",
        )

        self.assertEqual([trade["id"] for trade in filtered], [1])

    def test_filter_trades_can_apply_active_only_before_search(self):
        trades = [
            {"id": 1, "title": "Насос", "registeredNumber": "125", "bidSubmissionEndDate": None},
            {
                "id": 2,
                "title": "Насос",
                "registeredNumber": "126",
                "bidSubmissionEndDate": "2026-05-20",
            },
        ]

        filtered = PlatformMixin._filter_trades(
            trades,
            active_only=True,
            search_text="насос",
        )

        self.assertEqual([trade["id"] for trade in filtered], [2])


if __name__ == "__main__":
    unittest.main()
