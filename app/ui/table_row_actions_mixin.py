from PySide6.QtCore import QSignalBlocker

from app.ui.table_autosize import resize_table_to_contents
from config import Config


class TableRowActionsMixin:
    def _selected_table_cells(self):
        table = self.ui.KpTable
        cells = set()
        selection_model = table.selectionModel()
        if selection_model is not None:
            cells.update(
                (index.row(), index.column())
                for index in selection_model.selectedIndexes()
            )

        current_row = table.currentRow()
        current_col = table.currentColumn()
        if current_row >= 0 and current_col >= 0:
            cells.add((current_row, current_col))

        return sorted(
            (row, col)
            for row, col in cells
            if 0 <= row < table.rowCount() and 0 <= col < table.columnCount()
        )

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

    def _clear_dependent_cells_after_source_clear(self, row, col):
        if col in {4, 5}:
            if 0 <= row < len(self.tableData.get("totalPrice", [])):
                self.tableData["totalPrice"][row] = 0
            for dependent_col in (6, 7, 8, 9, 10, 11, 12):
                self._set_table_item(
                    row,
                    dependent_col,
                    "",
                    editable=(dependent_col in self.FORMULA_EDITABLE_COLUMNS),
                )
        elif col == 14:
            self._set_table_item(row, 13, "", editable=True)

    def _clear_selected_cells(self):
        if not Config.isTableOpened or self.ui.KpTable.rowCount() == 0:
            return

        clearable_columns = set(getattr(self, "BASE_EDITABLE_COLUMNS", self.EDITABLE_COLUMNS))
        selected_cells = [
            (row, col)
            for row, col in self._selected_table_cells()
            if col in clearable_columns
        ]
        if not selected_cells:
            status_bar = self.statusBar()
            if status_bar is not None:
                status_bar.showMessage("Выберите редактируемые ячейки для очистки", 2500)
            return

        self._push_undo_state()

        table = self.ui.KpTable
        blocker = QSignalBlocker(table)
        for row, col in selected_cells:
            if col == 4 and 0 <= row < len(self.tableData.get("amount", [])):
                self.tableData["amount"][row] = 0
            elif col == 5 and 0 <= row < len(self.tableData.get("unitPrice", [])):
                self.tableData["unitPrice"][row] = 0
            elif col == 14 and 0 <= row < len(self.tableData.get("termDelivery", [])):
                self.tableData["termDelivery"][row] = 0
            self._set_table_item(row, col, "", editable=True)
            self._clear_dependent_cells_after_source_clear(row, col)
        del blocker

        self.mixedCurrencyWarningShown = False
        self._apply_table_filters()
        resize_table_to_contents(table)
        self._update_total_tab_table()

        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(f"Очищено ячеек: {len(selected_cells)}", 2500)

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
