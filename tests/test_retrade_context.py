import unittest
from unittest.mock import patch

from ui_mixins.export_mixin import ExportMixin


class _FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)


class _FakeExportWorker:
    created = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.finished = _FakeSignal()
        self.error = _FakeSignal()
        self.started = False
        _FakeExportWorker.created.append(self)

    def start(self):
        self.started = True

    def isRunning(self):
        return False


class _FakeOffersTable:
    def __init__(self, row):
        self._row = row

    def currentRow(self):
        return self._row


class _FakeExportWindow(ExportMixin):
    def __init__(self):
        self._export_trade_worker = None
        self._pending_retrade_bid_id = None
        self._pending_retrade_context = {}
        self.current_retrade = ""
        self.current_retrade_context = {}
        self.current_retrade_excel_path = ""
        self.current_retrade_bid_id = None
        self.current_retrade_trade_id = None
        self.current_retrade_lot_id = None
        self._active_export_workflow = ""
        self.loading_states = []

    def _build_export_download_path(self, identifier):
        return f"/tmp/trade_{identifier}.xlsx"

    def _set_export_loading_state(self, *, is_loading):
        self.loading_states.append(is_loading)


class RetradeContextTests(unittest.TestCase):
    def setUp(self):
        _FakeExportWorker.created.clear()

    def test_build_current_retrade_context_uses_selected_offer_number(self):
        window = _FakeExportWindow()

        context = window._build_current_retrade_context(
            retrade={
                "id": 999,
                "number": "RT-1",
                "title": "Переторжка 1",
                "status": "Активна",
            },
            offer={
                "bid_id": 7001,
                "number": "740370",
                "bidder_title": "ООО Альфа",
                "price": "100",
            },
            trade_id=999,
            lot_id=55,
            bid_id=7001,
        )
        window._set_current_retrade_context(context)

        self.assertEqual(window.current_retrade, "740370")
        self.assertEqual(window.current_retrade_bid_id, 7001)
        self.assertEqual(window.current_retrade_trade_id, 999)
        self.assertEqual(window.current_retrade_lot_id, 55)
        self.assertEqual(window.current_retrade_context["retrade_number"], "RT-1")

    def test_import_bid_prefers_current_retrade_context_over_selection(self):
        window = _FakeExportWindow()
        window.table_retrade_offers = _FakeOffersTable(0)
        window.retrade_offers = [{"bid_id": 7002, "number": "OTHER"}]
        window._set_current_retrade_context(
            {
                "number": "740370",
                "bid_id": 7001,
                "trade_id": 999,
                "lot_id": 55,
            }
        )

        self.assertEqual(window._get_retrade_bid_id_for_import(), 7001)

    def test_start_retrade_export_sets_current_and_pending_context(self):
        window = _FakeExportWindow()
        window.current_retrade_excel_path = "/tmp/old_retrade.xlsx"
        context = {
            "number": "740370",
            "bid_id": 7001,
            "trade_id": 999,
            "lot_id": 55,
        }

        with patch("ui_mixins.export_mixin.ExportTradeWorker", _FakeExportWorker):
            window._start_export_worker(
                trade_id=999,
                lot_id=55,
                bid_id=7001,
                is_retrade=True,
                retrade_context=context,
            )

        self.assertEqual(window.current_retrade, "740370")
        self.assertEqual(window.current_retrade_excel_path, "")
        self.assertEqual(window.current_retrade_bid_id, 7001)
        self.assertEqual(window._pending_retrade_bid_id, 7001)
        self.assertEqual(window._pending_retrade_context, context)
        self.assertEqual(window._active_export_workflow, "retrade")
        self.assertEqual(len(_FakeExportWorker.created), 1)
        self.assertTrue(_FakeExportWorker.created[0].started)
        self.assertEqual(_FakeExportWorker.created[0].kwargs["bid_id"], 7001)


if __name__ == "__main__":
    unittest.main()
