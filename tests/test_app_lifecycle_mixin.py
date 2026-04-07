import unittest
from unittest.mock import patch

from config import Config
from app.ui.app_lifecycle_mixin import AppLifecycleMixin


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
    def __init__(self):
        self.logisticNum = _FakeLineEdit("2.5")
        self.customLine = _FakeLineEdit("1.4")
        self.termDeliveryLine = _FakeLineEdit("15")
        self.markupLine = _FakeLineEdit("1.8")
        self.requestNumberLine = _FakeLineEdit("  REQ-42  ")
        self.logisticVar = _FakeComboBox(1)


class _FakeDb:
    def __init__(self):
        self.close_calls = 0

    def close(self):
        self.close_calls += 1


class _BaseCloseRecorder:
    def __init__(self):
        self.base_close_events = []

    def closeEvent(self, event):
        self.base_close_events.append(event)


class _FakeWindow(AppLifecycleMixin, _BaseCloseRecorder):
    def __init__(self):
        super().__init__()
        self.ui = _FakeUi()
        self.db = _FakeDb()
        self.ensure_output_dirs_calls = 0
        self.save_config_calls = 0
        self.close_calls = 0

    def ensureOutputDirs(self):
        self.ensure_output_dirs_calls += 1

    def saveConfig(self):
        self.save_config_calls += 1

    def close(self):
        self.close_calls += 1


class AppLifecycleMixinTests(unittest.TestCase):
    def setUp(self):
        self._old_config = Config.config.copy()

    def tearDown(self):
        Config.config.clear()
        Config.config.update(self._old_config)

    @patch("app.ui.app_lifecycle_mixin.Tool.resourcePath")
    def test_resource_path_delegates_to_tool(self, resource_path):
        resource_path.return_value = "/tmp/app.ico"
        window = _FakeWindow()

        result = window.resourcePath("assets/app.ico")

        resource_path.assert_called_once_with("assets/app.ico")
        self.assertEqual(result, "/tmp/app.ico")

    def test_func_exit_system_calls_close(self):
        window = _FakeWindow()

        window.funcExitSystem()

        self.assertEqual(window.close_calls, 1)

    def test_close_event_updates_config_and_persists(self):
        window = _FakeWindow()
        event = object()

        window.closeEvent(event)

        self.assertEqual(Config.config["logisticNum"], "2.5")
        self.assertEqual(Config.config["customNum"], "1.4")
        self.assertEqual(Config.config["termDelivery"], "15")
        self.assertEqual(Config.config["markup"], "1.8")
        self.assertEqual(Config.config["requestNumber"], "REQ-42")
        self.assertEqual(Config.config["logisticVar"], "1")
        self.assertEqual(window.ensure_output_dirs_calls, 1)
        self.assertEqual(window.save_config_calls, 1)
        self.assertEqual(window.db.close_calls, 1)
        self.assertEqual(window.base_close_events, [event])


if __name__ == "__main__":
    unittest.main()
