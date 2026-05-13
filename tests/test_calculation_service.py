import unittest

from app.models.calculation_models import CalculationRowInput, CalculationSettings
from app.services.calculation_service import CalculationService


class CalculationServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = CalculationService()
        self.column_titles = {
            8: "Таможня",
            9: "Цена за ед.",
            10: "Цена реализации за ед. без НДС",
            11: "Итого реализации без НДС",
            12: "Итого с НДС",
            13: "Срок поставки",
        }
        self.default_formulas = {
            8: "Custom*Logistic",
            9: "Customs/Amount",
            10: "UnitSalePrice*Markup",
            11: "RealPrice*Amount",
            13: "SupplierTerm+TermDelivery",
        }
        self.named_parameters = {}

    def _title(self, col):
        return self.column_titles.get(col, str(col))

    def test_calculate_row_default_formula_chain(self):
        row_input = CalculationRowInput(
            amount=10,
            unit_price=5,
            total_price=50,
            currency="¥",
            logistic_value=50,
            supplier_term=10,
        )
        settings = CalculationSettings(
            custom=1,
            markup=1.2,
            vat_multiplier=1.2,
            term_delivery_days=15,
        )

        result = self.service.calculate_row(
            row_index=0,
            row_input=row_input,
            formulas=self.default_formulas,
            named_parameters=self.named_parameters,
            settings=settings,
            column_title_resolver=self._title,
        )

        self.assertEqual(result.customs_sum, 50.0)
        self.assertEqual(result.unit_sale_price, 5.0)
        self.assertEqual(result.real_price, 6.0)
        self.assertEqual(result.total_without_vat, 60.0)
        self.assertEqual(result.total_with_vat, 72.0)
        self.assertEqual(result.total_delivery_days, 25)

    def test_calculate_row_uses_zero_term_delivery_for_zero_supplier_term(self):
        row_input = CalculationRowInput(
            amount=10,
            unit_price=5,
            total_price=50,
            currency="¥",
            logistic_value=50,
            supplier_term=0,
        )
        settings = CalculationSettings(
            custom=1,
            markup=1.2,
            vat_multiplier=1.2,
            term_delivery_days=15,
        )

        result = self.service.calculate_row(
            row_index=0,
            row_input=row_input,
            formulas=self.default_formulas,
            named_parameters=self.named_parameters,
            settings=settings,
            column_title_resolver=self._title,
        )

        self.assertEqual(result.total_delivery_days, 0)

    def test_calculate_row_rejects_negative_formula_result(self):
        row_input = CalculationRowInput(
            amount=10,
            unit_price=5,
            total_price=50,
            currency="¥",
            logistic_value=50,
            supplier_term=10,
        )
        settings = CalculationSettings(
            custom=1,
            markup=1.2,
            vat_multiplier=1.2,
            term_delivery_days=15,
        )
        formulas = dict(self.default_formulas)
        formulas[10] = "UnitSalePrice-999"

        with self.assertRaises(ValueError) as context:
            self.service.calculate_row(
                row_index=0,
                row_input=row_input,
                formulas=formulas,
                named_parameters=self.named_parameters,
                settings=settings,
                column_title_resolver=self._title,
            )

        self.assertIn("Цена реализации за ед. без НДС", str(context.exception))
        self.assertIn("не может быть отрицательным", str(context.exception))

    def test_evaluate_formula_rejects_unknown_variable(self):
        with self.assertRaises(ValueError) as context:
            self.service.evaluate_formula(
                formula="Custom+UnknownVar",
                context={"custom": 1.0},
                row=1,
                col=8,
                parameters={},
                column_title_resolver=self._title,
            )

        message = str(context.exception)
        self.assertIn('Строка 2, столбец "Таможня"', message)
        self.assertIn('неизвестная переменная "UnknownVar"', message)

    def test_vat_multiplier_from_parameters_percent_mode(self):
        multiplier = self.service.vat_multiplier_from_parameters(
            {"parameters": {"1": ["НДС", "20", "percents"]}}
        )

        self.assertEqual(multiplier, 1.2)

    def test_vat_multiplier_from_parameters_invalid_value_returns_default(self):
        logs = []

        def fake_log(context, error, *, include_traceback):
            logs.append((context, str(error), include_traceback))

        multiplier = self.service.vat_multiplier_from_parameters(
            {"parameters": {"1": ["НДС", "abc", "percents"]}},
            log_exception=fake_log,
        )

        self.assertEqual(multiplier, 1.0)
        self.assertEqual(len(logs), 1)
        self.assertIn("Некорректное значение НДС", logs[0][0])
        self.assertFalse(logs[0][2])


if __name__ == "__main__":
    unittest.main()
