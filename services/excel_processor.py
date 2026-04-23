from __future__ import annotations

import pandas as pd


class ExcelProcessor:
    PRICE_COLUMN = "Предлагаемая цена за ед. (без учета НДС)"
    MANUFACTURER_COLUMN = "Производитель"
    TECH_COLUMN = "Технические характеристики"

    def can_fill_exported_excel(self, file_path: str) -> bool:
        df = pd.read_excel(file_path, nrows=0)
        required_columns = (
            self.PRICE_COLUMN,
            self.MANUFACTURER_COLUMN,
            self.TECH_COLUMN,
        )
        return all(col in df.columns for col in required_columns)

    def fill_exported_excel(self, file_path: str, source_rows: list) -> None:
        df = pd.read_excel(file_path)

        for col in [self.PRICE_COLUMN, self.MANUFACTURER_COLUMN, self.TECH_COLUMN]:
            if col not in df.columns:
                raise Exception(f"Не найдена колонка: {col}")

        if len(df) != len(source_rows):
            raise Exception(
                f"Количество строк не совпадает: Excel={len(df)}, Таблица={len(source_rows)}"
            )

        for i in range(len(df)):
            row = source_rows[i] if isinstance(source_rows[i], dict) else {}

            manufacturer = row.get("manufacturer")
            tech = (
                row.get("tech_characteristics")
                or row.get("technical_characteristics")
                or row.get("tech")
                or row.get("manufacturer")
            )

            df.at[i, self.PRICE_COLUMN] = row.get("price")
            df.at[i, self.MANUFACTURER_COLUMN] = manufacturer
            df.at[i, self.TECH_COLUMN] = tech

        df.to_excel(file_path, index=False)
