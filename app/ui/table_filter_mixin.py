from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QMenu


class TableFilterMixin:
    def _init_table_filters(self):
        table = self.ui.KpTable
        self._baseHeaderLabels = {}
        for col in range(table.columnCount()):
            item = table.horizontalHeaderItem(col)
            self._baseHeaderLabels[col] = item.text() if item is not None else str(col + 1)

        header = table.horizontalHeader()
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_filter_menu)
        self._refresh_filter_headers()

    def _column_values(self, col):
        values = set()
        for row in range(self.ui.KpTable.rowCount()):
            item = self.ui.KpTable.item(row, col)
            values.add((item.text() if item is not None else "").strip())
        return sorted((value for value in values if value != ""), key=lambda value: value.casefold())

    def _refresh_filter_headers(self):
        for col, base_label in self._baseHeaderLabels.items():
            item = self.ui.KpTable.horizontalHeaderItem(col)
            if item is None:
                continue
            if col in self.columnFilters:
                item.setText(f"{base_label} [Ф]")
            else:
                item.setText(base_label)

    @staticmethod
    def _match_filter_value(row_value, filter_spec):
        mode = filter_spec.get("mode", "equals")
        filter_value = str(filter_spec.get("value", "")).strip()
        row_text = str(row_value or "").strip()
        row_norm = row_text.casefold()
        filter_norm = filter_value.casefold()

        if mode == "equals":
            return row_norm == filter_norm
        if mode == "contains":
            return filter_norm in row_norm
        if mode == "starts_with":
            return row_norm.startswith(filter_norm)
        if mode == "ends_with":
            return row_norm.endswith(filter_norm)
        if mode == "empty":
            return row_text == ""
        return True

    def _set_text_filter(self, col, mode, prompt):
        current_filter = self.columnFilters.get(col, {})
        current_value = ""
        if current_filter.get("mode") == mode:
            current_value = str(current_filter.get("value", ""))

        value, ok = QInputDialog.getText(self, "Текстовый фильтр", prompt, text=current_value)
        if not ok:
            return False

        value = value.strip()
        if not value:
            self.error("Ошибка", "Введите текст для фильтра")
            return False

        self.columnFilters[col] = {"mode": mode, "value": value}
        return True

    def _apply_table_filters(self):
        table = self.ui.KpTable
        for row in range(table.rowCount()):
            is_visible = True
            for col, filter_spec in self.columnFilters.items():
                item = table.item(row, col)
                row_value = (item.text() if item is not None else "").strip()
                if not self._match_filter_value(row_value, filter_spec):
                    is_visible = False
                    break
            if is_visible and self.quickSearchText:
                row_has_match = False
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    row_text = (item.text() if item is not None else "").casefold()
                    if self.quickSearchText in row_text:
                        row_has_match = True
                        break
                is_visible = row_has_match
            table.setRowHidden(row, not is_visible)

    def _clear_all_filters(self):
        self.columnFilters.clear()
        self._refresh_filter_headers()
        self._apply_table_filters()

    def _show_filter_menu(self, pos):
        header = self.ui.KpTable.horizontalHeader()
        col = header.logicalIndexAt(pos)
        if col < 0:
            return

        menu = QMenu(self)
        column_name = self._baseHeaderLabels.get(col, self._column_title(col))
        title_action = menu.addAction(f"Фильтр: {column_name}")
        title_action.setEnabled(False)
        menu.addSeparator()

        clear_column_action = menu.addAction("Сбросить фильтр по столбцу")
        clear_column_action.setEnabled(col in self.columnFilters)
        clear_all_action = menu.addAction("Сбросить все фильтры")
        clear_all_action.setEnabled(bool(self.columnFilters))
        menu.addSeparator()

        contains_action = menu.addAction("Текстовый фильтр: содержит...")
        starts_with_action = menu.addAction("Текстовый фильтр: начинается с...")
        ends_with_action = menu.addAction("Текстовый фильтр: заканчивается на...")
        equals_text_action = menu.addAction("Текстовый фильтр: равно...")
        menu.addSeparator()

        all_values_action = menu.addAction("Все значения")
        empty_value_action = menu.addAction("(Пустые)")
        menu.addSeparator()

        value_actions = {}
        values = self._column_values(col)
        current_filter = self.columnFilters.get(col, {})
        current_mode = current_filter.get("mode")
        current_value = str(current_filter.get("value", "")).strip()
        current_value_norm = current_value.casefold()
        visible_limit = 150
        for value in values[:visible_limit]:
            action = menu.addAction(value)
            if current_mode == "equals" and value.casefold() == current_value_norm:
                action.setCheckable(True)
                action.setChecked(True)
            value_actions[action] = value

        if current_mode == "empty":
            empty_value_action.setCheckable(True)
            empty_value_action.setChecked(True)

        if len(values) > visible_limit:
            menu.addSeparator()
            extra_action = menu.addAction(f"Показано {visible_limit} из {len(values)} значений")
            extra_action.setEnabled(False)

        selected_action = menu.exec(header.mapToGlobal(pos))
        if selected_action is None:
            return
        if selected_action == clear_column_action:
            self.columnFilters.pop(col, None)
        elif selected_action == clear_all_action:
            self.columnFilters.clear()
        elif selected_action == contains_action:
            if not self._set_text_filter(col, "contains", f'{column_name}: содержит текст'):
                return
        elif selected_action == starts_with_action:
            if not self._set_text_filter(col, "starts_with", f'{column_name}: начинается с'):
                return
        elif selected_action == ends_with_action:
            if not self._set_text_filter(col, "ends_with", f'{column_name}: заканчивается на'):
                return
        elif selected_action == equals_text_action:
            if not self._set_text_filter(col, "equals", f'{column_name}: равно тексту'):
                return
        elif selected_action == all_values_action:
            self.columnFilters.pop(col, None)
        elif selected_action == empty_value_action:
            self.columnFilters[col] = {"mode": "empty", "value": ""}
        elif selected_action in value_actions:
            self.columnFilters[col] = {"mode": "equals", "value": value_actions[selected_action]}
        else:
            return

        self._refresh_filter_headers()
        self._apply_table_filters()

