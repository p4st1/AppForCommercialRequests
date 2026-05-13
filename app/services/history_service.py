from __future__ import annotations

import json
from typing import Callable

from app.repositories.offer_repository import OfferRepository
from tools import DatabaseTools as Tool


class HistoryService:
    def __init__(self, offer_repository: OfferRepository):
        self._offer_repository = offer_repository

    @staticmethod
    def event_name(event_type: str) -> str:
        mapping = {
            "docx": "КП (DOCX)",
            "excel": "Таблица (Excel)",
        }
        key = str(event_type or "").strip().lower()
        return mapping.get(key, key or "Событие")

    @staticmethod
    def format_total(total_amount, currency: str, *, fmt_number: Callable[[float], str]) -> str:
        if total_amount in (None, ""):
            return "—"
        try:
            value = float(total_amount)
        except (TypeError, ValueError):
            return "—"
        return Tool.formatPrice(fmt_number(value), str(currency or ""))

    @staticmethod
    def summarize_table_for_history(table_rows: list[list], *, total_col_index: int = 7) -> tuple[float, str, int]:
        total_amount = 0.0
        currency = ""
        rows_count = len(table_rows)
        for row in table_rows:
            if len(row) <= total_col_index:
                continue
            symbol, amount_text = Tool.parsePrice(str(row[total_col_index]))
            if symbol and not currency:
                currency = symbol
            try:
                total_amount += float(str(amount_text).replace(" ", "").replace(",", "."))
            except ValueError:
                continue
        return round(total_amount, 2), currency, rows_count

    @staticmethod
    def build_payload_json(table_rows: list[list], *, summary_columns: int) -> str:
        normalized_rows = []
        for row in table_rows:
            normalized_rows.append([str(value) for value in row[:summary_columns]])
        payload = {"table_data": normalized_rows}
        return json.dumps(payload, ensure_ascii=False)

    def record_docx_offer(
        self,
        *,
        customer_data,
        table_rows: list[list],
        output_path: str,
        selected_suppliers_count: int,
        summary_columns: int,
    ) -> int:
        total_amount, currency, items_count = self.summarize_table_for_history(table_rows, total_col_index=7)
        customer_name = " ".join(
            part for part in [customer_data[2], customer_data[1], customer_data[3]] if str(part).strip()
        ).strip()
        notes = ""
        if selected_suppliers_count > 1:
            notes = f"Выбрано заказчиков: {selected_suppliers_count}"

        payload_json = self.build_payload_json(table_rows, summary_columns=summary_columns)
        return self._offer_repository.create_doc_offer(
            customer_company=customer_data[7],
            customer_name=customer_name,
            items_count=items_count,
            total_amount=total_amount,
            currency=currency,
            file_path=str(output_path or ""),
            notes=notes,
            payload_json=payload_json,
        )

    def record_excel_export(
        self,
        *,
        items_count: int,
        total_amount: float,
        currency: str,
        file_path: str,
        notes: str = "Экспорт расчетной таблицы",
    ) -> int:
        return self._offer_repository.add_history_event(
            event_type="excel",
            items_count=items_count,
            total_amount=total_amount,
            currency=currency,
            file_path=file_path,
            notes=notes,
        )

    def get_history(self, *, limit: int = 1000):
        return self._offer_repository.get_history(limit=limit)

    def delete_event(self, event_id: int):
        self._offer_repository.delete_history_event(event_id=event_id)

    def save(self):
        self._offer_repository.save()
