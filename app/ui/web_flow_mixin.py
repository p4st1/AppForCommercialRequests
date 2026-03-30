import json
import re

from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QSplitter,
    QTextEdit,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from app.services.web_automation_scripts import WebAutomationScripts
from config import Config
from tools import DatabaseTools as Tool


class WebFlowMixin:
    def _ensure_web_tab(self):
        if hasattr(self.ui, "webView"):
            return

        self.ui.webTab = QWidget(self.ui.tabWidget)
        self.ui.webTab.setObjectName("webTab")

        root_layout = QVBoxLayout(self.ui.webTab)
        root_layout.setSpacing(8)
        root_layout.setContentsMargins(8, 8, 8, 8)

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self.ui.webUrlLine = QLineEdit(self.ui.webTab)
        self.ui.webUrlLine.setPlaceholderText("URL страницы")
        self.ui.webUrlLine.setText("https://etp.metal-it.ru/frame/index.html")

        self.ui.webLoginLine = QLineEdit(self.ui.webTab)
        self.ui.webLoginLine.setPlaceholderText("Логин")
        self.ui.webLoginLine.setMinimumWidth(170)

        self.ui.webPasswordLine = QLineEdit(self.ui.webTab)
        self.ui.webPasswordLine.setPlaceholderText("Пароль")
        self.ui.webPasswordLine.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.webPasswordLine.setMinimumWidth(170)
        saved_login, saved_password = self._get_saved_web_auth_credentials()
        self.ui.webLoginLine.setText(saved_login)
        self.ui.webPasswordLine.setText(saved_password)
        self.ui.webRequestNumberLine = QLineEdit(self.ui.webTab)
        self.ui.webRequestNumberLine.setPlaceholderText("Номер заявки")
        self.ui.webRequestNumberLine.setMinimumWidth(180)
        self.ui.webRequestNumberLine.setText(
            str(
                Config.config.get(
                    "webRequestNumber",
                    Config.config.get("requestNumber", ""),
                )
                or ""
            ).strip()
        )

        self.ui.webOpenButton = QPushButton("Открыть", self.ui.webTab)
        self.ui.webAuthButton = QPushButton("Авторизоваться", self.ui.webTab)
        self.ui.webStopAuthButton = QPushButton("Остановить авторизацию", self.ui.webTab)
        self.ui.webParseButton = QPushButton("Распарсить", self.ui.webTab)
        self.ui.webStopAuthButton.setVisible(False)

        controls_layout.addWidget(self.ui.webUrlLine, 1)
        controls_layout.addWidget(self.ui.webLoginLine)
        controls_layout.addWidget(self.ui.webPasswordLine)
        controls_layout.addWidget(self.ui.webRequestNumberLine)
        controls_layout.addWidget(self.ui.webOpenButton)
        controls_layout.addWidget(self.ui.webAuthButton)
        controls_layout.addWidget(self.ui.webStopAuthButton)
        controls_layout.addWidget(self.ui.webParseButton)

        self.ui.webStatusLabel = QLabel("Готово", self.ui.webTab)
        self.ui.webStatusLabel.setWordWrap(True)
        self.ui.webStatusLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        splitter = QSplitter(Qt.Orientation.Vertical, self.ui.webTab)
        self.ui.webView = QWebEngineView(splitter)
        self.ui.webParserOutput = QTextEdit(splitter)
        self.ui.webParserOutput.setReadOnly(True)
        self.ui.webParserOutput.setPlaceholderText("Результат парсинга появится здесь")
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 2)

        root_layout.addLayout(controls_layout)
        root_layout.addWidget(self.ui.webStatusLabel)
        root_layout.addWidget(splitter)

        self.ui.tabWidget.addTab(self.ui.webTab, "Веб")

        self.ui.webOpenButton.clicked.connect(self._open_web_page)
        self.ui.webAuthButton.clicked.connect(self._authorize_web_page)
        self.ui.webStopAuthButton.clicked.connect(self._stop_web_authorization_by_user)
        self.ui.webParseButton.clicked.connect(self._parse_web_page)
        self.ui.webUrlLine.returnPressed.connect(self._open_web_page)
        self.ui.webPasswordLine.returnPressed.connect(self._authorize_web_page)
        self.ui.webRequestNumberLine.returnPressed.connect(self._authorize_web_page)
        self.ui.webLoginLine.editingFinished.connect(self._store_web_auth_credentials_from_ui)
        self.ui.webPasswordLine.editingFinished.connect(self._store_web_auth_credentials_from_ui)
        self.ui.webRequestNumberLine.editingFinished.connect(self._store_web_request_number_from_ui)
        self.ui.webView.loadFinished.connect(self._on_web_page_loaded)
        self._webAuthRetryTimer = QTimer(self)
        self._webAuthRetryTimer.setSingleShot(True)
        self._webAuthRetryTimer.timeout.connect(self._retry_web_authorization)
        self._webRequestSearchTimer = QTimer(self)
        self._webRequestSearchTimer.setSingleShot(True)
        self._webRequestSearchTimer.timeout.connect(self._retry_web_request_search)
        self._update_web_auth_controls()

        self._open_web_page()

    def _set_web_status(self, text):
        if hasattr(self.ui, "webStatusLabel"):
            raw_text = str(text or "").strip()
            # Keep long URLs readable and prevent status text from stretching the window.
            def _shorten_url(match):
                url = match.group(0)
                if len(url) <= 120:
                    return url
                return f"{url[:72]}...{url[-32:]}"

            display_text = re.sub(r"https?://\S+", _shorten_url, raw_text)
            if len(display_text) > 220:
                display_text = f"{display_text[:180]}...{display_text[-30:]}"

            self.ui.webStatusLabel.setText(display_text)
            self.ui.webStatusLabel.setToolTip(raw_text)

    def _get_saved_web_auth_credentials(self):
        if not Config.settings.get("saveWebAuthData", False):
            return "", ""
        login = str(Config.config.get("webAuthLogin", "") or "").strip()
        password = str(Config.config.get("webAuthPassword", "") or "")
        return login, password

    def _get_web_auth_attempt_limit(self):
        default_limit = 25
        min_limit = 5
        max_limit = 120
        try:
            parsed = int(str(Config.config.get("webAuthMaxAttempts", default_limit)).strip())
        except (TypeError, ValueError):
            parsed = default_limit
        normalized = max(min_limit, min(max_limit, parsed))
        Config.config["webAuthMaxAttempts"] = str(normalized)
        return normalized

    def _persist_web_auth_credentials(self, login, password):
        if not Config.settings.get("saveWebAuthData", False):
            return
        normalized_login = str(login or "").strip()
        normalized_password = str(password or "")
        if (
            Config.config.get("webAuthLogin", "") == normalized_login
            and Config.config.get("webAuthPassword", "") == normalized_password
        ):
            return
        Config.config["webAuthLogin"] = normalized_login
        Config.config["webAuthPassword"] = normalized_password
        self.saveConfig()

    def _store_web_auth_credentials_from_ui(self):
        if not Config.settings.get("saveWebAuthData", False):
            return
        if not hasattr(self.ui, "webLoginLine") or not hasattr(self.ui, "webPasswordLine"):
            return
        self._persist_web_auth_credentials(
            self.ui.webLoginLine.text(),
            self.ui.webPasswordLine.text(),
        )

    def _persist_web_request_number(self, request_number):
        normalized_number = str(request_number or "").strip()
        if Config.config.get("webRequestNumber", "") == normalized_number:
            return
        Config.config["webRequestNumber"] = normalized_number
        self.saveConfig()

    def _store_web_request_number_from_ui(self):
        if not hasattr(self.ui, "webRequestNumberLine"):
            return
        self._persist_web_request_number(self.ui.webRequestNumberLine.text())

    def _open_web_page(self):
        if not hasattr(self.ui, "webView"):
            return

        self._stop_web_authorization()
        self._cancel_web_request_search(clear_pending=True)
        url_text = str(self.ui.webUrlLine.text() or "").strip()
        if not url_text:
            self.error("Ошибка", "Введите URL страницы")
            return

        if "://" not in url_text:
            url_text = f"https://{url_text}"
            self.ui.webUrlLine.setText(url_text)

        url = QUrl(url_text)
        if not url.isValid() or url.scheme() not in {"http", "https"}:
            self.error("Ошибка", "Введите корректный URL (http/https)")
            return

        self._set_web_status(f"Открытие страницы: {url.toString()}")
        self.ui.webView.setUrl(url)

    def _on_web_page_loaded(self, ok):
        current_url = self.ui.webView.url().toString()
        if ok:
            self._set_web_status(f"Страница загружена: {current_url}")
        else:
            self._set_web_status(f"Не удалось загрузить страницу: {current_url}")

        if not self._web_auth_active:
            if self._web_request_search_pending and self._web_request_search_attempts_left > 0:
                self._schedule_web_request_search(delay_ms=500 if ok else 1100)
            return
        page_changed = self._is_web_auth_page_changed(current_url)
        had_auth_attempt = self._web_auth_attempts_left < self._web_auth_total_attempts
        if (
            ok
            and page_changed
            and (
                self._web_auth_submitted
                or self._web_auth_seen_login_form
                or self._web_auth_seen_login_dialog
                or had_auth_attempt
            )
        ):
            self._set_web_status(f"Авторизация выполнена: {current_url}")
            self._navigate_to_bid_submission_tab()
            self._stop_web_authorization()
            return
        self._schedule_web_auth_retry(delay_ms=400 if ok else 1000)

    def _stop_web_authorization(self):
        self._web_auth_active = False
        self._web_auth_js_running = False
        self._web_auth_submitted = False
        self._web_auth_attempts_left = 0
        self._web_auth_total_attempts = 0
        self._web_auth_origin_url = ""
        self._web_auth_switched_to_frame = False
        self._web_auth_frame_urls_tried = set()
        self._web_auth_seen_login_form = False
        self._web_auth_seen_login_dialog = False
        if hasattr(self, "_webAuthRetryTimer"):
            self._webAuthRetryTimer.stop()
        self._update_web_auth_controls()

    def _stop_web_authorization_by_user(self):
        if not self._web_auth_active:
            return
        self._stop_web_authorization()
        self._set_web_status("Авторизация остановлена")

    def _update_web_auth_controls(self):
        if not hasattr(self.ui, "webAuthButton"):
            return
        is_active = bool(self._web_auth_active)
        self.ui.webAuthButton.setEnabled(not is_active)
        if hasattr(self.ui, "webStopAuthButton"):
            self.ui.webStopAuthButton.setVisible(is_active)
            self.ui.webStopAuthButton.setEnabled(is_active)

    def _schedule_web_auth_retry(self, delay_ms=700):
        if not self._web_auth_active or self._web_auth_js_running:
            return
        if self._web_auth_attempts_left <= 0:
            if self._is_web_auth_page_changed():
                current_url = self.ui.webView.url().toString()
                self._set_web_status(
                    f"Авторизация выполнена: {current_url}" if current_url else "Авторизация выполнена"
                )
                self._navigate_to_bid_submission_tab()
            elif self._web_auth_submitted:
                self._set_web_status("Форма входа отправлена. Проверьте, что вход выполнен.")
            elif self._web_auth_seen_login_form or self._web_auth_seen_login_dialog:
                self._set_web_status("Авторизация завершена. Проверьте доступ к данным.")
            else:
                self._set_web_status("Авторизация не выполнена: форма входа не найдена.")
                self.error("Ошибка", "Не удалось найти форму входа на странице.")
            self._stop_web_authorization()
            return
        if hasattr(self, "_webAuthRetryTimer"):
            self._webAuthRetryTimer.start(max(100, int(delay_ms)))

    def _retry_web_authorization(self):
        if not self._web_auth_active:
            return
        self._run_web_auth_attempt()

    def _is_web_auth_page_changed(self, current_url=None):
        start_url = str(self._web_auth_start_url or "").strip()
        if not start_url:
            return False
        if current_url is None:
            if not hasattr(self.ui, "webView"):
                return False
            current_url = self.ui.webView.url().toString()
        current_text = str(current_url or "").strip()
        if not current_text or current_text == start_url:
            return False
        if current_text in self._web_auth_frame_urls_tried:
            return False
        return True

    def _pick_web_auth_frame_url(self, frame_sources):
        if not isinstance(frame_sources, list):
            return ""

        current_url = self.ui.webView.url()
        current_text = current_url.toString().strip()
        scored = []
        for raw_source in frame_sources:
            source = str(raw_source or "").strip()
            if not source:
                continue
            resolved = current_url.resolved(QUrl(source))
            if not resolved.isValid() or resolved.scheme() not in {"http", "https"}:
                continue
            candidate = resolved.toString().strip()
            if not candidate or candidate in self._web_auth_frame_urls_tried:
                continue
            if candidate == current_text:
                continue
            score = 0
            low = candidate.casefold()
            if any(token in low for token in ("login", "signin", "sign-in", "auth", "sso", "passport")):
                score += 10
            if any(token in low for token in ("frame", "index", "default")):
                score += 1
            scored.append((score, candidate))

        if not scored:
            return ""
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1]

    def _open_web_auth_frame_candidate(self, frame_sources):
        candidate = self._pick_web_auth_frame_url(frame_sources)
        if not candidate:
            return False

        self._web_auth_frame_urls_tried.add(candidate)
        self._web_auth_switched_to_frame = True
        self._set_web_status(f"Форма входа в фрейме. Переход: {candidate}")
        self.ui.webView.setUrl(QUrl(candidate))
        return True

    def _navigate_to_bid_submission_tab(self):
        if not hasattr(self.ui, "webView"):
            return
        self._set_web_status("Авторизация выполнена. Переход во вкладку «Приём заявок»...")
        script = WebAutomationScripts.build_bid_submission_navigation_script()
        self.ui.webView.page().runJavaScript(script, self._on_bid_submission_navigation_completed)

    def _on_bid_submission_navigation_completed(self, result):
        delay_ms = 900
        if not isinstance(result, dict):
            self._start_web_request_search_if_needed(delay_ms=delay_ms)
            return

        if result.get("already_on_target"):
            self._set_web_status("Уже открыта вкладка «Приём заявок».")
            delay_ms = 400
        elif result.get("clicked"):
            self._set_web_status("Переход во вкладку «Приём заявок» выполнен.")
            delay_ms = 900
        elif result.get("redirected"):
            target_url = str(result.get("target_url", "")).strip()
            if target_url:
                self._set_web_status(f"Открывается вкладка «Приём заявок»: {target_url}")
            else:
                self._set_web_status("Открывается вкладка «Приём заявок».")
            delay_ms = 1400

        self._start_web_request_search_if_needed(delay_ms=delay_ms)

    def _cancel_web_request_search(self, clear_pending=False):
        self._web_request_search_js_running = False
        self._web_request_search_attempts_left = 0
        self._web_request_search_total_attempts = 0
        if hasattr(self, "_webRequestSearchTimer"):
            self._webRequestSearchTimer.stop()
        if clear_pending:
            self._web_request_search_pending = False

    def _start_web_request_search_if_needed(self, delay_ms=700):
        if not hasattr(self.ui, "webView"):
            return
        if not self._web_request_search_pending:
            return
        request_number = str(self._web_request_number or "").strip()
        if not request_number:
            self._web_request_search_pending = False
            return
        if self._web_request_search_total_attempts <= 0:
            self._web_request_search_total_attempts = 14
            self._web_request_search_attempts_left = self._web_request_search_total_attempts
        self._schedule_web_request_search(delay_ms)

    def _schedule_web_request_search(self, delay_ms=700):
        if (
            not self._web_request_search_pending
            or self._web_request_search_js_running
            or self._web_request_search_attempts_left <= 0
        ):
            return
        if hasattr(self, "_webRequestSearchTimer"):
            self._webRequestSearchTimer.start(max(120, int(delay_ms)))

    def _retry_web_request_search(self):
        if not self._web_request_search_pending:
            return
        self._run_web_request_search_attempt()

    def _run_web_request_search_attempt(self):
        if (
            not hasattr(self.ui, "webView")
            or not self._web_request_search_pending
            or self._web_request_search_js_running
        ):
            return

        if self._web_request_search_attempts_left <= 0:
            number = str(self._web_request_number or "").strip()
            if number:
                self._set_web_status(
                    f"Не удалось автоматически найти заявку №{number}. Проверьте номер и попробуйте снова."
                )
            self._cancel_web_request_search(clear_pending=True)
            return

        attempt_number = self._web_request_search_total_attempts - self._web_request_search_attempts_left + 1
        self._web_request_search_attempts_left -= 1
        self._web_request_search_js_running = True

        number = str(self._web_request_number or "").strip()
        self._set_web_status(
            f"Поиск заявки №{number}: попытка {attempt_number}/{self._web_request_search_total_attempts}..."
        )
        script = WebAutomationScripts.build_bid_request_search_script(number)
        self.ui.webView.page().runJavaScript(script, self._on_web_request_search_completed)

    def _on_web_request_search_completed(self, result):
        self._web_request_search_js_running = False
        if not self._web_request_search_pending:
            return

        number = str(self._web_request_number or "").strip()
        if not isinstance(result, dict):
            if self._web_request_search_attempts_left > 0:
                self._schedule_web_request_search(delay_ms=1100)
                return
            self._set_web_status(
                f"Не удалось автоматически найти заявку №{number}. Проверьте номер и попробуйте снова."
            )
            self._cancel_web_request_search(clear_pending=True)
            return

        message = str(result.get("message", "")).strip()
        match_found = bool(result.get("match_found"))
        match_opened = bool(result.get("match_opened"))
        retry = bool(result.get("retry"))

        if match_opened:
            self._set_web_status(message or f"Заявка №{number} найдена и открыта")
            self._cancel_web_request_search(clear_pending=True)
            return

        if match_found:
            if self._web_request_search_attempts_left > 0:
                self._set_web_status(message or f"Заявка №{number} найдена, пытаемся открыть...")
                self._schedule_web_request_search(delay_ms=800)
                return
            self._set_web_status(
                message or f"Заявка №{number} найдена, но открыть её автоматически не удалось."
            )
            self._cancel_web_request_search(clear_pending=True)
            return

        if retry and self._web_request_search_attempts_left > 0:
            self._set_web_status(message or f"Поиск заявки №{number}: ожидаем обновление списка...")
            self._schedule_web_request_search(delay_ms=950)
            return

        if self._web_request_search_attempts_left > 0:
            self._set_web_status(message or f"Поиск заявки №{number}: повторная попытка...")
            self._schedule_web_request_search(delay_ms=950)
            return

        self._set_web_status(
            message or f"Не удалось автоматически найти заявку №{number}. Проверьте номер и попробуйте снова."
        )
        self._cancel_web_request_search(clear_pending=True)

    def _run_web_auth_attempt(self):
        if not self._web_auth_active or self._web_auth_js_running:
            return
        if self._web_auth_attempts_left <= 0:
            self._schedule_web_auth_retry(0)
            return

        attempt_number = self._web_auth_total_attempts - self._web_auth_attempts_left + 1
        self._web_auth_attempts_left -= 1
        self._web_auth_js_running = True
        self._set_web_status(
            f"Попытка авторизации {attempt_number}/{self._web_auth_total_attempts}..."
        )
        script = WebAutomationScripts.build_web_auth_script(
            self._web_auth_login,
            self._web_auth_password,
        )
        self.ui.webView.page().runJavaScript(script, self._on_web_auth_completed)

    def _authorize_web_page(self):
        if not hasattr(self.ui, "webView"):
            return

        login = str(self.ui.webLoginLine.text() or "").strip()
        password = str(self.ui.webPasswordLine.text() or "")
        if not login or not password:
            self.error("Ошибка", "Введите логин и пароль")
            return
        self._persist_web_auth_credentials(login, password)
        request_number = ""
        if hasattr(self.ui, "webRequestNumberLine"):
            request_number = str(self.ui.webRequestNumberLine.text() or "").strip()
            self._persist_web_request_number(request_number)

        self._stop_web_authorization()
        self._cancel_web_request_search(clear_pending=True)
        self._web_request_number = request_number
        self._web_request_search_pending = bool(request_number)
        self._web_auth_login = login
        self._web_auth_password = password
        self._web_auth_start_url = self.ui.webView.url().toString()
        self._web_auth_origin_url = self._web_auth_start_url
        self._web_auth_switched_to_frame = False
        self._web_auth_frame_urls_tried = set()
        self._web_auth_seen_login_form = False
        self._web_auth_seen_login_dialog = False
        self._web_auth_total_attempts = self._get_web_auth_attempt_limit()
        self._web_auth_attempts_left = self._web_auth_total_attempts
        self._web_auth_active = True
        self._web_auth_submitted = False
        self._update_web_auth_controls()
        self._run_web_auth_attempt()

    def _on_web_auth_completed(self, result):
        self._web_auth_js_running = False
        if not self._web_auth_active:
            return

        if not isinstance(result, dict):
            self._schedule_web_auth_retry(delay_ms=900)
            return

        message = str(result.get("message", "")).strip()
        found_fields = bool(result.get("found_fields"))
        submitted = bool(result.get("submitted"))
        already_authorized = bool(result.get("already_authorized"))
        dialog_opened = bool(result.get("dialog_opened"))
        captcha_required = bool(result.get("captcha_required"))
        submit_disabled = bool(result.get("submit_disabled"))
        login_ui_present = bool(result.get("login_ui_present"))
        frame_sources = result.get("frame_sources")
        if not isinstance(frame_sources, list):
            frame_sources = []
        page_changed = self._is_web_auth_page_changed()

        if found_fields:
            self._web_auth_seen_login_form = True
        if dialog_opened:
            self._web_auth_seen_login_dialog = True

        if already_authorized:
            self._set_web_status(message or "Вход уже выполнен")
            self._navigate_to_bid_submission_tab()
            self._stop_web_authorization()
            return

        if (
            page_changed
            and not captcha_required
            and not submit_disabled
            and (
                submitted
                or self._web_auth_submitted
                or self._web_auth_seen_login_form
                or self._web_auth_seen_login_dialog
            )
            and (not found_fields or not login_ui_present)
        ):
            current_url = self.ui.webView.url().toString()
            self._set_web_status(
                f"Авторизация выполнена: {current_url}" if current_url else "Авторизация выполнена"
            )
            self._navigate_to_bid_submission_tab()
            self._stop_web_authorization()
            return

        if submitted:
            self._web_auth_submitted = True
            self._set_web_status(message or "Форма входа отправлена")
            self._schedule_web_auth_retry(delay_ms=1500)
            return

        if dialog_opened:
            self._set_web_status(message or "Открыто окно входа")
            self._schedule_web_auth_retry(delay_ms=500)
            return

        if (
            not found_fields
            and not dialog_opened
            and not captcha_required
            and not login_ui_present
            and (
                self._web_auth_submitted
                or self._web_auth_seen_login_form
                or self._web_auth_seen_login_dialog
                or page_changed
            )
        ):
            if page_changed:
                current_url = self.ui.webView.url().toString()
                self._set_web_status(
                    f"Авторизация выполнена: {current_url}" if current_url else "Авторизация выполнена"
                )
            else:
                self._set_web_status("Авторизация выполнена")
            self._navigate_to_bid_submission_tab()
            self._stop_web_authorization()
            return

        if captcha_required:
            if self._web_auth_attempts_left > 0:
                self._set_web_status(message or "Ожидание SmartCaptcha...")
                self._schedule_web_auth_retry(delay_ms=1200)
                return
            self._set_web_status("Для входа требуется пройти SmartCaptcha вручную")
            self.error(
                "SmartCaptcha",
                "Автоматический вход остановлен: требуется пройти SmartCaptcha.\n"
                "Пройдите капчу на странице и нажмите «Авторизоваться» снова.",
            )
            self._stop_web_authorization()
            return

        if submit_disabled and found_fields:
            if self._web_auth_attempts_left > 0:
                self._set_web_status(message or "Кнопка входа неактивна, ожидание...")
                self._schedule_web_auth_retry(delay_ms=900)
                return
            self._set_web_status(message or "Кнопка входа неактивна")
            self.error(
                "Ошибка",
                "Кнопка входа остается неактивной. Проверьте капчу и заполнение полей.",
            )
            self._stop_web_authorization()
            return

        if found_fields:
            self._set_web_status(message or "Данные введены, повторная попытка отправки...")
            self._schedule_web_auth_retry(delay_ms=700)
            return

        if self._open_web_auth_frame_candidate(frame_sources):
            return

        if self._web_auth_submitted:
            self._set_web_status(message or "Ожидание результата авторизации...")
            self._schedule_web_auth_retry(delay_ms=1200)
            return

        if self._web_auth_attempts_left > 0:
            self._set_web_status(message or "Форма входа пока не найдена, повтор...")
            self._schedule_web_auth_retry(delay_ms=800)
            return

        self._set_web_status(message or "Авторизация не выполнена")
        self.error("Ошибка", message or "Не удалось автоматически авторизоваться")
        self._stop_web_authorization()

    def _parse_web_page(self):
        if not hasattr(self.ui, "webView"):
            return

        self._set_web_status("Получение HTML и парсинг страницы...")
        self.ui.webParseButton.setEnabled(False)
        self.ui.webView.page().toHtml(self._on_web_html_ready)

    def _on_web_html_ready(self, html_text):
        self.ui.webParseButton.setEnabled(True)
        html_text = str(html_text or "")
        if not html_text.strip():
            self.ui.webParserOutput.setPlainText("HTML пустой, парсинг не выполнен.")
            self._set_web_status("HTML пустой, парсинг не выполнен")
            return

        try:
            payload = self.web_page_parser.extract_payload(
                html_text,
                current_url=self.ui.webView.url().toString(),
            )
        except Exception as e:
            Tool.log_exception("Ошибка парсинга веб-страницы", e, include_traceback=False)
            self.ui.webParserOutput.setPlainText(f"Ошибка парсинга: {e}")
            self._set_web_status(f"Ошибка парсинга: {e}")
            return

        self.ui.webParserOutput.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))
        self._set_web_status(
            "Парсинг завершен: "
            f"форм {payload['forms_count']}, таблиц {payload['tables_count']}, ссылок {payload['links_count']}"
        )
