import json
import unittest

from app.services.history_service import HistoryService


class _FakeOfferRepository:
    def __init__(self):
        self.created_offers = []
        self.created_events = []
        self.deleted_ids = []
        self.saved = False
        self._history_rows = [("row",)]

    def create_doc_offer(self, **kwargs):
        self.created_offers.append(kwargs)
        return 7

    def add_history_event(self, **kwargs):
        self.created_events.append(kwargs)
        return 0

    def get_history(self, limit=500):
        return self._history_rows[:limit]

    def delete_history_event(self, event_id):
        self.deleted_ids.append(event_id)

    def save(self):
        self.saved = True


class HistoryServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = _FakeOfferRepository()
        self.service = HistoryService(self.repo)

    def test_summarize_table_for_history_parses_total_and_currency(self):
        rows = [
            ["1", "Насос", "SKU1", "шт", "2", "¥10,00", "¥20,00", "¥24,00", "12 дней"],
            ["2", "Клапан", "SKU2", "шт", "1", "¥5,00", "¥5,00", "¥6,00", "10 дней"],
        ]

        total_amount, currency, items_count = self.service.summarize_table_for_history(rows, total_col_index=7)

        self.assertEqual(total_amount, 30.0)
        self.assertEqual(currency, "¥")
        self.assertEqual(items_count, 2)

    def test_build_payload_json_trims_to_summary_columns(self):
        rows = [
            ["1", "Насос", "SKU1", "шт", "2", "A", "B", "C", "D", "EXTRA"],
        ]

        payload = self.service.build_payload_json(rows, summary_columns=9)
        data = json.loads(payload)

        self.assertEqual(data["table_data"], [["1", "Насос", "SKU1", "шт", "2", "A", "B", "C", "D"]])

    def test_record_docx_offer_uses_customer_and_notes(self):
        customer_data = (
            1,
            "Иван",
            "Иванов",
            "Иванович",
            "",
            "",
            "",
            "ООО Ромашка",
            "Директор",
            "",
            "мужской",
        )
        rows = [
            ["1", "Насос", "SKU1", "шт", "2", "¥10,00", "¥20,00", "¥24,00", "12 дней"],
        ]

        offer_number = self.service.record_docx_offer(
            customer_data=customer_data,
            table_rows=rows,
            output_path="/tmp/out.docx",
            selected_suppliers_count=2,
            summary_columns=9,
        )

        self.assertEqual(offer_number, 7)
        self.assertEqual(len(self.repo.created_offers), 1)
        offer = self.repo.created_offers[0]
        self.assertEqual(offer["customer_company"], "ООО Ромашка")
        self.assertEqual(offer["customer_name"], "Иванов Иван Иванович")
        self.assertEqual(offer["items_count"], 1)
        self.assertEqual(offer["total_amount"], 24.0)
        self.assertEqual(offer["currency"], "¥")
        self.assertEqual(offer["notes"], "Выбрано заказчиков: 2")
        self.assertEqual(offer["file_path"], "/tmp/out.docx")

    def test_record_excel_export_creates_excel_history_event(self):
        self.service.record_excel_export(
            items_count=3,
            total_amount=1250.5,
            currency="¥",
            file_path="/tmp/out.xlsx",
        )

        self.assertEqual(len(self.repo.created_events), 1)
        event = self.repo.created_events[0]
        self.assertEqual(event["event_type"], "excel")
        self.assertEqual(event["items_count"], 3)
        self.assertEqual(event["total_amount"], 1250.5)
        self.assertEqual(event["currency"], "¥")
        self.assertEqual(event["file_path"], "/tmp/out.xlsx")

    def test_event_name_and_total_format(self):
        self.assertEqual(self.service.event_name("docx"), "КП (DOCX)")
        self.assertEqual(self.service.event_name("excel"), "Таблица (Excel)")
        self.assertEqual(self.service.event_name("other"), "other")
        self.assertEqual(self.service.event_name(""), "Событие")

        formatted = self.service.format_total(1000, "¥", fmt_number=lambda value: str(int(value)))
        self.assertEqual(formatted, "¥1 000,00")
        self.assertEqual(self.service.format_total(None, "¥", fmt_number=str), "—")

    def test_delete_get_and_save_delegate_to_repository(self):
        rows = self.service.get_history(limit=10)
        self.assertEqual(rows, [("row",)])

        self.service.delete_event(12)
        self.assertEqual(self.repo.deleted_ids, [12])

        self.service.save()
        self.assertTrue(self.repo.saved)


if __name__ == "__main__":
    unittest.main()
