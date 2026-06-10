from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RetradeExcelContext:
    file_path: Path
    bid_id: int | None = None


class RetradeService:
    """Boundary for the retrade Excel workflow.

    The current UI implementation still lives in ExportMixin for backward
    compatibility. This service marks the retrade workflow as Excel-only and
    keeps it separate from the submission workflow.
    """

    SUPPORTED_EXCEL_SUFFIXES = {".xlsx", ".xls", ".xlsm"}

    @classmethod
    def validate_excel_path(
        cls,
        file_path: str | Path,
        *,
        bid_id: Any = None,
    ) -> RetradeExcelContext:
        path = Path(file_path).expanduser()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Excel файл переторжки не найден: {path}")
        if path.suffix.lower() not in cls.SUPPORTED_EXCEL_SUFFIXES:
            raise ValueError("Переторжка работает только с Excel файлами")

        parsed_bid_id: int | None = None
        if bid_id is not None:
            try:
                parsed_bid_id = int(bid_id)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Некорректный bid_id переторжки: {bid_id}") from exc
            if parsed_bid_id <= 0:
                raise ValueError(f"Некорректный bid_id переторжки: {parsed_bid_id}")

        return RetradeExcelContext(file_path=path.resolve(), bid_id=parsed_bid_id)

    @staticmethod
    def workflow_steps() -> tuple[str, str, str]:
        return ("скачал Excel", "изменил цены", "импортировал Excel")

    @classmethod
    def import_excel(
        cls,
        *,
        bid_id: Any,
        file_path: str | Path,
        trade_id: Any = None,
        lot_id: Any = None,
        bid_number: str = "",
        bidder_title: str = "",
    ) -> str:
        context = cls.validate_excel_path(file_path, bid_id=bid_id)

        from services.trade_exporter import TradeExporter

        exporter = TradeExporter()
        return str(
            exporter.import_retrade_bid_data(
                bid_id=context.bid_id,
                file_path=str(context.file_path),
                trade_id=trade_id,
                lot_id=lot_id,
                bid_number=bid_number,
                bidder_title=bidder_title,
            )
        )
