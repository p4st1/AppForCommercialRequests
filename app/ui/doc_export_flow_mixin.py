from datetime import datetime, timedelta

from createDocument import mainWindow as createDocWindow
from PySide6.QtWidgets import QMessageBox
from config import Config
from tools import DatabaseTools as Tool

try:
    from PySide6.QtCore import QTimer
except Exception:
    QTimer = None

try:
    from PySide6.QtWidgets import QApplication
except Exception:
    QApplication = None


class DocExportFlowMixin:
    SUBMISSION_OFFER_VALIDITY_DAYS = Config.DEFAULT_OFFER_VALIDITY_DAYS
    PIPELINE_TRADE_SEARCH_LIMIT = 1000

    def openCreateDocWindow(
        self,
        tableData,
        *,
        force_google_docx: bool = False,
        on_document_created=None,
    ):
        window = createDocWindow(self, tableData=tableData)
        window.ui.numLine.setText(self.ui.requestNumberLine.text().strip())
        if force_google_docx and hasattr(window, "googleDocxFormatRadio"):
            window.googleDocxFormatRadio.setChecked(True)
            if hasattr(window, "docxFormatRadio"):
                window.docxFormatRadio.setEnabled(False)
            if hasattr(window, "pdfFormatRadio"):
                window.pdfFormatRadio.setEnabled(False)
        if callable(on_document_created) and hasattr(window, "documentCreated"):
            window.documentCreated.connect(on_document_created)
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

    @classmethod
    def _default_submission_offer_validity_period(cls) -> str:
        return (
            datetime.now() + timedelta(days=Config.get_offer_validity_days())
        ).strftime("%d.%m.%Y")

    @classmethod
    def _normalize_web_pipeline_submission_context(
        cls,
        submission_context,
    ) -> dict[str, str]:
        context = submission_context if isinstance(submission_context, dict) else {}
        result = {
            "customer": str(context.get("customer", "") or "").strip(),
            "producer": str(
                context.get("producer", "")
                or context.get("manufacturer", "")
                or ""
            ).strip(),
            "offer_validity_period": str(
                context.get("offer_validity_period", "") or ""
            ).strip(),
            "delivery_order": str(context.get("delivery_order", "") or "").strip(),
            "payment_terms": str(context.get("payment_terms", "") or "").strip(),
            "payment_condition": str(
                context.get("payment_condition", "") or ""
            ).strip(),
            "supplier_status": str(context.get("supplier_status", "") or "").strip(),
            "warranty": str(
                context.get("warranty", "")
                or context.get("guarantee", "")
                or ""
            ).strip(),
        }
        if not result["offer_validity_period"]:
            result["offer_validity_period"] = cls._default_submission_offer_validity_period()
        return result

    def _set_web_pipeline_submission_context(self, submission_context) -> None:
        self._web_pipeline_submission_context = (
            self._normalize_web_pipeline_submission_context(submission_context)
        )

    def _pop_web_pipeline_submission_context(self) -> dict[str, str]:
        context = getattr(self, "_web_pipeline_submission_context", {})
        self._web_pipeline_submission_context = {}
        return context if isinstance(context, dict) else {}

    def set_pipeline_status(self, text: str):
        label = getattr(self, "label_pipeline_status", None)
        if label is None and hasattr(self, "ui"):
            label = getattr(self.ui, "label_pipeline_status", None)
        if label is not None:
            label.setText(str(text or ""))
        if QApplication is not None:
            QApplication.processEvents()

    def _schedule_pipeline_status_reset(self) -> None:
        token = int(getattr(self, "_pipeline_status_reset_token", 0)) + 1
        self._pipeline_status_reset_token = token

        def _reset_status() -> None:
            if int(getattr(self, "_pipeline_status_reset_token", 0)) != token:
                return
            if bool(getattr(self, "_web_pipeline_active", False)):
                return
            self.set_pipeline_status("Готово")

        if QTimer is not None:
            QTimer.singleShot(3000, _reset_status)
            return
        _reset_status()

    def _set_pipeline_success_status(self) -> None:
        self._web_pipeline_active = False
        self.set_pipeline_status("✅ Готово")
        self._schedule_pipeline_status_reset()

    def _set_pipeline_error_status(self) -> None:
        self._web_pipeline_active = False
        self.set_pipeline_status("❌ Ошибка")
        self._schedule_pipeline_status_reset()

    def run_web_pipeline(self, trade_number: str = "", submission_context=None) -> None:
        try:
            raw_trade_number = str(trade_number or "").strip()
            if not raw_trade_number and hasattr(self.ui, "requestNumberLine"):
                raw_trade_number = self.ui.requestNumberLine.text().strip()
            if not raw_trade_number:
                raise ValueError("Номер заявки не указан")
        except Exception as exc:
            self._pop_web_pipeline_submission_context()
            self._set_pipeline_error_status()
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("получение номера заявки", str(exc)),
            )
            return

        self._web_pipeline_active = True
        self._set_web_pipeline_submission_context(submission_context)

        try:
            self.set_pipeline_status("🌐 Переход на вкладку Прием заявок...")
            ensure_tab = getattr(self, "_ensure_platform_tab", None)
            if callable(ensure_tab):
                ensure_tab()
            index_web = self.ui.tabWidget.indexOf(self.ui.webTab)
            if index_web < 0:
                raise RuntimeError("Вкладка 'Прием заявок' не найдена")
            self.ui.tabWidget.setCurrentIndex(index_web)
        except Exception as exc:
            self._set_pipeline_error_status()
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("переключение на вкладку 'Прием заявок'", str(exc)),
            )
            return

        self._set_web_pipeline_trade_number(raw_trade_number)
        try:
            self.set_pipeline_status("📥 Загрузка заявок...")
            self._trades_load_max_items_override = self.PIPELINE_TRADE_SEARCH_LIMIT
            load_trades_method = getattr(self, "load_trades", None)
            if not callable(load_trades_method):
                raise RuntimeError("Метод load_trades не найден")
            load_trades_method()
        except Exception as exc:
            if hasattr(self, "_trades_load_max_items_override"):
                del self._trades_load_max_items_override
            self._pop_web_pipeline_trade_number()
            self._pop_web_pipeline_submission_context()
            self._set_pipeline_error_status()
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("загрузка заявок", str(exc)),
            )

    @staticmethod
    def _normalize_trade_search_text(value) -> str:
        return str(value or "").strip().casefold()

    @classmethod
    def _trade_matches_number(cls, trade: dict, trade_number: str) -> bool:
        needle = cls._normalize_trade_search_text(trade_number)
        if not needle:
            return False
        needle_digits = "".join(ch for ch in needle if ch.isdigit())

        values = [
            trade.get("registeredNumber"),
            trade.get("number"),
            trade.get("id"),
        ]
        lots = trade.get("lots")
        if isinstance(lots, list):
            for lot in lots:
                if isinstance(lot, dict):
                    values.append(lot.get("id"))

        for value in values:
            text = cls._normalize_trade_search_text(value)
            if not text:
                continue
            if needle in text:
                return True
            text_digits = "".join(ch for ch in text if ch.isdigit())
            if needle_digits and text_digits and needle_digits == text_digits:
                return True
        return False

    @classmethod
    def _find_trade_for_pipeline(cls, trades: list, trade_number: str) -> dict | None:
        for current_trade in trades:
            if isinstance(current_trade, dict) and cls._trade_matches_number(
                current_trade,
                trade_number,
            ):
                return current_trade
        return None

    def _continue_web_pipeline_after_load(self) -> None:
        if hasattr(self, "_trades_load_max_items_override"):
            del self._trades_load_max_items_override
        trade_number = self._pop_web_pipeline_trade_number()
        if not trade_number:
            return

        try:
            trades = self.all_trades if isinstance(self.all_trades, list) else []
            trade = self._find_trade_for_pipeline(trades, trade_number)
        except Exception as exc:
            self._pop_web_pipeline_submission_context()
            self._set_pipeline_error_status()
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("поиск заявки", str(exc)),
            )
            return

        if trade is None:
            self._pop_web_pipeline_submission_context()
            self._set_pipeline_error_status()
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Заявка с номером {trade_number} не найдена",
            )
            return

        submission_context = self._pop_web_pipeline_submission_context()
        try:
            lots = trade.get("lots")
            if not isinstance(lots, list) or not lots:
                raise ValueError("В заявке отсутствуют лоты")
            first_lot = lots[0]
            if not isinstance(first_lot, dict):
                raise ValueError("Некорректный формат данных лота")
            lot_id = first_lot["id"]
        except Exception as exc:
            self._set_pipeline_error_status()
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("получение lot_id", str(exc)),
            )
            return

        try:
            self.set_pipeline_status("📤 Экспорт таблицы...")
            export_trade_method = getattr(self, "export_trade", None)
            if not callable(export_trade_method):
                raise RuntimeError("Метод export_trade не найден")
            set_submission_metadata = getattr(
                self,
                "_set_pending_submission_export_metadata",
                None,
            )
            if callable(set_submission_metadata):
                set_submission_metadata(
                    trade,
                    submission_context=submission_context,
                )
            export_trade_method(lot_id)
        except Exception as exc:
            self._set_pipeline_error_status()
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("экспорт заявки", str(exc)),
            )

    def on_trades_loaded(self, trades):
        parent_handler = getattr(super(), "on_trades_loaded", None)
        if callable(parent_handler):
            parent_handler(trades)
        if str(getattr(self, "_web_pipeline_trade_number", "") or "").strip():
            self.set_pipeline_status("🔍 Поиск заявки...")
        self._continue_web_pipeline_after_load()

    def on_error(self, message):
        trade_number = str(getattr(self, "_web_pipeline_trade_number", "") or "").strip()
        if trade_number:
            if hasattr(self, "_trades_load_max_items_override"):
                del self._trades_load_max_items_override
            self._pop_web_pipeline_trade_number()
            self._pop_web_pipeline_submission_context()
            error_text = str(message or "Неизвестная ошибка")
            Tool.write_log(f"Ошибка загрузки заявок (pipeline): {error_text}")
            set_auth_status = getattr(self, "_set_auth_status", None)
            if callable(set_auth_status) and "401" in error_text:
                set_auth_status(is_auth=False)
            finish_loading = getattr(self, "_finish_trades_loading", None)
            if callable(finish_loading):
                finish_loading("Ошибка загрузки заявок")
            self._set_pipeline_error_status()
            QMessageBox.critical(
                self,
                "Ошибка",
                self._pipeline_error_text("загрузка заявок", error_text),
            )
            return

        parent_handler = getattr(super(), "on_error", None)
        if callable(parent_handler):
            parent_handler(message)

    def _on_export_finished(self, file_path: str) -> None:
        parent_handler = getattr(super(), "_on_export_finished", None)
        if callable(parent_handler):
            parent_handler(file_path)
        if bool(getattr(self, "_web_pipeline_active", False)):
            self._set_pipeline_success_status()

    def _on_export_error(self, message: str) -> None:
        if bool(getattr(self, "_web_pipeline_active", False)):
            self._set_pipeline_error_status()
        parent_handler = getattr(super(), "_on_export_error", None)
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
