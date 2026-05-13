from decimal import Decimal, ROUND_HALF_UP


class NumberFormatMixin:
    @staticmethod
    def _fmt_number(value: float) -> str:
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.6f}".rstrip("0").rstrip(".")

    @staticmethod
    def _round_money(value) -> float:
        return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
