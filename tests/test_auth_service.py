import tempfile
import unittest
from pathlib import Path

from config import Config
from services.auth_service import AuthService, save_config
from tools import DatabaseTools as Tool


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        self._old_cfg_path = Config.cfg_path
        self._old_config = Config.config.copy()

    def tearDown(self):
        Config.cfg_path = self._old_cfg_path
        Config.config.clear()
        Config.config.update(self._old_config)

    def test_save_config_updates_root_and_config_cookies(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            Tool.save_json_atomic(
                config_path,
                {
                    "config": {"pathToSaveCP": "/tmp"},
                    "settings": {"autoFill": True},
                },
            )
            Config.cfg_path = str(config_path)
            Config.config = {}

            save_config(
                {
                    "cookies": {
                        "JSESSIONID": "session-value",
                        "__Host-refreshToken": "refresh-value",
                    }
                }
            )

            saved = Tool.load_json(config_path)
            self.assertEqual(
                saved["cookies"],
                {
                    "JSESSIONID": "session-value",
                    "__Host-refreshToken": "refresh-value",
                },
            )
            self.assertEqual(
                saved["config"]["cookies"],
                {
                    "JSESSIONID": "session-value",
                    "__Host-refreshToken": "refresh-value",
                },
            )
            self.assertEqual(saved["settings"]["autoFill"], True)
            self.assertEqual(
                Config.config["cookies"],
                {
                    "JSESSIONID": "session-value",
                    "__Host-refreshToken": "refresh-value",
                },
            )

    def test_extract_session_cookies_prefers_required_keys(self):
        extracted = AuthService._extract_session_cookies(
            [
                {"name": "JSESSIONID", "value": "session"},
                {"name": "__Host-refreshToken", "value": "refresh"},
                {"name": "XSRF-TOKEN", "value": "xsrf"},
            ]
        )

        self.assertEqual(
            extracted,
            {
                "JSESSIONID": "session",
                "__Host-refreshToken": "refresh",
            },
        )

    def test_extract_session_cookies_returns_all_if_required_missing(self):
        extracted = AuthService._extract_session_cookies(
            [
                {"name": "XSRF-TOKEN", "value": "xsrf"},
                {"name": "LOCALE", "value": "ru"},
            ]
        )

        self.assertEqual(extracted, {"XSRF-TOKEN": "xsrf", "LOCALE": "ru"})


if __name__ == "__main__":
    unittest.main()
