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


class _CaptureCookies:
    def __init__(self):
        self.calls = []

    def set(self, *args, **kwargs):
        self.calls.append((args, kwargs))

    @staticmethod
    def get_dict():
        return {}


class _CaptureSession:
    def __init__(self):
        self.headers = {}
        self.cookies = _CaptureCookies()


class _FakeResponse:
    def __init__(self, *, status_code: int, payload: dict, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"{self.status_code} HTTP error")

    def json(self):
        return self._payload


class _PostCaptureSession(_CaptureSession):
    def __init__(self, responses):
        super().__init__()
        self._responses = list(responses)
        self.post_calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.post_calls.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if not self._responses:
            raise AssertionError("Неожиданный вызов post без подготовленного ответа")
        return self._responses.pop(0)


class PlatformClientAuthTests(unittest.TestCase):
    def test_build_variables_uses_bid_submission_sitemap(self):
        variables = MetalITClient._build_variables(limit=20, skip=0)
        self.assertEqual(variables["tradeQueryDto"]["sitemapPage"], "purchases.trades.filters.BID_SUBMISSION")

    def test_client_sets_required_headers_and_cookie_aliases(self):
        session = _CaptureSession()
        MetalITClient(
            {
                "JSESSIONID": "session-cookie",
                "XSRF-TOKEN": "xsrf-token",
            },
            session=session,
        )

        self.assertIn("User-Agent", session.headers)
        self.assertEqual(session.headers["Content-Type"], "application/json")
        self.assertEqual(session.headers["Accept"], "application/json")
        self.assertEqual(session.headers["Referer"], "https://etp.metal-it.ru/")
        self.assertEqual(session.headers["Origin"], "https://etp.metal-it.ru")
        self.assertEqual(session.headers["X-XSRF-TOKEN"], "xsrf-token")

        cookie_names = [call[0][0] for call in session.cookies.calls if call and call[0]]
        self.assertIn("JSESSIONID", cookie_names)
        self.assertIn("__Host-JSESSIONID", cookie_names)

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

    def test_is_authenticated_returns_false_for_403_errors(self):
        client = MetalITClient({"JSESSIONID": "session-cookie"})

        with patch.object(client, "get_trades_page", side_effect=Exception("403 Forbidden")) as mocked:
            self.assertFalse(client.is_authenticated())

        mocked.assert_called_once_with(limit=1, skip=0)

    def test_is_authenticated_returns_false_for_any_other_error(self):
        client = MetalITClient({"JSESSIONID": "session-cookie"})

        with patch.object(client, "get_trades_page", side_effect=RuntimeError("network timeout")) as mocked:
            self.assertFalse(client.is_authenticated())

        mocked.assert_called_once_with(limit=1, skip=0)

    def test_load_retrades_uses_retrading_payload_and_pagination(self):
        session = _PostCaptureSession(
            responses=[
                _FakeResponse(
                    status_code=200,
                    payload={
                        "data": {
                            "trades": {
                                "items": [
                                    {
                                        "id": 101,
                                        "registeredNumber": "RET-101",
                                        "title": "Переторжка 101",
                                        "processStatus": "RETRADING_ACTIVE",
                                        "bidSubmissionEndDate": "2026-04-20T10:00:00Z",
                                    }
                                ],
                                "total": 51,
                            }
                        }
                    },
                ),
                _FakeResponse(
                    status_code=200,
                    payload={
                        "data": {
                            "trades": {
                                "items": [
                                    {
                                        "id": 102,
                                        "registeredNumber": "RET-102",
                                        "title": "Переторжка 102",
                                        "processStatus": "RETRADING_FINISHED",
                                        "bidSubmissionEndDate": "2026-04-21T10:00:00Z",
                                    }
                                ],
                                "total": 51,
                            }
                        }
                    },
                ),
            ]
        )
        client = MetalITClient({"JSESSIONID": "session-cookie"}, session=session)

        retrades = client.load_retrades()

        self.assertEqual(
            retrades,
            [
                {
                    "id": 101,
                    "number": "RET-101",
                    "title": "Переторжка 101",
                    "status": "RETRADING_ACTIVE",
                    "endDate": "2026-04-20T10:00:00Z",
                },
                {
                    "id": 102,
                    "number": "RET-102",
                    "title": "Переторжка 102",
                    "status": "RETRADING_FINISHED",
                    "endDate": "2026-04-21T10:00:00Z",
                },
            ],
        )
        self.assertEqual(client.retrades, retrades)
        self.assertEqual(len(session.post_calls), 2)
        self.assertEqual(
            session.post_calls[0]["json"]["variables"]["tradeQueryDto"]["sitemapPage"],
            "purchases.trades.filters.RETRADING",
        )
        self.assertEqual(session.post_calls[0]["json"]["variables"]["limit"], 50)
        self.assertEqual(session.post_calls[0]["json"]["variables"]["skip"], 0)
        self.assertEqual(session.post_calls[1]["json"]["variables"]["skip"], 50)
        self.assertIs(session.post_calls[0]["headers"], session.headers)

    def test_load_retrades_shows_auth_error_for_403(self):
        session = _PostCaptureSession(
            responses=[
                _FakeResponse(
                    status_code=403,
                    payload={},
                    text="Forbidden",
                )
            ]
        )
        client = MetalITClient({"JSESSIONID": "session-cookie"}, session=session)

        with self.assertRaisesRegex(RuntimeError, "Ошибка авторизации — обновите cookies"):
            client.load_retrades()


if __name__ == "__main__":
    unittest.main()
