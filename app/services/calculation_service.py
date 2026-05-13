from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Callable

from app.models.calculation_models import (
    CalculationRowInput,
    CalculationRowResult,
    CalculationSettings,
)
from tools import DatabaseTools as Tool


class CalculationService:
    TOKEN_PATTERN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
    NAMED_VAR_PATTERN = re.compile(r"\$([^$]+)\$")
    FORMULA_COLUMNS = (8, 9, 10, 11, 13)

    @staticmethod
    def round_money(value: float) -> float:
        return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @staticmethod
    def normalize_param_name(value: str) -> str:
        return str(value or "").strip().casefold()

    def vat_multiplier_from_parameters(
        self,
        params_data: dict,
        *,
        log_exception: Callable[..., None] | None = None,
    ) -> float:
        parameters = params_data.get("parameters", {}) if isinstance(params_data, dict) else {}
        for values in parameters.values():
            if len(values) < 3:
                continue
            name, value, calc_type = values[0], values[1], values[2]
            if name != "НДС":
                continue
            try:
                rate = float(str(value).replace(",", "."))
            except ValueError as error:
                if log_exception is not None:
                    log_exception(
                        f"Некорректное значение НДС: {value}",
                        error,
                        include_traceback=False,
                    )
                return 1.0
            if calc_type == "percents":
                return 1 + rate / 100
            return 1 + rate
        return 1.0

    def evaluate_formula(
        self,
        *,
        formula: str,
        context: dict[str, float],
        row: int,
        col: int,
        parameters: dict[str, tuple[str, str]],
        column_title_resolver: Callable[[int], str],
    ) -> float:
        column_title = column_title_resolver(col)
        expression = str(formula or "").strip().replace(",", ".")
        if expression.startswith("="):
            expression = expression[1:].strip()
        if not expression:
            raise ValueError(
                f'Строка {row + 1}, столбец "{column_title}": формула не может быть пустой'
            )

        def _replace_named_variable(match):
            token = match.group(1).strip()
            key = self.normalize_param_name(token)
            if key not in parameters:
                raise ValueError(
                    f'Строка {row + 1}, столбец "{column_title}": '
                    f'неизвестная переменная "${token}$"'
                )
            value, calc_type = parameters[key]
            if calc_type == "percents":
                return f"({value})/100"
            if calc_type == "multiply":
                return f"*({value})"
            if calc_type == "division":
                return f"/({value})"
            return f"({value})"

        expression = self.NAMED_VAR_PATTERN.sub(_replace_named_variable, expression).strip()
        while expression and expression[0] in "+*/":
            expression = expression[1:].strip()
        if not expression:
            raise ValueError(
                f'Строка {row + 1}, столбец "{column_title}": формула не может быть пустой'
            )

        def _replace_token(match):
            token = match.group(0)
            key = token.lower()
            if key not in context:
                key = key.replace("_", "")
            if key not in context:
                raise ValueError(
                    f'Строка {row + 1}, столбец "{column_title}": неизвестная переменная "{token}"'
                )
            return str(context[key])

        math_expression = self.TOKEN_PATTERN.sub(_replace_token, expression)
        try:
            return float(Tool._safe_eval(math_expression))
        except Exception as error:
            if isinstance(error, ValueError):
                raise
            raise ValueError(
                f'Строка {row + 1}, столбец "{column_title}": некорректная формула'
            ) from error

    def calculate_row(
        self,
        *,
        row_index: int,
        row_input: CalculationRowInput,
        formulas: dict[int, str],
        named_parameters: dict[str, tuple[str, str]],
        settings: CalculationSettings,
        column_title_resolver: Callable[[int], str],
    ) -> CalculationRowResult:
        effective_term_delivery = float(settings.term_delivery_days) if float(row_input.supplier_term) > 0 else 0.0
        context = {
            "amount": float(row_input.amount),
            "qty": float(row_input.amount),
            "unitprice": float(row_input.unit_price),
            "price": float(row_input.unit_price),
            "totalprice": float(row_input.total_price),
            "logistic": float(row_input.logistic_value),
            "custom": float(settings.custom),
            "markup": float(settings.markup),
            "vat": float(settings.vat_multiplier),
            "supplierterm": float(row_input.supplier_term),
            "termdelivery": effective_term_delivery,
        }

        customs_sum = self.round_money(
            self.evaluate_formula(
                formula=formulas[8],
                context=context,
                row=row_index,
                col=8,
                parameters=named_parameters,
                column_title_resolver=column_title_resolver,
            )
        )
        if customs_sum < 0:
            raise ValueError(
                f'Строка {row_index + 1}, столбец "{column_title_resolver(8)}": '
                "результат формулы не может быть отрицательным"
            )
        context["customs"] = float(customs_sum)

        unit_sale_price = self.round_money(
            self.evaluate_formula(
                formula=formulas[9],
                context=context,
                row=row_index,
                col=9,
                parameters=named_parameters,
                column_title_resolver=column_title_resolver,
            )
        )
        if unit_sale_price < 0:
            raise ValueError(
                f'Строка {row_index + 1}, столбец "{column_title_resolver(9)}": '
                "результат формулы не может быть отрицательным"
            )
        context["unitsaleprice"] = float(unit_sale_price)

        real_price = self.round_money(
            self.evaluate_formula(
                formula=formulas[10],
                context=context,
                row=row_index,
                col=10,
                parameters=named_parameters,
                column_title_resolver=column_title_resolver,
            )
        )
        if real_price < 0:
            raise ValueError(
                f'Строка {row_index + 1}, столбец "{column_title_resolver(10)}": '
                "результат формулы не может быть отрицательным"
            )
        context["realprice"] = float(real_price)

        total_without_vat = self.round_money(
            self.evaluate_formula(
                formula=formulas[11],
                context=context,
                row=row_index,
                col=11,
                parameters=named_parameters,
                column_title_resolver=column_title_resolver,
            )
        )
        if total_without_vat < 0:
            raise ValueError(
                f'Строка {row_index + 1}, столбец "{column_title_resolver(11)}": '
                "результат формулы не может быть отрицательным"
            )
        context["totalwithoutvat"] = float(total_without_vat)

        total_with_vat = self.round_money(total_without_vat * settings.vat_multiplier)
        if total_with_vat < 0:
            raise ValueError(
                f'Строка {row_index + 1}, столбец "{column_title_resolver(12)}": '
                "результат формулы не может быть отрицательным"
            )
        context["totalwithvat"] = float(total_with_vat)

        total_delivery_days = int(
            round(
                self.evaluate_formula(
                    formula=formulas[13],
                    context=context,
                    row=row_index,
                    col=13,
                    parameters=named_parameters,
                    column_title_resolver=column_title_resolver,
                )
            )
        )
        if total_delivery_days < 0:
            raise ValueError(
                f'Строка {row_index + 1}, столбец "{column_title_resolver(13)}": '
                "результат формулы не может быть отрицательным"
            )

        return CalculationRowResult(
            customs_sum=customs_sum,
            unit_sale_price=unit_sale_price,
            real_price=real_price,
            total_without_vat=total_without_vat,
            total_with_vat=total_with_vat,
            total_delivery_days=total_delivery_days,
        )
