from PySide6.QtCore import QSignalBlocker

from app.ui.table_autosize import resize_table_to_contents
from config import Config


class TableUndoMixin:
    def _capture_table_state(self):
        table = self.ui.KpTable
        table_rows = []
        for row in range(table.rowCount()):
            row_values = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                row_values.append(item.text() if item is not None else "")
            table_rows.append(row_values)

        return {
            "table_rows": table_rows,
            "table_data": {key: list(values) for key, values in self.tableData.items()},
            "formula_expressions": {
                col: list(self.formulaExpressions.get(col, [])) for col in self.FORMULA_EDITABLE_COLUMNS
            },
            "mixed_currency_warning": bool(self.mixedCurrencyWarningShown),
        }

    def _push_undo_state(self):
        if not Config.isTableOpened or self._is_restoring_undo:
            return
        self._pending_edit_undo_state = None
        self._undo_stack.append(self._capture_table_state())
        if len(self._undo_stack) > self.MAX_UNDO_STATES:
            self._undo_stack.pop(0)

    def _restore_table_state(self, state):
        self._clear_formula_fill_highlight()
        self._pending_edit_undo_state = None
        table_rows = state.get("table_rows", [])
        table = self.ui.KpTable
        self._is_restoring_undo = True
        try:
            blocker = QSignalBlocker(table)
            table.setRowCount(len(table_rows))
            for row, row_values in enumerate(table_rows):
                for col in range(table.columnCount()):
                    value = row_values[col] if col < len(row_values) else ""
                    self._set_table_item(row, col, value, editable=(col in self.EDITABLE_COLUMNS))
            del blocker
        finally:
            self._is_restoring_undo = False

        table_data_state = state.get("table_data", {})
        self.tableData = {
            "amount": list(table_data_state.get("amount", [])),
            "currency": list(table_data_state.get("currency", [])),
            "unitPrice": list(table_data_state.get("unitPrice", [])),
            "totalPrice": list(table_data_state.get("totalPrice", [])),
            "termDelivery": list(table_data_state.get("termDelivery", [])),
            "logistic": list(table_data_state.get("logistic", [])),
        }
        formula_state = state.get("formula_expressions", {})
        self.formulaExpressions = {
            col: list(formula_state.get(col, [])) for col in self.FORMULA_EDITABLE_COLUMNS
        }
        self.rows = len(table_rows)
        self.mixedCurrencyWarningShown = bool(state.get("mixed_currency_warning", False))
        Config.isTableOpened = self.rows > 0
        self._apply_table_filters()
        resize_table_to_contents(table)
        self._update_total_tab_table()

    def _undo_last_table_change(self):
        if not self._undo_stack:
            return
        state = self._undo_stack.pop()
        self._restore_table_state(state)

    def _clear_undo_history(self):
        self._undo_stack.clear()
        self._pending_edit_undo_state = None

    def _capture_state_before_cell_edit(self, row, col):
        if not Config.isTableOpened or self._is_restoring_undo:
            return
        if row < 0 or col not in self.EDITABLE_COLUMNS:
            return
        self._pending_edit_undo_state = self._capture_table_state()

    def _push_pending_edit_undo_state(self):
        if self._pending_edit_undo_state is None:
            return
        self._undo_stack.append(self._pending_edit_undo_state)
        self._pending_edit_undo_state = None
        if len(self._undo_stack) > self.MAX_UNDO_STATES:
            self._undo_stack.pop(0)
