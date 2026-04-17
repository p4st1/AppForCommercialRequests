from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QSignalBlocker, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config import Config
from services.platform_client import MetalITClient
from tools import DatabaseTools as Tool


class LoadTradesWorker(QThread):
    finished = Signal(list)
    error = Signal(str)

    def __init__(
        self,
        cookies: dict[str, str],
        max_items: int = 50,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._cookies = dict(cookies)
        self.max_items = max_items

    def run(self) -> None:
        try:
            if not self._cookies:
                raise ValueError("Не найдены cookies для авторизации")
            client = MetalITClient(self._cookies)
            trades = client.get_all_trades(max_items=self.max_items)
            self.finished.emit(trades)
        except Exception as exc:
            self.error.emit(str(exc))


class PlatformMixin:
    TRADE_HEADERS = (
        "id",
        "title",
        "registeredNumber",
        "bidSubmissionStartDate",
        "bidSubmissionEndDate",
        "currency.title",
    )

    def init_platform_mixin(self) -> None:
        self._load_trades_worker: LoadTradesWorker | None = None
        self._ensure_platform_tab()
        self.btn_load_trades.clicked.connect(self.load_trades_clicked)

    def _ensure_platform_tab(self) -> None:
        if (
            hasattr(self.ui, "tradesTable")
            and hasattr(self, "btn_load_trades")
            and hasattr(self.ui, "input_limit")
        ):
            return

        self.ui.webTab = QWidget(self.ui.tabWidget)
        self.ui.webTab.setObjectName("webTab")

        root_layout = QVBoxLayout(self.ui.webTab)
        root_layout.setSpacing(8)
        root_layout.setContentsMargins(8, 8, 8, 8)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("Заявки с площадки", self.ui.webTab)
        title_label.setObjectName("platformTitleLabel")

        self.btn_load_trades = QPushButton("Загрузить заявки", self.ui.webTab)
        self.btn_load_trades.setObjectName("btn_load_trades")
        self.ui.btn_load_trades = self.btn_load_trades

        self.input_limit = QLineEdit(self.ui.webTab)
        self.input_limit.setObjectName("input_limit")
        self.input_limit.setPlaceholderText("Количество заявок (например 50)")
        self.ui.input_limit = self.input_limit

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.input_limit)
        header_layout.addWidget(self.btn_load_trades)

        self.ui.tradesTable = QTableWidget(self.ui.webTab)
        self.ui.tradesTable.setObjectName("tradesTable")

        root_layout.addLayout(header_layout)
        root_layout.addWidget(self.ui.tradesTable)
        self.ui.tabWidget.addTab(self.ui.webTab, "Веб")

        self._setup_trades_table()

    def _setup_trades_table(self) -> None:
        table = self.ui.tradesTable
        table.setColumnCount(len(self.TRADE_HEADERS))
        table.setHorizontalHeaderLabels(self.TRADE_HEADERS)
        table.setRowCount(0)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(False)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

    @staticmethod
    def _normalize_cookies(raw: Any) -> dict[str, str]:
        if not isinstance(raw, dict):
            return {}
        return {
            str(key): str(value)
            for key, value in raw.items()
            if str(key).strip() and str(value).strip()
        }

    def _extract_cookies_from_payload(self, payload: dict[str, Any]) -> dict[str, str]:
        candidates: list[Any] = [payload.get("cookies")]

        config_section = payload.get("config")
        if isinstance(config_section, dict):
            candidates.append(config_section.get("cookies"))
            platform_section = config_section.get("platform")
            if isinstance(platform_section, dict):
                candidates.append(platform_section.get("cookies"))

        platform_root = payload.get("platform")
        if isinstance(platform_root, dict):
            candidates.append(platform_root.get("cookies"))

        for candidate in candidates:
            normalized = self._normalize_cookies(candidate)
            if normalized:
                return normalized

        return {}

    def load_cookies(self) -> dict[str, str]:
        candidate_paths: list[Path] = []
        cfg_path = str(getattr(Config, "cfg_path", "") or "").strip()
        if cfg_path:
            candidate_paths.append(Path(cfg_path))
        candidate_paths.append(Path("config.json"))

        seen: set[Path] = set()
        errors: list[str] = []

        for path in candidate_paths:
            resolved_path = path.expanduser()
            if resolved_path in seen:
                continue
            seen.add(resolved_path)

            if not resolved_path.exists():
                continue

            try:
                payload = Tool.load_json(resolved_path)
            except Exception as exc:
                errors.append(f"{resolved_path}: {exc}")
                continue

            cookies = self._extract_cookies_from_payload(payload)
            if not cookies:
                errors.append(
                    f"{resolved_path}: не найден раздел 'cookies' "
                    "(поддерживаются: cookies, config.cookies, config.platform.cookies)"
                )
                continue

            return cookies

        if errors:
            raise ValueError("; ".join(errors))

        raise FileNotFoundError("Не найден config.json с cookies")

    def load_trades_clicked(self) -> None:
        if self._load_trades_worker is not None and self._load_trades_worker.isRunning():
            return

        max_items = 50
        try:
            max_items = int(self.input_limit.text())
        except (TypeError, ValueError, AttributeError):
            max_items = 50
        if max_items <= 0:
            max_items = 50

        try:
            cookies = self.load_cookies()
        except Exception as exc:
            self.on_error(str(exc))
            return

        self._set_trades_loading_state(is_loading=True)

        worker = LoadTradesWorker(cookies=cookies, max_items=max_items, parent=self)
        worker.finished.connect(self.on_trades_loaded)
        worker.error.connect(self.on_error)
        self._load_trades_worker = worker
        worker.start()

    def on_trades_loaded(self, trades: list[dict[str, Any]]) -> None:
        self.populate_trades_table(trades)
        self._finish_trades_loading(f"Загружено заявок: {len(trades)}")

    def on_error(self, message: str) -> None:
        error_text = str(message or "Неизвестная ошибка")
        Tool.write_log(f"Ошибка загрузки заявок: {error_text}")
        print(f"Ошибка загрузки заявок: {error_text}")
        QMessageBox.warning(self, "Ошибка загрузки заявок", error_text)
        self._finish_trades_loading("Ошибка загрузки заявок")

    def _set_trades_loading_state(self, *, is_loading: bool) -> None:
        self.btn_load_trades.setEnabled(not is_loading)
        self.btn_load_trades.setText("Загрузка..." if is_loading else "Загрузить заявки")

    def _finish_trades_loading(self, status_message: str) -> None:
        self._set_trades_loading_state(is_loading=False)
        worker = self._load_trades_worker
        self._load_trades_worker = None
        if worker is not None:
            worker.deleteLater()
        status_bar = self.statusBar()
        if status_bar is not None and status_message:
            status_bar.showMessage(status_message, 4000)

    def populate_trades_table(self, trades: list[dict[str, Any]]) -> None:
        table = self.ui.tradesTable
        rows = trades if isinstance(trades, list) else []

        blocker = QSignalBlocker(table)
        table.clearContents()
        table.setRowCount(len(rows))

        for row_idx, trade in enumerate(rows):
            if not isinstance(trade, dict):
                continue

            currency = trade.get("currency")
            currency_title = ""
            if isinstance(currency, dict):
                currency_title = str(currency.get("title", "") or "")

            values = (
                trade.get("id", ""),
                trade.get("title", ""),
                trade.get("registeredNumber", ""),
                trade.get("bidSubmissionStartDate", ""),
                trade.get("bidSubmissionEndDate", ""),
                currency_title,
            )

            for col_idx, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                flags = item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                flags &= ~Qt.ItemFlag.ItemIsEditable
                item.setFlags(flags)
                table.setItem(row_idx, col_idx, item)

        del blocker
        table.resizeRowsToContents()
