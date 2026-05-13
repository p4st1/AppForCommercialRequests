from __future__ import annotations

from pathlib import Path
import re

from tools import DatabaseTools as Tool


class ProposalImportService:
    CURRENCY_PATTERN = re.compile(r"[¥$₽€]")
    DASH_PLACEHOLDER_CHARS = frozenset("-–—−")

    @staticmethod
    def normalize_header(text):
        value = str(text or "").strip().lower().replace("ё", "е")
        value = re.sub(r"[^a-zа-я0-9]+", "", value)
        return value

    @classmethod
    def is_dash_placeholder(cls, text):
        value = str(text or "").strip().replace("\u00A0", "").replace(" ", "")
        return bool(value) and all(char in cls.DASH_PLACEHOLDER_CHARS for char in value)

    def detect_price_column_currency(self, df, price_col, header_row):
        for row_idx in range(header_row + 1, len(df.index)):
            price_text = str(df.iat[row_idx, price_col]).strip()
            currency, _price_value = Tool.parsePrice(price_text)
            if currency:
                return currency
            match = self.CURRENCY_PATTERN.search(price_text)
            if match:
                return match.group(0)
        return ""

    def read_source_table(self, filename):
        import pandas as pd

        ext = Path(filename).suffix.lower()
        if ext in {".xls", ".xlsx"}:
            return pd.read_excel(filename, header=None, dtype=str).fillna("")

        errors = []
        for encoding in ("utf-8-sig", "utf-16", "cp1251", "utf-8"):
            try:
                return pd.read_csv(
                    filename,
                    header=None,
                    sep=";",
                    dtype=str,
                    encoding=encoding,
                    engine="python",
                    on_bad_lines="skip",
                ).fillna("")
            except Exception as error:
                errors.append(str(error))
        raise ValueError("Не удалось прочитать файл. Проверьте кодировку и формат CSV")

    def detect_columns(self, df):
        header_row = None
        max_rows = min(len(df.index), 50)
        max_cols = min(len(df.columns), 20)
        for row_idx in range(max_rows):
            row_values = [self.normalize_header(df.iat[row_idx, col]) for col in range(max_cols)]
            has_name = any("наименование" in value for value in row_values)
            has_qty = any("колво" in value or ("кол" in value and "во" in value) for value in row_values)
            has_price = any("цена" in value for value in row_values)
            if has_name and has_qty and has_price:
                header_row = row_idx
                break

        if header_row is None:
            header_row = 0

        mapping = {
            "number": None,
            "name": None,
            "sku": None,
            "unit": None,
            "qty": None,
            "price": None,
            "term": None,
        }

        for col in range(len(df.columns)):
            value = self.normalize_header(df.iat[header_row, col])
            if "наименование" in value:
                if mapping["name"] is None:
                    mapping["name"] = col
            elif "каталож" in value and "номер" in value:
                if mapping["sku"] is None:
                    mapping["sku"] = col
            elif value.startswith("ед") or "едизм" in value:
                if mapping["unit"] is None:
                    mapping["unit"] = col
            elif "колво" in value or ("кол" in value and "во" in value):
                if mapping["qty"] is None:
                    mapping["qty"] = col
            elif (
                "ценазаедбезндс" in value
                or ("цена" in value and "заед" in value)
                or ("цена" in value and mapping["price"] is None)
            ):
                if mapping["price"] is None:
                    mapping["price"] = col
            elif "срок" in value:
                if mapping["term"] is None:
                    mapping["term"] = col
            elif value in {"n", "no", "номер"} or "№" in str(df.iat[header_row, col]):
                if mapping["number"] is None:
                    mapping["number"] = col

        defaults = {
            "number": 0,
            "name": 1,
            "sku": 2,
            "unit": 3,
            "qty": 4,
            "price": 5,
            "term": 6,
        }
        for key, default_col in defaults.items():
            if mapping[key] is None:
                mapping[key] = default_col

        if max(mapping.values()) >= len(df.columns):
            raise ValueError("В таблице не хватает необходимых столбцов")
        return header_row, mapping

    def parse_source_rows(self, df):
        header_row, mapping = self.detect_columns(df)
        fallback_currency = self.detect_price_column_currency(df, mapping["price"], header_row)
        parsed_rows = []
        warnings = []
        blank_streak = 0

        for row_idx in range(header_row + 1, len(df.index)):
            number_text = str(df.iat[row_idx, mapping["number"]]).strip()
            name = str(df.iat[row_idx, mapping["name"]]).strip()
            sku = str(df.iat[row_idx, mapping["sku"]]).strip()
            unit = str(df.iat[row_idx, mapping["unit"]]).strip()
            qty_text = str(df.iat[row_idx, mapping["qty"]]).strip()
            price_text = str(df.iat[row_idx, mapping["price"]]).strip()
            term_text = str(df.iat[row_idx, mapping["term"]]).strip()

            if not any([name, sku, unit, qty_text, price_text, term_text]):
                blank_streak += 1
                if parsed_rows and blank_streak >= 2:
                    break
                continue
            blank_streak = 0

            if not name:
                warnings.append(f"Строка {row_idx + 1}: пропущено наименование, строка пропущена")
                continue

            try:
                qty = Tool.parse_int(qty_text, f"Кол-во (строка {row_idx + 1})", allow_zero=False)
            except ValueError as error:
                warnings.append(str(error))
                continue

            try:
                currency, price_value = Tool.parsePrice(price_text)
                if not currency:
                    match = self.CURRENCY_PATTERN.search(price_text)
                    if match:
                        currency = match.group(0)
                        price_value = price_text.replace(currency, "").strip()
                if not currency and self.is_dash_placeholder(price_value):
                    currency = fallback_currency
                if not currency:
                    raise ValueError("Не указана валюта")
                if self.is_dash_placeholder(price_value):
                    unit_price = 0
                else:
                    unit_price = Tool.parse_float(
                        price_value,
                        f"Цена (строка {row_idx + 1})",
                        allow_zero=True,
                    )
            except ValueError as error:
                warnings.append(f"Строка {row_idx + 1}: {error}")
                continue

            try:
                supplier_term_days = Tool.parse_delivery_days(term_text)
            except ValueError as error:
                warnings.append(f"Строка {row_idx + 1}: {error}. Установлено 0 дней")
                supplier_term_days = 0

            row_number = number_text if number_text else str(len(parsed_rows) + 1)
            parsed_rows.append(
                {
                    "number": row_number,
                    "name": name,
                    "sku": sku,
                    "unit": unit if unit else "шт.",
                    "qty": qty,
                    "currency": currency,
                    "unitPrice": unit_price,
                    "supplierTermDays": supplier_term_days,
                }
            )

        if not parsed_rows:
            raise ValueError("В файле не найдено ни одной валидной строки товара")

        return parsed_rows, warnings

    def load_source_rows(self, filename):
        df = self.read_source_table(filename)
        return self.parse_source_rows(df)
