from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidgetItem

from app.ui.table_autosize import configure_table_autosize, resize_table_to_contents


class TableSummaryViewMixin:
    def _setup_total_tab_table(self):
        table = self.ui.tableWidget_3
        table.setColumnCount(len(self.SUMMARY_HEADERS))
        table.setHorizontalHeaderLabels(self.SUMMARY_HEADERS)
        table.setRowCount(0)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(False)
        configure_table_autosize(table)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        table.setColumnWidth(1, 300)
        for col in range(2, len(self.SUMMARY_HEADERS)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

    def _update_total_tab_table(self):
        table = self.ui.tableWidget_3
        rows = self.getTableData() if self.ui.KpTable.rowCount() > 0 else []

        blocker = QSignalBlocker(table)
        table.clearContents()
        table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        del blocker
        resize_table_to_contents(table)
