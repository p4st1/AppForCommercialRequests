from PySide6.QtCore import QSignalBlocker

from app.ui.table_autosize import resize_table_to_contents
from config import Config
from tools import DatabaseTools as Tool


class TableCellEditMixin:
    def _update_total_price_cell(self, row):
        amount = self.tableData["amount"][row]
        unit_price = self.tableData["unitPrice"][row]
        currency = self.tableData["currency"][row]
        total_price = self._round_money(amount * unit_price)
        self.tableData["totalPrice"][row] = total_price
        self._set_table_item(row, 6, Tool.formatPrice(str(total_price), currency), editable=False)

    def _restore_edited_cell(self, row, col):
        if col == 4:
            self._set_table_item(row, col, self.tableData["amount"][row], editable=True)
            return
        if col == 5:
            self._set_table_item(
                row,
                col,
                Tool.formatPrice(
                    str(self.tableData["unitPrice"][row]),
                    self.tableData["currency"][row],
                ),
                editable=True,
            )
            return
        if col == 14:
            self._set_table_item(
                row,
                col,
                f"{self.tableData['termDelivery'][row]} дней",
                editable=True,
            )

    def tableItemChanged(self, item):
        if not Config.isTableOpened or item is None:
            return

        row = item.row()
        col = item.column()
        if row < 0 or row >= self.rows or col not in self.EDITABLE_COLUMNS:
            return

        self._push_pending_edit_undo_state()

        text = item.text().strip()
        needs_manual_summary_refresh = col in {0, 1, 2, 3}
        if col in self.FORMULA_EDITABLE_COLUMNS:
            target_rows = self._selected_rows_in_column(col)
            if row not in target_rows:
                target_rows.append(row)
            self._apply_formula_to_rows(col, target_rows, text, source_row=row)
            self._apply_table_filters()
            return

        try:
            if col == 4:
                parsed_amount = Tool.parse_int(text, f"Кол-во (строка {row + 1})", allow_zero=False)
                self.tableData["amount"][row] = parsed_amount
                blocker = QSignalBlocker(self.ui.KpTable)
                self._set_table_item(row, 4, parsed_amount, editable=True)
                self._update_total_price_cell(row)
                del blocker
                self.logisticCalculate()
                self.calculating()
            elif col == 5:
                currency, price_text = Tool.parsePrice(text)
                if not currency:
                    currency = self.tableData["currency"][row]
                    price_text = text
                parsed_price = Tool.parse_float(price_text, f"Цена (строка {row + 1})", allow_zero=True)
                self.tableData["currency"][row] = currency
                self.tableData["unitPrice"][row] = parsed_price
                blocker = QSignalBlocker(self.ui.KpTable)
                self._set_table_item(row, 5, Tool.formatPrice(str(parsed_price), currency), editable=True)
                self._update_total_price_cell(row)
                del blocker
                self.logisticCalculate()
                self.calculating()
            elif col == 14:
                parsed_term = Tool.parse_delivery_days(text)
                self.tableData["termDelivery"][row] = parsed_term
                blocker = QSignalBlocker(self.ui.KpTable)
                self._set_table_item(row, 14, f"{parsed_term} дней", editable=True)
                del blocker
                self.calculating()
            else:
                blocker = QSignalBlocker(self.ui.KpTable)
                self._set_table_item(row, col, text, editable=True)
                del blocker
        except ValueError as e:
            self.error("Ошибка", str(e))
            blocker = QSignalBlocker(self.ui.KpTable)
            self._restore_edited_cell(row, col)
            del blocker
        self._apply_table_filters()
        resize_table_to_contents(self.ui.KpTable)
        if needs_manual_summary_refresh:
            self._update_total_tab_table()
