from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem


class TableItemMixin:
    def _set_table_item(self, row, col, text, editable):
        item = self.ui.KpTable.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            self.ui.KpTable.setItem(row, col, item)

        item.setText(str(text))
        flags = item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if editable:
            flags |= Qt.ItemFlag.ItemIsEditable
        else:
            flags &= ~Qt.ItemFlag.ItemIsEditable
        item.setFlags(flags)
