from config import Config
from tools import DatabaseTools as Tool


class FormulaConfigMixin:
    @staticmethod
    def _normalize_param_name(value):
        return str(value or "").strip().casefold()

    def _load_formula_parameters(self):
        params_data = Tool.load_json(Config.vars_path)
        parameters = {}
        for values in params_data.get("parameters", {}).values():
            if len(values) < 3:
                continue
            variable, value, calc_type = values[0], values[1], values[2]
            key = self._normalize_param_name(variable)
            if not key:
                continue
            parameters[key] = (str(value).replace(",", "."), str(calc_type))
        return parameters

    def _eval_formula(self, formula, context, row, col, parameters):
        return self.calculation_service.evaluate_formula(
            formula=formula,
            context=context,
            row=row,
            col=col,
            parameters=parameters,
            column_title_resolver=self._column_title,
        )

    def _init_formula_expressions(self):
        self.formulaExpressions = {col: [] for col in self.FORMULA_EDITABLE_COLUMNS}
        for _ in range(self.rows):
            for col in self.FORMULA_EDITABLE_COLUMNS:
                self.formulaExpressions[col].append(self._default_formula(col))
