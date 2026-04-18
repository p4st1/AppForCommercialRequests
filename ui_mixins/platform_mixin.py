from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSignalBlocker, Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
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
from services.auth_service import AuthService
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


class AuthLoginWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(
        self,
        login: str,
        password: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._login = login
        self._password = password

    def run(self) -> None:
        try:
            service = AuthService(headless=False)
            cookies = service.login_and_save_session(self._login, self._password)
            self.finished.emit(cookies)
        except Exception as exc:
            self.error.emit(str(exc))


class AuthStatusWorker(QThread):
    finished = Signal(bool)

    def __init__(
        self,
        cookies: dict[str, str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._cookies = dict(cookies)

    def run(self) -> None:
        try:
            if not self._cookies:
                self.finished.emit(False)
                return
            client = MetalITClient(self._cookies)
            is_auth = client.is_authenticated()
            self.finished.emit(bool(is_auth))
        except Exception:
            self.finished.emit(False)


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
        self.all_trades: list[dict[str, Any]] = []
        self.filtered_trades: list[dict[str, Any]] = []
        self._load_trades_worker: LoadTradesWorker | None = None
        self._auth_login_worker: AuthLoginWorker | None = None
        self._auth_status_worker: AuthStatusWorker | None = None
        self._ensure_platform_tab()
        self.btn_login.clicked.connect(self.login)
        self.btn_load_trades.clicked.connect(self.load_trades_clicked)
        self.search_input.textChanged.connect(self.apply_search)
        self.checkbox_active.stateChanged.connect(self.apply_filters)
        self.refresh_auth_status_on_startup()

    def _ensure_platform_tab(self) -> None:
        if (
            hasattr(self.ui, "tradesTable")
            and hasattr(self, "btn_load_trades")
            and hasattr(self.ui, "input_limit")
            and hasattr(self, "btn_login")
            and hasattr(self.ui, "input_login")
            and hasattr(self.ui, "input_password")
            and hasattr(self, "search_input")
            and hasattr(self, "checkbox_active")
            and hasattr(self, "label_auth_status")
            and hasattr(self, "label_pipeline_status")
        ):
            return

        self.ui.webTab = QWidget(self.ui.tabWidget)
        self.ui.webTab.setObjectName("webTab")

        root_layout = QVBoxLayout(self.ui.webTab)
        root_layout.setSpacing(8)
        root_layout.setContentsMargins(8, 8, 8, 8)

        auth_layout = QHBoxLayout()
        auth_layout.setSpacing(8)
        auth_layout.setContentsMargins(0, 0, 0, 0)

        auth_label = QLabel("Авторизация", self.ui.webTab)
        auth_label.setObjectName("platformAuthLabel")

        self.label_auth_status = QLabel("Проверка авторизации...", self.ui.webTab)
        self.label_auth_status.setObjectName("label_auth_status")
        self.label_auth_status.setStyleSheet("color: #666666")
        self.ui.label_auth_status = self.label_auth_status

        self.input_login = QLineEdit(self.ui.webTab)
        self.input_login.setObjectName("input_login")
        self.input_login.setPlaceholderText("Логин")
        self.ui.input_login = self.input_login

        self.input_password = QLineEdit(self.ui.webTab)
        self.input_password.setObjectName("input_password")
        self.input_password.setPlaceholderText("Пароль")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.input_password = self.input_password

        self.btn_login = QPushButton("Войти", self.ui.webTab)
        self.btn_login.setObjectName("btn_login")
        self.ui.btn_login = self.btn_login

        auth_layout.addWidget(auth_label)
        auth_layout.addWidget(self.label_auth_status)
        auth_layout.addWidget(self.input_login)
        auth_layout.addWidget(self.input_password)
        auth_layout.addWidget(self.btn_login)
        auth_layout.addStretch(1)

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

        self.search_input = QLineEdit(self.ui.webTab)
        self.search_input.setObjectName("search_input")
        self.search_input.setPlaceholderText("Поиск по номеру или названию")
        self.ui.search_input = self.search_input

        self.checkbox_active = QCheckBox("Только активные", self.ui.webTab)
        self.checkbox_active.setObjectName("checkbox_active")
        self.ui.checkbox_active = self.checkbox_active

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.checkbox_active)
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(self.input_limit)
        header_layout.addWidget(self.btn_load_trades)

        pipeline_status_layout = QHBoxLayout()
        pipeline_status_layout.setSpacing(8)
        pipeline_status_layout.setContentsMargins(0, 0, 0, 0)

        pipeline_status_title = QLabel("Статус pipeline:", self.ui.webTab)
        pipeline_status_title.setObjectName("pipelineStatusTitle")

        self.label_pipeline_status = QLabel("Готово", self.ui.webTab)
        self.label_pipeline_status.setObjectName("label_pipeline_status")
        self.label_pipeline_status.setStyleSheet("color: #344054; font-weight: bold")
        self.ui.label_pipeline_status = self.label_pipeline_status

        pipeline_status_layout.addWidget(pipeline_status_title)
        pipeline_status_layout.addWidget(self.label_pipeline_status)
        pipeline_status_layout.addStretch(1)

        self.ui.tradesTable = QTableWidget(self.ui.webTab)
        self.ui.tradesTable.setObjectName("tradesTable")

        root_layout.addLayout(auth_layout)
        root_layout.addLayout(header_layout)
        root_layout.addLayout(pipeline_status_layout)
        root_layout.addWidget(self.ui.tradesTable)
        self.ui.tabWidget.addTab(self.ui.webTab, "Веб")

        self._setup_trades_table()

    def login(self) -> None:
        if self._auth_login_worker is not None and self._auth_login_worker.isRunning():
            return

        login = self.input_login.text().strip()
        password = self.input_password.text()
        if not login or not password:
            QMessageBox.warning(self, "Авторизация", "Введите логин и пароль")
            return

        self._set_login_loading_state(is_loading=True)
        worker = AuthLoginWorker(login=login, password=password, parent=self)
        worker.finished.connect(self.on_login_success)
        worker.error.connect(self.on_login_error)
        self._auth_login_worker = worker
        worker.start()

    def on_login_success(self, cookies: dict[str, str]) -> None:
        cookies_count = len(cookies) if isinstance(cookies, dict) else 0
        self._set_auth_status(is_auth=True)
        self._finish_login(
            f"Авторизация успешна. Cookies сохранены ({cookies_count})."
        )

    def on_login_error(self, message: str) -> None:
        error_text = str(message or "Неизвестная ошибка")
        Tool.write_log(f"Ошибка авторизации на площадке: {error_text}")
        print(f"Ошибка авторизации на площадке: {error_text}")
        QMessageBox.warning(self, "Ошибка авторизации", error_text)
        self._set_auth_status(is_auth=False)
        self._finish_login("Ошибка авторизации")

    def _set_login_loading_state(self, *, is_loading: bool) -> None:
        self.btn_login.setEnabled(not is_loading)
        self.input_login.setEnabled(not is_loading)
        self.input_password.setEnabled(not is_loading)
        self.btn_login.setText("Вход..." if is_loading else "Войти")

    def _finish_login(self, status_message: str) -> None:
        self._set_login_loading_state(is_loading=False)
        worker = self._auth_login_worker
        self._auth_login_worker = None
        if worker is not None:
            worker.deleteLater()
        status_bar = self.statusBar()
        if status_bar is not None and status_message:
            status_bar.showMessage(status_message, 4000)

    def refresh_auth_status_on_startup(self) -> None:
        if self._auth_status_worker is not None and self._auth_status_worker.isRunning():
            return

        self._set_auth_status_checking()
        try:
            cookies = self.load_cookies()
        except Exception as exc:
            Tool.write_log(
                "Проверка авторизации на старте: cookies не найдены или невалидны: "
                f"{exc}"
            )
            self._set_auth_status(is_auth=False)
            return

        worker = AuthStatusWorker(cookies=cookies, parent=self)
        worker.finished.connect(self.on_auth_status_checked)
        self._auth_status_worker = worker
        worker.start()

    def on_auth_status_checked(self, is_auth: bool) -> None:
        worker = self._auth_status_worker
        self._auth_status_worker = None
        if worker is not None:
            worker.deleteLater()
        self._set_auth_status(is_auth=bool(is_auth))

    def _set_auth_status_checking(self) -> None:
        self.label_auth_status.setText("Проверка авторизации...")
        self.label_auth_status.setStyleSheet("color: #666666")

    def _set_auth_status(self, *, is_auth: bool) -> None:
        if is_auth:
            self.label_auth_status.setText("Авторизован")
            self.label_auth_status.setStyleSheet("color: green")
            return
        self.label_auth_status.setText("Не авторизован")
        self.label_auth_status.setStyleSheet("color: red")

    def _setup_trades_table(self) -> None:
        table = self.ui.tradesTable
        table.setColumnCount(len(self.TRADE_HEADERS))
        table.setHorizontalHeaderLabels(self.TRADE_HEADERS)
        table.setRowCount(0)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(False)
        try:
            table.itemDoubleClicked.disconnect(self.on_trade_double_click)
        except (TypeError, RuntimeError):
            pass
        table.itemDoubleClicked.connect(self.on_trade_double_click)

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
        candidate_paths.extend([Path("config.json"), Path("utilities/config.json")])

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

    def load_trades(self) -> None:
        self.load_trades_clicked()

    def on_trades_loaded(self, trades: list[dict[str, Any]]) -> None:
        self.all_trades = trades if isinstance(trades, list) else []
        self.filtered_trades = list(self.all_trades)
        self.apply_filters()
        self._finish_trades_loading(f"Загружено заявок: {len(self.all_trades)}")

    def on_error(self, message: str) -> None:
        error_text = str(message or "Неизвестная ошибка")
        Tool.write_log(f"Ошибка загрузки заявок: {error_text}")
        print(f"Ошибка загрузки заявок: {error_text}")
        if "401" in error_text:
            self._set_auth_status(is_auth=False)
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
        today = datetime.now()
        sorting_enabled = table.isSortingEnabled()

        table.setSortingEnabled(False)
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

            end_date = trade.get("bidSubmissionEndDate")
            if end_date:
                try:
                    dt = datetime.fromisoformat(str(end_date).replace("Z", ""))
                    diff = (dt - today).days
                    if diff <= 1:
                        color = QColor(255, 200, 200)
                    elif diff <= 3:
                        color = QColor(255, 255, 200)
                    else:
                        color = QColor(200, 255, 200)
                except Exception:
                    color = QColor(255, 255, 255)
            else:
                color = QColor(220, 220, 220)

            for col_idx, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                flags = item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                flags &= ~Qt.ItemFlag.ItemIsEditable
                item.setFlags(flags)
                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, trade)
                table.setItem(row_idx, col_idx, item)

            for col_idx in range(table.columnCount()):
                item = table.item(row_idx, col_idx)
                if item:
                    item.setBackground(color)

        del blocker
        table.setSortingEnabled(sorting_enabled)
        table.resizeRowsToContents()
        table.resizeColumnsToContents()

    def on_trade_double_click(self, item: QTableWidgetItem) -> None:
        row = item.row()
        if row < 0:
            return

        trade: dict[str, Any] | None = None
        row_item = self.ui.tradesTable.item(row, 0)
        if row_item is not None:
            trade_data = row_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(trade_data, dict):
                trade = trade_data

        if trade is None and 0 <= row < len(self.filtered_trades):
            candidate = self.filtered_trades[row]
            if isinstance(candidate, dict):
                trade = candidate

        if not isinstance(trade, dict):
            return

        trade_id = trade.get("id")
        print("Открываем заявку:", trade_id)

    def apply_search(self, _: str = "") -> None:
        self.apply_filters()

    def apply_filters(self, _: int = 0) -> None:
        trades = list(self.all_trades) if isinstance(self.all_trades, list) else []

        if self.checkbox_active.isChecked():
            trades = [
                trade
                for trade in trades
                if isinstance(trade, dict) and trade.get("bidSubmissionEndDate") is not None
            ]

        text = self.search_input.text().lower().strip()
        if text:
            trades = [
                trade
                for trade in trades
                if isinstance(trade, dict)
                and (
                    text in (trade.get("title", "") or "").lower()
                    or text in str(trade.get("registeredNumber", "")).lower()
                )
            ]

        self.filtered_trades = trades
        self.populate_trades_table(self.filtered_trades)
