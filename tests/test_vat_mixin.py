import unittest
from types import SimpleNamespace
from unittest.mock import patch

from config import Config
from app.ui.vat_mixin import VatMixin, Tool


class _FakeWindow(VatMixin):
    def __init__(self, return_value):
        self.calculation_service = SimpleNamespace()
        self.calculation_service.calls = []

        def _vat_multiplier_from_parameters(params_data, log_exception):
            self.calculation_service.calls.append(
                {
                    "params_data": params_data,
                    "log_exception": log_exception,
                }
            )
            return return_value

        self.calculation_service.vat_multiplier_from_parameters = _vat_multiplier_from_parameters


class VatMixinTests(unittest.TestCase):
    def setUp(self):
        self._old_vars_path = Config.vars_path

    def tearDown(self):
        Config.vars_path = self._old_vars_path

    @patch("app.ui.vat_mixin.Tool.load_json")
    def test_vat_multiplier_loads_params_and_delegates_to_calculation_service(self, load_json):
        Config.vars_path = "/tmp/vars.json"
        load_json.return_value = {"parameters": {"1": [None, "20"]}}
        window = _FakeWindow(return_value=1.2)

        result = window._vat_multiplier()

        load_json.assert_called_once_with("/tmp/vars.json")
        self.assertEqual(result, 1.2)
        self.assertEqual(len(window.calculation_service.calls), 1)
        self.assertEqual(
            window.calculation_service.calls[0]["params_data"],
            {"parameters": {"1": [None, "20"]}},
        )
        self.assertIs(window.calculation_service.calls[0]["log_exception"], Tool.log_exception)


if __name__ == "__main__":
    unittest.main()
