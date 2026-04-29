from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from PySide6.QtCore import QSettings, QThread, Signal, QTimer, Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtUiTools import loadUiType
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
)

from app.ui.table_autosize import configure_table_autosize, resize_table_to_contents
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
    AUTO_TRADE_TIMER_MIN_MINUTES = 1
    AUTO_TRADE_TIMER_MAX_MINUTES = 1440
    BEST_PRICE_COLUMN_INDEX = 11
    RETRADE_INNER_TAB_MAIN = 0
    RETRADE_INNER_TAB_CALCULATIONS = 1
    RETRADE_INNER_TAB_HISTORY = 2
    TABLE_SETTINGS_ORG = "MyApp"
    TABLE_SETTINGS_APP = "TableSettings"
    TABLE_SETTINGS_FONT_MIN = 8
    TABLE_SETTINGS_FONT_MAX = 24
    TABLE_SETTINGS_DEFAULTS = {
        "font_size": 13,
        "bg_color": "#ffffff",
        "text_color": "#000000",
        "header_color": "#f3f3f3",
        "selection_color": "#cce5ff",
        "alternating": True,
    }
    RETRADE_UI_FILE = "retrade.ui"

    def init_export_mixin(self) -> None:
        self._export_trade_worker: ExportTradeWorker | None = None
        self.excel_processor = ExcelProcessor()
        self._auto_trade_timer: QTimer | None = None
        self.calculations_file_path = ""
        self.retrade_calculations_loaded = False
        self.retrade_calculations_data: dict[str, Any] = {
            "headers": [],
            "rows": [],
            "total_without_vat": None,
            "total_without_vat_currency": None,
            "totals": {
                "price": 0.0,
                "logistic": 0.0,
                "customs": 0.0,
            },
            "totals_currency": {
                "price": None,
                "logistic": None,
                "customs": None,
            },
        }
        self._ensure_auto_trade_timer()
        self._apply_main_table_font_settings()
        self._ensure_retrade_tab()
        self._ensure_auto_resize_columns_action()
        self._ensure_export_button()
        self.btn_export_trade.clicked.connect(self.export_selected_trade)
        self.btn_export_retrade.clicked.connect(self.export_selected_retrade)

    def _ensure_auto_resize_columns_action(self) -> None:
        if hasattr(self, "action_auto_resize_columns"):
            return

        action = QAction("Подогнать ширину столбцов", self)
        action.setObjectName("action_auto_resize_columns")
        action.setShortcut("Ctrl+Alt+A")
        action.triggered.connect(self._handle_auto_resize_columns)

        edit_menu = getattr(getattr(self, "ui", None), "EditMenu", None)
        if edit_menu is not None:
            edit_menu.addAction(action)

        self.action_auto_resize_columns = action
        self.ui.action_auto_resize_columns = action

    @staticmethod
    def _auto_resize_columns(table: QTableWidget) -> None:
        configure_table_autosize(table)
        table.resizeColumnsToContents()
        max_width = 400
        for column_index in range(table.columnCount()):
            width = table.columnWidth(column_index)
            if width > max_width:
                table.setColumnWidth(column_index, max_width)
        if table.columnCount() > 1:
            table.horizontalHeader().setSectionResizeMode(
                1,
                QHeaderView.ResizeMode.Interactive,
            )
            table.setColumnWidth(1, 300)
        table.resizeRowsToContents()
        table.viewport().update()

    @classmethod
    def _normalize_table_bool_setting(cls, raw_value: Any, default: bool) -> bool:
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, (int, float)):
            return bool(raw_value)
        if isinstance(raw_value, str):
            text = raw_value.strip().lower()
            if text in {"1", "true", "yes", "on"}:
                return True
            if text in {"0", "false", "no", "off"}:
                return False
        return bool(default)

    @classmethod
    def _normalize_table_color_setting(cls, raw_value: Any, default: str) -> str:
        text = str(raw_value or "").strip()
        color = QColor(text)
        if color.isValid():
            return color.name()
        fallback = QColor(default)
        if fallback.isValid():
            return fallback.name()
        return "#ffffff"

    @classmethod
    def _load_table_settings(cls) -> dict[str, Any]:
        defaults = cls.TABLE_SETTINGS_DEFAULTS
        settings = QSettings(cls.TABLE_SETTINGS_ORG, cls.TABLE_SETTINGS_APP)

        font_size_raw = settings.value("font_size", defaults["font_size"])
        try:
            font_size = int(font_size_raw)
        except (TypeError, ValueError):
            font_size = int(defaults["font_size"])
        font_size = max(cls.TABLE_SETTINGS_FONT_MIN, min(cls.TABLE_SETTINGS_FONT_MAX, font_size))

        bg_color = cls._normalize_table_color_setting(
            settings.value("bg_color", defaults["bg_color"]),
            str(defaults["bg_color"]),
        )
        text_color = cls._normalize_table_color_setting(
            settings.value("text_color", defaults["text_color"]),
            str(defaults["text_color"]),
        )
        header_color = cls._normalize_table_color_setting(
            settings.value("header_color", defaults["header_color"]),
            str(defaults["header_color"]),
        )
        selection_color = cls._normalize_table_color_setting(
            settings.value("selection_color", defaults["selection_color"]),
            str(defaults["selection_color"]),
        )
        alternating = cls._normalize_table_bool_setting(
            settings.value("alternating", defaults["alternating"]),
            bool(defaults["alternating"]),
        )

        return {
            "font_size": font_size,
            "bg_color": bg_color,
            "text_color": text_color,
            "header_color": header_color,
            "selection_color": selection_color,
            "alternating": alternating,
        }

    @classmethod
    def _apply_font_size_and_geometry(
        cls,
        table: QTableWidget,
        font_size: int,
        *,
        bold_header: bool = True,
    ) -> None:
        table_font = table.font()
        table_font.setPixelSize(font_size)
        table.setFont(table_font)

        row_height = 24
        vertical_header = table.verticalHeader()
        vertical_header.setMinimumSectionSize(row_height)
        vertical_header.setDefaultSectionSize(row_height)

        horizontal_header = table.horizontalHeader()
        header_font = horizontal_header.font()
        header_font.setPixelSize(font_size)
        header_font.setBold(bold_header)
        horizontal_header.setFont(header_font)

        header_height = max(28, horizontal_header.fontMetrics().height() + 12)
        horizontal_header.setFixedHeight(header_height)

        configure_table_autosize(table, min_row_height=row_height)

    @classmethod
    def apply_table_settings(cls, table: QTableWidget) -> None:
        table_settings = cls._load_table_settings()
        font_size = int(table_settings["font_size"])
        bg_color = str(table_settings["bg_color"])
        text_color = str(table_settings["text_color"])
        header_color = str(table_settings["header_color"])
        selection_color = str(table_settings["selection_color"])

        cls._apply_font_size_and_geometry(table, font_size, bold_header=True)

        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine)
        table.setStyleSheet(
            f"""
QTableWidget {{
    background-color: {bg_color};
    color: {text_color};
    gridline-color: #d0d0d0;
    font-size: {font_size}px;
}}

QHeaderView::section {{
    background-color: {header_color};
    font-weight: bold;
    border: 1px solid #d0d0d0;
    padding: 4px;
}}

QTableWidget::item {{
    border: 1px solid #e0e0e0;
    padding: 4px;
}}

QTableWidget::item:selected {{
    background-color: {selection_color};
    color: black;
}}

QTableWidget::item:hover {{
    background-color: #f5f5f5;
}}
"""
        )
        table.setAlternatingRowColors(bool(table_settings["alternating"]))
        table.setMouseTracking(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        vertical_header = table.verticalHeader()
        vertical_header.setVisible(False)

        horizontal_header = table.horizontalHeader()
        horizontal_header.setStretchLastSection(False)
        horizontal_header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        if table.columnCount() > 1:
            horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            table.setColumnWidth(1, 300)
        if table.rowCount() > 0:
            resize_table_to_contents(table)

    def _apply_main_table_font_settings(self) -> None:
        table = getattr(getattr(self, "ui", None), "KpTable", None)
        if not isinstance(table, QTableWidget):
            return

        table_settings = self._load_table_settings()
        font_size = int(table_settings["font_size"])
        self._apply_font_size_and_geometry(table, font_size, bold_header=True)

    @classmethod
    def _configure_excel_like_table(cls, table: QTableWidget) -> None:
        cls.apply_table_settings(table)

    def _get_active_retrade_table(self) -> QTableWidget | None:
        tabs = getattr(self, "tabWidget", None)
        if tabs is None:
            tabs = getattr(getattr(self, "ui", None), "tabWidget", None)
        retrade_tab = getattr(self, "retrade_tab", None)
        if not isinstance(tabs, QTabWidget) or retrade_tab is None:
            return None
        if tabs.currentWidget() is not retrade_tab:
            return None

        inner_tabs = getattr(self, "retrade_inner_tabs", None)
        if not isinstance(inner_tabs, QTabWidget):
            return None

        current_index = inner_tabs.currentIndex()
        if current_index == self.RETRADE_INNER_TAB_MAIN:
            table = getattr(self, "retrade_table", None)
            return table if isinstance(table, QTableWidget) else None
        if current_index == self.RETRADE_INNER_TAB_CALCULATIONS:
            table = getattr(self, "retrade_calculations_table", None)
            return table if isinstance(table, QTableWidget) else None
        return None

    def refresh_retrade_table_settings(self) -> None:
        self._apply_main_table_font_settings()
        for table_name in ("retrade_table", "retrade_calculations_table"):
            table = getattr(self, table_name, None)
            if isinstance(table, QTableWidget):
                self.apply_table_settings(table)

    def _handle_auto_resize_columns(self) -> None:
        table = self._get_active_retrade_table()
        if table is None:
            return
        self._auto_resize_columns(table)

    def _get_retrade_ui_path(self) -> Path:
        resource_path = getattr(self, "resourcePath", None)
        candidate_paths = []
        if callable(resource_path):
            candidate_paths.append(Path(resource_path(self.RETRADE_UI_FILE)))
        candidate_paths.append(Path(Tool.resourcePath(self.RETRADE_UI_FILE)))
        candidate_paths.append(Path(__file__).resolve().parents[1] / self.RETRADE_UI_FILE)

        for candidate_path in candidate_paths:
            if candidate_path.exists():
                return candidate_path

        searched_paths = ", ".join(str(path) for path in candidate_paths)
        raise RuntimeError(f"Не найден {self.RETRADE_UI_FILE}; проверенные пути: {searched_paths}")

    def _copy_retrade_ui_attrs(self, retrade_form: Any, attr_names: tuple[str, ...]) -> None:
        for attr_name in attr_names:
            widget = getattr(retrade_form, attr_name)
            setattr(self, attr_name, widget)
            setattr(self.ui, attr_name, widget)

    def _ensure_retrade_tab(self) -> None:
        if hasattr(self, "table_retrade") and hasattr(self, "retrade_tab"):
            return

        tabs = getattr(self, "tabWidget", None)
        if tabs is None:
            tabs = getattr(getattr(self, "ui", None), "tabWidget", None)
        if not isinstance(tabs, QTabWidget):
            raise RuntimeError("Не найден tabWidget для вкладки Переторжка")

        form_class, base_class = loadUiType(str(self._get_retrade_ui_path()))
        retrade_tab = base_class(tabs)
        retrade_form = form_class()
        retrade_form.setupUi(retrade_tab)

        self._copy_retrade_ui_attrs(
            retrade_form,
            (
                "table_retrade",
                "retrade_inner_tabs",
                "retrade_main_table_tab",
                "retrade_calculations_tab",
                "retrade_history_tab",
                "retrade_calculations_container",
                "retrade_calculations_totals",
                "btn_auto_trade",
                "btn_open_retrade_calculations",
                "btnGenerate",
                "btn_load_retrade_excel",
                "label_auto_trade_status",
                "label_retrade_calculations_status",
                "retrade_calculations_table",
                "retrade_total_without_vat_label",
                "retrade_price_total_label",
                "sum_label",
                "total_label",
                "profit_label",
            ),
        )

        self.retrade_tab = retrade_tab
        self.retrade_table = self.table_retrade
        self.retradingTable = self.retrade_table
        self.retrade_calculations_container_layout = (
            retrade_form.retradeCalculationsContainerLayout
        )
        self.total_without_vat_label = self.retrade_total_without_vat_label
        self.price_total_label = self.retrade_price_total_label
        self.ui.retradeTab = retrade_tab
        self.ui.retrade_tab = retrade_tab
        self.ui.retrade_table = self.retrade_table
        self.ui.retradingTable = self.retradingTable
        self.ui.retrade_calculations_container_layout = (
            self.retrade_calculations_container_layout
        )
        self.ui.total_without_vat_label = self.total_without_vat_label
        self.ui.price_total_label = self.price_total_label
        self.ui.update_retrade_table = self.update_retrade_table

        self._configure_excel_like_table(self.retrade_table)
        self._configure_excel_like_table(self.retrade_calculations_table)
        self._set_auto_trade_status(False)
        self._set_retrade_calculations_loaded_status(False)

        self.btn_auto_trade.clicked.connect(self._toggle_auto_trade_status)
        self.btn_open_retrade_calculations.clicked.connect(
            self._open_retrade_calculations
        )
        self.btnGenerate.clicked.connect(self.generate_retrade_calculation)
        self.btn_load_retrade_excel.clicked.connect(self.load_retrade_excel)

        tab_index = tabs.addTab(retrade_tab, "Переторжка")
        self.retrade_tab_index = tab_index
        self.retrade_inner_tabs.setCurrentIndex(self.RETRADE_INNER_TAB_MAIN)
        self._clear_retrade_calculations_view()

    @staticmethod
    def _load_retrade_excel_rows(file_path: str) -> list[list[Any]]:
        workbook = load_workbook(file_path, data_only=True)
        try:
            worksheet = workbook.active
            return [list(row) for row in worksheet.iter_rows(values_only=True)]
        finally:
            workbook.close()

    def _fill_retrade_table_from_excel_rows(self, data: list[list[Any]]) -> None:
        table = getattr(self, "retrade_table", None)
        if table is None:
            raise RuntimeError("Таблица Переторжка не найдена")

        rows = [list(row or []) for row in data]
        headers = rows[0] if rows else []
        data_rows = rows[1:] if rows else []
        cols_count = max(
            [len(headers), *(len(row) for row in data_rows)],
            default=0,
        )

        self._configure_excel_like_table(table)
        table.clear()
        table.setColumnCount(cols_count)
        table.setRowCount(len(data_rows))

        if cols_count > 0:
            header_labels = [
                "" if value is None else str(value)
                for value in headers
            ]
            if len(header_labels) < cols_count:
                header_labels.extend("" for _ in range(cols_count - len(header_labels)))
            table.setHorizontalHeaderLabels(header_labels[:cols_count])

        for row_index, row_values in enumerate(data_rows):
            for col_index, cell_value in enumerate(row_values[:cols_count]):
                text = "" if cell_value is None else str(cell_value)
                item = QTableWidgetItem(text)
                if self._is_numeric_table_value(cell_value):
                    item.setTextAlignment(
                        int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    )
                else:
                    item.setTextAlignment(
                        int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    )
                table.setItem(row_index, col_index, item)

        resize_table_to_contents(table)

    def load_retrade_excel(self) -> None:
        default_dir_raw = str(Config.config.get("pathToSaveExcel", "")).strip()
        default_dir = (
            str(Path(default_dir_raw).expanduser())
            if default_dir_raw
            else str(Path.home())
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите Excel файл",
            default_dir,
            "Excel Files (*.xlsx *.xls)",
        )
        if not file_path:
            return

        try:
            data = self._load_retrade_excel_rows(file_path)
            self._fill_retrade_table_from_excel_rows(data)
        except Exception as exc:
            error_text = f"Не удалось загрузить Excel файл: {exc}"
            Tool.write_log(error_text)
            QMessageBox.warning(self, "Ошибка", error_text)
            return

        self._activate_retrade_tab()
        self._log_ui(f"Excel спецификации загружен: {file_path}")
        status_bar_getter = getattr(self, "statusBar", None)
        status_bar = status_bar_getter() if callable(status_bar_getter) else None
        if status_bar is not None:
            status_bar.showMessage("Excel спецификации загружен в Переторжку", 5_000)

    def _open_retrade_calculations_tab(self) -> None:
        inner_tabs = getattr(self, "retrade_inner_tabs", None)
        if isinstance(inner_tabs, QTabWidget):
            inner_tabs.setCurrentIndex(self.RETRADE_INNER_TAB_CALCULATIONS)

    def _open_retrade_calculations(self) -> None:
        default_dir_raw = str(Config.config.get("pathToSaveExcel", "")).strip()
        default_dir = (
            str(Path(default_dir_raw).expanduser())
            if default_dir_raw
            else str(Path.home())
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите Excel файл расчетов",
            default_dir,
            "Excel Files (*.xlsx)",
        )
        if not file_path:
            return

        try:
            cells_data = self._load_retrade_calculations_cells_data(file_path)
        except Exception as exc:
            error_text = f"Не удалось прочитать Excel файл: {exc}"
            Tool.write_log(error_text)
            QMessageBox.warning(self, "Ошибка", error_text)
            return

        self.calculations_file_path = file_path
        parsed = self._parse_retrade_calculations(cells_data)
        headers = parsed["headers"]
        rows = parsed["rows"]
        total_without_vat = parsed.get("total_without_vat")
        total_without_vat_currency = parsed.get("total_without_vat_currency")
        totals = parsed.get("totals", {})
        totals_currency = parsed.get("totals_currency", {})
        self._fill_retrade_calculations_view(
            headers,
            rows,
            total_without_vat=total_without_vat,
            total_without_vat_currency=total_without_vat_currency,
            totals=totals,
            totals_currency=totals_currency,
        )
        self._open_retrade_calculations_tab()

        self._log_calc("файл загружен")
        self._log_calc(f"заголовков: {len(headers)}")
        self._log_calc(f"строк данных: {len(rows)}")
        self._log_calc(f"сумма товаров: {totals.get('price', 0)}")
        self._log_calc(f"логистика: {totals.get('logistic', 0)}")
        self._log_calc(f"таможня: {totals.get('customs', 0)}")

    def _get_retrade_source_table(self) -> Any:
        table = getattr(self, "retradingTable", None)
        if table is not None:
            return table

        table = getattr(self, "retrade_table", None)
        if table is not None:
            return table

        ui = getattr(self, "ui", None)
        if ui is not None:
            table = getattr(ui, "retradingTable", None)
            if table is not None:
                return table
            return getattr(ui, "retrade_table", None)
        return None

    @staticmethod
    def _text_from_table_item(item: Any) -> str:
        if item is None:
            return ""
        text_getter = getattr(item, "text", None)
        if callable(text_getter):
            return str(text_getter() or "")
        return str(item)

    @classmethod
    def _find_best_price_column_index(cls, table: Any) -> int:
        try:
            column_count = int(table.columnCount())
        except Exception:
            return cls.BEST_PRICE_COLUMN_INDEX

        header_getter = getattr(table, "horizontalHeaderItem", None)
        if callable(header_getter):
            for column_index in range(column_count):
                header_text = cls._text_from_table_item(
                    header_getter(column_index)
                ).casefold()
                if "лучш" in header_text and "цен" in header_text:
                    return column_index

        return cls.BEST_PRICE_COLUMN_INDEX

    @classmethod
    def _parse_best_price_value(cls, value: Any) -> float | None:
        text = "" if value is None else str(value).replace("\xa0", " ").strip()
        if not text:
            return None

        _, raw_text = Tool.parsePrice(text)
        normalized = (
            str(raw_text or "")
            .replace("\xa0", " ")
            .replace(" ", "")
            .replace(",", ".")
        )
        match = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", normalized)
        if match is None:
            return None

        try:
            return float(match.group(0))
        except Exception:
            return None

    @classmethod
    def _extract_retrade_best_prices(cls, table: Any) -> list[float | None]:
        best_price_column_index = cls._find_best_price_column_index(table)
        best_prices: list[float | None] = []

        try:
            row_count = int(table.rowCount())
        except Exception:
            return best_prices

        for row in range(row_count):
            item = table.item(row, best_price_column_index)
            best_prices.append(
                cls._parse_best_price_value(cls._text_from_table_item(item))
            )

        return best_prices

    @classmethod
    def _write_best_prices_to_calculations_file(
        cls,
        file_path: str,
        best_prices: list[float | None],
    ) -> str:
        workbook = load_workbook(file_path)
        try:
            sheet_original = workbook.worksheets[0]
            sheet_copy = workbook.copy_worksheet(sheet_original)
            sheet_copy.title = "Обновленный расчет"

            new_col_index = sheet_copy.max_column + 1
            sheet_copy.cell(row=1, column=new_col_index).value = "Лучшая цена"
            sheet_copy.column_dimensions[get_column_letter(new_col_index)].width = 18

            start_row = 2
            for index, price in enumerate(best_prices):
                excel_row = start_row + index
                if price is not None:
                    sheet_copy.cell(row=excel_row, column=new_col_index).value = price

            workbook.save(file_path)
            return sheet_copy.title
        finally:
            workbook.close()

    def generate_retrade_calculation(self) -> None:
        calculations_file_path = str(
            getattr(self, "calculations_file_path", "") or ""
        ).strip()
        if not calculations_file_path:
            QMessageBox.warning(self, "Ошибка", "Файл расчетов не выбран")
            return

        table = self._get_retrade_source_table()
        if table is None:
            QMessageBox.warning(self, "Ошибка", "Таблица Переторжка не найдена")
            return

        try:
            best_prices = self._extract_retrade_best_prices(table)
            sheet_title = self._write_best_prices_to_calculations_file(
                calculations_file_path,
                best_prices,
            )
        except Exception as exc:
            error_text = f"Не удалось обновить расчет: {exc}"
            Tool.write_log(error_text)
            QMessageBox.warning(self, "Ошибка", error_text)
            return

        self._log_calc(f"расчет обновлен: {calculations_file_path}")
        self._log_calc(f"лист: {sheet_title}")
        status_bar_getter = getattr(self, "statusBar", None)
        status_bar = status_bar_getter() if callable(status_bar_getter) else None
        if status_bar is not None:
            status_bar.showMessage("Расчет успешно обновлен", 5_000)
        QMessageBox.information(self, "Готово", "Расчет успешно обновлен")

    @staticmethod
    def _load_retrade_calculations_cells_data(file_path: str) -> list[list[dict[str, Any]]]:
        workbook_values = load_workbook(file_path, data_only=True)
        worksheet_values = workbook_values.active

        data: list[list[dict[str, Any]]] = []
        for row in worksheet_values.iter_rows(values_only=False):
            parsed_row: list[dict[str, Any]] = []
            for cell in row:
                value = cell.value
                currency = ExportMixin._detect_currency(value, cell.number_format)
                parsed_row.append(
                    {
                        "value": value,
                        "currency": currency,
                    }
                )
            data.append(parsed_row)

        warning_message = (
            "WARNING: Some formula cells returned None. Excel file may need recalculation."
        )
        workbook_formulas = None
        try:
            workbook_formulas = load_workbook(file_path, data_only=False)
            worksheet_formulas = workbook_formulas.active

            has_unresolved_formula = False
            for formula_row in worksheet_formulas.iter_rows(values_only=False):
                for formula_cell in formula_row:
                    formula_value = formula_cell.value
                    if not (isinstance(formula_value, str) and formula_value.startswith("=")):
                        continue

                    calculated_value = worksheet_values.cell(
                        row=formula_cell.row,
                        column=formula_cell.column,
                    ).value
                    if calculated_value is None:
                        has_unresolved_formula = True
                        break
                if has_unresolved_formula:
                    break

            if has_unresolved_formula:
                print(warning_message)
                Tool.write_log(warning_message)
        finally:
            try:
                workbook_formulas.close()
            except Exception:
                pass
            try:
                workbook_values.close()
            except Exception:
                pass

        return data

    @staticmethod
    def _detect_currency(value: Any, number_format: Any) -> str | None:
        number_format_text = str(number_format or "").upper()
        if "₽" in number_format_text or "RUB" in number_format_text:
            return "RUB"
        if "$" in number_format_text or "USD" in number_format_text:
            return "USD"
        if "€" in number_format_text or "EUR" in number_format_text:
            return "EUR"

        if isinstance(value, str):
            text_lower = value.lower()
            if "руб" in text_lower or "rub" in text_lower:
                return "RUB"
            if "$" in value or "usd" in text_lower:
                return "USD"
            if "€" in value or "eur" in text_lower:
                return "EUR"
        return None

    def _clear_retrade_calculations_view(self) -> None:
        table = getattr(self, "retrade_calculations_table", None)
        if isinstance(table, QTableWidget):
            table.clear()
            table.setRowCount(0)
            table.setColumnCount(0)

        for label_name in ("sum_label", "total_label", "profit_label"):
            label = getattr(self, label_name, None)
            if isinstance(label, QLabel):
                label.setText("-")

        self.retrade_calculations_data = {
            "headers": [],
            "rows": [],
            "total_without_vat": None,
            "total_without_vat_currency": None,
            "totals": {
                "price": 0.0,
                "logistic": 0.0,
                "customs": 0.0,
            },
            "totals_currency": {
                "price": None,
                "logistic": None,
                "customs": None,
            },
        }
        total_without_vat_label = getattr(self, "total_without_vat_label", None)
        if isinstance(total_without_vat_label, QLabel):
            total_without_vat_label.setText("")
            total_without_vat_label.setVisible(False)
        price_total_label = getattr(self, "price_total_label", None)
        if isinstance(price_total_label, QLabel):
            price_total_label.setText("")
            price_total_label.setVisible(False)
        self._set_retrade_calculations_loaded_status(False)

    @staticmethod
    def _normalize_retrade_calculations_cell(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        try:
            if pd.isna(value):
                return ""
        except Exception:
            pass
        return str(value).strip()

    @classmethod
    def _parse_retrade_numeric_value(cls, value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            candidate = text.replace(" ", "").replace(",", ".")
        else:
            candidate = value
        try:
            return float(candidate)
        except Exception:
            return None

    @staticmethod
    def _is_numeric_table_value(value: Any) -> bool:
        if value is None or isinstance(value, bool):
            return False
        if not isinstance(value, (int, float)):
            return False
        try:
            return not pd.isna(value)
        except Exception:
            return True

    @classmethod
    def _format_number_ru(cls, value: Any) -> str:
        numeric_value = cls._parse_retrade_numeric_value(value)
        if numeric_value is None:
            return cls._normalize_retrade_calculations_cell(value)

        formatted = f"{numeric_value:,.2f}"
        return formatted.replace(",", " ").replace(".", ",")

    @classmethod
    def _format_retrade_calculations_cell_for_display(cls, cell: Any) -> str:
        if isinstance(cell, dict):
            raw_value = cell.get("value")
            currency = cell.get("currency")
        else:
            raw_value = cell
            currency = None

        formatted_value = cls._format_number_ru(raw_value)
        if not formatted_value:
            return ""

        if cls._parse_retrade_numeric_value(raw_value) is None:
            return formatted_value

        if currency == "RUB":
            return f"{formatted_value} ₽"
        if currency == "USD":
            return f"{formatted_value} $"
        if currency == "EUR":
            return f"{formatted_value} €"
        return formatted_value

    @classmethod
    def _is_retrade_calculations_value_present(cls, value: Any) -> bool:
        return bool(cls._normalize_retrade_calculations_cell(value))

    @classmethod
    def _is_retrade_calculations_cell_present(cls, cell_data: Any) -> bool:
        if isinstance(cell_data, dict):
            value = cell_data.get("value")
            currency = cell_data.get("currency")
            return cls._is_retrade_calculations_value_present(value) or bool(currency)
        return cls._is_retrade_calculations_value_present(cell_data)

    @classmethod
    def _is_retrade_position_cell(cls, value: Any) -> bool:
        if value is None or isinstance(value, bool):
            return False

        if isinstance(value, (int, float)):
            try:
                if pd.isna(value):
                    return False
            except Exception:
                pass
            return True

        if isinstance(value, str):
            return value.strip().isdigit()

        return False

    @staticmethod
    def _is_service_retrade_column_header(header: str) -> bool:
        lowered = header.lower()
        return "сумма" in lowered or "итого" in lowered or "прибыль" in lowered

    @staticmethod
    def _is_price_per_unit_header(header: Any) -> bool:
        return isinstance(header, str) and "цена за ед" in header.lower()

    @staticmethod
    def _find_retrade_column(headers: list[Any], keywords: list[str]) -> int | None:
        for index, header in enumerate(headers):
            if not isinstance(header, str):
                continue
            lowered_header = header.lower()
            if any(keyword in lowered_header for keyword in keywords):
                return index
        return None

    @classmethod
    def _sum_retrade_column(
        cls,
        rows: list[list[dict[str, Any]]],
        col_index: int | None,
    ) -> tuple[float, str | None]:
        if col_index is None:
            return 0.0, None

        total = 0.0
        detected_currency: str | None = None
        for row in rows:
            if col_index >= len(row):
                continue
            cell = row[col_index]
            if isinstance(cell, dict):
                value = cell.get("value")
                if detected_currency is None and cell.get("currency"):
                    detected_currency = cell.get("currency")
            else:
                value = cell

            numeric_value = cls._parse_retrade_numeric_value(value)
            if numeric_value is None:
                continue
            total += numeric_value

        return total, detected_currency

    @staticmethod
    def _is_total_without_vat_marker(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return "итого без ндс" in value.lower()

    @classmethod
    def _extract_total_without_vat_from_row(
        cls,
        row_cells: list[dict[str, Any]],
    ) -> tuple[Any, str | None]:
        numeric_candidates: list[tuple[Any, str | None]] = []
        for cell in row_cells:
            if not isinstance(cell, dict):
                continue
            value = cell.get("value")
            numeric = cls._parse_retrade_numeric_value(value)
            if numeric is None:
                continue
            numeric_candidates.append((value, cell.get("currency")))

        if not numeric_candidates:
            return None, None

        selected_value, selected_currency = numeric_candidates[-1]
        return selected_value, selected_currency

    @staticmethod
    def _log_calc(message: str) -> None:
        text = f"[CALC] {message}"
        print(text)
        Tool.write_log(text)

    @classmethod
    def _parse_retrade_calculations(
        cls,
        cells_data: list[list[dict[str, Any]]],
    ) -> dict[str, Any]:
        headers: list[str] = []
        position_rows: list[list[dict[str, Any]]] = []
        total_without_vat: Any = None
        total_without_vat_currency: str | None = None
        header_found = False

        for raw_row in cells_data:
            row_data = list(raw_row or [])
            if not any(cls._is_retrade_calculations_cell_present(cell) for cell in row_data):
                continue

            if not header_found:
                headers = [
                    cls._normalize_retrade_calculations_cell(
                        cell.get("value") if isinstance(cell, dict) else cell
                    )
                    for cell in row_data
                ]
                while headers and not headers[-1]:
                    headers.pop()
                header_found = True
                continue

            normalized_row: list[dict[str, Any]] = []
            for cell in row_data:
                if isinstance(cell, dict):
                    normalized_row.append(
                        {
                            "value": cell.get("value"),
                            "currency": cell.get("currency"),
                        }
                    )
                else:
                    normalized_row.append({"value": cell, "currency": None})

            while normalized_row and not cls._is_retrade_calculations_cell_present(normalized_row[-1]):
                normalized_row.pop()
            if not normalized_row:
                continue

            if any(
                cls._is_total_without_vat_marker(cell.get("value"))
                for cell in normalized_row
                if isinstance(cell, dict)
            ):
                extracted_value, extracted_currency = cls._extract_total_without_vat_from_row(
                    normalized_row
                )
                if extracted_value is not None:
                    total_without_vat = extracted_value
                    total_without_vat_currency = extracted_currency
                continue

            first_cell_value = (
                normalized_row[0].get("value")
                if normalized_row and isinstance(normalized_row[0], dict)
                else None
            )
            if not cls._is_retrade_position_cell(first_cell_value):
                continue

            position_rows.append(normalized_row)

        filtered_headers: list[str] = []
        filtered_indices: list[int] = []
        for index, header in enumerate(headers):
            if not isinstance(header, str):
                continue
            if cls._is_service_retrade_column_header(header):
                continue
            filtered_headers.append(header)
            filtered_indices.append(index)

        filtered_rows: list[list[dict[str, Any]]] = []
        for row in position_rows:
            new_row: list[dict[str, Any]] = []
            for index in filtered_indices:
                if index < len(row):
                    new_row.append(row[index])
                else:
                    new_row.append({"value": None, "currency": None})

            while new_row and not cls._is_retrade_calculations_cell_present(new_row[-1]):
                new_row.pop()
            if not new_row:
                continue
            filtered_rows.append(new_row)

        price_col_index = cls._find_retrade_column(filtered_headers, ["цена за ед"])
        logistic_col_index = cls._find_retrade_column(
            filtered_headers,
            ["логист", "доставк", "транспорт"],
        )
        customs_col_index = cls._find_retrade_column(filtered_headers, ["тамож", "пошлин"])

        if price_col_index is None:
            cls._log_calc("Ошибка: столбец 'Цена за ед. без НДС' не найден")
        if logistic_col_index is None:
            cls._log_calc("Ошибка: столбец 'Логистика' не найден")
        if customs_col_index is None:
            cls._log_calc("Ошибка: столбец 'Таможня' не найден")

        price_total, price_total_currency = cls._sum_retrade_column(filtered_rows, price_col_index)
        logistic_total, logistic_total_currency = cls._sum_retrade_column(
            filtered_rows,
            logistic_col_index,
        )
        customs_total, customs_total_currency = cls._sum_retrade_column(
            filtered_rows,
            customs_col_index,
        )

        return {
            "headers": filtered_headers,
            "rows": filtered_rows,
            "total_without_vat": total_without_vat,
            "total_without_vat_currency": total_without_vat_currency,
            "totals": {
                "price": price_total,
                "logistic": logistic_total,
                "customs": customs_total,
            },
            "totals_currency": {
                "price": price_total_currency,
                "logistic": logistic_total_currency,
                "customs": customs_total_currency,
            },
        }

    def _fill_retrade_calculations_view(
        self,
        headers: list[str],
        rows: list[list[dict[str, Any]]],
        *,
        total_without_vat: Any = None,
        total_without_vat_currency: str | None = None,
        totals: dict[str, float] | None = None,
        totals_currency: dict[str, str | None] | None = None,
    ) -> None:
        self._clear_retrade_calculations_view()

        table = getattr(self, "retrade_calculations_table", None)
        if isinstance(table, QTableWidget):
            self._configure_excel_like_table(table)
            column_count = max(len(headers), max((len(row) for row in rows), default=0))
            table.setRowCount(len(rows))
            table.setColumnCount(column_count)
            if column_count > 0:
                header_labels = list(headers[:column_count])
                if len(header_labels) < column_count:
                    header_labels.extend(
                        f"Колонка {index + 1}"
                        for index in range(len(header_labels), column_count)
                    )
                table.setHorizontalHeaderLabels(header_labels)
            for row_index, row_values in enumerate(rows):
                for col_index in range(column_count):
                    cell_payload = (
                        row_values[col_index]
                        if col_index < len(row_values)
                        else {"value": None, "currency": None}
                    )
                    if isinstance(cell_payload, dict):
                        currency = cell_payload.get("currency")
                    else:
                        currency = None

                    display_value = self._format_retrade_calculations_cell_for_display(cell_payload)
                    item = QTableWidgetItem(display_value)
                    item.setData(Qt.ItemDataRole.UserRole, cell_payload)
                    raw_value = cell_payload.get("value") if isinstance(cell_payload, dict) else cell_payload
                    if self._is_numeric_table_value(raw_value):
                        item.setTextAlignment(
                            int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        )
                    else:
                        item.setTextAlignment(
                            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                        )
                    if currency:
                        item.setToolTip(f"Валюта: {currency}")
                    table.setItem(row_index, col_index, item)
            resize_table_to_contents(table)

        totals_data = totals or {}
        totals_currency_data = totals_currency or {}
        default_currency = total_without_vat_currency
        price_currency = totals_currency_data.get("price") or default_currency
        logistic_currency = totals_currency_data.get("logistic") or default_currency
        customs_currency = totals_currency_data.get("customs") or default_currency

        price_display = self._format_retrade_calculations_cell_for_display(
            {
                "value": totals_data.get("price", 0.0),
                "currency": price_currency,
            }
        )
        logistic_display = self._format_retrade_calculations_cell_for_display(
            {
                "value": totals_data.get("logistic", 0.0),
                "currency": logistic_currency,
            }
        )
        customs_display = self._format_retrade_calculations_cell_for_display(
            {
                "value": totals_data.get("customs", 0.0),
                "currency": customs_currency,
            }
        )

        sum_label = getattr(self, "sum_label", None)
        if isinstance(sum_label, QLabel):
            sum_label.setText(price_display or "0,00")
        total_label = getattr(self, "total_label", None)
        if isinstance(total_label, QLabel):
            total_label.setText(logistic_display or "0,00")
        profit_label = getattr(self, "profit_label", None)
        if isinstance(profit_label, QLabel):
            profit_label.setText(customs_display or "0,00")

        total_without_vat_label = getattr(self, "total_without_vat_label", None)
        if isinstance(total_without_vat_label, QLabel):
            if total_without_vat is None:
                total_without_vat_label.setText("")
                total_without_vat_label.setVisible(False)
            else:
                formatted_total = self._format_retrade_calculations_cell_for_display(
                    {
                        "value": total_without_vat,
                        "currency": total_without_vat_currency,
                    }
                )
                if formatted_total:
                    total_without_vat_label.setText(f"Итого без НДС: {formatted_total}")
                    total_without_vat_label.setVisible(True)
                else:
                    total_without_vat_label.setText("")
                    total_without_vat_label.setVisible(False)

        price_total_label = getattr(self, "price_total_label", None)
        if isinstance(price_total_label, QLabel):
            price_total_label.setText("")
            price_total_label.setVisible(False)

        self.retrade_calculations_data = {
            "headers": list(headers),
            "rows": [list(row) for row in rows],
            "total_without_vat": total_without_vat,
            "total_without_vat_currency": total_without_vat_currency,
            "totals": {
                "price": totals_data.get("price", 0.0),
                "logistic": totals_data.get("logistic", 0.0),
                "customs": totals_data.get("customs", 0.0),
            },
            "totals_currency": {
                "price": price_currency,
                "logistic": logistic_currency,
                "customs": customs_currency,
            },
        }
        self._set_retrade_calculations_loaded_status(bool(headers or rows))

    def _set_retrade_calculations_loaded_status(self, is_loaded: bool) -> None:
        self.retrade_calculations_loaded = bool(is_loaded)
        status_label = getattr(self, "label_retrade_calculations_status", None)
        if not isinstance(status_label, QLabel):
            return

        if self.retrade_calculations_loaded:
            status_label.setText("Расчеты подключены")
            status_label.setStyleSheet("color: #1f8f3a; font-weight: 600;")
            return

        status_label.setText("Расчеты не подключены")
        status_label.setStyleSheet("color: #c62828; font-weight: 600;")

    def _toggle_auto_trade_status(self) -> None:
        status_label = getattr(self, "label_auto_trade_status", None)
        if status_label is None:
            return
        is_enabled = str(status_label.text() or "").strip() == "Включено"
        if is_enabled:
            self._stop_auto_trade_timer()
            self._set_auto_trade_status(False)
            self._log_ui("Автоматическое ведение торгов: Выключено")
            return

        if not self._confirm_auto_trade_enable_if_needed():
            return

        self._set_auto_trade_status(True)
        self._log_ui("Автоматическое ведение торгов: Включено")
        self._start_auto_trade_timer_if_needed()

    def _set_auto_trade_status(self, is_enabled: bool) -> None:
        status_label = getattr(self, "label_auto_trade_status", None)
        if status_label is None:
            return
        if is_enabled:
            status_label.setText("Включено")
            status_label.setStyleSheet("color: #1f8f3a; font-weight: 600;")
            return
        status_label.setText("Выключено")
        status_label.setStyleSheet("color: #c62828; font-weight: 600;")

    def _confirm_auto_trade_enable(self) -> bool:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("Подтверждение включения")
        dialog.setText(
            "Вы собираетесь включить автоматическое ведение торгов.\n\n"
            "ВНИМАНИЕ:\n"
            "Данная функция работает в автоматическом режиме и может отправлять ценовые "
            "предложения без дополнительного подтверждения.\n\n"
            "Использование функции требует ОБЯЗАТЕЛЬНОГО контроля со стороны пользователя.\n\n"
            "Рекомендуется не оставлять систему без присмотра во время работы.\n\n"
            "Продолжить?"
        )
        yes_button = dialog.addButton("Да", QMessageBox.ButtonRole.YesRole)
        cancel_button = dialog.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
        dialog.setDefaultButton(cancel_button)
        dialog.exec()
        return dialog.clickedButton() is yes_button

    def _confirm_auto_trade_enable_if_needed(self) -> bool:
        if bool(Config.settings.get("skip_auto_trade_warning", False)):
            return True
        return self._confirm_auto_trade_enable()

    def _ensure_auto_trade_timer(self) -> QTimer:
        timer = getattr(self, "_auto_trade_timer", None)
        if isinstance(timer, QTimer):
            return timer

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(self._on_auto_trade_timer_timeout)
        self._auto_trade_timer = timer
        return timer

    def _stop_auto_trade_timer(self) -> None:
        timer = self._ensure_auto_trade_timer()
        if timer.isActive():
            timer.stop()

    def _start_auto_trade_timer_if_needed(self) -> None:
        self._stop_auto_trade_timer()
        if not bool(Config.settings.get("use_auto_trade_timer", False)):
            return

        default_minutes = int(Config.DEFAULT_SETTINGS.get("auto_trade_timer_minutes", 30))
        raw_minutes = Config.settings.get("auto_trade_timer_minutes", default_minutes)
        try:
            minutes = int(raw_minutes)
        except (TypeError, ValueError):
            minutes = default_minutes
        minutes = max(
            self.AUTO_TRADE_TIMER_MIN_MINUTES,
            min(self.AUTO_TRADE_TIMER_MAX_MINUTES, minutes),
        )

        timer = self._ensure_auto_trade_timer()
        timer.start(minutes * 60 * 1000)
        self._log_auto_trade(f"Таймер запущен на {minutes} мин")

    def _on_auto_trade_timer_timeout(self) -> None:
        self._set_auto_trade_status(False)
        self._log_auto_trade("Автоматические торги выключены по таймеру")

    @staticmethod
    def _log_auto_trade(message: str) -> None:
        text = f"[AUTO TRADE] {message}"
        print(text)
        Tool.write_log(text)

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

    @staticmethod
    def _log_ui(message: str) -> None:
        text = f"[UI] {message}"
        print(text)
        Tool.write_log(text)

    def update_retrade_table(self, df: pd.DataFrame) -> None:
        table = getattr(self, "retrade_table", None)
        if table is None:
            raise RuntimeError("Таблица Переторжка не найдена")
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame()

        self._log_ui("Обновление таблицы Переторжка")

        self._configure_excel_like_table(table)
        table.clear()
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns.tolist())

        for row_index in range(len(df)):
            for col_index in range(len(df.columns)):
                cell_value = df.iloc[row_index, col_index]
                value = "" if pd.isna(cell_value) else str(cell_value)
                item = QTableWidgetItem(value)
                if self._is_numeric_table_value(cell_value):
                    item.setTextAlignment(
                        int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    )
                else:
                    item.setTextAlignment(
                        int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    )
                table.setItem(row_index, col_index, item)

        resize_table_to_contents(table)
        self._log_ui(f"Строк: {len(df)}")

    def _activate_retrade_tab(self) -> None:
        tabs = getattr(self, "tabWidget", None)
        if tabs is None:
            tabs = getattr(getattr(self, "ui", None), "tabWidget", None)
        retrade_tab = getattr(self, "retrade_tab", None)
        if isinstance(tabs, QTabWidget) and retrade_tab is not None:
            index = tabs.indexOf(retrade_tab)
            if index >= 0:
                tabs.setCurrentIndex(index)
        inner_tabs = getattr(self, "retrade_inner_tabs", None)
        if isinstance(inner_tabs, QTabWidget):
            inner_tabs.setCurrentIndex(self.RETRADE_INNER_TAB_MAIN)

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
                if excel_processor.can_fill_exported_excel(file_path_text):
                    excel_processor.fill_exported_excel(
                        file_path_text,
                        self.get_table_rows(),
                    )
                else:
                    Tool.write_log(
                        "Пропуск пост-обработки Excel: файл сформирован напрямую из JSON"
                    )

                export_path = Path(file_path_text).expanduser()
                if not export_path.exists() or not export_path.is_file():
                    raise FileNotFoundError(f"Excel файл не найден: {export_path}")

                try:
                    dataframe = pd.read_excel(export_path)
                except ValueError as exc:
                    if "No columns to parse from file" in str(exc):
                        dataframe = pd.DataFrame()
                    else:
                        raise

                self._log_ui("Excel загружен")
                update_method = getattr(getattr(self, "ui", None), "update_retrade_table", None)
                if callable(update_method):
                    update_method(dataframe)
                else:
                    self.update_retrade_table(dataframe)
                self._activate_retrade_tab()
            except Exception as exc:
                error_text = str(exc or "Ошибка обработки Excel")
                Tool.write_log(f"Ошибка пост-обработки Excel: {error_text}")
                QMessageBox.critical(self, "Ошибка", error_text)
                set_pipeline_error_status = getattr(self, "_set_pipeline_error_status", None)
                if callable(set_pipeline_error_status):
                    set_pipeline_error_status()
                self._finish_export("Ошибка пост-обработки Excel")
                return

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
