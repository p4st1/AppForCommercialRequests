from config import Config
from tools import DatabaseTools as Tool


class FormulaInputMixin:
    def _parse_input_parameters(self, show_error=True):
        try:
            custom = float(Tool.evalWithVars(self.ui.customLine.text().replace(",", ".")))
            markup = float(Tool.evalWithVars(self.ui.markupLine.text().replace(",", ".")))
            logistic = float(Tool.evalWithVars(self.ui.logisticNum.text().replace(",", ".")))
            term_delivery = Tool.parse_int(self.ui.termDeliveryLine.text(), "Срок поставки", allow_zero=True)
            if custom <= 0:
                raise ValueError('Поле "Таможня" должно быть положительным')
            if markup <= 0:
                raise ValueError('Поле "Наценка" должно быть положительным')
            if logistic < 0:
                raise ValueError('Поле "Логистика" должно быть неотрицательным')
        except Exception as e:
            if show_error:
                self.error("Ошибка", str(e))
            return None

        self.formulaCustom = custom
        self.formulaMarkup = markup
        self.formulaLogistic = logistic
        self.termDeliveryDays = term_delivery

        self.ui.customLine.setText(self._fmt_number(custom))
        self.ui.markupLine.setText(self._fmt_number(markup))
        self.ui.logisticNum.setText(self._fmt_number(logistic))
        self.ui.termDeliveryLine.setText(str(term_delivery))

        return {
            "custom": custom,
            "markup": markup,
            "logistic": logistic,
            "termDelivery": term_delivery,
        }

    def processFormula(self):
        parsed = self._parse_input_parameters(show_error=True)
        if parsed is None:
            return

        if Config.isTableOpened:
            try:
                self.logisticCalculate(apply_filters=False)
                self.calculating()
            except ValueError as e:
                self.error("Ошибка", str(e))
