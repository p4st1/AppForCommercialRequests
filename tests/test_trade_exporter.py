import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pandas as pd

try:
    import requests  # noqa: F401
except ModuleNotFoundError:
    sys.modules["requests"] = ModuleType("requests")

from services.trade_exporter import TradeExporter


class _FakeResponse:
    def __init__(self, *, status_code: int = 200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class _FakeCookies:
    def set(self, *_args, **_kwargs):
        return None


class _FakeSession:
    def __init__(self, *, get_responses=None, post_responses=None):
        self.get_responses = list(get_responses or [])
        self.post_responses = list(post_responses or [])
        self.get_calls = []
        self.post_calls = []
        self.headers = {}
        self.cookies = _FakeCookies()
        self.closed = False

    def get(self, url, timeout=None):
        self.get_calls.append({"url": url, "timeout": timeout})
        if not self.get_responses:
            raise AssertionError("Неожиданный GET без подготовленного ответа")
        return self.get_responses.pop(0)

    def post(self, url, json=None, timeout=None):
        self.post_calls.append({"url": url, "json": json, "timeout": timeout})
        if not self.post_responses:
            raise AssertionError("Неожиданный POST без подготовленного ответа")
        return self.post_responses.pop(0)

    def close(self):
        self.closed = True


class _FakePage:
    def __init__(self, url):
        self.url = url


class TradeExporterTests(unittest.TestCase):
    def setUp(self):
        self.exporter = TradeExporter()

    def test_extract_bid_rows_from_submission_stages(self):
        trade_payload = {
            "submissionStages": [
                {
                    "tradeResult": {
                        "lotResults": [
                            {
                                "bidPlaces": [
                                    {
                                        "bid": {
                                            "id": 7001,
                                            "number": "BID-001",
                                            "price": 12345.67,
                                            "currency": {"code": "RUB"},
                                            "status": {"title": "Подана"},
                                            "bidDate": 1711111111111,
                                            "bidder": {
                                                "title": "ООО Ромашка",
                                                "inn": "7701000000",
                                            },
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }

        bids, has_bid_places = self.exporter._extract_bid_rows(trade_payload, emit_logs=False)

        self.assertTrue(has_bid_places)
        self.assertEqual(
            bids,
            [
                {
                    "Номер": "BID-001",
                    "Компания": "ООО Ромашка",
                    "ИНН": "7701000000",
                    "Цена": 12345.67,
                    "Валюта": "RUB",
                    "Статус": "Подана",
                    "Дата": 1711111111111,
                    "ID": 7001,
                }
            ],
        )

    def test_export_trade_data_writes_excel_directly_from_json(self):
        fake_session = _FakeSession(
            get_responses=[
                _FakeResponse(
                    payload={
                        "id": 101,
                        "submissionStages": [
                            {
                                "tradeResult": {
                                    "lotResults": [
                                        {
                                            "bidPlaces": [
                                                {
                                                    "bid": {
                                                        "id": 9001,
                                                        "number": "BID-9001",
                                                        "price": 5000,
                                                        "currency": {"code": "RUB"},
                                                        "status": {"title": "Подана"},
                                                        "bidDate": 1711111111000,
                                                        "bidder": {
                                                            "title": "ООО Тест",
                                                            "inn": "7702000000",
                                                        },
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        ],
                    }
                )
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = os.path.join(tmpdir, "trade.xlsx")
            with (
                patch.object(self.exporter, "_load_cookies_for_export", return_value={"JSESSIONID": "s"}),
                patch.object(self.exporter, "_build_api_session", return_value=fake_session),
            ):
                saved_path = self.exporter.export_trade_data(101, target_path)

            self.assertEqual(saved_path, str(Path(target_path).resolve()))
            self.assertTrue(fake_session.closed)
            self.assertEqual(len(fake_session.get_calls), 1)

            frame = pd.read_excel(target_path)
            self.assertEqual(list(frame.columns), list(TradeExporter.EXPORT_COLUMNS))
            self.assertEqual(int(frame.at[0, "ID"]), 9001)
            self.assertEqual(frame.at[0, "Компания"], "ООО Тест")

    def test_export_lot_data_resolves_trade_id_and_creates_excel(self):
        fake_session = _FakeSession(
            post_responses=[
                _FakeResponse(
                    payload={
                        "data": {
                            "trades": {
                                "items": [
                                    {
                                        "id": 777,
                                        "lots": [{"id": 55}],
                                    }
                                ],
                                "total": 1,
                            }
                        }
                    }
                )
            ],
            get_responses=[
                _FakeResponse(
                    payload={
                        "id": 777,
                        "submissionStages": [
                            {
                                "tradeResult": {
                                    "lotResults": [
                                        {
                                            "bidPlaces": [
                                                {
                                                    "bid": {
                                                        "id": 8001,
                                                        "number": "BID-8001",
                                                        "price": 1200,
                                                        "currency": {"code": "USD"},
                                                        "status": {"title": "На рассмотрении"},
                                                        "bidDate": 1711111112000,
                                                        "bidder": {
                                                            "title": "АО Лотос",
                                                            "inn": "7803000000",
                                                        },
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        ],
                    }
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = os.path.join(tmpdir, "lot.xlsx")
            with (
                patch.object(self.exporter, "_load_cookies_for_export", return_value={"JSESSIONID": "s"}),
                patch.object(self.exporter, "_build_api_session", return_value=fake_session),
            ):
                self.exporter.export_lot_data(55, target_path)

            self.assertEqual(len(fake_session.post_calls), 1)
            variables = fake_session.post_calls[0]["json"]["variables"]
            self.assertEqual(
                variables["tradeQueryDto"]["sitemapPage"],
                TradeExporter.DEFAULT_SITEMAP_PAGE,
            )

            frame = pd.read_excel(target_path)
            self.assertEqual(int(frame.at[0, "ID"]), 8001)
            self.assertEqual(frame.at[0, "Валюта"], "USD")

    def test_submission_export_url_uses_bids_new_lot_page(self):
        self.assertEqual(
            TradeExporter._build_submission_export_url(556675785),
            "https://etp.metal-it.ru/bids/new?lot=556675785",
        )

    def test_validate_submission_export_page_rejects_wrong_route(self):
        TradeExporter._validate_submission_export_page(
            _FakePage("https://etp.metal-it.ru/bids/new?lot=556675785")
        )

        with self.assertRaisesRegex(RuntimeError, "неправильная страница"):
            TradeExporter._validate_submission_export_page(
                _FakePage("https://etp.metal-it.ru/trades/123")
            )

    def test_submission_download_path_preserves_excel_suffix(self):
        target_path = Path("/tmp/export.xlsx")

        self.assertEqual(
            TradeExporter._target_path_for_download(target_path, "export.xls"),
            Path("/tmp/export.xls"),
        )
        self.assertEqual(
            TradeExporter._target_path_for_download(target_path, "export.csv"),
            Path("/tmp/export.csv"),
        )

    def test_export_retrade_lot_data_delegates_to_bid_export_when_bid_id_provided(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = os.path.join(tmpdir, "retrade.xlsx")
            with patch.object(
                self.exporter,
                "export_retrade_bid_data",
                return_value=target_path,
            ) as export_bid_mock:
                saved_path = self.exporter.export_retrade_lot_data(
                    lot_id=10,
                    trade_id=999,
                    bid_id=2,
                    download_path=target_path,
                )

            export_bid_mock.assert_called_once_with(
                bid_id=2,
                download_path=str(Path(target_path).expanduser()),
            )
            self.assertEqual(saved_path, target_path)

    def test_import_retrade_lot_data_delegates_to_bid_import_when_bid_id_provided(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = os.path.join(tmpdir, "retrade.xlsx")
            Path(source_path).write_bytes(b"placeholder")
            with patch.object(
                self.exporter,
                "import_retrade_bid_data",
                return_value=source_path,
            ) as import_bid_mock:
                imported_path = self.exporter.import_retrade_lot_data(
                    lot_id=10,
                    trade_id=999,
                    bid_id=2,
                    file_path=source_path,
                )

            import_bid_mock.assert_called_once_with(
                bid_id=2,
                file_path=source_path,
            )
            self.assertEqual(imported_path, source_path)

    def test_validate_import_file_path_requires_existing_excel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "retrade.xlsx"
            source_path.write_bytes(b"placeholder")

            self.assertEqual(
                self.exporter._validate_import_file_path(str(source_path)),
                source_path.resolve(),
            )

            with self.assertRaises(FileNotFoundError):
                self.exporter._validate_import_file_path(str(source_path.with_name("missing.xlsx")))

            with self.assertRaises(ValueError):
                self.exporter._validate_import_file_path(str(source_path.with_suffix(".csv")))


if __name__ == "__main__":
    unittest.main()
