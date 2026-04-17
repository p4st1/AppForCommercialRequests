from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tools import DatabaseTools as Tool

try:
    import pandas as pd
except Exception:  # pragma: no cover - guarded for test/runtime environments without pandas
    pd = None


class ExcelLoadWorker(QThread):
    finished = Signal(object, object)
    error = Signal(str)

    def __init__(self, *, file_path: str, parent: Any = None) -> None:
        super().__init__(parent)
        self._file_path = str(file_path)

    def run(self) -> None:
        try:
            if pd is None:
                raise RuntimeError("Не установлен pandas. Установите зависимости приложения.")

            dataframe = pd.read_excel(self._file_path)
            headers = [str(column) for column in dataframe.columns.tolist()]
            rows: list[list[str]] = []

            for row in dataframe.itertuples(index=False, name=None):
                prepared_row: list[str] = []
                for value in row:
                    if pd.isna(value):
                        prepared_row.append("")
                    else:
                        prepared_row.append(str(value))
                rows.append(prepared_row)

            self.finished.emit(headers, rows)
        except Exception as exc:
            self.error.emit(str(exc))


class ExcelViewerMixin:
    def init_excel_viewer_mixin(self) -> None:
        self._excel_preview_workers: dict[ExcelLoadWorker, dict[str, Any]] = {}

    def _ensure_excel_viewer_state(self) -> None:
        if not isinstance(getattr(self, "_excel_preview_workers", None), dict):
            self._excel_preview_workers = {}

    def _get_main_tab_widget(self) -> Any:
        tab_widget = getattr(self, "tabWidget", None)
        if tab_widget is None:
            ui_obj = getattr(self, "ui", None)
            tab_widget = getattr(ui_obj, "tabWidget", None) if ui_obj is not None else None

        if tab_widget is None:
            raise RuntimeError("Не найден tabWidget для отображения Excel")
        return tab_widget

    def open_excel_in_new_tab(self, file_path: str) -> None:
        self._ensure_excel_viewer_state()

        normalized_path = str(file_path or "").strip()
        if not normalized_path:
            raise ValueError("Путь к Excel файлу не указан")

        excel_path = Path(normalized_path).expanduser()
        if not excel_path.exists() or not excel_path.is_file():
            raise FileNotFoundError(f"Excel файл не найден: {excel_path}")

        tabs = self._get_main_tab_widget()

        excel_tab = QWidget(tabs)
        excel_tab.setObjectName("excelPreviewTab")
        layout = QVBoxLayout(excel_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        table = QTableWidget(excel_tab)
        table.setObjectName("excelPreviewTable")
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        table.setRowCount(1)
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels(["Статус"])
        table.setItem(0, 0, QTableWidgetItem("Загрузка Excel..."))

        layout.addWidget(table)

        tab_index = tabs.addTab(excel_tab, "Excel")
        tabs.setCurrentIndex(tab_index)

        resolved_path = str(excel_path.resolve())
        worker = ExcelLoadWorker(file_path=resolved_path, parent=self)
        self._excel_preview_workers[worker] = {
            "tab": excel_tab,
            "table": table,
            "path": resolved_path,
        }
        worker.finished.connect(self._on_excel_loaded)
        worker.error.connect(self._on_excel_load_error)
        worker.start()

    def _pop_excel_worker_context(self, worker: Any) -> dict[str, Any] | None:
        workers = getattr(self, "_excel_preview_workers", None)
        if not isinstance(workers, dict):
            return None
        return workers.pop(worker, None)

    def _cleanup_excel_worker(self, worker: Any) -> None:
        if worker is not None and hasattr(worker, "deleteLater"):
            worker.deleteLater()

    def _on_excel_loaded(self, headers: Any, rows: Any) -> None:
        sender = getattr(self, "sender", None)
        worker = sender() if callable(sender) else None
        context = self._pop_excel_worker_context(worker)
        if context is None:
            self._cleanup_excel_worker(worker)
            return

        table = context.get("table")
        if not isinstance(table, QTableWidget):
            self._cleanup_excel_worker(worker)
            return

        header_labels = [str(item) for item in (headers or [])]
        table_rows = rows if isinstance(rows, list) else []
        column_count = len(header_labels)
        if column_count == 0:
            column_count = max((len(row) for row in table_rows if isinstance(row, list)), default=0)

        table.setUpdatesEnabled(False)
        try:
            table.clear()
            table.setRowCount(len(table_rows))
            table.setColumnCount(column_count)
            if header_labels:
                table.setHorizontalHeaderLabels(header_labels)

            for row_index, row_values in enumerate(table_rows):
                if not isinstance(row_values, list):
                    continue
                for column_index in range(min(len(row_values), column_count)):
                    value = str(row_values[column_index])
                    table.setItem(row_index, column_index, QTableWidgetItem(value))
        finally:
            table.setUpdatesEnabled(True)

        table.resizeColumnsToContents()
        table.resizeRowsToContents()

        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(f"Excel открыт: {Path(context['path']).name}", 5_000)

        Tool.write_log(f"Excel открыт во вкладке: {context['path']}")
        self._cleanup_excel_worker(worker)

    def _on_excel_load_error(self, message: str) -> None:
        sender = getattr(self, "sender", None)
        worker = sender() if callable(sender) else None
        context = self._pop_excel_worker_context(worker)

        error_text = str(message or "Не удалось открыть Excel файл")
        Tool.write_log(f"Ошибка чтения Excel: {error_text}")

        if context is not None:
            table = context.get("table")
            if isinstance(table, QTableWidget):
                table.clear()
                table.setRowCount(1)
                table.setColumnCount(1)
                table.setHorizontalHeaderLabels(["Ошибка"])
                table.setItem(0, 0, QTableWidgetItem(error_text))

        QMessageBox.warning(self, "Просмотр Excel", error_text)
        self._cleanup_excel_worker(worker)
