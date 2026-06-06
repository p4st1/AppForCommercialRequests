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

    def test_extract_session_cookies_returns_all_available_values(self):
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
                "XSRF-TOKEN": "xsrf",
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

    def test_wait_for_login_success_waits_for_bid_submission_text(self):
        service = AuthService()

        class _Page:
            def __init__(self):
                self.calls = []

            def wait_for_selector(self, selector, timeout=None):
                self.calls.append((selector, timeout))
                return None

        page = _Page()
        service._wait_for_login_success(page)

        self.assertEqual(
            page.calls,
            [(service.LOGIN_SUCCESS_SELECTOR, service.CAPTCHA_WAIT_TIMEOUT_MS)],
        )

    def test_wait_for_login_success_raises_clear_error_on_timeout(self):
        service = AuthService()

        class _Page:
            @staticmethod
            def wait_for_selector(_selector, timeout=None):
                raise TimeoutError(timeout)

        with self.assertRaisesRegex(
            Exception,
            "Не удалось определить успешный вход \\(возможно капча не решена\\)",
        ):
            service._wait_for_login_success(_Page())

    def test_goto_with_fallback_retries_on_domcontentloaded_timeout(self):
        service = AuthService(timeout_ms=30_000)

        class _Page:
            def __init__(self):
                self.goto_calls = []
                self.load_state_calls = []

            def goto(self, url, **kwargs):
                self.goto_calls.append((url, kwargs))
                if len(self.goto_calls) == 1:
                    raise TimeoutError("timeout")
                return None

            def wait_for_load_state(self, state, timeout=None):
                self.load_state_calls.append((state, timeout))

        page = _Page()

        service._goto_with_fallback(page, "https://example.test", description="тест")

        self.assertEqual(page.goto_calls[0][1]["wait_until"], "domcontentloaded")
        self.assertEqual(page.goto_calls[0][1]["timeout"], 60_000)
        self.assertEqual(page.goto_calls[1][1]["wait_until"], "commit")
        self.assertEqual(page.goto_calls[1][1]["timeout"], 30_000)
        self.assertEqual(page.load_state_calls, [("domcontentloaded", 10_000)])


if __name__ == "__main__":
    unittest.main()
