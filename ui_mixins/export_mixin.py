from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QPushButton

from config import Config
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
        download_path: str,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._trade_id = int(trade_id) if trade_id is not None else None
        self._lot_id = int(lot_id) if lot_id is not None else None
        if self._trade_id is None and self._lot_id is None:
            raise ValueError("Не указан trade_id или lot_id для экспорта")
        self._download_path = str(download_path)

    def run(self) -> None:
        try:
            exporter = TradeExporter()
            if self._lot_id is not None:
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
        self._ensure_export_button()
        self.btn_export_trade.clicked.connect(self.export_selected_trade)

    def _ensure_export_button(self) -> None:
        if hasattr(self, "btn_export_trade"):
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

        self.btn_export_trade = QPushButton("Экспорт", web_tab)
        self.btn_export_trade.setObjectName("btn_export_trade")
        self.ui.btn_export_trade = self.btn_export_trade
        header_layout.addWidget(self.btn_export_trade)

    def export_selected_trade(self) -> None:
        try:
            trade_id = self._get_selected_trade_id_for_export()
            self._start_export_worker(trade_id=trade_id)
        except Exception as exc:
            self._on_export_error(str(exc))

    def export_trade(self, lot_id: int) -> None:
        self._start_export_worker(lot_id=lot_id)

    def _start_export_worker(
        self,
        *,
        trade_id: int | None = None,
        lot_id: int | None = None,
    ) -> None:
        if self._export_trade_worker is not None and self._export_trade_worker.isRunning():
            raise RuntimeError("Экспорт заявки уже выполняется")

        if trade_id is None and lot_id is None:
            raise ValueError("Не указан идентификатор для экспорта")

        identifier = trade_id if trade_id is not None else lot_id
        identifier_value = int(identifier)
        if identifier_value <= 0:
            raise ValueError(f"Некорректный идентификатор для экспорта: {identifier}")

        download_path = self._build_export_download_path(identifier_value)
        self._set_export_loading_state(is_loading=True)

        worker = ExportTradeWorker(
            trade_id=trade_id,
            lot_id=lot_id,
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
    def _build_export_download_path(trade_id: int) -> str:
        base_dir_raw = str(Config.config.get("pathToSaveExcel", "") or "").strip()
        base_dir = Path(base_dir_raw).expanduser() if base_dir_raw else (Path.home() / "Downloads")
        if base_dir.exists() and not base_dir.is_dir():
            raise NotADirectoryError(f"Папка для экспорта недоступна: {base_dir}")
        base_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"trade_{int(trade_id)}_{timestamp}.xlsx"
        return str((base_dir / file_name).resolve())

    def _set_export_loading_state(self, *, is_loading: bool) -> None:
        self.btn_export_trade.setEnabled(not is_loading)
        self.btn_export_trade.setText("Экспорт..." if is_loading else "Экспорт")

    def _finish_export(self, status_message: str) -> None:
        self._set_export_loading_state(is_loading=False)
        worker = self._export_trade_worker
        self._export_trade_worker = None
        if worker is not None:
            worker.deleteLater()
        status_bar = self.statusBar()
        if status_bar is not None and status_message:
            status_bar.showMessage(status_message, 5_000)

    def _on_export_finished(self, file_path: str) -> None:
        file_path_text = str(file_path or "").strip()

        if file_path_text:
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
