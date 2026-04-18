import unittest
import sys
from types import ModuleType
from unittest.mock import patch

requests = sys.modules.get("requests")
if requests is None:
    requests = ModuleType("requests")

    class _Cookies:
        def set(self, *_args, **_kwargs):
            return None

    class _Session:
        def __init__(self):
            self.headers = {}
            self.cookies = _Cookies()

    requests.Session = _Session
    sys.modules["requests"] = requests

from services.platform_client import MetalITClient


class PlatformClientAuthTests(unittest.TestCase):
    def test_is_authenticated_returns_true_when_request_succeeds(self):
        client = MetalITClient({"JSESSIONID": "session-cookie"})

        with patch.object(client, "get_trades_page", return_value=[{"id": 1}]) as mocked:
            self.assertTrue(client.is_authenticated())

        mocked.assert_called_once_with(limit=1, skip=0)

    def test_is_authenticated_returns_false_for_401_errors(self):
        client = MetalITClient({"JSESSIONID": "session-cookie"})

        with patch.object(client, "get_trades_page", side_effect=Exception("401 Unauthorized")) as mocked:
            self.assertFalse(client.is_authenticated())

        mocked.assert_called_once_with(limit=1, skip=0)

    def test_is_authenticated_returns_false_for_any_other_error(self):
        client = MetalITClient({"JSESSIONID": "session-cookie"})

        with patch.object(client, "get_trades_page", side_effect=RuntimeError("network timeout")) as mocked:
            self.assertFalse(client.is_authenticated())

        mocked.assert_called_once_with(limit=1, skip=0)


if __name__ == "__main__":
    unittest.main()
