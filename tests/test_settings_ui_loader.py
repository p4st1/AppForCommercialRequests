import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PySide6 import QtWidgets

if not hasattr(QtWidgets, "QMainWindow"):
    raise unittest.SkipTest("PySide6.QtWidgets is stubbed without QMainWindow")

from settings import mainWindow


class _FakeDesignerUi:
    setup_calls = []

    def setupUi(self, window):
        self.setup_calls.append(window)


class _FakeGeneratedUi:
    setup_calls = []

    def setupUi(self, window):
        self.setup_calls.append(window)


class SettingsUiLoaderTests(unittest.TestCase):
    def test_load_designer_ui_prefers_ui_file(self):
        def fake_load_ui_type(path):
            self.assertEqual(path, "/tmp/settingsAppGui.ui")
            return _FakeDesignerUi, object

        dummy_window = SimpleNamespace(
            _get_settings_ui_path=lambda: Path("/tmp/settingsAppGui.ui")
        )
        _FakeDesignerUi.setup_calls.clear()
        with patch("settings.loadUiType", fake_load_ui_type):
            ui = mainWindow._load_designer_ui(dummy_window)

        self.assertIsInstance(ui, _FakeDesignerUi)
        self.assertEqual(_FakeDesignerUi.setup_calls, [dummy_window])

    def test_load_designer_ui_falls_back_to_generated_ui(self):
        dummy_window = SimpleNamespace(_get_settings_ui_path=lambda: None)
        _FakeGeneratedUi.setup_calls.clear()
        with patch("settings.loadUiType", None), patch(
            "settings.GeneratedSettingsUi",
            _FakeGeneratedUi,
        ):
            ui = mainWindow._load_designer_ui(dummy_window)

        self.assertIsInstance(ui, _FakeGeneratedUi)
        self.assertEqual(_FakeGeneratedUi.setup_calls, [dummy_window])


if __name__ == "__main__":
    unittest.main()
