from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

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
    RETRADE_INNER_TAB_MAIN = 0
    RETRADE_INNER_TAB_CALCULATIONS = 1
    RETRADE_INNER_TAB_HISTORY = 2

    def init_export_mixin(self) -> None:
        self._export_trade_worker: ExportTradeWorker | None = None
        self.excel_processor = ExcelProcessor()
        self._auto_trade_timer: QTimer | None = None
        self.retrade_calculations_loaded = False
        self._ensure_auto_trade_timer()
        self._ensure_retrade_tab()
        self._ensure_export_button()
        self.btn_export_trade.clicked.connect(self.export_selected_trade)
        self.btn_export_retrade.clicked.connect(self.export_selected_retrade)

    def _ensure_retrade_tab(self) -> None:
        if hasattr(self, "retrade_table") and hasattr(self, "retrade_tab"):
            return

        tabs = getattr(self, "tabWidget", None)
        if tabs is None:
            tabs = getattr(getattr(self, "ui", None), "tabWidget", None)
        if not isinstance(tabs, QTabWidget):
            raise RuntimeError("Не найден tabWidget для вкладки Переторжка")

        retrade_tab = QWidget(tabs)
        retrade_tab.setObjectName("retradeTab")
        root_layout = QVBoxLayout(retrade_tab)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.retrade_inner_tabs = QTabWidget(retrade_tab)
        self.retrade_inner_tabs.setObjectName("retrade_inner_tabs")

        main_table_tab = QWidget(self.retrade_inner_tabs)
        main_table_tab.setObjectName("retrade_main_table_tab")
        main_table_layout = QVBoxLayout(main_table_tab)
        main_table_layout.setContentsMargins(0, 0, 0, 0)
        main_table_layout.setSpacing(0)

        self.retrade_table = QTableWidget(main_table_tab)
        self.retrade_table.setObjectName("retrade_table")
        main_table_layout.addWidget(self.retrade_table, 1)
        self.retrade_inner_tabs.addTab(main_table_tab, "Основная таблица")

        calculations_tab = QWidget(self.retrade_inner_tabs)
        calculations_tab.setObjectName("retrade_calculations_tab")
        calculations_layout = QVBoxLayout(calculations_tab)
        calculations_layout.setContentsMargins(0, 0, 0, 0)
        calculations_layout.setSpacing(0)
        calculations_title = QLabel("Расчеты", calculations_tab)
        calculations_layout.addWidget(calculations_title)

        calculations_container = QWidget(calculations_tab)
        calculations_container.setObjectName("retrade_calculations_container")
        calculations_container_layout = QVBoxLayout(calculations_container)
        calculations_container_layout.setContentsMargins(0, 0, 0, 0)
        calculations_container_layout.setSpacing(0)

        self.retrade_calculations_table = QTableWidget(calculations_container)
        self.retrade_calculations_table.setObjectName("retrade_calculations_table")
        calculations_container_layout.addWidget(self.retrade_calculations_table, 1)

        totals_container = QWidget(calculations_container)
        totals_container.setObjectName("retrade_calculations_totals")
        totals_layout = QFormLayout(totals_container)
        totals_layout.setContentsMargins(0, 0, 0, 0)

        self.sum_label = QLabel("-", totals_container)
        self.total_label = QLabel("-", totals_container)
        self.profit_label = QLabel("-", totals_container)

        totals_layout.addRow("Сумма:", self.sum_label)
        totals_layout.addRow("Итого:", self.total_label)
        totals_layout.addRow("Прибыль:", self.profit_label)
        calculations_container_layout.addWidget(totals_container)
        calculations_layout.addWidget(calculations_container, 1)
        self.retrade_inner_tabs.addTab(calculations_tab, "Расчеты")

        history_tab = QWidget(self.retrade_inner_tabs)
        history_tab.setObjectName("retrade_history_tab")
        history_layout = QVBoxLayout(history_tab)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.setSpacing(0)
        history_title = QLabel("История", history_tab)
        history_placeholder = QLabel(
            "История изменений будет добавлена позже",
            history_tab,
        )
        history_layout.addWidget(history_title)
        history_layout.addWidget(history_placeholder)
        history_layout.addStretch(1)
        self.retrade_inner_tabs.addTab(history_tab, "История")

        self.retrade_inner_tabs.setCurrentIndex(self.RETRADE_INNER_TAB_MAIN)
        root_layout.addWidget(self.retrade_inner_tabs, 1)

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_auto_trade = QPushButton("Автоматическое ведение торгов", retrade_tab)
        self.btn_open_retrade_calculations = QPushButton("Открыть расчеты", retrade_tab)
        self.label_auto_trade_status = QLabel("Выключено", retrade_tab)
        self.label_retrade_calculations_status = QLabel(
            "Расчеты не подключены",
            retrade_tab,
        )
        self._set_auto_trade_status(False)
        self._set_retrade_calculations_loaded_status(False)
        controls_layout.addWidget(self.btn_auto_trade)
        controls_layout.addWidget(self.btn_open_retrade_calculations)
        controls_layout.addWidget(self.label_auto_trade_status)
        controls_layout.addWidget(self.label_retrade_calculations_status)
        controls_layout.addStretch(1)
        root_layout.addLayout(controls_layout)

        self.btn_auto_trade.clicked.connect(self._toggle_auto_trade_status)
        self.btn_open_retrade_calculations.clicked.connect(
            self._open_retrade_calculations
        )

        tab_index = tabs.addTab(retrade_tab, "Переторжка")
        self.retrade_tab = retrade_tab
        self.retrade_tab_index = tab_index
        self.retrade_main_table_tab = main_table_tab
        self.retrade_calculations_tab = calculations_tab
        self.retrade_history_tab = history_tab
        self.retrade_calculations_container = calculations_container
        self.retrade_calculations_container_layout = calculations_container_layout
        self.retrade_calculations_totals = totals_container
        self.ui.retradeTab = retrade_tab
        self.ui.retrade_inner_tabs = self.retrade_inner_tabs
        self.ui.retrade_calculations_table = self.retrade_calculations_table
        self.ui.sum_label = self.sum_label
        self.ui.total_label = self.total_label
        self.ui.profit_label = self.profit_label
        self.ui.label_retrade_calculations_status = self.label_retrade_calculations_status
        self.ui.update_retrade_table = self.update_retrade_table
        self._clear_retrade_calculations_view()

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
            dataframe = self._load_retrade_calculations_dataframe(file_path)
        except Exception as exc:
            error_text = f"Не удалось прочитать Excel файл: {exc}"
            Tool.write_log(error_text)
            QMessageBox.warning(self, "Ошибка", error_text)
            return

        parsed = self._parse_retrade_calculations(dataframe)
        headers = parsed["headers"]
        rows = parsed["rows"]
        self._fill_retrade_calculations_view(headers, rows)
        self._open_retrade_calculations_tab()

        self._log_calc("файл загружен")
        self._log_calc(f"заголовков: {len(headers)}")
        self._log_calc(f"строк данных: {len(rows)}")

    @staticmethod
    def _load_retrade_calculations_dataframe(file_path: str) -> pd.DataFrame:
        workbook_values = load_workbook(file_path, data_only=True)
        worksheet_values = workbook_values.active

        data: list[list[Any]] = []
        for row in worksheet_values.iter_rows(values_only=True):
            data.append(list(row))

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

        return pd.DataFrame(data)

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

        self._set_retrade_calculations_loaded_status(False)

    @staticmethod
    def _normalize_retrade_calculations_cell(value: Any) -> str:
        if pd.isna(value):
            return ""
        return str(value).strip()

    @staticmethod
    def _log_calc(message: str) -> None:
        text = f"[CALC] {message}"
        print(text)
        Tool.write_log(text)

    @classmethod
    def _parse_retrade_calculations(
        cls,
        dataframe: pd.DataFrame,
    ) -> dict[str, list]:
        headers: list[str] = []
        rows: list[list[str]] = []
        header_found = False

        for _, raw_row in dataframe.iterrows():
            raw_values = raw_row.tolist()
            if not any(pd.notna(x) for x in raw_values):
                continue

            row_values = [
                cls._normalize_retrade_calculations_cell(cell_value)
                for cell_value in raw_values
            ]
            while row_values and not row_values[-1]:
                row_values.pop()
            if not row_values:
                continue
            if not any(str(value or "").strip() for value in row_values):
                continue

            if not header_found:
                headers = row_values
                header_found = True
                continue

            rows.append(row_values)

        return {
            "headers": headers,
            "rows": rows,
        }

    def _fill_retrade_calculations_view(
        self,
        headers: list[str],
        rows: list[list[str]],
    ) -> None:
        self._clear_retrade_calculations_view()

        table = getattr(self, "retrade_calculations_table", None)
        if isinstance(table, QTableWidget):
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
                    value = row_values[col_index] if col_index < len(row_values) else ""
                    table.setItem(row_index, col_index, QTableWidgetItem(str(value)))
            table.resizeRowsToContents()
            table.resizeColumnsToContents()

        sum_label = getattr(self, "sum_label", None)
        if isinstance(sum_label, QLabel):
            sum_label.setText("-")
        total_label = getattr(self, "total_label", None)
        if isinstance(total_label, QLabel):
            total_label.setText("-")
        profit_label = getattr(self, "profit_label", None)
        if isinstance(profit_label, QLabel):
            profit_label.setText("-")

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

        table.clear()
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns.tolist())

        for row_index in range(len(df)):
            for col_index in range(len(df.columns)):
                cell_value = df.iloc[row_index, col_index]
                value = "" if pd.isna(cell_value) else str(cell_value)
                table.setItem(row_index, col_index, QTableWidgetItem(value))

        table.resizeRowsToContents()
        table.resizeColumnsToContents()
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
