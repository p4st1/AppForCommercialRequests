from PySide6.QtCore import QSignalBlocker

from config import Config


class TableRowActionsMixin:
    def _selected_table_rows(self):
        table = self.ui.KpTable
        rows = set()
        selection_model = table.selectionModel()
        if selection_model is not None:
            rows.update(index.row() for index in selection_model.selectedRows())
            if not rows:
                rows.update(index.row() for index in selection_model.selectedIndexes())
        current_row = table.currentRow()
        if current_row >= 0:
            rows.add(current_row)
        return sorted(row for row in rows if 0 <= row < table.rowCount())

    def _selected_rows_in_column(self, col):
        table = self.ui.KpTable
        rows = set()
        selection_model = table.selectionModel()
        if selection_model is not None:
            rows.update(index.row() for index in selection_model.selectedIndexes() if index.column() == col)
            if not rows:
                rows.update(index.row() for index in selection_model.selectedRows())
            if not rows:
                rows.update(index.row() for index in selection_model.selectedIndexes())
        current_row = table.currentRow()
        current_col = table.currentColumn()
        if current_col == col and current_row >= 0:
            rows.add(current_row)
        return sorted(row for row in rows if 0 <= row < self.rows)

    def _duplicate_selected_rows(self):
        if not Config.isTableOpened or self.ui.KpTable.rowCount() == 0:
            return

        selected_rows = self._selected_table_rows()
        if not selected_rows:
            return

        self._push_undo_state()

        table = self.ui.KpTable
        blocker = QSignalBlocker(table)
        offset = 0
        for source_row in selected_rows:
            source_index = source_row + offset
            insert_index = source_index + 1
            table.insertRow(insert_index)

            for col in range(table.columnCount()):
                src_item = table.item(source_index, col)
                src_text = src_item.text() if src_item is not None else ""
                self._set_table_item(insert_index, col, src_text, editable=(col in self.EDITABLE_COLUMNS))

            for key in ("amount", "currency", "unitPrice", "totalPrice", "termDelivery", "logistic"):
                self.tableData[key].insert(insert_index, self.tableData[key][source_index])
            for col in self.FORMULA_EDITABLE_COLUMNS:
                self.formulaExpressions[col].insert(insert_index, self.formulaExpressions[col][source_index])

            offset += 1
        del blocker

        self.rows = table.rowCount()
        self.mixedCurrencyWarningShown = False
        self.logisticCalculate()
        self.calculating()
        self._apply_table_filters()
        self._update_total_tab_table()

    def _delete_selected_rows(self):
        if not Config.isTableOpened or self.ui.KpTable.rowCount() == 0:
            return

        selected_rows = self._selected_table_rows()
        if not selected_rows:
            return

        self._push_undo_state()

        table = self.ui.KpTable
        blocker = QSignalBlocker(table)
        for row in sorted(selected_rows, reverse=True):
            if 0 <= row < table.rowCount():
                table.removeRow(row)
            for key in ("amount", "currency", "unitPrice", "totalPrice", "termDelivery", "logistic"):
                if 0 <= row < len(self.tableData[key]):
                    del self.tableData[key][row]
            for col in self.FORMULA_EDITABLE_COLUMNS:
                formulas = self.formulaExpressions.get(col, [])
                if 0 <= row < len(formulas):
                    del formulas[row]
        del blocker

        self.rows = table.rowCount()
        self.mixedCurrencyWarningShown = False
        if self.rows == 0:
            self.closeTable(clear_undo=False)
            return

        self.logisticCalculate()
        self.calculating()
        self._apply_table_filters()
        self._update_total_tab_table()
