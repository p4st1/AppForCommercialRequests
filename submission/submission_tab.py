from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSignalBlocker, QThread, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.table_autosize import configure_table_autosize, resize_table_to_contents
from config import Config
from services.excel_processor import ExcelProcessor
from tools import DatabaseTools as Tool

from .submission_playwright import SubmissionPlaywright
from .submission_service import (
    FIELD_ORDER,
    SUBMISSION_HEADERS,
    SubmissionHeader,
    SubmissionPayload,
    SubmissionRow,
    SubmissionService,
    SubmissionValidationIssue,
)


class SubmitSubmissionWorker(QThread):
    ready = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        *,
        cookies: dict[str, str],
        payload: SubmissionPayload,
        import_file_path: str,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._cookies = dict(cookies)
        self._payload = payload
        self._import_file_path = str(import_file_path)

    def run(self) -> None:
        try:
            submitter = SubmissionPlaywright(
                self._cookies,
                headless=False,
                allow_submit=False,
                timeout_ms=90_000,
            )
            result = submitter.submit(
                self._payload,
                import_file_path=self._import_file_path,
                final_submit=False,
                on_manual_confirmation_ready=self.ready.emit,
            )
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


class SubmissionTabMixin:
    SUBMISSION_HEADERS = SUBMISSION_HEADERS
    SUBMISSION_ERROR_COLOR = QColor(255, 214, 214)
    SUBMISSION_WARNING_COLOR = QColor(255, 245, 204)
    SUBMISSION_STATUS_STYLES = {
        "ready": "color: #1f8f3a; font-weight: 700;",
        "warning": "color: #b7791f; font-weight: 700;",
        "error": "color: #c62828; font-weight: 700;",
        "idle": "color: #344054; font-weight: 700;",
    }

    def init_submission_tab(self) -> None:
        self.submission_service = SubmissionService()
        self._submission_loaded_kp_rows: list[SubmissionRow] = []
        self._submission_loaded_kp_path = ""
        self._submission_trade_id = ""
        self._submission_lot_id = ""
        self._submission_submit_worker: SubmitSubmissionWorker | None = None
        self._updating_submission_table = False
        self._ensure_submission_tab()

    def _ensure_submission_tab(self) -> None:
        if isinstance(getattr(self, "submission_table", None), QTableWidget):
            return

        tabs = getattr(getattr(self, "ui", None), "tabWidget", None)
        if not isinstance(tabs, QTabWidget):
            raise RuntimeError("Не найден tabWidget для вкладки Подача заявки")

        tab = QWidget(tabs)
        tab.setObjectName("submissionTab")
        root_layout = QVBoxLayout(tab)
        root_layout.setSpacing(8)
        root_layout.setContentsMargins(8, 8, 8, 8)

        header_layout = QGridLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setHorizontalSpacing(12)
        header_layout.setVerticalSpacing(6)

        self.submission_number_input = QLineEdit(tab)
        self.submission_number_input.setObjectName("submission_number_input")
        self.submission_title_input = QLineEdit(tab)
        self.submission_title_input.setObjectName("submission_title_input")
        self.submission_customer_input = QLineEdit(tab)
        self.submission_customer_input.setObjectName("submission_customer_input")
        self.submission_currency_input = QLineEdit(tab)
        self.submission_currency_input.setObjectName("submission_currency_input")
        self.submission_offer_validity_input = QLineEdit(tab)
        self.submission_offer_validity_input.setObjectName("submission_offer_validity_input")
        self.submission_offer_validity_input.setPlaceholderText("дд.мм.гггг")
        self.submission_delivery_order_input = QLineEdit(tab)
        self.submission_delivery_order_input.setObjectName("submission_delivery_order_input")
        self.submission_payment_terms_input = QLineEdit(tab)
        self.submission_payment_terms_input.setObjectName("submission_payment_terms_input")
        self.submission_total_label = QLabel("0,00", tab)
        self.submission_total_label.setObjectName("submission_total_label")
        self.submission_status_label = QLabel("Черновик", tab)
        self.submission_status_label.setObjectName("submission_status_label")
        self.submission_status_label.setStyleSheet(self.SUBMISSION_STATUS_STYLES["idle"])

        header_items = (
            ("Номер заявки:", self.submission_number_input, 0, 0),
            ("Название заявки:", self.submission_title_input, 0, 2),
            ("Заказчик:", self.submission_customer_input, 1, 0),
            ("Валюта:", self.submission_currency_input, 1, 2),
            ("Срок действия КП:", self.submission_offer_validity_input, 2, 0),
            ("Общая сумма:", self.submission_total_label, 2, 2),
            ("Порядок доставки:", self.submission_delivery_order_input, 3, 0),
            ("Условие оплаты:", self.submission_payment_terms_input, 3, 2),
            ("Статус:", self.submission_status_label, 4, 0),
        )
        for caption, widget, row, column in header_items:
            caption_label = QLabel(caption, tab)
            caption_label.setStyleSheet("color: #667085;")
            header_layout.addWidget(caption_label, row, column)
            header_layout.addWidget(widget, row, column + 1)

        self.submission_table = QTableWidget(tab)
        self.submission_table.setObjectName("submission_table")
        self._setup_submission_table(self.submission_table)

        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        self.btn_load_submission_kp = QPushButton("Загрузить КП", tab)
        self.btn_load_submission_kp.setObjectName("btn_load_submission_kp")
        self.btn_fill_submission_from_kp = QPushButton("Заполнить из КП", tab)
        self.btn_fill_submission_from_kp.setObjectName("btn_fill_submission_from_kp")
        self.btn_save_submission = QPushButton("Сохранить заявку", tab)
        self.btn_save_submission.setObjectName("btn_save_submission")
        self.btn_submit_submission = QPushButton("Подать заявку", tab)
        self.btn_submit_submission.setObjectName("btn_submit_submission")

        actions_layout.addWidget(self.btn_load_submission_kp)
        actions_layout.addWidget(self.btn_fill_submission_from_kp)
        actions_layout.addStretch(1)
        actions_layout.addWidget(self.btn_save_submission)
        actions_layout.addWidget(self.btn_submit_submission)

        root_layout.addLayout(header_layout)
        root_layout.addWidget(self.submission_table)
        root_layout.addLayout(actions_layout)

        self.submission_tab = tab
        self.ui.submission_tab = tab
        self.ui.submission_offer_validity_input = self.submission_offer_validity_input
        self.ui.submission_delivery_order_input = self.submission_delivery_order_input
        self.ui.submission_payment_terms_input = self.submission_payment_terms_input
        self.ui.submission_table = self.submission_table
        self.ui.btn_load_submission_kp = self.btn_load_submission_kp
        self.ui.btn_fill_submission_from_kp = self.btn_fill_submission_from_kp
        self.ui.btn_save_submission = self.btn_save_submission
        self.ui.btn_submit_submission = self.btn_submit_submission

        tabs.addTab(tab, "Подача заявки")

        self.btn_load_submission_kp.clicked.connect(self.load_submission_kp)
        self.btn_fill_submission_from_kp.clicked.connect(self.fill_submission_from_kp)
        self.btn_save_submission.clicked.connect(self.save_submission)
        self.btn_submit_submission.clicked.connect(self.submit_submission)
        self.submission_table.itemChanged.connect(self._on_submission_item_changed)
        for input_widget in (
            self.submission_number_input,
            self.submission_title_input,
            self.submission_customer_input,
            self.submission_currency_input,
            self.submission_offer_validity_input,
            self.submission_delivery_order_input,
            self.submission_payment_terms_input,
        ):
            input_widget.textChanged.connect(self._set_submission_dirty_status)

    def _setup_submission_table(self, table: QTableWidget) -> None:
        table.setColumnCount(len(self.SUBMISSION_HEADERS))
        table.setHorizontalHeaderLabels(self.SUBMISSION_HEADERS)
        table.setRowCount(10)
        table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(
            """
QTableWidget::item:selected {
    background-color: #eaf3ff;
    color: #101828;
}

QTableWidget::item:selected:!active {
    background-color: #f2f4f7;
    color: #101828;
}
"""
        )
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        configure_table_autosize(
            table,
            text_columns={0: 260, 6: 180, 7: 320, 8: 160, 9: 140},
        )

    def _set_submission_status(self, status: str, text: str) -> None:
        label = getattr(self, "submission_status_label", None)
        if isinstance(label, QLabel):
            label.setText(text)
            label.setStyleSheet(
                self.SUBMISSION_STATUS_STYLES.get(status, self.SUBMISSION_STATUS_STYLES["idle"])
            )

    def _set_submission_dirty_status(self, *_args: Any) -> None:
        self._set_submission_status("idle", "Черновик")

    def _submission_item_text(self, row: int, col: int) -> str:
        item = self.submission_table.item(row, col)
        return item.text().strip() if item is not None else ""

    def _ensure_submission_item(self, row: int, col: int) -> QTableWidgetItem:
        item = self.submission_table.item(row, col)
        if item is None:
            item = QTableWidgetItem("")
            self.submission_table.setItem(row, col, item)
        return item

    def _submission_row_has_content(self, row: int) -> bool:
        return any(
            self._submission_item_text(row, col)
            for col in range(self.submission_table.columnCount())
        )

    def _submission_row_has_zero_price(self, row: int) -> bool:
        price_text = self._submission_item_text(row, 3)
        total_text = self._submission_item_text(row, 4)
        price = self.submission_service.parse_number(price_text)
        total = self.submission_service.parse_number(total_text)
        if price is not None and abs(price) < 1e-9:
            return True
        return not price_text and total is not None and abs(total) < 1e-9

    def _on_submission_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_submission_table or item is None:
            return
        if item.column() in {1, 3, 4}:
            self._recalculate_submission_row(item.row())
        if item.row() == self.submission_table.rowCount() - 1 and self._submission_row_has_content(item.row()):
            self.submission_table.insertRow(self.submission_table.rowCount())
        self._update_submission_total()
        self._set_submission_dirty_status()

    def _recalculate_submission_row(self, row: int) -> None:
        qty = self.submission_service.parse_number(self._submission_item_text(row, 1))
        unit_price = self.submission_service.parse_number(self._submission_item_text(row, 3))
        if qty is None or unit_price is None:
            return
        total_item = self._ensure_submission_item(row, 4)
        self._updating_submission_table = True
        try:
            total_item.setText(self.submission_service.format_money(qty * unit_price))
        finally:
            self._updating_submission_table = False

    def _submission_rows_from_table(self) -> list[SubmissionRow]:
        rows: list[SubmissionRow] = []
        for row_index in range(self.submission_table.rowCount()):
            cells = [
                self._submission_item_text(row_index, col)
                for col in range(self.submission_table.columnCount())
            ]
            row = self.submission_service.build_row_from_cells(cells)
            if row.has_content():
                rows.append(row)
        return rows

    def _submission_currency_from_table(self) -> str:
        table = getattr(self, "submission_table", None)
        if table is None:
            return ""

        priority_values: list[str] = []
        header_values: list[str] = []
        all_values: list[str] = []
        priority_columns = {3, 4}
        for col_index in range(table.columnCount()):
            header_item = (
                table.horizontalHeaderItem(col_index)
                if callable(getattr(table, "horizontalHeaderItem", None))
                else None
            )
            if header_item is not None:
                header_text = str(header_item.text() or "").strip()
                if header_text:
                    header_values.append(header_text)
        for row_index in range(table.rowCount()):
            for col_index in range(table.columnCount()):
                text = self._submission_item_text(row_index, col_index)
                if not text:
                    continue
                if col_index in priority_columns:
                    priority_values.append(text)
                else:
                    all_values.append(text)

        return self.submission_service.detect_currency_from_values(
            priority_values + header_values + all_values
        )

    def _submission_header_from_inputs(self) -> SubmissionHeader:
        currency = (
            self.submission_currency_input.text().strip()
            or self._submission_currency_from_table()
        )
        return SubmissionHeader(
            trade_id=str(getattr(self, "_submission_trade_id", "") or "").strip(),
            number=self.submission_number_input.text().strip(),
            title=self.submission_title_input.text().strip(),
            customer=self.submission_customer_input.text().strip(),
            currency=currency,
            offer_validity_period=self.submission_offer_validity_input.text().strip(),
            delivery_order=self.submission_delivery_order_input.text().strip(),
            payment_terms=self.submission_payment_terms_input.text().strip(),
            lot_id=str(getattr(self, "_submission_lot_id", "") or "").strip(),
        )

    def _submission_payload(self) -> SubmissionPayload:
        return self.submission_service.prepare_payload(
            self._submission_header_from_inputs(),
            self._submission_rows_from_table(),
        )

    def _submission_import_file_path(self) -> Path:
        path_text = str(getattr(self, "_submission_loaded_kp_path", "") or "").strip()
        if not path_text:
            raise ValueError(
                "Не найден Excel файл для импорта. "
                "Сначала выгрузите заявку кнопкой 'Экспорт' из таблицы приема заявок."
            )

        path = Path(path_text).expanduser()
        if path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError(
                "Для подачи через площадку нужен Excel файл, полученный кнопкой 'Экспорт'."
            )
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Excel файл для импорта не найден: {path}")
        return path.resolve()

    @staticmethod
    def _submission_source_rows_for_excel(payload: SubmissionPayload) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for row in payload.rows:
            rows.append(
                {
                    "name": row.name,
                    "qty": row.qty,
                    "unit": row.unit,
                    "price": row.unit_price,
                    "unit_price": row.unit_price,
                    "total": row.total,
                    "delivery_time": row.delivery_time,
                    "manufacturer": row.manufacturer,
                    "technical_characteristics": row.technical,
                    "supplier_status": row.supplier_status,
                    "warranty": row.warranty,
                }
            )
        return rows

    def _prepare_submission_import_file(self, payload: SubmissionPayload) -> str:
        import_path = self._submission_import_file_path()
        processor = ExcelProcessor()
        try:
            if processor.can_fill_exported_excel(str(import_path)):
                processor.fill_exported_excel(
                    str(import_path),
                    self._submission_source_rows_for_excel(payload),
                    strict_row_count=False,
                )
        except Exception as exc:
            Tool.write_log(f"Не удалось обновить Excel перед импортом заявки: {exc}")
            raise
        return str(import_path)

    def _update_submission_total(self) -> None:
        payload = self._submission_payload()
        self.submission_total_label.setText(
            self.submission_service.format_money(payload.header.total)
        )

    def _set_submission_rows(self, rows: list[SubmissionRow]) -> None:
        table = self.submission_table
        self._updating_submission_table = True
        table.setUpdatesEnabled(False)
        try:
            table.clearContents()
            row_count = max(len(rows) + 1, 10)
            table.setRowCount(row_count)
            for row_index, row in enumerate(rows):
                unit_price = self.submission_service.parse_number(row.unit_price)
                total = self.submission_service.parse_number(row.total)
                zero_price_row = (
                    unit_price == 0.0
                    or (unit_price is None and total == 0.0)
                )
                for col_index, value in enumerate(row.to_cells()):
                    if zero_price_row and col_index in {8, 9}:
                        text = ""
                    elif col_index in {3, 4}:
                        text = self.submission_service.format_money(value)
                    else:
                        text = "" if value is None else str(value)
                    item = QTableWidgetItem(text)
                    if col_index in {1, 3, 4}:
                        item.setTextAlignment(
                            int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        )
                    table.setItem(row_index, col_index, item)
        finally:
            table.setUpdatesEnabled(True)
            self._updating_submission_table = False

        resize_table_to_contents(table)
        self._update_submission_total()
        self._set_submission_status("idle", "Черновик")

    def load_submission_kp(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите КП для подачи заявки",
            "",
            "КП (*.docx *.xlsx *.xlsm *.csv)",
        )
        if not file_path:
            return

        try:
            rows = self.submission_service.load_kp(file_path)
        except Exception as exc:
            Tool.write_log(f"Ошибка загрузки КП для подачи заявки: {exc}")
            QMessageBox.warning(self, "Подача заявки", f"Не удалось загрузить КП:\n{exc}")
            return

        self._submission_loaded_kp_rows = rows
        self._submission_loaded_kp_path = file_path
        self._submission_trade_id = ""
        self._submission_lot_id = ""
        self._set_submission_currency_from_file(file_path)
        self._set_submission_status("idle", f"КП загружено: {len(rows)} поз.")
        status_bar = self.statusBar() if callable(getattr(self, "statusBar", None)) else None
        if status_bar is not None:
            status_bar.showMessage("КП загружено для подачи заявки", 3_000)

    def fill_submission_from_kp(self) -> None:
        if not self._submission_loaded_kp_rows:
            QMessageBox.warning(self, "Подача заявки", "Сначала загрузите КП")
            return
        self._set_submission_rows(self._submission_loaded_kp_rows)

    def activate_submission_tab(self) -> None:
        self._ensure_submission_tab()
        tabs = getattr(getattr(self, "ui", None), "tabWidget", None)
        tab = getattr(self, "submission_tab", None)
        if isinstance(tabs, QTabWidget) and tab is not None:
            index = tabs.indexOf(tab)
            if index >= 0:
                tabs.setCurrentIndex(index)

    def load_submission_export_file(self, file_path: str | Path) -> int:
        self._ensure_submission_tab()
        path = Path(file_path).expanduser()
        rows = self.submission_service.load_kp(path)
        self._submission_loaded_kp_rows = rows
        self._submission_loaded_kp_path = str(path)
        self._submission_trade_id = ""
        self._submission_lot_id = self._submission_lot_id_from_export_path(path)
        self._set_submission_currency_from_file(path)
        self._set_submission_rows(rows)
        self._set_submission_status("idle", f"Загружено из экспорта: {len(rows)} поз.")
        self.activate_submission_tab()

        status_bar = self.statusBar() if callable(getattr(self, "statusBar", None)) else None
        if status_bar is not None:
            status_bar.showMessage("Экспорт загружен во вкладку Подача заявки", 5_000)
        return len(rows)

    def _set_submission_currency_from_file(self, file_path: str | Path) -> None:
        currency = self.submission_service.detect_currency(file_path)
        self._submission_export_detected_currency = currency
        if currency:
            blocker = QSignalBlocker(self.submission_currency_input)
            try:
                self.submission_currency_input.setText(currency)
            finally:
                del blocker

    def _apply_submission_row_defaults(self, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        field_values = {
            "supplier_status": str(metadata.get("supplier_status", "") or "").strip(),
            "warranty": str(
                metadata.get("warranty", "")
                or metadata.get("guarantee", "")
                or ""
            ).strip(),
        }
        field_values = {key: value for key, value in field_values.items() if value}

        column_by_field = {field: index for index, field in enumerate(FIELD_ORDER)}
        columns_to_clear_on_zero = (
            column_by_field.get("supplier_status"),
            column_by_field.get("warranty"),
        )
        if not field_values and not any(
            column is not None for column in columns_to_clear_on_zero
        ):
            return

        self._updating_submission_table = True
        blocker = QSignalBlocker(self.submission_table)
        try:
            for row in range(self.submission_table.rowCount()):
                if not self._submission_row_has_content(row):
                    continue
                if self._submission_row_has_zero_price(row):
                    for column in columns_to_clear_on_zero:
                        if column is None:
                            continue
                        item = self.submission_table.item(row, column)
                        if item is not None:
                            item.setText("")
                    continue
                for field, value in field_values.items():
                    column = column_by_field.get(field)
                    if column is None or self._submission_item_text(row, column):
                        continue
                    self._ensure_submission_item(row, column).setText(value)
        finally:
            del blocker
            self._updating_submission_table = False
        self._update_submission_total()

    def apply_submission_export_metadata(self, metadata: dict[str, Any] | None) -> None:
        if not isinstance(metadata, dict):
            return

        self._ensure_submission_tab()
        metadata = dict(metadata)
        detected_currency = str(
            getattr(self, "_submission_export_detected_currency", "") or ""
        ).strip()
        metadata_currency = (
            self.submission_service.normalize_currency_code(metadata.get("currency"))
            or str(metadata.get("currency", "") or "").strip()
        )
        table_currency = self._submission_currency_from_table()
        if metadata_currency:
            metadata["currency"] = metadata_currency
        elif table_currency:
            metadata["currency"] = table_currency
        elif detected_currency:
            metadata["currency"] = detected_currency
        lot_id = str(metadata.get("lot_id", "") or "").strip()
        if lot_id:
            self._submission_lot_id = lot_id
        trade_id = str(
            metadata.get("trade_id", "") or metadata.get("id", "") or ""
        ).strip()
        if trade_id:
            self._submission_trade_id = trade_id
        field_map = (
            ("number", self.submission_number_input),
            ("title", self.submission_title_input),
            ("customer", self.submission_customer_input),
            ("currency", self.submission_currency_input),
            ("offer_validity_period", self.submission_offer_validity_input),
            ("delivery_order", self.submission_delivery_order_input),
            ("payment_terms", self.submission_payment_terms_input),
        )
        blockers: list[QSignalBlocker] = []
        try:
            for key, input_widget in field_map:
                value = str(metadata.get(key, "") or "").strip()
                if key == "currency":
                    value = self.submission_service.normalize_currency_code(value) or value
                if not value:
                    continue
                blockers.append(QSignalBlocker(input_widget))
                input_widget.setText(value)
        finally:
            blockers.clear()
        self._apply_submission_row_defaults(metadata)

    @staticmethod
    def _submission_lot_id_from_export_path(path: str | Path) -> str:
        name = Path(path).name
        match = re.match(r"submission_(\d+)_\d{8}_\d{6}\.", name)
        return match.group(1) if match is not None else ""

    def _clear_submission_highlight(self) -> None:
        for row in range(self.submission_table.rowCount()):
            for col in range(self.submission_table.columnCount()):
                item = self.submission_table.item(row, col)
                if item is not None:
                    item.setBackground(QColor())

    def _clear_submission_table_selection(self) -> None:
        table = getattr(self, "submission_table", None)
        if table is None:
            return
        clear_selection = getattr(table, "clearSelection", None)
        if callable(clear_selection):
            try:
                clear_selection()
            except Exception:
                pass
        selection_model_getter = getattr(table, "selectionModel", None)
        if callable(selection_model_getter):
            try:
                selection_model = selection_model_getter()
                clear_model = getattr(selection_model, "clear", None)
                if callable(clear_model):
                    clear_model()
            except Exception:
                pass
        set_current_item = getattr(table, "setCurrentItem", None)
        if callable(set_current_item):
            try:
                set_current_item(None)
            except Exception:
                pass

    def _highlight_submission_issues(self, issues: list[SubmissionValidationIssue]) -> None:
        self._clear_submission_highlight()
        row_severity: dict[int, str] = {}
        for issue in issues:
            if issue.row is None:
                continue
            if issue.severity == "error":
                row_severity[int(issue.row)] = "error"
            elif row_severity.get(int(issue.row)) != "error":
                row_severity[int(issue.row)] = "warning"

        for row, severity in row_severity.items():
            color = (
                self.SUBMISSION_ERROR_COLOR
                if severity == "error"
                else self.SUBMISSION_WARNING_COLOR
            )
            for col in range(self.submission_table.columnCount()):
                item = self._ensure_submission_item(row, col)
                item.setBackground(color)
        self._clear_submission_table_selection()

    @staticmethod
    def _validation_message(issues: list[SubmissionValidationIssue]) -> str:
        errors = [issue.message for issue in issues if issue.severity == "error"]
        warnings = [issue.message for issue in issues if issue.severity == "warning"]
        lines: list[str] = []
        if errors:
            lines.append("Ошибки:")
            lines.extend(f"- {message}" for message in errors[:20])
            if len(errors) > 20:
                lines.append(f"... и ещё {len(errors) - 20}")
        if warnings:
            if lines:
                lines.append("")
            lines.append("Предупреждения:")
            lines.extend(f"- {message}" for message in warnings[:20])
            if len(warnings) > 20:
                lines.append(f"... и ещё {len(warnings) - 20}")
        return "\n".join(lines)

    @staticmethod
    def _developer_skip_table_fill_errors_enabled() -> bool:
        return bool(Config.settings.get("developer_skip_table_fill_errors", False))

    def _submission_has_blocking_errors(
        self,
        issues: list[SubmissionValidationIssue],
    ) -> bool:
        return self.submission_service.has_errors(issues) and not (
            self._developer_skip_table_fill_errors_enabled()
        )

    def check_submission_data(self, *, show_success: bool = True) -> list[SubmissionValidationIssue]:
        rows = self._submission_rows_from_table()
        header = self._submission_header_from_inputs()
        issues = self.submission_service.validate(header, rows)
        self._highlight_submission_issues(issues)
        self._update_submission_total()

        if self.submission_service.has_errors(issues):
            if self._developer_skip_table_fill_errors_enabled():
                message = self._validation_message(issues)
                Tool.write_log(
                    "Ошибки проверки заявки пропущены настройкой разработчика:\n"
                    f"{message}"
                )
                self._set_submission_status("warning", "Ошибки пропущены")
                if show_success:
                    QMessageBox.warning(
                        self,
                        "Проверка заявки",
                        f"{message}\n\n"
                        "Ошибки пропущены настройкой разработчика.",
                    )
                return issues
            self._set_submission_status("error", "Есть ошибки")
            QMessageBox.warning(self, "Проверка заявки", self._validation_message(issues))
            return issues

        if issues:
            self._set_submission_status("warning", "Есть предупреждения")
            QMessageBox.information(self, "Проверка заявки", self._validation_message(issues))
            return issues

        self._set_submission_status("ready", "Готово")
        if show_success:
            QMessageBox.information(self, "Проверка заявки", "Данные готовы к подаче")
        return issues

    def _submission_save_dir(self) -> Path:
        base_dir_raw = str(Config.config.get("pathToSaveExcel", "") or "").strip()
        base_dir = Path(base_dir_raw).expanduser() if base_dir_raw else Path.home() / "Documents"
        return base_dir / "submissions"

    def save_submission(self) -> None:
        payload = self._submission_payload()
        issues = self.check_submission_data(show_success=False)
        if self._submission_has_blocking_errors(issues):
            return
        try:
            saved_path = self.submission_service.save_payload(
                payload,
                self._submission_save_dir(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Сохранить заявку", f"Не удалось сохранить заявку:\n{exc}")
            return
        self._set_submission_status("ready", "Сохранено")
        status_bar = self.statusBar() if callable(getattr(self, "statusBar", None)) else None
        if status_bar is not None:
            status_bar.showMessage(f"Заявка сохранена: {saved_path}", 5_000)

    def _extract_submission_cookies(self, payload: Any) -> dict[str, str]:
        if not isinstance(payload, dict):
            return {}
        candidates = [
            payload.get("cookies"),
            payload.get("config", {}).get("cookies")
            if isinstance(payload.get("config"), dict)
            else None,
        ]
        for candidate in candidates:
            if isinstance(candidate, dict):
                cookies = {
                    str(key).strip(): str(value).strip()
                    for key, value in candidate.items()
                    if str(key).strip() and str(value).strip()
                }
                if cookies:
                    return cookies
        return {}

    def _load_submission_cookies(self) -> dict[str, str]:
        cookies = self._extract_submission_cookies({"cookies": Config.config.get("cookies")})
        if cookies:
            return cookies

        candidate_paths = Tool.config_candidate_paths()

        seen: set[Path] = set()
        for path in candidate_paths:
            resolved = path.expanduser()
            if resolved in seen or not resolved.exists():
                continue
            seen.add(resolved)
            try:
                payload = json.loads(resolved.read_text(encoding="utf-8"))
            except Exception:
                continue
            cookies = self._extract_submission_cookies(payload)
            if cookies:
                return cookies
        raise ValueError("Не найдены cookies для авторизации")

    def _confirm_submission_dialog(self) -> bool:
        message_box = QMessageBox(self)
        icon_enum = getattr(QMessageBox, "Icon", None)
        question_icon = (
            getattr(icon_enum, "Question", None)
            if icon_enum is not None
            else getattr(QMessageBox, "Question", None)
        )
        if question_icon is not None:
            message_box.setIcon(question_icon)
        message_box.setWindowTitle("Подтверждение подачи")
        message_box.setText(
            "Открыть сайт и подготовить заявку к ручной подаче?\n"
            "Программа загрузит таблицу и срок действия КП, но финальную кнопку на сайте не нажмет.\n\n"
            "Перед ручной подачей обязательно проверьте:\n"
            "- цены\n"
            "- сроки\n"
            "- характеристики\n"
            "- производителя\n\n"
            "Ответственность за проверку несет пользователь."
        )
        role_enum = getattr(QMessageBox, "ButtonRole", QMessageBox)
        accept_role = getattr(role_enum, "AcceptRole", 0)
        reject_role = getattr(role_enum, "RejectRole", accept_role)
        yes_button = message_box.addButton("Да", accept_role)
        cancel_button = message_box.addButton("Отмена", reject_role)
        message_box.setDefaultButton(cancel_button)
        message_box.setEscapeButton(cancel_button)
        message_box.exec()
        return message_box.clickedButton() == yes_button

    def submit_submission(self) -> None:
        if self._submission_submit_worker is not None and self._submission_submit_worker.isRunning():
            return

        issues = self.check_submission_data(show_success=False)
        if self._submission_has_blocking_errors(issues):
            return
        if not self._confirm_submission_dialog():
            return

        payload = self._submission_payload()
        try:
            import_file_path = self._prepare_submission_import_file(payload)
        except Exception as exc:
            QMessageBox.warning(self, "Подача заявки", str(exc))
            return

        try:
            cookies = self._load_submission_cookies()
        except Exception as exc:
            QMessageBox.warning(self, "Подача заявки", str(exc))
            return

        self._set_submission_loading_state(is_loading=True)
        worker = SubmitSubmissionWorker(
            cookies=cookies,
            payload=payload,
            import_file_path=import_file_path,
            parent=self,
        )
        worker.ready.connect(self._on_submission_ready_for_manual_confirmation)
        worker.finished.connect(self._on_submission_finished)
        worker.error.connect(self._on_submission_error)
        self._submission_submit_worker = worker
        worker.start()

    def _set_submission_loading_state(self, *, is_loading: bool) -> None:
        for button in (
            getattr(self, "btn_load_submission_kp", None),
            getattr(self, "btn_fill_submission_from_kp", None),
            getattr(self, "btn_save_submission", None),
        ):
            if isinstance(button, QPushButton):
                button.setEnabled(not is_loading)
        if isinstance(getattr(self, "btn_submit_submission", None), QPushButton):
            self.btn_submit_submission.setEnabled(not is_loading)
            self.btn_submit_submission.setText("Подготовка..." if is_loading else "Подать заявку")
        if is_loading:
            self._set_submission_status("idle", "Подготовка...")

    def _finish_submission_worker(self) -> None:
        self._set_submission_loading_state(is_loading=False)
        worker = self._submission_submit_worker
        self._submission_submit_worker = None
        if worker is not None:
            worker.deleteLater()

    def _on_submission_ready_for_manual_confirmation(self, message: str) -> None:
        info_text = str(message or "").strip()
        Tool.write_log(f"Заявка подготовлена к ручной подаче: {info_text}")
        self._set_submission_status("warning", "Ожидание пользователя")
        status_bar = self.statusBar() if callable(getattr(self, "statusBar", None)) else None
        if status_bar is not None:
            status_bar.showMessage(
                info_text or "Таблица загружена на сайт. Ожидается ручная подача.",
                10_000,
            )

    def _on_submission_finished(self, message: str) -> None:
        Tool.write_log(f"Подача заявки завершена: {message}")
        message_text = str(message or "")
        status_text = "Подано" if "подан" in message_text.casefold() else "Загружено"
        self._set_submission_status("ready", status_text)
        self._finish_submission_worker()
        QMessageBox.information(self, "Подача заявки", message)

    def _on_submission_error(self, message: str) -> None:
        error_text = str(message or "Неизвестная ошибка")
        Tool.write_log(f"Ошибка подачи заявки: {error_text}")
        self._set_submission_status("error", "Ошибка подачи")
        self._finish_submission_worker()
        QMessageBox.warning(self, "Подача заявки", error_text)
