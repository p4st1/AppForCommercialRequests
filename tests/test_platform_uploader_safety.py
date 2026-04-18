import unittest
import sys
from types import ModuleType
from unittest.mock import patch

playwright = sys.modules.get("playwright")
if playwright is None:
    playwright = ModuleType("playwright")
    sys.modules["playwright"] = playwright

sync_api = sys.modules.get("playwright.sync_api")
if sync_api is None:
    sync_api = ModuleType("playwright.sync_api")
    sync_api.Locator = object
    sync_api.Page = object
    sync_api.TimeoutError = TimeoutError

    def _missing_sync_playwright():
        raise RuntimeError("playwright is not available in test environment")

    sync_api.sync_playwright = _missing_sync_playwright
    sys.modules["playwright.sync_api"] = sync_api

from services.platform_uploader import TradeUploader


class _FakeLocator:
    def __init__(self, count: int) -> None:
        self._count = count
        self.clicked = False
        self.click_timeout = None

    def count(self) -> int:
        return self._count

    @property
    def first(self):
        return self

    def click(self, *, timeout=None) -> None:
        self.clicked = True
        self.click_timeout = timeout


class _FakePage:
    def __init__(self, submit_count: int) -> None:
        self.submit_locator = _FakeLocator(submit_count)

    def locator(self, selector: str) -> _FakeLocator:
        if selector == "button:has-text('Подать предложение')":
            return self.submit_locator
        raise AssertionError(f"Неожиданный селектор: {selector}")


class TradeUploaderSafetyTests(unittest.TestCase):
    def test_submit_trade_is_blocked_when_allow_submit_is_false(self):
        uploader = TradeUploader({"JSESSIONID": "session-cookie"})

        with self.assertRaisesRegex(PermissionError, "allow_submit=False"):
            uploader.submit_trade(trade_id=123, file_path="proposal.xlsx")

    def test_submit_click_is_blocked_when_multiple_submit_buttons_found(self):
        uploader = TradeUploader({"JSESSIONID": "session-cookie"}, allow_submit=True)
        page = _FakePage(submit_count=2)

        with self.assertRaisesRegex(RuntimeError, "несколько кнопок"):
            uploader._click_submit_button(page)

        self.assertFalse(page.submit_locator.clicked)

    def test_submit_click_logs_button_text_before_click(self):
        uploader = TradeUploader({"JSESSIONID": "session-cookie"}, allow_submit=True)
        page = _FakePage(submit_count=1)

        with patch("builtins.print") as mocked_print:
            uploader._click_submit_button(page)

        mocked_print.assert_called_once_with("CLICK:", "Подать предложение")
        self.assertTrue(page.submit_locator.clicked)
        self.assertEqual(page.submit_locator.click_timeout, 4_000)


if __name__ == "__main__":
    unittest.main()
