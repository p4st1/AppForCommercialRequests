from PySide6.QtCore import Qt, QSignalBlocker
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from config import Config


class FormulaEditingMixin:
    @staticmethod
    def _format_row_ranges(rows):
        normalized = sorted(set(int(row) for row in rows if int(row) >= 0))
        if not normalized:
            return ""

        one_based = [row + 1 for row in normalized]
        ranges = []
        start = one_based[0]
        end = one_based[0]

        for value in one_based[1:]:
            if value == end + 1:
                end = value
                continue
            ranges.append((start, end))
            start = value
            end = value
        ranges.append((start, end))

        return ", ".join(f"{left}-{right}" if left != right else str(left) for left, right in ranges)

    def _clear_formula_fill_highlight(self):
        if hasattr(self, "_formula_fill_highlight_timer"):
            self._formula_fill_highlight_timer.stop()
        if not self._formula_fill_highlight_cells:
            return

        table = self.ui.KpTable
        blocker = QSignalBlocker(table)
        for row, col, previous_background in self._formula_fill_highlight_cells:
            if row < 0 or col < 0 or row >= table.rowCount() or col >= table.columnCount():
                continue
            item = table.item(row, col)
            if item is None:
                continue
            item.setData(Qt.ItemDataRole.BackgroundRole, previous_background)
        del blocker
        self._formula_fill_highlight_cells = []

    def _show_formula_fill_feedback(self, col, rows, source_row=None):
        table = self.ui.KpTable
        self._clear_formula_fill_highlight()

        highlighted = []
        highlight_color = QColor("#FFE9A8")
        blocker = QSignalBlocker(table)
        for row in sorted(set(rows)):
            if row < 0 or row >= table.rowCount():
                continue
            item = table.item(row, col)
            if item is None:
                continue
            previous_background = item.data(Qt.ItemDataRole.BackgroundRole)
            item.setData(Qt.ItemDataRole.BackgroundRole, highlight_color)
            highlighted.append((row, col, previous_background))
        del blocker

        self._formula_fill_highlight_cells = highlighted
        if highlighted:
            self._formula_fill_highlight_timer.start(1200)

        status_bar = self.statusBar()
        if status_bar is None:
            return
        rows_label = self._format_row_ranges(rows)
        if not rows_label:
            return
        source_text = f" из строки {source_row + 1}" if source_row is not None and source_row >= 0 else ""
        status_bar.showMessage(
            f'Формула в столбце "{self._column_title(col)}" протянута{source_text} по строкам: {rows_label}',
            2500,
        )

    def _apply_formula_to_rows(self, col, rows, formula_text, source_row=None):
        target_rows = sorted(set(rows))
        if col not in self.FORMULA_EDITABLE_COLUMNS or not target_rows:
            return False

        text = str(formula_text or "").strip()
        if not text:
            if source_row is not None:
                message = f'Строка {source_row + 1}, столбец "{self._column_title(col)}": формула не может быть пустой'
            else:
                message = f'Столбец "{self._column_title(col)}": формула не может быть пустой'
            self.error(
                "Ошибка",
                message,
            )
            return False

        old_formulas = {row: self.formulaExpressions[col][row] for row in target_rows}
        try:
            for row in target_rows:
                self.formulaExpressions[col][row] = text
            self.calculating()
            if len(target_rows) > 1:
                self._show_formula_fill_feedback(col, target_rows, source_row=source_row)
            return True
        except ValueError as e:
            for row, previous_value in old_formulas.items():
                self.formulaExpressions[col][row] = previous_value
            self.calculating()
            self.error("Ошибка", str(e))
            return False

    def _fill_formula_to_selection(self):
        if not Config.isTableOpened or self.rows <= 0:
            return

        table = self.ui.KpTable
        status_bar = self.statusBar()
        source_col = table.currentColumn()
        if source_col not in self.FORMULA_EDITABLE_COLUMNS:
            if status_bar is not None:
                status_bar.showMessage("Выберите ячейку в столбце с формулой для протягивания", 2500)
            return

        selected_rows = self._selected_rows_in_column(source_col)
        selected_rows = sorted(set(selected_rows))
        if len(selected_rows) <= 1:
            if status_bar is not None:
                status_bar.showMessage("Для протягивания формулы выделите минимум две строки", 2500)
            return

        source_row = selected_rows[0]
        self._push_undo_state()
        source_formula = self.formulaExpressions[source_col][source_row]
        self._apply_formula_to_rows(source_col, selected_rows, source_formula, source_row=source_row)
        self._apply_table_filters()

    def _fill_formula_on_ctrl_selection(self):
        if not Config.isTableOpened or self.rows <= 0:
            return
        if self._is_restoring_undo:
            return

        modifiers = QApplication.keyboardModifiers()
        if not (modifiers & Qt.KeyboardModifier.ControlModifier):
            return

        table = self.ui.KpTable
        source_row = table.currentRow()
        source_col = table.currentColumn()
        if source_col not in self.FORMULA_EDITABLE_COLUMNS:
            return
        if source_row < 0 or source_row >= self.rows:
            return

        selected_rows = self._selected_rows_in_column(source_col)
        selected_rows = sorted(set(selected_rows))
        if len(selected_rows) <= 1:
            return

        source_formula = str(self.formulaExpressions[source_col][source_row] or "").strip()
        if not source_formula:
            return

        if all(self.formulaExpressions[source_col][row] == source_formula for row in selected_rows):
            return

        self._push_undo_state()
        if self._apply_formula_to_rows(source_col, selected_rows, source_formula, source_row=source_row):
            self._apply_table_filters()
