import json
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QDate, Qt, QUrl, QSignalBlocker
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.table_autosize import configure_table_autosize, resize_table_to_contents
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

        self._setup_history_filter_controls()

        self.ui.historyTable = QTableWidget(self.ui.historyTab)
        self.ui.historyTable.setObjectName("historyTable")

        root_layout.addLayout(header_layout)
        root_layout.addWidget(self.ui.historyFiltersFrame)
        root_layout.addWidget(self.ui.historyTable)
        self.ui.tabWidget.addTab(self.ui.historyTab, "История")
        self.ui.historyRefreshButton.clicked.connect(self.updateHistoryTable)
        self.ui.historyTable.itemDoubleClicked.connect(self._openHistoryFile)
        self.ui.historyTable.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.historyTable.customContextMenuRequested.connect(self._show_history_context_menu)

    def _setup_history_filter_controls(self):
        self.ui.historyFiltersFrame = QFrame(self.ui.historyTab)
        self.ui.historyFiltersFrame.setObjectName("historyFiltersFrame")
        self.ui.historyFiltersFrame.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QGridLayout(self.ui.historyFiltersFrame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)

        self.ui.historyCustomerFilterLine = QLineEdit(self.ui.historyFiltersFrame)
        self.ui.historyCustomerFilterLine.setPlaceholderText("Компания или контакт")

        self.ui.historyEventFilterCombo = QComboBox(self.ui.historyFiltersFrame)
        self.ui.historyEventFilterCombo.addItem("Все события", "")
        self.ui.historyEventFilterCombo.addItem("КП (DOCX)", "docx")
        self.ui.historyEventFilterCombo.addItem("Таблица (Excel)", "excel")

        self.ui.historyPeriodFilterCombo = QComboBox(self.ui.historyFiltersFrame)
        self.ui.historyPeriodFilterCombo.addItem("Все время", "all")
        self.ui.historyPeriodFilterCombo.addItem("Сегодня", "today")
        self.ui.historyPeriodFilterCombo.addItem("Последние 7 дней", "last_7_days")
        self.ui.historyPeriodFilterCombo.addItem("Последние 30 дней", "last_30_days")
        self.ui.historyPeriodFilterCombo.addItem("Текущий месяц", "current_month")
        self.ui.historyPeriodFilterCombo.addItem("Произвольный период", "custom")

        current_day = QDate.currentDate()
        self.ui.historyDateFromEdit = QDateEdit(current_day, self.ui.historyFiltersFrame)
        self.ui.historyDateFromEdit.setCalendarPopup(True)
        self.ui.historyDateFromEdit.setDisplayFormat("dd.MM.yyyy")
        self.ui.historyDateToEdit = QDateEdit(current_day, self.ui.historyFiltersFrame)
        self.ui.historyDateToEdit.setCalendarPopup(True)
        self.ui.historyDateToEdit.setDisplayFormat("dd.MM.yyyy")

        self.ui.historySearchLine = QLineEdit(self.ui.historyFiltersFrame)
        self.ui.historySearchLine.setPlaceholderText("Файл, заметка или № КП")
        self.ui.historyResetFiltersButton = QPushButton("Сбросить", self.ui.historyFiltersFrame)
        self.ui.historyResultCountLabel = QLabel("", self.ui.historyFiltersFrame)

        layout.addWidget(QLabel("Заказчик:", self.ui.historyFiltersFrame), 0, 0)
        layout.addWidget(self.ui.historyCustomerFilterLine, 0, 1)
        layout.addWidget(QLabel("Событие:", self.ui.historyFiltersFrame), 0, 2)
        layout.addWidget(self.ui.historyEventFilterCombo, 0, 3)
        layout.addWidget(QLabel("Период:", self.ui.historyFiltersFrame), 0, 4)
        layout.addWidget(self.ui.historyPeriodFilterCombo, 0, 5)
        layout.addWidget(QLabel("С:", self.ui.historyFiltersFrame), 1, 0)
        layout.addWidget(self.ui.historyDateFromEdit, 1, 1)
        layout.addWidget(QLabel("По:", self.ui.historyFiltersFrame), 1, 2)
        layout.addWidget(self.ui.historyDateToEdit, 1, 3)
        layout.addWidget(QLabel("Поиск:", self.ui.historyFiltersFrame), 1, 4)
        layout.addWidget(self.ui.historySearchLine, 1, 5)
        layout.addWidget(self.ui.historyResetFiltersButton, 0, 6, 2, 1)
        layout.addWidget(self.ui.historyResultCountLabel, 0, 7, 2, 1)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(5, 2)
        layout.setColumnStretch(7, 1)

        self.ui.historyCustomerFilterLine.textChanged.connect(self.updateHistoryTable)
        self.ui.historyEventFilterCombo.currentIndexChanged.connect(self.updateHistoryTable)
        self.ui.historyPeriodFilterCombo.currentIndexChanged.connect(
            self._on_history_period_changed
        )
        self.ui.historyDateFromEdit.dateChanged.connect(self._on_history_custom_date_changed)
        self.ui.historyDateToEdit.dateChanged.connect(self._on_history_custom_date_changed)
        self.ui.historySearchLine.textChanged.connect(self.updateHistoryTable)
        self.ui.historyResetFiltersButton.clicked.connect(self._reset_history_filters)
        self._on_history_period_changed()

    @staticmethod
    def _history_period_bounds(period_key: str, *, today: date | None = None):
        current_day = today or date.today()
        if period_key == "today":
            return current_day, current_day
        if period_key == "last_7_days":
            return current_day - timedelta(days=6), current_day
        if period_key == "last_30_days":
            return current_day - timedelta(days=29), current_day
        if period_key == "current_month":
            return current_day.replace(day=1), current_day
        return None, None

    def _history_selected_period(self) -> str:
        return str(self.ui.historyPeriodFilterCombo.currentData() or "all")

    def _set_history_date_controls_enabled(self, enabled: bool):
        self.ui.historyDateFromEdit.setEnabled(enabled)
        self.ui.historyDateToEdit.setEnabled(enabled)

    def _on_history_period_changed(self, *_args):
        period_key = self._history_selected_period()
        if period_key == "all":
            self._set_history_date_controls_enabled(False)
            self.updateHistoryTable()
            return

        self._set_history_date_controls_enabled(True)
        if period_key != "custom":
            date_from, date_to = self._history_period_bounds(period_key)
            if date_from is not None and date_to is not None:
                blocker_from = QSignalBlocker(self.ui.historyDateFromEdit)
                blocker_to = QSignalBlocker(self.ui.historyDateToEdit)
                self.ui.historyDateFromEdit.setDate(
                    QDate(date_from.year, date_from.month, date_from.day)
                )
                self.ui.historyDateToEdit.setDate(
                    QDate(date_to.year, date_to.month, date_to.day)
                )
                del blocker_from, blocker_to
        self.updateHistoryTable()

    def _on_history_custom_date_changed(self, *_args):
        if self._history_selected_period() != "custom":
            blocker = QSignalBlocker(self.ui.historyPeriodFilterCombo)
            self.ui.historyPeriodFilterCombo.setCurrentIndex(
                self.ui.historyPeriodFilterCombo.findData("custom")
            )
            del blocker
        self.updateHistoryTable()

    def _reset_history_filters(self, *_args):
        blocker_customer = QSignalBlocker(self.ui.historyCustomerFilterLine)
        blocker_event = QSignalBlocker(self.ui.historyEventFilterCombo)
        blocker_period = QSignalBlocker(self.ui.historyPeriodFilterCombo)
        blocker_search = QSignalBlocker(self.ui.historySearchLine)
        self.ui.historyCustomerFilterLine.clear()
        self.ui.historyEventFilterCombo.setCurrentIndex(0)
        self.ui.historyPeriodFilterCombo.setCurrentIndex(0)
        self.ui.historySearchLine.clear()
        del blocker_customer, blocker_event, blocker_period, blocker_search
        self._on_history_period_changed()

    def _history_filter_values(self) -> dict:
        period_key = self._history_selected_period()
        date_from = ""
        date_to = ""
        if period_key != "all":
            start_date = self.ui.historyDateFromEdit.date()
            end_date = self.ui.historyDateToEdit.date()
            if start_date > end_date:
                start_date, end_date = end_date, start_date
            date_from = start_date.toString("yyyy-MM-dd")
            date_to = end_date.toString("yyyy-MM-dd")

        return {
            "customer_query": self.ui.historyCustomerFilterLine.text().strip(),
            "event_type": str(self.ui.historyEventFilterCombo.currentData() or ""),
            "date_from": date_from,
            "date_to": date_to,
            "search_text": self.ui.historySearchLine.text().strip(),
        }

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
        configure_table_autosize(table, text_columns={3: 180, 4: 180, 7: 260, 8: 180})

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive)
        table.setColumnWidth(3, 180)
        table.setColumnWidth(4, 180)
        table.setColumnWidth(7, 260)
        table.setColumnWidth(8, 180)

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

    def _open_history_remote_url(self, remote_url: str):
        value = str(remote_url or "").strip()
        if not value:
            return
        QDesktopServices.openUrl(QUrl(value))

    def _copy_history_remote_url(self, remote_url: str):
        value = str(remote_url or "").strip()
        if not value:
            return
        QApplication.clipboard().setText(value)
        if self.statusBar() is not None:
            self.statusBar().showMessage("Ссылка скопирована", 2500)

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
        remote_url = str(meta.get("remote_url", "") or "").strip()
        event_type = str(meta.get("event_type", "") or "").strip().lower()

        if row >= 0:
            table.selectRow(row)

        menu = QMenu(self)
        refresh_action = menu.addAction("Обновить")

        repeat_action = None
        open_file_action = None
        open_folder_action = None
        copy_path_action = None
        open_link_action = None
        copy_link_action = None
        delete_action = None

        if row >= 0:
            menu.addSeparator()
            if event_type == "docx":
                repeat_action = menu.addAction("Повторить создание КП")
            if file_path:
                open_file_action = menu.addAction("Открыть файл")
                open_folder_action = menu.addAction("Открыть папку файла")
                copy_path_action = menu.addAction("Скопировать путь")
            if remote_url:
                open_link_action = menu.addAction("Открыть ссылку Google Drive")
                copy_link_action = menu.addAction("Скопировать ссылку")
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
        if action == open_link_action:
            self._open_history_remote_url(remote_url)
            return
        if action == copy_link_action:
            self._copy_history_remote_url(remote_url)
            return
        if action == delete_action:
            self._delete_history_event(row)

    def updateHistoryTable(self, *_args):
        if not hasattr(self.ui, "historyTable"):
            return

        try:
            rows = self.history_service.get_history(
                limit=1000,
                **self._history_filter_values(),
            )
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
                remote_url,
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
            remote_url_text = str(remote_url or "").strip()
            link_text = "Открыть" if remote_url_text else "—"
            meta = {
                "id": int(_entry_id),
                "event_type": str(event_type or "").strip().lower(),
                "file_path": file_path_text,
                "remote_url": remote_url_text,
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
                link_text,
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
                if col_idx == self.HISTORY_LINK_COLUMN and remote_url_text:
                    item.setData(Qt.ItemDataRole.UserRole, remote_url_text)
                    item.setToolTip(remote_url_text)
                table.setItem(row_idx, col_idx, item)

        del blocker
        self.ui.historyResultCountLabel.setText(f"Найдено: {len(rows)}")
        resize_table_to_contents(table, text_columns={3: 180, 4: 180, 7: 260, 8: 180})

    def _openHistoryFile(self, item):
        if item is None or not hasattr(self.ui, "historyTable"):
            return

        row = item.row()
        meta = self._history_row_meta(row)
        remote_url = str(meta.get("remote_url", "") or "").strip()
        if item.column() == self.HISTORY_LINK_COLUMN and remote_url:
            self._open_history_remote_url(remote_url)
            return
        file_path = str(meta.get("file_path", "") or "").strip()
        self._open_history_file_path(file_path)
