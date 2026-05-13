from tools import DatabaseTools as Tool


class TableSummaryMixin:
    def getTableData(self):
        table_data = []
        row_count = self.ui.KpTable.rowCount()
        for row in range(row_count):
            row_data = []
            for col in self.SUMMARY_SOURCE_COLUMNS:
                item = self.ui.KpTable.item(row, col)
                row_data.append(item.text() if item is not None else "")
            table_data.append(row_data)
        return table_data

    def _has_mixed_currencies(self):
        return len(set(self.tableData.get("currency", []))) > 1

    def _table_column_total(self, col: int):
        total = 0.0
        currency = ""
        for row in range(self.ui.KpTable.rowCount()):
            item = self.ui.KpTable.item(row, col)
            if item is None:
                continue
            symb, amount_text = Tool.parsePrice(item.text())
            if symb and not currency:
                currency = symb
            try:
                total += float(str(amount_text).replace(" ", "").replace(",", "."))
            except ValueError as e:
                Tool.log_exception(
                    f"Не удалось распарсить сумму в строке {row + 1}: {amount_text}",
                    e,
                    include_traceback=False,
                )
                continue
        return self._round_money(total), currency
