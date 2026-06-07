from __future__ import annotations

import re
from typing import Any


class CurrencyService:
    CURRENCY_CODES = {
        "AUD",
        "BYN",
        "CHF",
        "CNY",
        "EUR",
        "GBP",
        "INR",
        "JPY",
        "KZT",
        "RSD",
        "RUB",
        "TRY",
        "UAH",
        "USD",
    }
    CURRENCY_ALIASES = {
        "₽": "RUB",
        "руб": "RUB",
        "руб.": "RUB",
        "рубль": "RUB",
        "рубля": "RUB",
        "рублей": "RUB",
        "рубли": "RUB",
        "рубл": "RUB",
        "rur": "RUB",
        "$": "USD",
        "доллар": "USD",
        "доллара": "USD",
        "долларов": "USD",
        "usd": "USD",
        "€": "EUR",
        "евро": "EUR",
        "eur": "EUR",
        "¥": "CNY",
        "юан": "CNY",
        "юань": "CNY",
        "юаня": "CNY",
        "юаней": "CNY",
        "юани": "CNY",
        "yuan": "CNY",
        "cny": "CNY",
        "cyn": "CNY",
        "₸": "KZT",
        "тенге": "KZT",
        "kzt": "KZT",
    }

    @classmethod
    def normalize_currency_code(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""

        upper_text = text.upper()
        for code in sorted(cls.CURRENCY_CODES, key=len, reverse=True):
            if re.search(rf"(?<![A-Z]){re.escape(code)}(?![A-Z])", upper_text):
                return code

        normalized = text.casefold().replace("ё", "е")
        compact = re.sub(r"\s+", " ", normalized)
        for alias, code in cls.CURRENCY_ALIASES.items():
            if alias in compact:
                return code
        return ""

    @classmethod
    def detect_currency_from_value(cls, value: Any) -> str:
        if isinstance(value, dict):
            priority_keys = (
                "currency",
                "currency_code",
                "price_currency",
                "unit_price_currency",
                "total_currency",
            )
            for key in priority_keys:
                code = cls.normalize_currency_code(value.get(key))
                if code:
                    return code

            value_keys = (
                "unit_price",
                "price",
                "proposal_price",
                "total",
                "sum",
                "amount",
            )
            for key in value_keys:
                code = cls.detect_currency_from_value(value.get(key))
                if code:
                    return code

            return cls.detect_currency_from_values(value.values())

        row_values = cls._row_like_values(value)
        if row_values is not None:
            return cls.detect_currency_from_values(row_values)

        if isinstance(value, (list, tuple, set)):
            return cls.detect_currency_from_values(value)

        return cls.normalize_currency_code(value)

    @classmethod
    def detect_currency_from_values(cls, values: Any) -> str:
        if values is None:
            return ""
        if isinstance(values, dict):
            return cls.detect_currency_from_value(values)
        if isinstance(values, (str, bytes)) or not hasattr(values, "__iter__"):
            return cls.detect_currency_from_value(values)

        for value in values:
            code = cls.detect_currency_from_value(value)
            if code:
                return code
        return ""

    @staticmethod
    def _row_like_values(value: Any) -> tuple[Any, ...] | None:
        fields = (
            "unit_price",
            "total",
            "name",
            "unit",
            "delivery_time",
            "manufacturer",
            "technical",
            "supplier_status",
            "warranty",
        )
        if not any(hasattr(value, field) for field in fields):
            return None
        return tuple(getattr(value, field, None) for field in fields)
