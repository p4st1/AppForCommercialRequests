from PySide6.QtWidgets import QFileDialog
import pandas as pd


class DocFromExcelMixin:
    def exportDocFromExcel(self):
        filename = QFileDialog.getOpenFileName(
            self,
            "Открыть файл",
            "",
            "csv (*.csv);;",
        )[0]
        if not filename:
            return

        df = pd.read_csv(filename, header=None, sep=";").dropna(how="all")
        data = df.values.tolist()
        table_data = []
        for row in data:
            if pd.notna(row[0]):
                table_data.append([*row[:5], *row[10:14]])
            else:
                break

        self.openCreateDocWindow((len(table_data[1:]), table_data[1:]))
