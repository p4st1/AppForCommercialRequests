from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from config import Config
from create import createExcelFile as exportExcelFile
from services.google_drive_service import GoogleDriveService


class ExcelExportFlowMixin:
    EXPORT_DESTINATION_LOCAL = "local"
    EXPORT_DESTINATION_GOOGLE_DRIVE = "google_drive"

    def _show_excel_export_status(self, message, timeout_ms=0):
        show_status = getattr(self, "_show_status_message", None)
        if callable(show_status):
            show_status(message, timeout_ms)
            return
        status_bar_getter = getattr(self, "statusBar", None)
        status_bar = status_bar_getter() if callable(status_bar_getter) else None
        if status_bar is not None and message:
            status_bar.showMessage(str(message), int(timeout_ms or 0))

    def exportExcel(self):
        if not Config.isTableOpened:
            self.error("Ошибка", "Загрузите КП поставщика")
            return
        if self._has_mixed_currencies():
            self.error(
                "Ошибка",
                "Создание Excel для таблицы со смешанной валютой не поддерживается.",
            )
            return

        parsed = self._parse_input_parameters(show_error=True)
        if parsed is None:
            return

        tableData = []
        logistic_formulas = []
        row_count = self.ui.KpTable.rowCount()
        column_count = self.ui.KpTable.columnCount()
        item_data_role = getattr(Qt, "ItemDataRole", None)
        user_role = getattr(item_data_role, "UserRole", 32)

        for row in range(row_count):
            row_data = []
            for col in range(column_count):
                item = self.ui.KpTable.item(row, col)
                row_data.append(item.text() if item is not None else "")
            tableData.append(row_data)
            logistic_item = self.ui.KpTable.item(row, 7)
            logistic_formula = logistic_item.data(user_role) if logistic_item is not None else ""
            if isinstance(logistic_formula, dict):
                logistic_formula = logistic_formula.get("formula", "")
            logistic_formulas.append(str(logistic_formula or ""))

        destination = self._choose_excel_export_destination()
        if not destination:
            return

        payload = self._build_excel_export_payload(
            tableData,
            logistic_formulas,
            parsed,
        )
        if destination == self.EXPORT_DESTINATION_GOOGLE_DRIVE:
            self._start_google_drive_excel_export(payload)
            return

        self._show_excel_export_status("Экспорт таблицы...")
        export_result = exportExcelFile(payload)
        if not getattr(export_result, "success", False):
            error_text = getattr(export_result, "error_message", "") or "Не удалось создать Excel"
            self._show_excel_export_status("Ошибка экспорта таблицы", 5000)
            self.error("Ошибка", error_text)
            return

        self._finish_excel_export(export_result)

    def _choose_excel_export_destination(self) -> str:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Сохранение расчетов")
        dialog.setText("Куда сохранить расчеты?")
        local_button = dialog.addButton("На ПК", QMessageBox.ButtonRole.AcceptRole)
        drive_button = dialog.addButton("Google Drive", QMessageBox.ButtonRole.ActionRole)
        dialog.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
        dialog.exec()
        clicked_button = dialog.clickedButton()
        if clicked_button is local_button:
            return self.EXPORT_DESTINATION_LOCAL
        if clicked_button is drive_button:
            return self.EXPORT_DESTINATION_GOOGLE_DRIVE
        return ""

    def _build_excel_export_payload(self, table_data, logistic_formulas, parsed, *, docx_remote_url: str = ""):
        return {
            "table_rows": table_data,
            "request_number": self.ui.requestNumberLine.text().strip(),
            "logistic_mode": self.ui.logisticVar.currentIndex(),
            "logistic_value": parsed["logistic"],
            "custom_value": parsed["custom"],
            "markup_value": parsed["markup"],
            "term_delivery": parsed["termDelivery"],
            "vat_multiplier": self._vat_multiplier(),
            "named_parameters": self._load_formula_parameters(),
            "logistic_formulas": logistic_formulas,
            "formula_expressions": {
                col: list(self.formulaExpressions.get(col, [])) for col in self.FORMULA_EDITABLE_COLUMNS
            },
            "docx_remote_url": str(docx_remote_url or "").strip(),
        }

    def _start_google_drive_excel_export(self, payload):
        self._show_excel_export_status("Подготовка экспорта таблицы в Google Drive...")
        summary_rows = self.getTableData()
        self.openCreateDocWindow(
            (len(summary_rows), summary_rows),
            force_google_docx=True,
            on_document_created=lambda result: self._export_excel_to_google_drive(
                payload,
                result,
            ),
        )

    def _export_excel_to_google_drive(self, payload, docx_result):
        docx_remote_url = str(
            (docx_result if isinstance(docx_result, dict) else {}).get("remote_url", "") or ""
        ).strip()
        if not docx_remote_url:
            self._show_excel_export_status("Ошибка экспорта таблицы", 5000)
            self.error("Ошибка", "Не удалось получить ссылку на DOCX КП в Google Drive")
            return

        self._show_excel_export_status("Экспорт таблицы в Google Drive...")
        drive_payload = dict(payload)
        drive_payload["docx_remote_url"] = docx_remote_url
        export_result = exportExcelFile(drive_payload)
        if not getattr(export_result, "success", False):
            error_text = getattr(export_result, "error_message", "") or "Не удалось создать Excel"
            self._show_excel_export_status("Ошибка экспорта таблицы", 5000)
            self.error("Ошибка", error_text)
            return

        output_path = str(getattr(export_result, "output_path", "") or "").strip()
        try:
            upload_result = GoogleDriveService().upload_excel(output_path)
            exportExcelFile.append_calculations_remote_link_to_file(
                output_path,
                upload_result.web_view_link,
            )
            GoogleDriveService().update_excel(
                upload_result.file_id,
                output_path,
            )
        except Exception as exc:
            self._show_excel_export_status("Ошибка загрузки Excel в Google Drive", 5000)
            QMessageBox.critical(
                self,
                "Ошибка",
                "Локальный XLSX сохранен, но не удалось загрузить его на Google Drive:\n"
                f"{exc}",
            )
            return

        self._finish_excel_export(
            export_result,
            remote_url=upload_result.web_view_link,
            google_drive=True,
        )

    def _finish_excel_export(self, export_result, *, remote_url: str = "", google_drive: bool = False):
        self._show_excel_export_status("Экспорт таблицы завершен", 5000)
        total_amount, currency = self._table_column_total(12)
        self.history_service.record_excel_export(
            items_count=self.ui.KpTable.rowCount(),
            total_amount=total_amount,
            currency=currency,
            file_path=getattr(export_result, "output_path", ""),
            remote_url=remote_url,
        )
        self.history_service.save()
        self.updateHistoryTable()
        output_path = str(getattr(export_result, "output_path", "") or "").strip()
        message = (
            "Расчеты успешно сохранены и загружены на Google Drive."
            if google_drive
            else "Расчеты успешно сохранены."
        )
        if output_path:
            message = f"{message}\n{output_path}"
        if remote_url:
            message = f"{message}\n{remote_url}"
        QMessageBox.information(self, "Сохранение расчетов", message)
