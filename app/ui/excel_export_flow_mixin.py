from PySide6.QtCore import Qt

from config import Config
from create import createExcelFile as exportExcelFile


class ExcelExportFlowMixin:
    def exportExcel(self):
        if not Config.isTableOpened:
            self.error("Ошибка", "Загрузите КП поставщика")
            return
        if self._has_mixed_currencies():
            self.error(
                "Ошибка",
                "Создание Excel для таблицы со смешанной валютой не поддерживается.",
            )
            return

        parsed = self._parse_input_parameters(show_error=True)
        if parsed is None:
            return

        tableData = []
        logistic_formulas = []
        row_count = self.ui.KpTable.rowCount()
        column_count = self.ui.KpTable.columnCount()

        for row in range(row_count):
            row_data = []
            for col in range(column_count):
                item = self.ui.KpTable.item(row, col)
                row_data.append(item.text() if item is not None else "")
            tableData.append(row_data)
            logistic_item = self.ui.KpTable.item(row, 7)
            logistic_formula = logistic_item.data(Qt.ItemDataRole.UserRole) if logistic_item is not None else ""
            if isinstance(logistic_formula, dict):
                logistic_formula = logistic_formula.get("formula", "")
            logistic_formulas.append(str(logistic_formula or ""))

        export_result = exportExcelFile(
            {
                "table_rows": tableData,
                "request_number": self.ui.requestNumberLine.text().strip(),
                "logistic_mode": self.ui.logisticVar.currentIndex(),
                "logistic_value": parsed["logistic"],
                "custom_value": parsed["custom"],
                "markup_value": parsed["markup"],
                "term_delivery": parsed["termDelivery"],
                "vat_multiplier": self._vat_multiplier(),
                "named_parameters": self._load_formula_parameters(),
                "logistic_formulas": logistic_formulas,
                "formula_expressions": {
                    col: list(self.formulaExpressions.get(col, [])) for col in self.FORMULA_EDITABLE_COLUMNS
                },
            }
        )
        if not getattr(export_result, "success", False):
            error_text = getattr(export_result, "error_message", "") or "Не удалось создать Excel"
            self.error("Ошибка", error_text)
            return

        total_amount, currency = self._table_column_total(12)
        self.history_service.record_excel_export(
            items_count=row_count,
            total_amount=total_amount,
            currency=currency,
            file_path=getattr(export_result, "output_path", ""),
        )
        self.history_service.save()
        self.updateHistoryTable()
