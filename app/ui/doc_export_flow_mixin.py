from createDocument import mainWindow as createDocWindow
from PySide6.QtWidgets import QMessageBox
from config import Config
from tools import DatabaseTools as Tool


class DocExportFlowMixin:
    def openCreateDocWindow(self, tableData):
        window = createDocWindow(self, tableData=tableData)
        window.ui.numLine.setText(self.ui.requestNumberLine.text().strip())
        window.show()
        window.windowClosed.connect(self.updateHistoryTable)
        if Config.settings["closeTable"]:
            window.windowClosed.connect(self.closeTable)
            self.ui.KpTable.setRowCount(0)

    @staticmethod
    def _pipeline_error_text(step: str, details: str = "") -> str:
        message = f"Ошибка на этапе: {step}"
        details_text = str(details or "").strip()
        if details_text:
            message += f"\n{details_text}"
        return message

    def _set_web_pipeline_trade_number(self, trade_number: str) -> None:
        self._web_pipeline_trade_number = str(trade_number or "").strip()

    def _pop_web_pipeline_trade_number(self) -> str:
        trade_number = str(getattr(self, "_web_pipeline_trade_number", "") or "").strip()
        self._web_pipeline_trade_number = ""
        return trade_number

    def run_web_pipeline(self, trade_number: str = "") -> None:
        try:
            raw_trade_number = str(trade_number or "").strip()
            if not raw_trade_number and hasattr(self.ui, "requestNumberLine"):
                raw_trade_number = self.ui.requestNumberLine.text().strip()
            if not raw_trade_number:
                raise ValueError("Номер заявки не указан")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("получение номера заявки", str(exc)),
            )
            return

        try:
            ensure_tab = getattr(self, "_ensure_platform_tab", None)
            if callable(ensure_tab):
                ensure_tab()
            index_web = self.ui.tabWidget.indexOf(self.ui.webTab)
            if index_web < 0:
                raise RuntimeError("Вкладка 'Веб' не найдена")
            self.ui.tabWidget.setCurrentIndex(index_web)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("переключение на вкладку 'Веб'", str(exc)),
            )
            return

        self._set_web_pipeline_trade_number(raw_trade_number)
        try:
            load_trades_method = getattr(self, "load_trades", None)
            if not callable(load_trades_method):
                raise RuntimeError("Метод load_trades не найден")
            load_trades_method()
        except Exception as exc:
            self._pop_web_pipeline_trade_number()
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("загрузка заявок", str(exc)),
            )

    def _continue_web_pipeline_after_load(self) -> None:
        trade_number = self._pop_web_pipeline_trade_number()
        if not trade_number:
            return

        try:
            trades = self.all_trades if isinstance(self.all_trades, list) else []
            trade = next(
                (
                    current_trade
                    for current_trade in trades
                    if trade_number in str(current_trade.get("registeredNumber", ""))
                ),
                None,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("поиск заявки", str(exc)),
            )
            return

        if trade is None:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Заявка с номером {trade_number} не найдена",
            )
            return

        try:
            lots = trade.get("lots")
            if not isinstance(lots, list) or not lots:
                raise ValueError("В заявке отсутствуют лоты")
            first_lot = lots[0]
            if not isinstance(first_lot, dict):
                raise ValueError("Некорректный формат данных лота")
            lot_id = first_lot["id"]
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("получение lot_id", str(exc)),
            )
            return

        try:
            export_trade_method = getattr(self, "export_trade", None)
            if not callable(export_trade_method):
                raise RuntimeError("Метод export_trade не найден")
            export_trade_method(lot_id)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("экспорт заявки", str(exc)),
            )

    def on_trades_loaded(self, trades):
        parent_handler = getattr(super(), "on_trades_loaded", None)
        if callable(parent_handler):
            parent_handler(trades)
        self._continue_web_pipeline_after_load()

    def on_error(self, message):
        trade_number = str(getattr(self, "_web_pipeline_trade_number", "") or "").strip()
        if trade_number:
            self._pop_web_pipeline_trade_number()
            error_text = str(message or "Неизвестная ошибка")
            Tool.write_log(f"Ошибка загрузки заявок (pipeline): {error_text}")
            set_auth_status = getattr(self, "_set_auth_status", None)
            if callable(set_auth_status) and "401" in error_text:
                set_auth_status(is_auth=False)
            finish_loading = getattr(self, "_finish_trades_loading", None)
            if callable(finish_loading):
                finish_loading("Ошибка загрузки заявок")
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("загрузка заявок", error_text),
            )
            return

        parent_handler = getattr(super(), "on_error", None)
        if callable(parent_handler):
            parent_handler(message)

    def exportDocs(self):
        if not Config.isTableOpened:
            self.error("Ошибка", "Загрузите КП поставщика")
            return
        if self._has_mixed_currencies():
            self.error(
                "Ошибка",
                "Создание КП в DOCX для таблицы со смешанной валютой не поддерживается.",
            )
            return

        Tool.write_log("CREATING DOCX")
        table_data = self.getTableData()
        self.openCreateDocWindow((len(table_data), table_data))
        Tool.write_log("CREATING DOCX...")
