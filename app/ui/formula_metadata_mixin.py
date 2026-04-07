class FormulaMetadataMixin:
    def _get_formula_for_editor(self, row, col):
        if col not in self.FORMULA_EDITABLE_COLUMNS:
            return None
        formulas = self.formulaExpressions.get(col, [])
        if row < 0 or row >= len(formulas):
            return None
        return formulas[row]

    @staticmethod
    def _default_formula(col):
        defaults = {
            8: "Custom*Logistic",
            9: "Customs/Amount",
            10: "UnitSalePrice*Markup",
            11: "RealPrice*Amount",
            13: "SupplierTerm+TermDelivery",
        }
        return defaults[col]

    def _column_title(self, col):
        if col in self._baseHeaderLabels:
            return self._baseHeaderLabels[col]
        item = self.ui.KpTable.horizontalHeaderItem(col)
        return item.text() if item is not None else str(col)
