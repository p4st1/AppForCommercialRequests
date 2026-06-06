from PySide6.QtCore import Qt, QSignalBlocker
from PySide6.QtWidgets import QMessageBox

from app.models.calculation_models import CalculationRowInput, CalculationSettings
from app.ui.table_autosize import resize_table_to_contents, table_update_guard
from config import Config
from tools import DatabaseTools as Tool


class CalculationFlowMixin:
    def calculating(self, *, apply_filters=True, resize=True, update_summary=True):
        if not self.tableData["amount"] or not self.tableData["logistic"]:
            return

        for col in self.FORMULA_EDITABLE_COLUMNS:
            if len(self.formulaExpressions.get(col, [])) != self.rows:
                self._init_formula_expressions()
                break

        named_parameters = self._load_formula_parameters()
        vat_multiplier = self._vat_multiplier()
        calculation_settings = CalculationSettings(
            custom=float(self.formulaCustom),
            markup=float(self.formulaMarkup),
            vat_multiplier=float(vat_multiplier),
            term_delivery_days=int(self.termDeliveryDays),
        )
        with table_update_guard(self.ui.KpTable):
            blocker = QSignalBlocker(self.ui.KpTable)
            for row_num in range(self.rows):
                row_input = CalculationRowInput(
                    amount=float(self.tableData["amount"][row_num]),
                    unit_price=float(self.tableData["unitPrice"][row_num]),
                    total_price=float(self.tableData["totalPrice"][row_num]),
                    currency=str(self.tableData["currency"][row_num]),
                    logistic_value=float(self.tableData["logistic"][row_num]),
                    supplier_term=float(self.tableData["termDelivery"][row_num]),
                )
                row_formulas = {
                    8: self.formulaExpressions[8][row_num],
                    9: self.formulaExpressions[9][row_num],
                    10: self.formulaExpressions[10][row_num],
                    11: self.formulaExpressions[11][row_num],
                    13: self.formulaExpressions[13][row_num],
                }
                row_result = self.calculation_service.calculate_row(
                    row_index=row_num,
                    row_input=row_input,
                    formulas=row_formulas,
                    named_parameters=named_parameters,
                    settings=calculation_settings,
                    column_title_resolver=self._column_title,
                )
                currency = row_input.currency

                self._set_table_item(
                    row_num,
                    8,
                    Tool.formatPrice(str(row_result.customs_sum), currency),
                    editable=True,
                )
                self._set_table_item(
                    row_num,
                    9,
                    Tool.formatPrice(str(row_result.unit_sale_price), currency),
                    editable=True,
                )
                self._set_table_item(
                    row_num,
                    10,
                    Tool.formatPrice(str(row_result.real_price), currency),
                    editable=True,
                )
                self._set_table_item(
                    row_num,
                    11,
                    Tool.formatPrice(str(row_result.total_without_vat), currency),
                    editable=True,
                )
                self._set_table_item(
                    row_num,
                    12,
                    Tool.formatPrice(str(row_result.total_with_vat), currency),
                    editable=False,
                )
                self._set_table_item(
                    row_num,
                    13,
                    f"{row_result.total_delivery_days} дней",
                    editable=True,
                )
            del blocker

        if apply_filters:
            self._apply_table_filters()
        if resize:
            resize_table_to_contents(self.ui.KpTable)
        if update_summary:
            self._update_total_tab_table()

    def logisticVarChanged(self, _):
        if Config.isTableOpened:
            try:
                self.logisticCalculate(apply_filters=False)
                self.calculating()
            except ValueError as e:
                self.error("Ошибка", str(e))

    def logisticCalculate(self, *, apply_filters=True):
        if not self.tableData["totalPrice"]:
            return

        logistic_var = self.ui.logisticVar.currentIndex()
        currencies = set(self.tableData["currency"])
        if logistic_var == 1 and len(currencies) > 1:
            if not self.mixedCurrencyWarningShown:
                QMessageBox.warning(
                    self,
                    "Внимание",
                    "Режим 'распределение' недоступен при смешанной валюте. "
                    "Переключено на режим 'коэффициент'.",
                )
                self.mixedCurrencyWarningShown = True
            self.ui.logisticVar.blockSignals(True)
            self.ui.logisticVar.setCurrentIndex(0)
            self.ui.logisticVar.blockSignals(False)
            logistic_var = 0

        logistic_num = self.formulaLogistic
        logistic_num_text = self._fmt_number(logistic_num)
        total_sum = sum(self.tableData["totalPrice"])
        total_sum_text = self._fmt_number(total_sum)
        self.tableData["logistic"] = []

        with table_update_guard(self.ui.KpTable):
            blocker = QSignalBlocker(self.ui.KpTable)
            for row_num in range(self.rows):
                base_total = self.tableData["totalPrice"][row_num]
                if logistic_var == 1:
                    if total_sum <= 0:
                        f = 0
                        formula_text = "0"
                    else:
                        f = self._round_money(base_total + logistic_num / total_sum * base_total)
                        formula_text = f"TotalPrice+{logistic_num_text}/{total_sum_text}*TotalPrice"
                else:
                    f = self._round_money(base_total * logistic_num)
                    formula_text = f"TotalPrice*{logistic_num_text}"
                currency = self.tableData["currency"][row_num]
                self._set_table_item(
                    row_num,
                    7,
                    Tool.formatPrice(str(f), currency),
                    editable=False,
                )
                logistic_item = self.ui.KpTable.item(row_num, 7)
                if logistic_item is not None:
                    logistic_item.setData(Qt.ItemDataRole.UserRole, formula_text)
                self.tableData["logistic"].append(f)
            del blocker
        if apply_filters:
            self._apply_table_filters()
