from __future__ import annotations

from database import Database


class OfferRepository:
    def __init__(self, db: Database):
        self._db = db

    def get_next_doc_offer_number(self, date_value: str | None = None) -> int:
        return self._db.getNextOfferNumber(date_value=date_value)

    def create_doc_offer(
        self,
        *,
        customer_company: str = "",
        customer_name: str = "",
        items_count: int = 0,
        total_amount: float | None = None,
        currency: str = "",
        file_path: str = "",
        remote_url: str = "",
        notes: str = "",
        payload_json: str = "",
    ) -> int:
        return self._db.createOffer(
            customer_company=customer_company,
            customer_name=customer_name,
            items_count=items_count,
            total_amount=total_amount,
            currency=currency,
            file_path=file_path,
            remote_url=remote_url,
            notes=notes,
            payload_json=payload_json,
        )

    def add_history_event(
        self,
        *,
        event_type: str,
        customer_company: str = "",
        customer_name: str = "",
        items_count: int = 0,
        total_amount: float | None = None,
        currency: str = "",
        file_path: str = "",
        remote_url: str = "",
        notes: str = "",
        payload_json: str = "",
    ) -> int:
        return self._db.addHistoryEvent(
            event_type=event_type,
            customer_company=customer_company,
            customer_name=customer_name,
            items_count=items_count,
            total_amount=total_amount,
            currency=currency,
            file_path=file_path,
            remote_url=remote_url,
            notes=notes,
            payload_json=payload_json,
        )

    def get_history(self, limit: int = 500):
        return self._db.getOffersHistory(limit=limit)

    def delete_history_event(self, event_id: int):
        self._db.deleteHistoryEvent(event_id=event_id)

    def save(self):
        self._db.save()
