from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSignalBlocker, Qt, QThread, QTimer, Signal
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

from app.ui.table_autosize import configure_table_autosize, resize_table_to_contents
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
        login: str = "",
        password: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._cookies = dict(cookies)
        self.max_items = max_items
        self._login = str(login or "").strip()
        self._password = str(password or "")

    @staticmethod
    def _is_auth_error(message: str) -> bool:
        text = str(message or "").lower()
        return (
            "401" in text
            or "403" in text
            or "forbidden" in text
            or "unauthorized" in text
        )

    def run(self) -> None:
        try:
            if not self._cookies:
                raise ValueError("Не найдены cookies для авторизации")
            client = MetalITClient(self._cookies)
            trades = client.get_all_trades(max_items=self.max_items)
            self.finished.emit(trades)
        except Exception as exc:
            error_text = str(exc or "Неизвестная ошибка")
            should_retry_auth = self._is_auth_error(error_text) or (
                "cookie" in error_text.lower()
            )
            if not should_retry_auth:
                self.error.emit(error_text)
                return

            if not self._login or not self._password:
                self.error.emit(
                    "Сессия истекла (401/403). "
                    "Для авто-переавторизации сохраните логин и пароль в настройках."
                )
                return

            try:
                print("AUTH: выполняем авто-переавторизацию из сохраненных учетных данных")
                service = AuthService(headless=False)
                refreshed_cookies = service.login_and_save_session(
                    self._login,
                    self._password,
                )
                if not isinstance(refreshed_cookies, dict) or not refreshed_cookies:
                    raise RuntimeError("После переавторизации не получены cookies")
                self._cookies = dict(refreshed_cookies)
                client = MetalITClient(self._cookies)
                trades = client.get_all_trades(max_items=self.max_items)
                self.finished.emit(trades)
            except Exception as retry_exc:
                self.error.emit(str(retry_exc))


class LoadRetradesWorker(QThread):
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
        self.client: MetalITClient | None = None

    @staticmethod
    def _is_forbidden_error(message: str) -> bool:
        text = str(message or "").lower()
        return "403" in text or "forbidden" in text

    def run(self) -> None:
        try:
            if not self._cookies:
                raise ValueError("Не найдены cookies для авторизации")
            self.client = MetalITClient(self._cookies)
            retrades = self.client.load_retrades(limit=50)
            if self.max_items > 0:
                retrades = retrades[: self.max_items]
            print(f"Загружено переторжек: {len(retrades)}")
            self.finished.emit(retrades)
        except Exception as exc:
            error_text = str(exc or "Неизвестная ошибка")
            if self._is_forbidden_error(error_text):
                self.error.emit("Ошибка авторизации — обновите cookies")
                return
            self.error.emit(error_text)


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
    STATUS_CHECK_TIMEOUT_SECONDS = 5.0

    def __init__(
        self,
        cookies: dict[str, str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._cookies = dict(cookies)

    def _interruption_requested(self) -> bool:
        is_interruption_requested = getattr(self, "isInterruptionRequested", None)
        if not callable(is_interruption_requested):
            return False
        try:
            return bool(is_interruption_requested())
        except RuntimeError:
            return True

    def run(self) -> None:
        try:
            if self._interruption_requested():
                return
            if not self._cookies:
                self.finished.emit(False)
                return
            client = MetalITClient(
                self._cookies,
                timeout=self.STATUS_CHECK_TIMEOUT_SECONDS,
            )
            is_auth = client.is_authenticated()
            if not self._interruption_requested():
                self.finished.emit(bool(is_auth))
        except Exception:
            if not self._interruption_requested():
                self.finished.emit(False)


class PlatformMixin:
    SEARCH_DEBOUNCE_MS = 250
    MIN_SEARCH_CHARS = 3
    TRADE_AUTOSIZE_ROW_LIMIT = 200
    AUTH_STATUS_REFRESH_DELAY_MS = 0

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
        self.retrades: list[dict[str, Any]] = []
        self.retrade_offers: list[dict[str, Any]] = []
        self._load_trades_worker: LoadTradesWorker | None = None
        self._load_retrades_worker: LoadRetradesWorker | None = None
        self._auth_login_worker: AuthLoginWorker | None = None
        self._auth_status_worker: AuthStatusWorker | None = None
        self._auth_status_refresh_timer: QTimer | None = None
        self._ensure_platform_tab()
        self._platform_search_timer = QTimer(self)
        self._platform_search_timer.setSingleShot(True)
        self._platform_search_timer.setInterval(self.SEARCH_DEBOUNCE_MS)
        self._platform_search_timer.timeout.connect(self.apply_filters)
        self._apply_web_auth_autofill_if_enabled()
        self.btn_login.clicked.connect(self.login)
        self.btn_load_trades.clicked.connect(self.load_trades_clicked)
        self.btn_load_retrades.clicked.connect(self.load_retrades)
        self.table_retrades.itemSelectionChanged.connect(self.on_retrade_selection_changed)
        self.search_input.textChanged.connect(self.apply_search)
        self.checkbox_active.stateChanged.connect(self.apply_filters)
        self._schedule_auth_status_refresh()

    def _schedule_auth_status_refresh(self) -> None:
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(self.refresh_auth_status_on_startup)
        self._auth_status_refresh_timer = timer
        timer.start(self.AUTH_STATUS_REFRESH_DELAY_MS)

    def _ensure_platform_tab(self) -> None:
        if (
            hasattr(self.ui, "tradesTable")
            and hasattr(self.ui, "table_retrades")
            and hasattr(self.ui, "table_retrade_offers")
            and hasattr(self, "btn_load_trades")
            and hasattr(self, "btn_load_retrades")
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

        self.btn_load_retrades = QPushButton("Загрузить переторжки", self.ui.webTab)
        self.btn_load_retrades.setObjectName("btn_load_retrades")
        self.ui.btn_load_retrades = self.btn_load_retrades

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
        header_layout.addWidget(self.btn_load_retrades)

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

        retrades_label = QLabel("Переторжки", self.ui.webTab)
        retrades_label.setObjectName("retradesTitleLabel")

        self.table_retrades = QTableWidget(self.ui.webTab)
        self.table_retrades.setObjectName("table_retrades")
        self.ui.table_retrades = self.table_retrades

        retrade_offers_label = QLabel("Предложения переторжки", self.ui.webTab)
        retrade_offers_label.setObjectName("retradeOffersTitleLabel")

        self.table_retrade_offers = QTableWidget(self.ui.webTab)
        self.table_retrade_offers.setObjectName("table_retrade_offers")
        self.ui.table_retrade_offers = self.table_retrade_offers

        root_layout.addLayout(auth_layout)
        root_layout.addLayout(header_layout)
        root_layout.addLayout(pipeline_status_layout)
        root_layout.addWidget(self.ui.tradesTable)
        root_layout.addWidget(retrades_label)
        root_layout.addWidget(self.table_retrades)
        root_layout.addWidget(retrade_offers_label)
        root_layout.addWidget(self.table_retrade_offers)
        self.ui.tabWidget.addTab(self.ui.webTab, "Прием заявок")

        self._setup_trades_table()
        self._setup_retrades_table()
        self._setup_retrade_offers_table()

    def login(self) -> None:
        if self._auth_login_worker is not None and self._auth_login_worker.isRunning():
            return

        login = self.input_login.text().strip()
        password = self.input_password.text()
        if not login or not password:
            QMessageBox.warning(self, "Авторизация", "Введите логин и пароль")
            return

        if bool(Config.settings.get("autoFillWebAuth", False)):
            self._save_web_auth_credentials(login, password)

        self._set_login_loading_state(is_loading=True)
        worker = AuthLoginWorker(login=login, password=password, parent=self)
        worker.finished.connect(self.on_login_success)
        worker.error.connect(self.on_login_error)
        self._auth_login_worker = worker
        worker.start()

    def on_login_success(self, cookies: dict[str, str]) -> None:
        cookies_count = len(cookies) if isinstance(cookies, dict) else 0
        try:
            self._save_web_auth_to_root_config(cookies)
        except Exception as exc:
            Tool.write_log(f"Не удалось сохранить web cookies в config.json: {exc}")
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
        if bool(getattr(self, "_app_is_closing", False)):
            return
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
        if bool(getattr(self, "_app_is_closing", False)):
            return
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

        configure_table_autosize(table)
        self._set_trades_table_fast_resize_mode(table)

    @staticmethod
    def _set_trades_table_fast_resize_mode(
        table: QTableWidget,
        *,
        apply_default_widths: bool = True,
    ) -> None:
        header = table.horizontalHeader()
        interactive = QHeaderView.ResizeMode.Interactive
        header.setSectionResizeMode(0, interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, interactive)
        header.setSectionResizeMode(3, interactive)
        header.setSectionResizeMode(4, interactive)
        header.setSectionResizeMode(5, interactive)

        vertical_header = table.verticalHeader()
        vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vertical_header.setDefaultSectionSize(24)
        vertical_header.setMinimumSectionSize(20)

        if apply_default_widths:
            for column, width in (
                (0, 86),
                (1, 420),
                (2, 150),
                (3, 170),
                (4, 170),
                (5, 100),
            ):
                table.setColumnWidth(column, width)

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

    @staticmethod
    def _extract_web_auth_from_payload(payload: dict[str, Any]) -> tuple[str, str]:
        if not isinstance(payload, dict):
            return "", ""

        login = ""
        password = ""
        config_section = payload.get("config")
        if isinstance(config_section, dict):
            login = str(config_section.get("platformLogin", "") or "").strip()
            password = str(config_section.get("platformPassword", "") or "")
            if not login:
                platform_section = config_section.get("platform")
                if isinstance(platform_section, dict):
                    login = str(platform_section.get("login", "") or "").strip()
                    password = str(platform_section.get("password", "") or "")

        if not login:
            login = str(payload.get("platformLogin", "") or "").strip()
        if not password:
            password = str(payload.get("platformPassword", "") or "")

        platform_root = payload.get("platform")
        if isinstance(platform_root, dict):
            if not login:
                login = str(platform_root.get("login", "") or "").strip()
            if not password:
                password = str(platform_root.get("password", "") or "")

        return login, password

    def _load_web_auth_credentials(self) -> tuple[str, str]:
        login = str(Config.config.get("platformLogin", "") or "").strip()
        password = str(Config.config.get("platformPassword", "") or "")
        if login and password:
            return login, password

        candidate_paths = Tool.config_candidate_paths()

        seen: set[Path] = set()
        for path in candidate_paths:
            resolved_path = path.expanduser()
            if resolved_path in seen:
                continue
            seen.add(resolved_path)
            if not resolved_path.exists():
                continue
            try:
                payload = Tool.load_json(resolved_path)
            except Exception:
                continue
            loaded_login, loaded_password = self._extract_web_auth_from_payload(payload)
            if loaded_login and loaded_password:
                return loaded_login, loaded_password
        return "", ""

    def _apply_web_auth_autofill_if_enabled(self) -> None:
        if not bool(Config.settings.get("autoFillWebAuth", False)):
            return
        login, password = self._load_web_auth_credentials()
        if login:
            self.input_login.setText(login)
        if password:
            self.input_password.setText(password)

    def _save_web_auth_credentials_to_path(
        self,
        path: Path,
        *,
        login: str,
        password: str,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {}
        if path.exists():
            try:
                loaded = Tool.load_json(path)
                if isinstance(loaded, dict):
                    payload = loaded
            except Exception:
                payload = {}

        normalized_payload = Tool.merge_config_with_defaults(payload)
        config_section = normalized_payload.get("config")
        if not isinstance(config_section, dict):
            config_section = {}
        normalized_payload["config"] = dict(config_section)
        normalized_payload["config"]["platformLogin"] = login
        normalized_payload["config"]["platformPassword"] = password

        platform_section = normalized_payload["config"].get("platform")
        if not isinstance(platform_section, dict):
            platform_section = {}
        normalized_payload["config"]["platform"] = dict(platform_section)
        normalized_payload["config"]["platform"]["login"] = login
        normalized_payload["config"]["platform"]["password"] = password

        Tool.save_json_atomic(path, normalized_payload)

    def _save_web_auth_credentials(self, login_raw: Any, password_raw: Any) -> None:
        login = str(login_raw or "").strip()
        password = str(password_raw or "")
        if not login or not password:
            return

        if isinstance(Config.config, dict):
            Config.config["platformLogin"] = login
            Config.config["platformPassword"] = password

        cfg_path = str(getattr(Config, "cfg_path", "") or "").strip()
        cfg_file = Path(cfg_path).expanduser() if cfg_path else Tool.user_config_path()
        self._save_web_auth_credentials_to_path(
            cfg_file,
            login=login,
            password=password,
        )

    def _save_web_auth_to_root_config(self, cookies_raw: Any) -> None:
        cookies = self._normalize_cookies(cookies_raw)
        if not cookies:
            return

        cfg_path = str(getattr(Config, "cfg_path", "") or "").strip()
        config_path = Path(cfg_path).expanduser() if cfg_path else Tool.user_config_path()
        payload: dict[str, Any] = {}
        if config_path.exists():
            try:
                loaded = Tool.load_json(config_path)
                if isinstance(loaded, dict):
                    payload = loaded
            except Exception as exc:
                Tool.write_log(f"Не удалось прочитать config.json перед сохранением cookies: {exc}")
                payload = {}

        normalized_payload = Tool.merge_config_with_defaults(payload)
        normalized_payload["cookies"] = cookies
        config_section = normalized_payload.get("config")
        if not isinstance(config_section, dict):
            config_section = {}
        normalized_payload["config"] = dict(config_section)
        normalized_payload["config"]["cookies"] = cookies

        Tool.save_json_atomic(config_path, normalized_payload)
        if isinstance(Config.config, dict):
            Config.config["cookies"] = cookies

    def load_cookies(self) -> dict[str, str]:
        candidate_paths = Tool.config_candidate_paths()

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

        max_items = self._parse_max_items_input()
        login, password = self._load_web_auth_credentials()
        if not login:
            login = self.input_login.text().strip()
        if not password:
            password = self.input_password.text()
        cookies: dict[str, str] = {}
        load_cookies_error = ""

        try:
            cookies = self.load_cookies()
        except Exception as exc:
            load_cookies_error = str(exc or "")
            if not login or not password:
                self.on_error(load_cookies_error)
                return
            Tool.write_log(
                "Cookies не найдены или невалидны. "
                "Будет выполнена авто-переавторизация перед загрузкой заявок."
            )

        self._set_trades_loading_state(is_loading=True)

        worker = LoadTradesWorker(
            cookies=cookies,
            max_items=max_items,
            login=login,
            password=password,
            parent=self,
        )
        worker.finished.connect(self.on_trades_loaded)
        worker.error.connect(self.on_error)
        self._load_trades_worker = worker
        worker.start()

    def load_trades(self) -> None:
        self.load_trades_clicked()

    def load_retrades(self) -> None:
        if (
            self._load_retrades_worker is not None
            and self._load_retrades_worker.isRunning()
        ):
            return

        max_items = self._parse_max_items_input()

        try:
            cookies = self.load_cookies()
        except Exception as exc:
            self.on_retrades_error(str(exc))
            return

        self._set_retrades_loading_state(is_loading=True)

        worker = LoadRetradesWorker(cookies=cookies, max_items=max_items, parent=self)
        worker.finished.connect(self.on_retrades_loaded)
        worker.error.connect(self.on_retrades_error)
        self._load_retrades_worker = worker
        worker.start()

    def on_trades_loaded(self, trades: list[dict[str, Any]]) -> None:
        self.all_trades = trades if isinstance(trades, list) else []
        self.filtered_trades = list(self.all_trades)
        self.apply_filters()
        self._finish_trades_loading(f"Загружено заявок: {len(self.all_trades)}")

    def on_retrades_loaded(self, retrades: list[dict[str, Any]]) -> None:
        self.retrades = retrades if isinstance(retrades, list) else []
        self.retrade_offers = []
        self.populate_retrades_table(self.retrades)
        self.populate_retrade_offers_table([])
        self._finish_retrades_loading(f"Загружено переторжек: {len(self.retrades)}")

    def on_error(self, message: str) -> None:
        error_text = str(message or "Неизвестная ошибка")
        Tool.write_log(f"Ошибка загрузки заявок: {error_text}")
        print(f"Ошибка загрузки заявок: {error_text}")
        if "401" in error_text or "403" in error_text:
            self._set_auth_status(is_auth=False)
        QMessageBox.warning(self, "Ошибка загрузки заявок", error_text)
        self._finish_trades_loading("Ошибка загрузки заявок")

    def _set_trades_loading_state(self, *, is_loading: bool) -> None:
        self.btn_load_trades.setEnabled(not is_loading)
        self.btn_load_trades.setText("Загрузка..." if is_loading else "Загрузить заявки")

    def _set_retrades_loading_state(self, *, is_loading: bool) -> None:
        self.btn_load_retrades.setEnabled(not is_loading)
        self.btn_load_retrades.setText(
            "Загрузка..." if is_loading else "Загрузить переторжки"
        )

    def _finish_trades_loading(self, status_message: str) -> None:
        self._set_trades_loading_state(is_loading=False)
        worker = self._load_trades_worker
        self._load_trades_worker = None
        if worker is not None:
            worker.deleteLater()
        status_bar = self.statusBar()
        if status_bar is not None and status_message:
            status_bar.showMessage(status_message, 4000)

    def _finish_retrades_loading(self, status_message: str) -> None:
        self._set_retrades_loading_state(is_loading=False)
        worker = self._load_retrades_worker
        self._load_retrades_worker = None
        if worker is not None:
            worker.deleteLater()
        status_bar = self.statusBar()
        if status_bar is not None and status_message:
            status_bar.showMessage(status_message, 4000)

    def on_retrades_error(self, message: str) -> None:
        error_text = str(message or "Неизвестная ошибка")
        Tool.write_log(f"Ошибка загрузки переторжек: {error_text}")
        print(f"Ошибка загрузки переторжек: {error_text}")
        self.retrade_offers = []
        self.populate_retrade_offers_table([])
        if (
            "401" in error_text
            or "403" in error_text
            or "Ошибка доступа — требуется повторная авторизация" in error_text
            or "Ошибка авторизации — обновите cookies" in error_text
        ):
            self._set_auth_status(is_auth=False)
        QMessageBox.warning(self, "Ошибка загрузки переторжек", error_text)
        self._finish_retrades_loading("Ошибка загрузки переторжек")

    def _setup_retrades_table(self) -> None:
        table = self.table_retrades
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(("Номер", "Название", "Статус", "Дата окончания"))
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
        configure_table_autosize(table)

    def _setup_retrade_offers_table(self) -> None:
        table = self.table_retrade_offers
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(("number", "bidder_title", "price", "status"))
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
        configure_table_autosize(table)

    def populate_retrades_table(self, retrades: list[dict[str, Any]]) -> None:
        table = self.table_retrades
        rows = retrades if isinstance(retrades, list) else []

        blocker = QSignalBlocker(table)
        table.clearContents()
        table.setRowCount(len(rows))

        for row_idx, retrade in enumerate(rows):
            if not isinstance(retrade, dict):
                continue

            values = (
                retrade.get("number", "")
                or retrade.get("registeredNumber", "")
                or retrade.get("id", ""),
                retrade.get("title", "") or "",
                retrade.get("status", "") or retrade.get("processStatus", ""),
                retrade.get("endDate", "") or retrade.get("bidSubmissionEndDate", ""),
            )

            for col_idx, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                flags = item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                flags &= ~Qt.ItemFlag.ItemIsEditable
                item.setFlags(flags)
                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, retrade)
                table.setItem(row_idx, col_idx, item)

        del blocker
        resize_table_to_contents(table)

    def populate_retrade_offers_table(self, offers: list[dict[str, Any]]) -> None:
        table = self.table_retrade_offers
        rows = offers if isinstance(offers, list) else []

        blocker = QSignalBlocker(table)
        table.clearContents()
        table.setRowCount(len(rows))

        for row_idx, offer in enumerate(rows):
            if not isinstance(offer, dict):
                continue

            values = (
                offer.get("number", ""),
                offer.get("bidder_title", ""),
                offer.get("price", ""),
                offer.get("status", ""),
            )
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                flags = item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                flags &= ~Qt.ItemFlag.ItemIsEditable
                item.setFlags(flags)
                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, offer)
                table.setItem(row_idx, col_idx, item)

        del blocker
        resize_table_to_contents(table)

    def on_retrade_selection_changed(self) -> None:
        table = self.table_retrades
        selected_row = table.currentRow()
        if selected_row < 0 or selected_row >= len(self.retrades):
            self.retrade_offers = []
            self.populate_retrade_offers_table([])
            return

        retrade = self.retrades[selected_row]
        if not isinstance(retrade, dict):
            self.retrade_offers = []
            self.populate_retrade_offers_table([])
            return

        offers_cached = retrade.get("offers")
        if isinstance(offers_cached, list):
            self.retrade_offers = offers_cached
            self.populate_retrade_offers_table(self.retrade_offers)
            return

        trade_id_raw = retrade.get("id")
        try:
            trade_id = int(trade_id_raw)
        except (TypeError, ValueError):
            self.retrade_offers = []
            self.populate_retrade_offers_table([])
            return

        try:
            cookies = self.load_cookies()
            client = MetalITClient(cookies)
            offers = client.get_retrading_offers(trade_id)
        except Exception as exc:
            error_text = str(exc or "Неизвестная ошибка")
            Tool.write_log(f"Ошибка загрузки предложений переторжки: {error_text}")
            print(f"Ошибка загрузки предложений переторжки: {error_text}")
            offers = []

        retrade["offers"] = offers
        self.retrade_offers = offers
        self.populate_retrade_offers_table(offers)

    def _parse_max_items_input(self) -> int:
        override = getattr(self, "_trades_load_max_items_override", None)
        if override is not None:
            try:
                value = int(override)
            except (TypeError, ValueError):
                value = 50
            return value if value > 0 else 50

        max_items = 50
        try:
            max_items = int(self.input_limit.text())
        except (TypeError, ValueError, AttributeError):
            max_items = 50
        if max_items <= 0:
            max_items = 50
        return max_items

    def populate_trades_table(self, trades: list[dict[str, Any]]) -> None:
        table = self.ui.tradesTable
        rows = trades if isinstance(trades, list) else []
        today = datetime.now()
        sorting_enabled = table.isSortingEnabled()
        updates_enabled = table.updatesEnabled()

        self._set_trades_table_fast_resize_mode(table)
        table.setSortingEnabled(False)
        blocker = QSignalBlocker(table)
        table.setUpdatesEnabled(False)
        try:
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
                    flags = (
                        item.flags()
                        | Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsEnabled
                    )
                    flags &= ~Qt.ItemFlag.ItemIsEditable
                    item.setFlags(flags)
                    item.setBackground(color)
                    if col_idx == 0:
                        item.setData(Qt.ItemDataRole.UserRole, trade)
                    table.setItem(row_idx, col_idx, item)
        finally:
            del blocker
            table.setSortingEnabled(sorting_enabled)
            table.setUpdatesEnabled(updates_enabled)

        if len(rows) <= self.TRADE_AUTOSIZE_ROW_LIMIT:
            resize_table_to_contents(table)
            self._set_trades_table_fast_resize_mode(table, apply_default_widths=False)
        else:
            viewport = table.viewport()
            if viewport is not None:
                viewport.update()

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
        timer = getattr(self, "_platform_search_timer", None)
        if isinstance(timer, QTimer):
            timer.start()
            return
        self.apply_filters()

    def apply_filters(self, _: int = 0) -> None:
        timer = getattr(self, "_platform_search_timer", None)
        if isinstance(timer, QTimer) and timer.isActive():
            timer.stop()

        search_text = self._normalize_search_text(self.search_input.text())
        if self._is_search_text_too_short(search_text):
            self.filtered_trades = []
            self.populate_trades_table([])
            self._show_platform_status(
                f"Введите минимум {self.MIN_SEARCH_CHARS} символа для поиска"
            )
            return

        trades = self._filter_trades(
            self.all_trades,
            active_only=self.checkbox_active.isChecked(),
            search_text=search_text,
        )

        self.filtered_trades = trades
        self.populate_trades_table(self.filtered_trades)

    @staticmethod
    def _normalize_search_text(value: Any) -> str:
        return " ".join(str(value or "").casefold().split())

    @classmethod
    def _is_search_text_too_short(cls, search_text: str) -> bool:
        return bool(search_text) and len(search_text) < cls.MIN_SEARCH_CHARS

    @classmethod
    def _filter_trades(
        cls,
        trades: list[dict[str, Any]] | Any,
        *,
        active_only: bool,
        search_text: str,
    ) -> list[dict[str, Any]]:
        rows = (
            [trade for trade in trades if isinstance(trade, dict)]
            if isinstance(trades, list)
            else []
        )

        if active_only:
            rows = [
                trade
                for trade in rows
                if trade.get("bidSubmissionEndDate") is not None
            ]

        text = cls._normalize_search_text(search_text)
        if not text:
            return rows

        return [
            trade
            for trade in rows
            if (
                text in cls._normalize_search_text(trade.get("title", ""))
                or text in cls._normalize_search_text(trade.get("registeredNumber", ""))
            )
        ]

    def _show_platform_status(self, message: str, timeout_ms: int = 3000) -> None:
        status_bar_getter = getattr(self, "statusBar", None)
        status_bar = status_bar_getter() if callable(status_bar_getter) else None
        if status_bar is not None and message:
            status_bar.showMessage(message, timeout_ms)
