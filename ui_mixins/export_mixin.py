from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QPushButton

from config import Config
from services.excel_processor import ExcelProcessor
from services.trade_exporter import TradeExporter
from tools import DatabaseTools as Tool


class ExportTradeWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        *,
        trade_id: int | None = None,
        lot_id: int | None = None,
        bid_id: int | None = None,
        is_retrade: bool = False,
        download_path: str,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._trade_id = int(trade_id) if trade_id is not None else None
        self._lot_id = int(lot_id) if lot_id is not None else None
        self._bid_id = int(bid_id) if bid_id is not None else None
        self._is_retrade = bool(is_retrade)
        if self._trade_id is None and self._lot_id is None:
            raise ValueError("Не указан trade_id или lot_id для экспорта")
        self._download_path = str(download_path)

    def run(self) -> None:
        try:
            exporter = TradeExporter()
            if self._lot_id is not None and self._is_retrade:
                saved_path = exporter.export_retrade_lot_data(
                    lot_id=self._lot_id,
                    download_path=self._download_path,
                    trade_id=self._trade_id,
                    bid_id=self._bid_id,
                )
            elif self._lot_id is not None:
                saved_path = exporter.export_lot_data(
                    lot_id=self._lot_id,
                    download_path=self._download_path,
                )
            else:
                saved_path = exporter.export_trade_data(
                    trade_id=int(self._trade_id),
                    download_path=self._download_path,
                )
            self.finished.emit(saved_path)
        except Exception as exc:
            self.error.emit(str(exc))


class ExportMixin:
    def init_export_mixin(self) -> None:
        self._export_trade_worker: ExportTradeWorker | None = None
        self.excel_processor = ExcelProcessor()
        self._ensure_export_button()
        self.btn_export_trade.clicked.connect(self.export_selected_trade)
        self.btn_export_retrade.clicked.connect(self.export_selected_retrade)

    def _ensure_export_button(self) -> None:
        if hasattr(self, "btn_export_trade") and hasattr(self, "btn_export_retrade"):
            return

        ensure_tab = getattr(self, "_ensure_platform_tab", None)
        if callable(ensure_tab):
            ensure_tab()

        web_tab = getattr(self.ui, "webTab", None)
        if web_tab is None:
            raise RuntimeError("Не найден webTab для кнопки экспорта")

        root_layout = web_tab.layout()
        header_layout: QHBoxLayout | None = None
        if root_layout is not None and root_layout.count() > 0:
            header_item = root_layout.itemAt(0)
            if header_item is not None:
                layout = header_item.layout()
                if isinstance(layout, QHBoxLayout):
                    header_layout = layout

        if header_layout is None:
            raise RuntimeError("Не удалось найти layout заголовка вкладки заявок")

        if not hasattr(self, "btn_export_trade"):
            self.btn_export_trade = QPushButton("Экспорт", web_tab)
            self.btn_export_trade.setObjectName("btn_export_trade")
            self.ui.btn_export_trade = self.btn_export_trade
            header_layout.addWidget(self.btn_export_trade)

        if not hasattr(self, "btn_export_retrade"):
            self.btn_export_retrade = QPushButton("Экспорт переторжки", web_tab)
            self.btn_export_retrade.setObjectName("btn_export_retrade")
            self.ui.btn_export_retrade = self.btn_export_retrade
            header_layout.addWidget(self.btn_export_retrade)

    def export_selected_trade(self) -> None:
        try:
            trade_id = self._get_selected_trade_id_for_export()
            self._start_export_worker(trade_id=trade_id)
        except Exception as exc:
            self._on_export_error(str(exc))

    def export_trade(self, lot_id: int) -> None:
        self._start_export_worker(lot_id=lot_id)

    def export_selected_retrade(self) -> None:
        table_retrades = getattr(self, "table_retrades", None)
        if table_retrades is None:
            table_retrades = getattr(getattr(self, "ui", None), "table_retrades", None)
        if table_retrades is None:
            QMessageBox.warning(self, "Ошибка", "Таблица переторжек не найдена")
            return

        selected = table_retrades.currentRow()
        retrades = getattr(self, "retrades", [])
        if selected < 0 or not isinstance(retrades, list) or selected >= len(retrades):
            QMessageBox.warning(self, "Ошибка", "Выберите переторжку")
            return

        retr = retrades[selected]
        if not isinstance(retr, dict):
            QMessageBox.warning(self, "Ошибка", "Выберите переторжку")
            return

        try:
            trade_id = self._parse_positive_trade_id(retr.get("id"))
            lot_id = self._get_retrade_lot_id_for_export(retr)
            bid_id = self._get_selected_retrade_bid_id_for_export()
            self._start_export_worker(
                trade_id=trade_id,
                lot_id=lot_id,
                bid_id=bid_id,
                is_retrade=True,
            )
        except Exception as exc:
            self._on_export_error(str(exc))

    @staticmethod
    def _parse_positive_trade_id(raw_trade_id: Any) -> int:
        try:
            trade_id = int(raw_trade_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Некорректный trade_id переторжки: {raw_trade_id}") from exc
        if trade_id <= 0:
            raise ValueError(f"Некорректный trade_id переторжки: {trade_id}")
        return trade_id

    @staticmethod
    def _parse_positive_lot_id(raw_lot_id: Any) -> int:
        try:
            lot_id = int(raw_lot_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Некорректный lot_id для экспорта переторжки: {raw_lot_id}") from exc
        if lot_id <= 0:
            raise ValueError(f"Некорректный lot_id для экспорта переторжки: {lot_id}")
        return lot_id

    def _get_retrade_lot_id_for_export(self, retrade: dict[str, Any]) -> int:
        lots = retrade.get("lots")
        if isinstance(lots, list) and lots:
            first_lot = lots[0]
            if isinstance(first_lot, dict):
                return self._parse_positive_lot_id(first_lot.get("id"))

        raise Exception("У выбранной переторжки отсутствует lot_id")

    @staticmethod
    def _parse_positive_bid_id(raw_bid_id: Any) -> int:
        try:
            bid_id = int(raw_bid_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Некорректный bid_id для экспорта переторжки: {raw_bid_id}") from exc
        if bid_id <= 0:
            raise ValueError(f"Некорректный bid_id для экспорта переторжки: {bid_id}")
        return bid_id

    def _get_selected_retrade_bid_id_for_export(self) -> int:
        table_offers = getattr(self, "table_retrade_offers", None)
        if table_offers is None:
            table_offers = getattr(getattr(self, "ui", None), "table_retrade_offers", None)
        if table_offers is None:
            raise Exception("Таблица предложений переторжки не найдена")

        offers = getattr(self, "retrade_offers", [])
        if not isinstance(offers, list) or not offers:
            raise Exception("Нет предложений переторжки для экспорта")

        selected_row = table_offers.currentRow()
        if selected_row < 0 or selected_row >= len(offers):
            raise Exception("Выберите предложение переторжки")

        selected_offer = offers[selected_row]
        if not isinstance(selected_offer, dict):
            raise Exception("Выберите предложение переторжки")

        return self._parse_positive_bid_id(selected_offer.get("bid_id"))

    def _start_export_worker(
        self,
        *,
        trade_id: int | None = None,
        lot_id: int | None = None,
        bid_id: int | None = None,
        is_retrade: bool = False,
    ) -> None:
        if self._export_trade_worker is not None and self._export_trade_worker.isRunning():
            raise RuntimeError("Экспорт заявки уже выполняется")

        if trade_id is None and lot_id is None:
            raise ValueError("Не указан идентификатор для экспорта")
        if trade_id is not None and int(trade_id) <= 0:
            raise ValueError(f"Некорректный идентификатор для экспорта: {trade_id}")
        if lot_id is not None and int(lot_id) <= 0:
            raise ValueError(f"Некорректный идентификатор для экспорта: {lot_id}")
        if bid_id is not None and int(bid_id) <= 0:
            raise ValueError(f"Некорректный идентификатор для экспорта: {bid_id}")
        if is_retrade and lot_id is None:
            raise Exception("У выбранной переторжки отсутствует lot_id")
        if is_retrade and (trade_id is None or int(trade_id) <= 0):
            raise Exception("Не указан trade_id для открытия страницы переторжки")
        if is_retrade and (bid_id is None or int(bid_id) <= 0):
            raise Exception("Выберите предложение переторжки")

        identifier_for_path: Any = (
            trade_id
            if trade_id is not None
            else lot_id
            if lot_id is not None
            else "unknown"
        )
        download_path = self._build_export_download_path(identifier_for_path)
        self._set_export_loading_state(is_loading=True)

        worker = ExportTradeWorker(
            trade_id=trade_id,
            lot_id=lot_id,
            bid_id=bid_id,
            is_retrade=is_retrade,
            download_path=download_path,
            parent=self,
        )
        worker.finished.connect(self._on_export_finished)
        worker.error.connect(self._on_export_error)
        self._export_trade_worker = worker
        worker.start()

    def _get_selected_trade_id_for_export(self) -> int:
        shared_getter = getattr(self, "_get_selected_trade_id", None)
        if callable(shared_getter):
            return int(shared_getter())

        table = getattr(self.ui, "tradesTable", None)
        if table is None:
            raise RuntimeError("Таблица заявок не найдена")

        selection_model = table.selectionModel()
        selected_rows = selection_model.selectedRows() if selection_model is not None else []
        if not selected_rows:
            raise ValueError("Выберите заявку в таблице перед экспортом")

        row = selected_rows[0].row()
        trade_item = table.item(row, 0)
        trade_text = trade_item.text().strip() if trade_item is not None else ""
        if not trade_text:
            raise ValueError("Не удалось получить trade_id из выбранной строки")

        try:
            return int(trade_text)
        except ValueError as exc:
            raise ValueError(f"Некорректный trade_id в таблице: {trade_text}") from exc

    @staticmethod
    def _build_export_download_path(identifier: Any) -> str:
        base_dir_raw = str(Config.config.get("pathToSaveExcel", "") or "").strip()
        base_dir = Path(base_dir_raw).expanduser() if base_dir_raw else (Path.home() / "Downloads")
        if base_dir.exists() and not base_dir.is_dir():
            raise NotADirectoryError(f"Папка для экспорта недоступна: {base_dir}")
        base_dir.mkdir(parents=True, exist_ok=True)

        identifier_text = str(identifier or "").strip()
        safe_identifier = re.sub(r"[^0-9A-Za-z_-]+", "_", identifier_text).strip("_") or "unknown"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"trade_{safe_identifier}_{timestamp}.xlsx"
        return str((base_dir / file_name).resolve())

    def _set_export_loading_state(self, *, is_loading: bool) -> None:
        if hasattr(self, "btn_export_trade"):
            self.btn_export_trade.setEnabled(not is_loading)
            self.btn_export_trade.setText("Экспорт..." if is_loading else "Экспорт")
        if hasattr(self, "btn_export_retrade"):
            self.btn_export_retrade.setEnabled(not is_loading)
            self.btn_export_retrade.setText(
                "Экспорт..." if is_loading else "Экспорт переторжки"
            )

    def _finish_export(self, status_message: str) -> None:
        self._set_export_loading_state(is_loading=False)
        worker = self._export_trade_worker
        self._export_trade_worker = None
        if worker is not None:
            worker.deleteLater()
        status_bar = self.statusBar()
        if status_bar is not None and status_message:
            status_bar.showMessage(status_message, 5_000)

    def get_table_rows(self) -> list[dict]:
        table = getattr(getattr(self, "ui", None), "KpTable", None)
        if table is None:
            return []

        rows: list[dict] = []
        row_count = table.rowCount()

        for row_index in range(row_count):
            price_item = table.item(row_index, 10) or table.item(row_index, 5)
            manufacturer_item = table.item(row_index, 1)
            tech_item = table.item(row_index, 2)

            price_text = price_item.text().strip() if price_item is not None else ""
            _, raw_price = Tool.parsePrice(price_text)
            raw_price = str(raw_price or "").replace(" ", "").replace(",", ".").strip()
            if raw_price:
                try:
                    price_value = float(raw_price)
                except ValueError:
                    price_value = raw_price
            else:
                price_value = ""

            rows.append(
                {
                    "price": price_value,
                    "manufacturer": manufacturer_item.text().strip() if manufacturer_item is not None else "",
                    "tech_characteristics": tech_item.text().strip() if tech_item is not None else "",
                }
            )

        return rows

    def _on_export_finished(self, file_path: str) -> None:
        file_path_text = str(file_path or "").strip()

        if not file_path_text:
            Tool.write_log("Экспорт переторжки пропущен: пользователь не участвует")
            QMessageBox.information(
                self,
                "Экспорт заявки",
                "Экспорт пропущен: нет участия в выбранной переторжке",
            )
            self._finish_export("Экспорт пропущен")
            return

        if file_path_text:
            excel_processor = getattr(self, "excel_processor", None)
            if excel_processor is None:
                excel_processor = ExcelProcessor()
                self.excel_processor = excel_processor

            try:
                excel_processor.fill_exported_excel(
                    file_path_text,
                    self.get_table_rows(),
                )
            except Exception as exc:
                error_text = str(exc or "Ошибка обработки Excel")
                Tool.write_log(f"Ошибка пост-обработки Excel: {error_text}")
                QMessageBox.critical(self, "Ошибка", error_text)
                set_pipeline_error_status = getattr(self, "_set_pipeline_error_status", None)
                if callable(set_pipeline_error_status):
                    set_pipeline_error_status()
                self._finish_export("Ошибка пост-обработки Excel")
                return

            open_excel = getattr(self, "open_excel_in_new_tab", None)
            if callable(open_excel):
                try:
                    open_excel(file_path_text)
                except Exception as exc:
                    preview_error = str(exc or "Неизвестная ошибка")
                    Tool.write_log(f"Не удалось открыть Excel во вкладке: {preview_error}")
                    status_bar = self.statusBar()
                    if status_bar is not None:
                        status_bar.showMessage("Файл экспортирован, но предпросмотр Excel не открыт", 5_000)

        info_text = (
            f"Файл успешно экспортирован:\n{file_path_text}"
            if file_path_text
            else "Файл успешно экспортирован"
        )
        Tool.write_log(f"Экспорт заявки завершен: {file_path_text}")
        QMessageBox.information(self, "Экспорт заявки", info_text)
        self._finish_export("Excel файл экспортирован")

    def _on_export_error(self, message: str) -> None:
        error_text = str(message or "Неизвестная ошибка")
        Tool.write_log(f"Ошибка экспорта заявки: {error_text}")
        QMessageBox.warning(self, "Ошибка экспорта заявки", error_text)
        self._finish_export("Ошибка экспорта заявки")
