import unittest
from pathlib import Path
from unittest.mock import patch

from config import Config
from app.ui.config_io_mixin import ConfigIoMixin


class _SaveWindow(ConfigIoMixin):
    pass


class _LoadWindow(ConfigIoMixin):
    def __init__(self):
        self.save_calls = 0

    def saveConfig(self):
        self.save_calls += 1


class ConfigIoMixinTests(unittest.TestCase):
    def setUp(self):
        self._old_cfg_path = Config.cfg_path
        self._old_config = Config.config.copy()
        self._old_settings = Config.settings.copy()

    def tearDown(self):
        Config.cfg_path = self._old_cfg_path
        Config.config.clear()
        Config.config.update(self._old_config)
        Config.settings.clear()
        Config.settings.update(self._old_settings)

    @patch("app.ui.config_io_mixin.Tool.save_json_atomic")
    def test_save_config_writes_combined_payload(self, save_json_atomic):
        window = _SaveWindow()
        Config.cfg_path = "/tmp/config.json"
        Config.config = {"a": 1}
        Config.settings = {"b": 2}

        window.saveConfig()

        save_json_atomic.assert_called_once_with(
            "/tmp/config.json",
            {"config": {"a": 1}, "settings": {"b": 2}},
        )

    @patch("app.ui.config_io_mixin.Tool.ensure_directory")
    @patch("app.ui.config_io_mixin.Path.home")
    def test_ensure_output_dirs_updates_config_paths(self, path_home, ensure_directory):
        window = _SaveWindow()
        Config.config = {"pathToSaveCP": "", "pathToSaveExcel": ""}
        path_home.return_value = Path("/Users/tester")
        ensure_directory.side_effect = [
            Path("/Users/tester/Documents/cp"),
            Path("/Users/tester/Documents/cp/excel"),
        ]

        window.ensureOutputDirs()

        ensure_directory.assert_any_call("", Path("/Users/tester/Documents"))
        ensure_directory.assert_any_call(
            Path("/Users/tester/Documents/cp"),
            Path("/Users/tester/Documents/cp"),
        )
        self.assertEqual(Config.config["pathToSaveCP"], "/Users/tester/Documents/cp")
        self.assertEqual(Config.config["pathToSaveExcel"], "/Users/tester/Documents/cp/excel")

    @patch("app.ui.config_io_mixin.Tool.merge_config_with_defaults")
    @patch("app.ui.config_io_mixin.Tool.load_json")
    def test_load_config_applies_merged_data_and_calls_save(self, load_json, merge_config):
        window = _LoadWindow()
        Config.cfg_path = "/tmp/config.json"
        load_json.return_value = {"raw": "data"}
        merge_config.return_value = {
            "config": {"x": "1"},
            "settings": {"autoFill": False},
        }

        window.loadConfig()

        load_json.assert_called_once_with("/tmp/config.json")
        merge_config.assert_called_once_with({"raw": "data"})
        self.assertEqual(Config.config, {"x": "1"})
        self.assertEqual(Config.settings, {"autoFill": False})
        self.assertEqual(window.save_calls, 1)

    @patch("app.ui.config_io_mixin.Tool.merge_config_with_defaults")
    @patch("app.ui.config_io_mixin.Tool.log_exception")
    @patch("app.ui.config_io_mixin.Tool.load_json", side_effect=RuntimeError("boom"))
    def test_load_config_logs_and_uses_empty_data_when_load_fails(
        self,
        _load_json,
        log_exception,
        merge_config,
    ):
        window = _LoadWindow()
        Config.cfg_path = "/tmp/config.json"
        merge_config.return_value = {
            "config": {"x": "1"},
            "settings": {"autoFill": True},
        }

        window.loadConfig()

        merge_config.assert_called_once_with({})
        self.assertEqual(window.save_calls, 1)
        log_exception.assert_called_once()
        self.assertEqual(log_exception.call_args.kwargs, {"include_traceback": False})


if __name__ == "__main__":
    unittest.main()
