import json
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QSignalBlocker
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tools import DatabaseTools as Tool


class HistoryFlowMixin:
    def _ensure_history_tab(self):
        if hasattr(self.ui, "historyTable"):
            return

        self.ui.historyTab = QWidget(self.ui.tabWidget)
        self.ui.historyTab.setObjectName("historyTab")

        root_layout = QVBoxLayout(self.ui.historyTab)
        root_layout.setSpacing(8)
        root_layout.setContentsMargins(8, 8, 8, 8)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel("История создания КП и экспортов", self.ui.historyTab)
        self.ui.historyRefreshButton = QPushButton("Обновить", self.ui.historyTab)
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.ui.historyRefreshButton)

        self.ui.historyTable = QTableWidget(self.ui.historyTab)
        self.ui.historyTable.setObjectName("historyTable")

        root_layout.addLayout(header_layout)
        root_layout.addWidget(self.ui.historyTable)
        self.ui.tabWidget.addTab(self.ui.historyTab, "История")
        self.ui.historyRefreshButton.clicked.connect(self.updateHistoryTable)
        self.ui.historyTable.itemDoubleClicked.connect(self._openHistoryFile)
        self.ui.historyTable.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.historyTable.customContextMenuRequested.connect(self._show_history_context_menu)

    def _setup_history_tab_table(self):
        if not hasattr(self.ui, "historyTable"):
            return

        table = self.ui.historyTable
        table.setColumnCount(len(self.HISTORY_HEADERS))
        table.setHorizontalHeaderLabels(self.HISTORY_HEADERS)
        table.setRowCount(0)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(False)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

    def _history_event_name(self, event_type: str) -> str:
        return self.history_service.event_name(event_type)

    def _format_history_total(self, total_amount, currency: str) -> str:
        return self.history_service.format_total(
            total_amount,
            currency,
            fmt_number=self._fmt_number,
        )

    def _history_row_meta(self, row: int) -> dict:
        if row < 0:
            return {}
        item = self.ui.historyTable.item(row, self.HISTORY_META_COLUMN)
        if item is None:
            return {}
        meta = item.data(Qt.ItemDataRole.UserRole)
        return meta if isinstance(meta, dict) else {}

    def _open_history_file_path(self, file_path: str):
        value = str(file_path or "").strip()
        if not value:
            return
        path = Path(value)
        if not path.exists():
            self.error("Ошибка", f"Файл не найден:\n{value}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_history_file_dir(self, file_path: str):
        value = str(file_path or "").strip()
        if not value:
            return
        path = Path(value)
        directory = path.parent
        if not directory.exists():
            self.error("Ошибка", f"Папка не найдена:\n{directory}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))

    def _copy_history_file_path(self, file_path: str):
        value = str(file_path or "").strip()
        if not value:
            return
        QApplication.clipboard().setText(value)
        if self.statusBar() is not None:
            self.statusBar().showMessage("Путь к файлу скопирован", 2500)

    def _repeat_history_doc(self, row: int):
        meta = self._history_row_meta(row)
        if str(meta.get("event_type", "")).strip().lower() != "docx":
            self.error("Ошибка", "Повторить можно только создание КП (DOCX)")
            return

        payload_text = str(meta.get("payload_json", "") or "").strip()
        if not payload_text:
            self.error("Ошибка", "Для этой записи не сохранена исходная таблица")
            return

        try:
            payload = json.loads(payload_text)
        except Exception as e:
            Tool.log_exception(
                "Не удалось прочитать payload истории",
                e,
                include_traceback=False,
            )
            self.error("Ошибка", "Не удалось прочитать данные таблицы из истории")
            return

        rows = payload.get("table_data", [])
        if not isinstance(rows, list) or not rows:
            self.error("Ошибка", "В истории нет валидной таблицы для повторного создания")
            return

        normalized_rows = []
        for row_data in rows:
            if not isinstance(row_data, list):
                continue
            normalized_rows.append([str(value) for value in row_data[: len(self.SUMMARY_HEADERS)]])

        if not normalized_rows:
            self.error("Ошибка", "В истории нет валидной таблицы для повторного создания")
            return

        self.openCreateDocWindow((len(normalized_rows), normalized_rows))

    def _delete_history_event(self, row: int):
        meta = self._history_row_meta(row)
        event_id = meta.get("id")
        if not event_id:
            return

        confirm = QMessageBox.question(
            self,
            "Удаление записи",
            "Удалить выбранную запись из истории?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            self.history_service.delete_event(int(event_id))
            self.history_service.save()
            self.updateHistoryTable()
        except Exception as e:
            self.error("Ошибка", f"Не удалось удалить запись:\n{e}")

    def _show_history_context_menu(self, pos):
        table = self.ui.historyTable
        clicked_item = table.itemAt(pos)
        row = clicked_item.row() if clicked_item is not None else -1
        meta = self._history_row_meta(row) if row >= 0 else {}
        file_path = str(meta.get("file_path", "") or "").strip()
        event_type = str(meta.get("event_type", "") or "").strip().lower()

        if row >= 0:
            table.selectRow(row)

        menu = QMenu(self)
        refresh_action = menu.addAction("Обновить")

        repeat_action = None
        open_file_action = None
        open_folder_action = None
        copy_path_action = None
        delete_action = None

        if row >= 0:
            menu.addSeparator()
            if event_type == "docx":
                repeat_action = menu.addAction("Повторить создание КП")
            if file_path:
                open_file_action = menu.addAction("Открыть файл")
                open_folder_action = menu.addAction("Открыть папку файла")
                copy_path_action = menu.addAction("Скопировать путь")
            delete_action = menu.addAction("Удалить запись")

        action = menu.exec(table.viewport().mapToGlobal(pos))
        if action is None:
            return
        if action == refresh_action:
            self.updateHistoryTable()
            return
        if action == repeat_action:
            self._repeat_history_doc(row)
            return
        if action == open_file_action:
            self._open_history_file_path(file_path)
            return
        if action == open_folder_action:
            self._open_history_file_dir(file_path)
            return
        if action == copy_path_action:
            self._copy_history_file_path(file_path)
            return
        if action == delete_action:
            self._delete_history_event(row)

    def updateHistoryTable(self):
        if not hasattr(self.ui, "historyTable"):
            return

        try:
            rows = self.history_service.get_history(limit=1000)
        except Exception as e:
            Tool.write_log(f"Ошибка загрузки истории: {e}")
            return

        table = self.ui.historyTable
        blocker = QSignalBlocker(table)
        table.clearContents()
        table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            (
                _entry_id,
                offer_number,
                date_value,
                created_at,
                event_type,
                customer_company,
                customer_name,
                items_count,
                total_amount,
                currency,
                file_path,
                _notes,
                payload_json,
            ) = row

            date_text = str(created_at or "").strip() or str(date_value or "").strip()
            event_text = self._history_event_name(event_type)
            offer_text = str(offer_number) if int(offer_number or 0) > 0 else "—"
            company_text = str(customer_company or "").strip() or "—"
            contact_text = str(customer_name or "").strip() or "—"
            items_text = str(max(0, int(items_count or 0)))
            total_text = self._format_history_total(total_amount, str(currency or ""))
            file_path_text = str(file_path or "").strip()
            file_text = Path(file_path_text).name if file_path_text else "—"
            meta = {
                "id": int(_entry_id),
                "event_type": str(event_type or "").strip().lower(),
                "file_path": file_path_text,
                "payload_json": str(payload_json or ""),
            }

            values = [
                date_text,
                event_text,
                offer_text,
                company_text,
                contact_text,
                items_text,
                total_text,
                file_text,
            ]

            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(
                    (item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    & ~Qt.ItemFlag.ItemIsEditable
                )
                if col_idx == self.HISTORY_META_COLUMN:
                    item.setData(Qt.ItemDataRole.UserRole, meta)
                if col_idx == self.HISTORY_FILE_COLUMN and file_path_text:
                    item.setData(Qt.ItemDataRole.UserRole, file_path_text)
                    item.setToolTip(file_path_text)
                table.setItem(row_idx, col_idx, item)

        del blocker
        table.resizeRowsToContents()

    def _openHistoryFile(self, item):
        if item is None or not hasattr(self.ui, "historyTable"):
            return

        row = item.row()
        meta = self._history_row_meta(row)
        file_path = str(meta.get("file_path", "") or "").strip()
        self._open_history_file_path(file_path)

