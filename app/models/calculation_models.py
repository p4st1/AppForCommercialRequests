from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CalculationRowInput:
    amount: float
    unit_price: float
    total_price: float
    currency: str
    logistic_value: float
    supplier_term: float


@dataclass(frozen=True)
class CalculationSettings:
    custom: float
    markup: float
    vat_multiplier: float
    term_delivery_days: int


@dataclass(frozen=True)
class CalculationRowResult:
    customs_sum: float
    unit_sale_price: float
    real_price: float
    total_without_vat: float
    total_with_vat: float
    total_delivery_days: int
