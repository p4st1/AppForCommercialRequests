import sys
import unittest
from types import ModuleType
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
        "QFileDialog",
        "QGridLayout",
        "QHBoxLayout",
        "QHeaderView",
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
    qtwidgets.QMessageBox = getattr(qtwidgets, "QMessageBox", _QMessageBox)
    pyside6.QtWidgets = qtwidgets


_ensure_pyside_stubs()

try:
    import requests  # noqa: F401
except ModuleNotFoundError:
    requests = ModuleType("requests")

    class _StubCookies:
        def set(self, *_args, **_kwargs):
            return None

    class _StubSession:
        def __init__(self):
            self.headers = {}
            self.cookies = _StubCookies()

    requests.Session = _StubSession
    sys.modules["requests"] = requests

from ui_mixins.platform_mixin import PlatformMixin, SiteStatusWorker


class _FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class _FakeRequests:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def get(self, url, timeout=None, allow_redirects=None):
        self.calls.append(
            {
                "url": url,
                "timeout": timeout,
                "allow_redirects": allow_redirects,
            }
        )
        if self.error is not None:
            raise self.error
        return self.response


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


class PlatformMixinLoadActionTests(unittest.TestCase):
    def test_load_trades_entrypoints_load_all_trades(self):
        calls = []

        class _Window(PlatformMixin):
            def _start_trades_loading(self, **kwargs):
                calls.append(kwargs)

        window = _Window()

        window.load_trades_clicked()
        window.load_trades()

        self.assertEqual(
            calls,
            [
                {"max_items": 0, "requested_all": True},
                {"max_items": 0, "requested_all": True},
            ],
        )


class SiteStatusWorkerTests(unittest.TestCase):
    def test_site_connection_returns_available_for_success_status(self):
        fake_requests = _FakeRequests(_FakeResponse(200))

        with patch("ui_mixins.platform_mixin.requests", fake_requests):
            is_available, details = SiteStatusWorker.check_site_connection(
                url="https://example.test",
                timeout=1.5,
            )

        self.assertTrue(is_available)
        self.assertEqual(details, "HTTP 200")
        self.assertEqual(
            fake_requests.calls,
            [
                {
                    "url": "https://example.test",
                    "timeout": 1.5,
                    "allow_redirects": True,
                }
            ],
        )

    def test_site_connection_treats_client_status_as_reachable(self):
        fake_requests = _FakeRequests(_FakeResponse(403))

        with patch("ui_mixins.platform_mixin.requests", fake_requests):
            is_available, details = SiteStatusWorker.check_site_connection()

        self.assertTrue(is_available)
        self.assertEqual(details, "HTTP 403")

    def test_site_connection_marks_server_error_unavailable(self):
        fake_requests = _FakeRequests(_FakeResponse(503))

        with patch("ui_mixins.platform_mixin.requests", fake_requests):
            is_available, details = SiteStatusWorker.check_site_connection()

        self.assertFalse(is_available)
        self.assertEqual(details, "HTTP 503")

    def test_site_connection_reports_missing_requests_dependency(self):
        with patch("ui_mixins.platform_mixin.requests", None):
            is_available, details = SiteStatusWorker.check_site_connection()

        self.assertFalse(is_available)
        self.assertEqual(details, "requests не установлен")


if __name__ == "__main__":
    unittest.main()
