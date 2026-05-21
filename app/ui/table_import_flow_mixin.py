from pathlib import Path

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.ui.table_autosize import refresh_table_viewport, resize_table_to_contents, table_update_guard
from config import Config
from tools import DatabaseTools as Tool


class TableImportFlowMixin:
    def _show_full_table_tab(self):
        tabs = getattr(getattr(self, "ui", None), "tabWidget", None)
        full_table_tab = getattr(getattr(self, "ui", None), "tab", None)
        if tabs is None:
            return

        set_current_widget = getattr(tabs, "setCurrentWidget", None)
        if callable(set_current_widget) and full_table_tab is not None:
            set_current_widget(full_table_tab)
            return

        index_of = getattr(tabs, "indexOf", None)
        set_current_index = getattr(tabs, "setCurrentIndex", None)
        if callable(index_of) and callable(set_current_index) and full_table_tab is not None:
            index = index_of(full_table_tab)
            if index >= 0:
                set_current_index(index)

    def openTable(self, file=None):
        filename = file
        if not filename:
            filename = QFileDialog.getOpenFileName(
                self,
                "Открыть файл",
                "",
                "csv (*.csv);; Excel Files (*.xls *.xlsx)",
            )[0]
        if not filename:
            return

        if not Path(filename).exists():
            self.error("Ошибка", f"Файл не найден: {filename}")
            return

        params = self._parse_input_parameters(show_error=True)
        if params is None:
            return

        self.closeTable()
        try:
            parsed_rows, warnings = self.proposal_import_service.load_source_rows(filename)
        except Exception as e:
            Tool.log_exception(
                f"Не удалось загрузить КП поставщика: {filename}",
                e,
                include_traceback=False,
            )
            self.error("Ошибка", f"Невозможно прочитать таблицу\n{e}")
            return
        Tool.write_log(f"КП поставщика прочитано: {filename}; строк: {len(parsed_rows)}")

        table = self.ui.KpTable
        summary_table = getattr(self.ui, "tableWidget_3", None)
        table_data = {
            "amount": [],
            "currency": [],
            "unitPrice": [],
            "totalPrice": [],
            "termDelivery": [],
            "logistic": [],
        }

        with table_update_guard(table, summary_table):
            table.setRowCount(len(parsed_rows))
            blocker = QSignalBlocker(table)
            for row_num, row in enumerate(parsed_rows):
                total_price = self._round_money(row["qty"] * row["unitPrice"])
                self._set_table_item(row_num, 0, row["number"], editable=True)
                self._set_table_item(row_num, 1, row["name"], editable=True)
                self._set_table_item(row_num, 2, row["sku"], editable=True)
                self._set_table_item(row_num, 3, row["unit"], editable=True)
                self._set_table_item(row_num, 4, row["qty"], editable=True)
                self._set_table_item(
                    row_num,
                    5,
                    Tool.formatPrice(str(row["unitPrice"]), row["currency"]),
                    editable=True,
                )
                self._set_table_item(
                    row_num,
                    6,
                    Tool.formatPrice(str(total_price), row["currency"]),
                    editable=False,
                )
                self._set_table_item(row_num, 14, f"{row['supplierTermDays']} дней", editable=True)

                table_data["amount"].append(row["qty"])
                table_data["currency"].append(row["currency"])
                table_data["unitPrice"].append(row["unitPrice"])
                table_data["totalPrice"].append(total_price)
                table_data["termDelivery"].append(row["supplierTermDays"])
            del blocker

            self.tableData = table_data
            self.rows = len(parsed_rows)
            self._init_formula_expressions()
            self._clear_undo_history()
            self.mixedCurrencyWarningShown = False
            self.logisticCalculate(apply_filters=False)
            self.calculating(apply_filters=False, resize=False, update_summary=False)
            self._table_filter_all_visible = False
            self._table_filter_row_count = None
            self._apply_table_filters()
            resize_table_to_contents(table)
            update_total_tab_table = getattr(self, "_update_total_tab_table", None)
            if callable(update_total_tab_table):
                update_total_tab_table()

        Config.config["lastTable"] = filename
        self.saveConfig()
        Config.isTableOpened = True
        self._show_full_table_tab()

        scroll_to_top = getattr(table, "scrollToTop", None)
        if callable(scroll_to_top):
            scroll_to_top()
        scroll_to_left = getattr(table, "scrollToLeft", None)
        if callable(scroll_to_left):
            scroll_to_left()
        refresh_table_viewport(table, force_updates_enabled=True)

        hidden_rows = 0
        is_row_hidden = getattr(table, "isRowHidden", None)
        if callable(is_row_hidden):
            hidden_rows = sum(1 for row in range(table.rowCount()) if is_row_hidden(row))
        first_row_height = None
        row_height = getattr(table, "rowHeight", None)
        if callable(row_height) and table.rowCount() > 0:
            first_row_height = row_height(0)
        viewport = table.viewport() if callable(getattr(table, "viewport", None)) else None
        viewport_updates = None
        viewport_updates_enabled = getattr(viewport, "updatesEnabled", None)
        if callable(viewport_updates_enabled):
            viewport_updates = viewport_updates_enabled()
        Tool.write_log(
            "КП поставщика отображено: "
            f"rows={self.rows}, table_rows={table.rowCount()}, "
            f"hidden_rows={hidden_rows}, first_row_height={first_row_height}, "
            f"viewport_updates={viewport_updates}"
        )

        if warnings:
            trimmed = warnings[:10]
            message = "Найдены проблемы в таблице:\n- " + "\n- ".join(trimmed)
            if len(warnings) > 10:
                message += f"\n... и еще {len(warnings) - 10}"
            QMessageBox.warning(self, "Внимание", message)
