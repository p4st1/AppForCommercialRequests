import unittest
from types import SimpleNamespace
from unittest.mock import patch

from config import Config
from app.ui.formula_input_mixin import FormulaInputMixin
from app.ui.number_format_mixin import NumberFormatMixin


class _FakeLineEdit:
    def __init__(self, value):
        self._value = str(value)

    def text(self):
        return self._value

    def setText(self, value):
        self._value = str(value)


class _FakeWindow(FormulaInputMixin, NumberFormatMixin):
    def __init__(self):
        self.ui = SimpleNamespace(
            customLine=_FakeLineEdit("1"),
            markupLine=_FakeLineEdit("1"),
            logisticNum=_FakeLineEdit("1"),
            termDeliveryLine=_FakeLineEdit("0"),
        )
        self.formulaCustom = None
        self.formulaMarkup = None
        self.formulaLogistic = None
        self.termDeliveryDays = None
        self.error_calls = []
        self.logistic_calls = 0
        self.calculating_calls = 0
        self.raise_calculating = None

    def error(self, title, text):
        self.error_calls.append((title, text))

    def logisticCalculate(self, **_kwargs):
        self.logistic_calls += 1

    def calculating(self):
        self.calculating_calls += 1
        if self.raise_calculating is not None:
            raise self.raise_calculating


class FormulaInputMixinTests(unittest.TestCase):
    def setUp(self):
        self._old_is_table_opened = Config.isTableOpened

    def tearDown(self):
        Config.isTableOpened = self._old_is_table_opened

    @patch("app.ui.formula_input_mixin.Tool.parse_int", return_value=7)
    @patch("app.ui.formula_input_mixin.Tool.evalWithVars", side_effect=lambda expr: expr)
    def test_parse_input_parameters_success_updates_state_and_ui(self, _eval_with_vars, _parse_int):
        window = _FakeWindow()
        window.ui.customLine = _FakeLineEdit("1,5")
        window.ui.markupLine = _FakeLineEdit("2")
        window.ui.logisticNum = _FakeLineEdit("3,25")
        window.ui.termDeliveryLine = _FakeLineEdit("7")

        result = window._parse_input_parameters(show_error=True)

        self.assertEqual(
            result,
            {"custom": 1.5, "markup": 2.0, "logistic": 3.25, "termDelivery": 7},
        )
        self.assertEqual(window.formulaCustom, 1.5)
        self.assertEqual(window.formulaMarkup, 2.0)
        self.assertEqual(window.formulaLogistic, 3.25)
        self.assertEqual(window.termDeliveryDays, 7)
        self.assertEqual(window.ui.customLine.text(), "1.5")
        self.assertEqual(window.ui.markupLine.text(), "2")
        self.assertEqual(window.ui.logisticNum.text(), "3.25")
        self.assertEqual(window.ui.termDeliveryLine.text(), "7")
        self.assertEqual(window.error_calls, [])

    @patch("app.ui.formula_input_mixin.Tool.parse_int", return_value=7)
    @patch("app.ui.formula_input_mixin.Tool.evalWithVars", side_effect=["0", "2", "3"])
    def test_parse_input_parameters_validation_error_with_message(self, _eval_with_vars, _parse_int):
        window = _FakeWindow()

        result = window._parse_input_parameters(show_error=True)

        self.assertIsNone(result)
        self.assertEqual(window.error_calls, [("Ошибка", 'Поле "Таможня" должно быть положительным')])

    @patch("app.ui.formula_input_mixin.Tool.parse_int", return_value=7)
    @patch("app.ui.formula_input_mixin.Tool.evalWithVars", side_effect=["0", "2", "3"])
    def test_parse_input_parameters_can_suppress_error_message(self, _eval_with_vars, _parse_int):
        window = _FakeWindow()

        result = window._parse_input_parameters(show_error=False)

        self.assertIsNone(result)
        self.assertEqual(window.error_calls, [])

    @patch.object(FormulaInputMixin, "_parse_input_parameters", return_value={"custom": 1})
    def test_process_formula_runs_recalculation_when_table_open(self, _parse):
        Config.isTableOpened = True
        window = _FakeWindow()

        window.processFormula()

        self.assertEqual(window.logistic_calls, 1)
        self.assertEqual(window.calculating_calls, 1)
        self.assertEqual(window.error_calls, [])

    @patch.object(FormulaInputMixin, "_parse_input_parameters", return_value={"custom": 1})
    def test_process_formula_handles_calculating_value_error(self, _parse):
        Config.isTableOpened = True
        window = _FakeWindow()
        window.raise_calculating = ValueError("Calc failed")

        window.processFormula()

        self.assertEqual(window.logistic_calls, 1)
        self.assertEqual(window.calculating_calls, 1)
        self.assertEqual(window.error_calls, [("Ошибка", "Calc failed")])

    @patch.object(FormulaInputMixin, "_parse_input_parameters", return_value={"custom": 1})
    def test_process_formula_skips_recalculation_when_table_closed(self, _parse):
        Config.isTableOpened = False
        window = _FakeWindow()

        window.processFormula()

        self.assertEqual(window.logistic_calls, 0)
        self.assertEqual(window.calculating_calls, 0)
        self.assertEqual(window.error_calls, [])


if __name__ == "__main__":
    unittest.main()
