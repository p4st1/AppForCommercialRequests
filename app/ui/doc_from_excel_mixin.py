from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
import pandas as pd

from services.google_drive_service import GoogleDriveService


class DocFromExcelMixin:
    DOC_FROM_CALCULATIONS_SOURCE_LOCAL = "local"
    DOC_FROM_CALCULATIONS_SOURCE_GOOGLE = "google"

    def exportDocFromExcel(self):
        source = self._choose_doc_from_calculations_source()
        if not source:
            return

        if source == self.DOC_FROM_CALCULATIONS_SOURCE_GOOGLE:
            self._export_doc_from_google_calculations()
            return

        filename = QFileDialog.getOpenFileName(
            self,
            "Открыть файл расчетов",
            "",
            "Расчеты (*.csv *.xlsx *.xlsm *.xls);;CSV (*.csv);;Excel (*.xlsx *.xlsm *.xls)",
        )[0]
        if not filename:
            return

        self._export_doc_from_calculations_file(filename)

    def _choose_doc_from_calculations_source(self) -> str:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Скачать КП из расчетов")
        dialog.setText("Откуда взять файл расчетов?")
        local_button = dialog.addButton("С ПК", QMessageBox.ButtonRole.AcceptRole)
        google_button = dialog.addButton(
            "По ссылке Google Таблиц",
            QMessageBox.ButtonRole.ActionRole,
        )
        dialog.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
        dialog.exec()

        clicked_button = dialog.clickedButton()
        if clicked_button is local_button:
            return self.DOC_FROM_CALCULATIONS_SOURCE_LOCAL
        if clicked_button is google_button:
            return self.DOC_FROM_CALCULATIONS_SOURCE_GOOGLE
        return ""

    def _export_doc_from_google_calculations(self) -> None:
        link, accepted = QInputDialog.getText(
            self,
            "Скачать КП из расчетов",
            "Ссылка на Google Таблицу или файл расчетов:",
        )
        if not accepted:
            return

        link = str(link or "").strip()
        if not link:
            QMessageBox.warning(self, "Ошибка", "Укажите ссылку на Google Таблицу")
            return

        try:
            download_result = GoogleDriveService().download_excel(link)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Не удалось скачать расчеты с Google Drive:\n{exc}",
            )
            return

        self._export_doc_from_calculations_file(str(download_result.local_path))

    def _export_doc_from_calculations_file(self, filename: str) -> None:
        try:
            df = self._read_calculations_dataframe(filename)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Не удалось прочитать файл расчетов:\n{exc}",
            )
            return

        data = df.values.tolist()
        table_data = []
        for row in data:
            row_values = list(row)
            first_cell = row_values[0] if row_values else None
            if pd.notna(first_cell):
                padded_row = [*row_values, *[""] * 14]
                table_data.append([*padded_row[:5], *padded_row[10:14]])
            else:
                break

        self.openCreateDocWindow((len(table_data[1:]), table_data[1:]))

    @staticmethod
    def _read_calculations_dataframe(filename: str):
        path = Path(filename).expanduser()
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(str(path), header=None, sep=";").dropna(how="all")
        if suffix in {".xlsx", ".xlsm", ".xls"}:
            return pd.read_excel(str(path), header=None).dropna(how="all")
        raise ValueError(f"Неподдерживаемый формат файла расчетов: {suffix}")
