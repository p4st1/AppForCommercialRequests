from config import Config
from tools import DatabaseTools as Tool


class VatMixin:
    def _vat_multiplier(self):
        params_data = Tool.load_json(Config.vars_path)
        return self.calculation_service.vat_multiplier_from_parameters(
            params_data,
            log_exception=Tool.log_exception,
        )
