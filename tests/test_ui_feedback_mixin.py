import sys
import unittest
from types import ModuleType
from unittest.mock import patch


pyside6 = sys.modules.get("PySide6")
if pyside6 is None:
    pyside6 = ModuleType("PySide6")
    sys.modules["PySide6"] = pyside6

qtcore = sys.modules.get("PySide6.QtCore")
if qtcore is None:
    qtcore = ModuleType("PySide6.QtCore")
    sys.modules["PySide6.QtCore"] = qtcore
if not hasattr(qtcore, "QUrl"):
    class _QUrl:
        def __init__(self, value):
            self.value = value

    qtcore.QUrl = _QUrl
pyside6.QtCore = qtcore

qtgui = sys.modules.get("PySide6.QtGui")
if qtgui is None:
    qtgui = ModuleType("PySide6.QtGui")
    sys.modules["PySide6.QtGui"] = qtgui
if not hasattr(qtgui, "QDesktopServices"):
    class _QDesktopServices:
        @staticmethod
        def openUrl(_url):
            return True

    qtgui.QDesktopServices = _QDesktopServices
pyside6.QtGui = qtgui

qtwidgets = sys.modules.get("PySide6.QtWidgets")
if qtwidgets is None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    sys.modules["PySide6.QtWidgets"] = qtwidgets
if not hasattr(qtwidgets, "QMessageBox"):
    class _QMessageBox:
        def __init__(self, _parent=None):
            pass

        def setWindowTitle(self, _title):
            pass

        def setText(self, _text):
            pass

        def exec(self):
            return 0

    qtwidgets.QMessageBox = _QMessageBox
pyside6.QtWidgets = qtwidgets

from app.ui.ui_feedback_mixin import UiFeedbackMixin


class _FakeWindow(UiFeedbackMixin):
    pass


class _FakeMessageBox:
    instances = []

    def __init__(self, parent=None):
        self.parent = parent
        self.title = ""
        self.text = ""
        self.exec_calls = 0
        self.__class__.instances.append(self)

    def setWindowTitle(self, title):
        self.title = title

    def setText(self, text):
        self.text = text

    def exec(self):
        self.exec_calls += 1
        return 0


class UiFeedbackMixinTests(unittest.TestCase):
    def setUp(self):
        _FakeMessageBox.instances.clear()

    @patch("app.ui.ui_feedback_mixin.QDesktopServices.openUrl")
    @patch("app.ui.ui_feedback_mixin.QUrl", side_effect=lambda value: f"url:{value}")
    def test_open_url_calls_desktop_services(self, q_url, open_url):
        window = _FakeWindow()

        window.open_url("https://example.com")

        q_url.assert_called_once_with("https://example.com")
        open_url.assert_called_once_with("url:https://example.com")

    @patch("app.ui.ui_feedback_mixin.Tool.log_exception")
    @patch("app.ui.ui_feedback_mixin.QDesktopServices.openUrl", side_effect=RuntimeError("boom"))
    @patch("app.ui.ui_feedback_mixin.QUrl", side_effect=lambda value: value)
    def test_open_url_logs_exception(self, _q_url, _open_url, log_exception):
        window = _FakeWindow()

        window.open_url("https://bad.example")

        log_exception.assert_called_once()
        args = log_exception.call_args.args
        kwargs = log_exception.call_args.kwargs
        self.assertEqual(args[0], "Не удалось открыть URL: https://bad.example")
        self.assertIsInstance(args[1], RuntimeError)
        self.assertEqual(kwargs, {"include_traceback": False})

    @patch("app.ui.ui_feedback_mixin.QMessageBox", _FakeMessageBox)
    def test_error_shows_message_box(self):
        window = _FakeWindow()

        window.error("Ошибка", "Что-то пошло не так")

        self.assertEqual(len(_FakeMessageBox.instances), 1)
        message_box = _FakeMessageBox.instances[0]
        self.assertIs(message_box.parent, window)
        self.assertEqual(message_box.title, "Ошибка")
        self.assertEqual(message_box.text, "Что-то пошло не так")
        self.assertEqual(message_box.exec_calls, 1)


if __name__ == "__main__":
    unittest.main()
