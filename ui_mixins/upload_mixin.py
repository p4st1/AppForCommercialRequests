from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QPushButton

from config import Config
from services.platform_uploader import TradeUploader
from tools import DatabaseTools as Tool


class UploadTradeWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        *,
        trade_id: int,
        file_path: str,
        cookies: dict[str, str],
        allow_submit: bool = False,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._trade_id = int(trade_id)
        self._file_path = str(file_path)
        self._cookies = dict(cookies)
        self._allow_submit = bool(allow_submit)

    def run(self) -> None:
        try:
            uploader = TradeUploader(
                self._cookies,
                headless=False,
                allow_submit=self._allow_submit,
            )
            result_message = uploader.submit_trade(self._trade_id, self._file_path)
            self.finished.emit(result_message)
        except Exception as exc:
            self.error.emit(str(exc))


class UploadMixin:
    def init_upload_mixin(self) -> None:
        self._upload_trade_worker: UploadTradeWorker | None = None
        self._allow_submit: bool = False
        self._ensure_upload_button()
        self.btn_upload_kp.clicked.connect(self.upload_selected_trade)

    def _ensure_upload_button(self) -> None:
        if hasattr(self, "btn_upload_kp"):
            return

        ensure_tab = getattr(self, "_ensure_platform_tab", None)
        if callable(ensure_tab):
            ensure_tab()

        web_tab = getattr(self.ui, "webTab", None)
        if web_tab is None:
            raise RuntimeError("Не найден webTab для кнопки загрузки КП")

        root_layout = web_tab.layout()
        header_layout: QHBoxLayout | None = None
        if root_layout is not None and root_layout.count() > 0:
            header_item = root_layout.itemAt(0)
            if header_item is not None:
                layout = header_item.layout()
                if isinstance(layout, QHBoxLayout):
                    header_layout = layout

        if header_layout is None:
            raise RuntimeError("Не удалось найти layout заголовка вкладки заявок")

        self.btn_upload_kp = QPushButton("Загрузить КП", web_tab)
        self.btn_upload_kp.setObjectName("btn_upload_kp")
        self.ui.btn_upload_kp = self.btn_upload_kp
        header_layout.addWidget(self.btn_upload_kp)

    def upload_selected_trade(self) -> None:
        if self._upload_trade_worker is not None and self._upload_trade_worker.isRunning():
            return

        self._allow_submit = False
        allow_submit = False
        if self._confirm_submit_trade():
            allow_submit = True
        if not allow_submit:
            status_bar = self.statusBar()
            if status_bar is not None:
                status_bar.showMessage("Отправка КП отменена пользователем", 5_000)
            return

        try:
            trade_id = self._get_selected_trade_id()
            excel_path = self._resolve_excel_path_from_project()
            cookies = self.load_cookies()
        except Exception as exc:
            self._on_upload_error(str(exc))
            return

        self._allow_submit = allow_submit
        self._set_upload_loading_state(is_loading=True)

        worker = UploadTradeWorker(
            trade_id=trade_id,
            file_path=str(excel_path),
            cookies=cookies,
            allow_submit=self._allow_submit,
            parent=self,
        )
        worker.finished.connect(self._on_upload_finished)
        worker.error.connect(self._on_upload_error)
        self._upload_trade_worker = worker
        worker.start()

    def _confirm_submit_trade(self) -> bool:
        confirm = QMessageBox.question(
            self,
            "Подтверждение отправки",
            "Вы действительно хотите ОТПРАВИТЬ КП?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return confirm == QMessageBox.StandardButton.Yes

    def _get_selected_trade_id(self) -> int:
        table = getattr(self.ui, "tradesTable", None)
        if table is None:
            raise RuntimeError("Таблица заявок не найдена")

        selection_model = table.selectionModel()
        selected_rows = selection_model.selectedRows() if selection_model is not None else []
        if not selected_rows:
            raise ValueError("Выберите заявку в таблице перед загрузкой КП")

        row = selected_rows[0].row()
        trade_item = table.item(row, 0)
        trade_text = trade_item.text().strip() if trade_item is not None else ""
        if not trade_text:
            raise ValueError("Не удалось получить trade_id из выбранной строки")

        try:
            return int(trade_text)
        except ValueError as exc:
            raise ValueError(f"Некорректный trade_id в таблице: {trade_text}") from exc

    def _resolve_excel_path_from_project(self) -> Path:
        last_table_raw = str(Config.config.get("lastTable", "") or "").strip()
        if last_table_raw:
            last_table_path = Path(last_table_raw).expanduser()
            if (
                last_table_path.exists()
                and last_table_path.is_file()
                and last_table_path.suffix.lower() in {".xlsx", ".xls"}
            ):
                return last_table_path.resolve()

        project_dir = Tool.ensure_directory(
            Config.config.get("pathToSaveExcel") or Config.config.get("pathToSaveCP"),
            Tool.user_data_dir("MyApp") / "imports",
        )
        excel_candidates = sorted(
            [
                *project_dir.glob("*.xlsx"),
                *project_dir.glob("*.xls"),
            ]
        )
        excel_candidates = [
            path
            for path in excel_candidates
            if path.is_file()
            and not path.name.startswith("~$")
            and path.name.lower() not in {"template.xlsx", "template.xls"}
        ]

        if len(excel_candidates) == 1:
            return excel_candidates[0].resolve()
        if not excel_candidates:
            raise FileNotFoundError(
                "Не найден Excel файл в папке импорта. "
                "Сначала откройте КП поставщика или выберите папку сохранения в настройках."
            )

        candidates_text = ", ".join(path.name for path in excel_candidates[:5])
        raise ValueError(
            "Найдено несколько Excel файлов в папке импорта. "
            f"Откройте нужный файл через 'Загрузить КП поставщика' (найдено: {candidates_text})."
        )

    def _set_upload_loading_state(self, *, is_loading: bool) -> None:
        self.btn_upload_kp.setEnabled(not is_loading)
        self.btn_upload_kp.setText("Загрузка..." if is_loading else "Загрузить КП")

    def _finish_upload(self, status_message: str) -> None:
        self._allow_submit = False
        self._set_upload_loading_state(is_loading=False)
        worker = self._upload_trade_worker
        self._upload_trade_worker = None
        if worker is not None:
            worker.deleteLater()
        status_bar = self.statusBar()
        if status_bar is not None and status_message:
            status_bar.showMessage(status_message, 5_000)

    def _on_upload_finished(self, message: str) -> None:
        info_text = str(message or "Файл успешно загружен")
        Tool.write_log(f"Загрузка КП завершена: {info_text}")
        QMessageBox.information(self, "Загрузка КП", info_text)
        self._finish_upload("КП успешно загружено")

    def _on_upload_error(self, message: str) -> None:
        error_text = str(message or "Неизвестная ошибка")
        Tool.write_log(f"Ошибка загрузки КП: {error_text}")
        QMessageBox.warning(self, "Ошибка загрузки КП", error_text)
        self._finish_upload("Ошибка загрузки КП")
