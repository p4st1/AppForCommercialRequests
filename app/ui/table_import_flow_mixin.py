from pathlib import Path

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.ui.table_autosize import resize_table_to_contents
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
            self.error("Ошибка", f"Невозможно прочитать таблицу\n{e}")
            return

        self.ui.KpTable.setRowCount(len(parsed_rows))
        self.tableData = {
            "amount": [],
            "currency": [],
            "unitPrice": [],
            "totalPrice": [],
            "termDelivery": [],
            "logistic": [],
        }

        blocker = QSignalBlocker(self.ui.KpTable)
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

            self.tableData["amount"].append(row["qty"])
            self.tableData["currency"].append(row["currency"])
            self.tableData["unitPrice"].append(row["unitPrice"])
            self.tableData["totalPrice"].append(total_price)
            self.tableData["termDelivery"].append(row["supplierTermDays"])
        del blocker

        self.rows = len(parsed_rows)
        self._init_formula_expressions()
        self._clear_undo_history()
        self.mixedCurrencyWarningShown = False
        self.logisticCalculate()
        self.calculating()
        resize_table_to_contents(self.ui.KpTable)
        self._apply_table_filters()

        Config.config["lastTable"] = filename
        self.saveConfig()
        Config.isTableOpened = True
        self._show_full_table_tab()

        if warnings:
            trimmed = warnings[:10]
            message = "Найдены проблемы в таблице:\n- " + "\n- ".join(trimmed)
            if len(warnings) > 10:
                message += f"\n... и еще {len(warnings) - 10}"
            QMessageBox.warning(self, "Внимание", message)
