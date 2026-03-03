from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QStyledItemDelegate,
    QMenu,
    QInputDialog,
    QHeaderView,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QSplitter,
    QTextEdit,
)
from PySide6.QtGui import QIcon, QDesktopServices, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QUrl, QSignalBlocker, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from createDocument import mainWindow as createDocWindow
from create import createExcelFile as exportExcelFile
from customers import mainWindow as customersWindow
from settings import mainWindow as settingsWindow
from tools import DatabaseTools as Tool
from params import mainWindow as paramsWindow
from database import Database
from config import Config
from ui_mainGui import Ui_MainWindow
from ui_theme import apply_unified_theme
from datetime import datetime
from pathlib import Path
from lxml import html as lxml_html
from lxml.etree import ParserError
import pandas as pd
import shutil
import re
import json


class FormulaDelegate(QStyledItemDelegate):
    def __init__(self, parent, formula_provider, before_edit_callback=None):
        super().__init__(parent)
        self._formula_provider = formula_provider
        self._before_edit_callback = before_edit_callback

    def setEditorData(self, editor, index):
        if self._before_edit_callback is not None:
            self._before_edit_callback(index.row(), index.column())
        formula = self._formula_provider(index.row(), index.column())
        if formula is not None and hasattr(editor, "setText"):
            editor.setText(formula)
            return
        super().setEditorData(editor, index)


class mainWindow(QMainWindow):
    BASE_EDITABLE_COLUMNS = {0, 1, 2, 3, 4, 5, 14}
    FORMULA_EDITABLE_COLUMNS = {8, 9, 10, 11, 13}
    EDITABLE_COLUMNS = BASE_EDITABLE_COLUMNS | FORMULA_EDITABLE_COLUMNS
    MAX_UNDO_STATES = 30
    SUMMARY_SOURCE_COLUMNS = (0, 1, 2, 3, 4, 10, 11, 12, 13)
    SUMMARY_HEADERS = (
        "№",
        "Наименование",
        "Каталожный товар",
        "Ед. изм.",
        "Кол-во",
        "Цена за ед. без НДС",
        "Итого без НДС",
        "Итого с НДС",
        "Срок поставки",
    )
    HISTORY_HEADERS = (
        "Дата/время",
        "Событие",
        "№ КП",
        "Компания",
        "Контакт",
        "Позиций",
        "Сумма",
        "Файл",
    )
    HISTORY_META_COLUMN = 0
    HISTORY_FILE_COLUMN = 7

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(self.resourcePath("assets/app.ico")))
        self.applyEnterpriseStyle()
        self._load_updates_tab_text()

        self.tableData = {
            "amount": [],
            "currency": [],
            "unitPrice": [],
            "totalPrice": [],
            "termDelivery": [],
            "logistic": [],
        }
        self.formulaExpressions = {col: [] for col in self.FORMULA_EDITABLE_COLUMNS}
        self.rows = 0
        self.formulaCustom = 1.0
        self.formulaMarkup = 1.0
        self.formulaLogistic = 1.0
        self.termDeliveryDays = 0
        self.mixedCurrencyWarningShown = False
        self.columnFilters = {}
        self._baseHeaderLabels = {}
        self.quickSearchText = ""
        self._shortcuts = []
        self._undo_stack = []
        self._is_restoring_undo = False
        self._pending_edit_undo_state = None
        self._web_auth_active = False
        self._web_auth_login = ""
        self._web_auth_password = ""
        self._web_auth_attempts_left = 0
        self._web_auth_total_attempts = 0
        self._web_auth_js_running = False
        self._web_auth_submitted = False
        self._web_auth_start_url = ""
        self._web_auth_origin_url = ""
        self._web_auth_switched_to_frame = False
        self._web_auth_frame_urls_tried = set()
        self._web_auth_seen_login_form = False
        self._web_auth_seen_login_dialog = False

        self.loadConfig()
        self.ensureOutputDirs()

        self.db = Database()
        if self.db.open(Config.db_path) == -1:
            self.error("Ошибка", "Не удалось открыть базу данных")

        if Config.settings["autoFill"]:
            self.ui.logisticNum.setText(Config.config["logisticNum"])
            self.ui.customLine.setText(Config.config["customNum"])
            self.ui.termDeliveryLine.setText(Config.config["termDelivery"])
            self.ui.markupLine.setText(Config.config["markup"])
            self.ui.logisticVar.setCurrentIndex(int(Config.config["logisticVar"]))

        self.ui.openTableButton.clicked.connect(self.openTable)
        self.ui.openTableMenuButton.triggered.connect(self.openTable)
        self.ui.closeTableMenuButton.triggered.connect(self.closeTable)
        self.ui.createDocMenuButton.triggered.connect(self.exportDocs)
        self.ui.createExcelMenuButton.triggered.connect(self.exportExcel)

        self.ui.editParamsButton.triggered.connect(self.openParamsWindow)

        self.ui.suppliersMenuButton.triggered.connect(self.openSuppliersWindow)
        self.ui.settingsMenuButton.triggered.connect(self.openSettingsWindow)
        self.ui.exportMenuButton.triggered.connect(self.exportDatabase)
        self.ui.importMenuButton.triggered.connect(self.importDatabase)
        self.ui.clearCacheMenuButton.triggered.connect(self.clear_cache)
        self.ui.changeFormButton.triggered.connect(self.testFeature)
        self.ui.changeFormButton.setChecked(Config.settings["testFeature"])

        self.ui.helpMenuButton.triggered.connect(self.show_help)
        self.ui.aboutMenuButton.triggered.connect(self.show_about)
        self.ui.GitHubMenuButton.triggered.connect(
            lambda: self.open_url("https://github.com/p4st1/AppForCommercialRequests")
        )
        self.ui.supportMenuButton.triggered.connect(self.show_help)

        self.ui.createDocButton.clicked.connect(self.exportDocs)
        self.ui.createExcelButton.clicked.connect(self.exportExcel)
        self.ui.createDocFromExcelButton.clicked.connect(self.exportDocFromExcel)

        self.ui.logisticVar.currentIndexChanged.connect(self.logisticVarChanged)
        self.ui.logisticNum.editingFinished.connect(self.processFormula)
        self.ui.markupLine.editingFinished.connect(self.processFormula)
        self.ui.customLine.editingFinished.connect(self.processFormula)
        self.ui.termDeliveryLine.editingFinished.connect(self.processFormula)
        self.ui.closeTableButton.clicked.connect(self.closeTable)
        self.ui.KpTable.itemChanged.connect(self.tableItemChanged)
        self.ui.KpTable.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self.ui.KpTable.setItemDelegate(
            FormulaDelegate(
                self.ui.KpTable,
                self._get_formula_for_editor,
                self._capture_state_before_cell_edit,
            )
        )
        self.ui.KpTable.resizeColumnsToContents()
        self._setup_table_quick_search()
        self._setup_shortcuts()
        self._init_table_filters()
        self._setup_total_tab_table()
        self._update_total_tab_table()
        self._ensure_history_tab()
        self._ensure_web_tab()
        self._setup_history_tab_table()
        self._full_table_panel_widgets = list(
            dict.fromkeys(self._collect_layout_widgets(self.ui.funcButtons))
        )
        self.ui.tabWidget.currentChanged.connect(self._on_main_tab_changed)
        self.updateHistoryTable()

        if Config.settings["openLastTab"] and Config.config["lastTable"]:
            last_table = Config.config["lastTable"]
            if Path(last_table).exists():
                self.openTable(file=last_table)
            else:
                Config.config["lastTable"] = ""
                self.saveConfig()

        if Config.settings["openUpdateTab"]:
            self.ui.tabWidget.setCurrentIndex(2)
        else:
            self.ui.tabWidget.setCurrentIndex(1)
        self._on_main_tab_changed(self.ui.tabWidget.currentIndex())

    def applyEnterpriseStyle(self):
        apply_unified_theme(self)

    def _collect_layout_widgets(self, layout):
        widgets = []
        if layout is None:
            return widgets
        for index in range(layout.count()):
            item = layout.itemAt(index)
            widget = item.widget()
            if widget is not None:
                widgets.append(widget)
                continue
            child_layout = item.layout()
            if child_layout is not None:
                widgets.extend(self._collect_layout_widgets(child_layout))
        return widgets

    def _on_main_tab_changed(self, _index):
        show_panel = self.ui.tabWidget.currentWidget() is self.ui.tab
        for widget in self._full_table_panel_widgets:
            widget.setVisible(show_panel)

    def _load_updates_tab_text(self):
        updates_path = Path(self.resourcePath("assets/updates.txt"))
        if not updates_path.exists():
            return
        try:
            updates_text = updates_path.read_text(encoding="utf-8")
        except Exception as e:
            Tool.log_exception(
                f"Не удалось загрузить текст обновлений: {updates_path}",
                e,
                include_traceback=False,
            )
            return
        self.ui.textUpdates.setPlainText(updates_text)

    def loadConfig(self):
        try:
            data = Tool.load_json(Config.cfg_path)
        except Exception as e:
            Tool.log_exception(
                f"Не удалось загрузить конфигурацию: {Config.cfg_path}",
                e,
                include_traceback=False,
            )
            data = {}
        normalized = Tool.merge_config_with_defaults(data)
        Config.config = normalized["config"]
        Config.settings = normalized["settings"]
        self.saveConfig()

    def saveConfig(self):
        Tool.save_json_atomic(
            Config.cfg_path,
            {"config": Config.config, "settings": Config.settings},
        )

    def ensureOutputDirs(self):
        default_dir = Path.home() / "Documents"
        cp_dir = Tool.ensure_directory(Config.config.get("pathToSaveCP"), default_dir)
        excel_dir = Tool.ensure_directory(Config.config.get("pathToSaveExcel") or cp_dir, cp_dir)
        Config.config["pathToSaveCP"] = str(cp_dir)
        Config.config["pathToSaveExcel"] = str(excel_dir)

    def _set_table_item(self, row, col, text, editable):
        item = self.ui.KpTable.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            self.ui.KpTable.setItem(row, col, item)

        item.setText(str(text))
        flags = item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if editable:
            flags |= Qt.ItemFlag.ItemIsEditable
        else:
            flags &= ~Qt.ItemFlag.ItemIsEditable
        item.setFlags(flags)

    def _setup_total_tab_table(self):
        table = self.ui.tableWidget_3
        table.setColumnCount(len(self.SUMMARY_HEADERS))
        table.setHorizontalHeaderLabels(self.SUMMARY_HEADERS)
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
        for col in range(2, len(self.SUMMARY_HEADERS)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

    def _update_total_tab_table(self):
        table = self.ui.tableWidget_3
        rows = self.getTableData() if self.ui.KpTable.rowCount() > 0 else []

        blocker = QSignalBlocker(table)
        table.clearContents()
        table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        del blocker
        table.resizeRowsToContents()

    def _ensure_history_tab(self):
        if hasattr(self.ui, "historyTable"):
            return

        self.ui.historyTab = QWidget(self.ui.tabWidget)
        self.ui.historyTab.setObjectName("historyTab")

        root_layout = QVBoxLayout(self.ui.historyTab)
        root_layout.setSpacing(8)
        root_layout.setContentsMargins(8, 8, 8, 8)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel("История создания КП и экспортов", self.ui.historyTab)
        self.ui.historyRefreshButton = QPushButton("Обновить", self.ui.historyTab)
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.ui.historyRefreshButton)

        self.ui.historyTable = QTableWidget(self.ui.historyTab)
        self.ui.historyTable.setObjectName("historyTable")

        root_layout.addLayout(header_layout)
        root_layout.addWidget(self.ui.historyTable)
        self.ui.tabWidget.addTab(self.ui.historyTab, "История")
        self.ui.historyRefreshButton.clicked.connect(self.updateHistoryTable)
        self.ui.historyTable.itemDoubleClicked.connect(self._openHistoryFile)
        self.ui.historyTable.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.historyTable.customContextMenuRequested.connect(self._show_history_context_menu)

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

        self.ui.webOpenButton = QPushButton("Открыть", self.ui.webTab)
        self.ui.webAuthButton = QPushButton("Авторизоваться", self.ui.webTab)
        self.ui.webParseButton = QPushButton("Распарсить", self.ui.webTab)

        controls_layout.addWidget(self.ui.webUrlLine, 1)
        controls_layout.addWidget(self.ui.webLoginLine)
        controls_layout.addWidget(self.ui.webPasswordLine)
        controls_layout.addWidget(self.ui.webOpenButton)
        controls_layout.addWidget(self.ui.webAuthButton)
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
        self.ui.webParseButton.clicked.connect(self._parse_web_page)
        self.ui.webUrlLine.returnPressed.connect(self._open_web_page)
        self.ui.webPasswordLine.returnPressed.connect(self._authorize_web_page)
        self.ui.webLoginLine.editingFinished.connect(self._store_web_auth_credentials_from_ui)
        self.ui.webPasswordLine.editingFinished.connect(self._store_web_auth_credentials_from_ui)
        self.ui.webView.loadFinished.connect(self._on_web_page_loaded)
        self._webAuthRetryTimer = QTimer(self)
        self._webAuthRetryTimer.setSingleShot(True)
        self._webAuthRetryTimer.timeout.connect(self._retry_web_authorization)

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

    def _open_web_page(self):
        if not hasattr(self.ui, "webView"):
            return

        self._stop_web_authorization()
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
            return
        page_changed = self._is_web_auth_page_changed(current_url)
        if (
            ok
            and page_changed
            and (
                self._web_auth_submitted
                or self._web_auth_seen_login_form
                or self._web_auth_seen_login_dialog
            )
        ):
            self._set_web_status(f"Авторизация выполнена: {current_url}")
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

    def _schedule_web_auth_retry(self, delay_ms=700):
        if not self._web_auth_active or self._web_auth_js_running:
            return
        if self._web_auth_attempts_left <= 0:
            if self._is_web_auth_page_changed():
                current_url = self.ui.webView.url().toString()
                self._set_web_status(
                    f"Авторизация выполнена: {current_url}" if current_url else "Авторизация выполнена"
                )
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

    @staticmethod
    def _build_web_auth_script(login, password):
        script = """
(() => {
  const loginValue = __LOGIN__;
  const passwordValue = __PASSWORD__;
  const submitTextPattern = /войти|вход|login|sign\\s*in|submit|ok|авториз/i;
  const loginOpenTextPattern = /войти|вход|login|sign\\s*in|авториз/i;
  const loginEntryPattern = /войти|вход|login|sign\\s*in|авториз/i;
  const accountTextPattern = /личный\\s*кабинет|мой\\s*кабинет|профил|my\\s*account|account|profile|dashboard/i;
  const accountHrefPattern = /\\/(profile|account|cabinet|lk|dashboard)(\\/|$)|[#?](profile|account|cabinet|lk|dashboard)/i;
  const nextButtonPattern = /далее|continue|next/i;
  const frameSources = [];
  try {
    const frameNodes = Array.from(document.querySelectorAll('frame[src], iframe[src]'));
    for (const frameNode of frameNodes) {
      const src = String(frameNode.getAttribute('src') || '').trim();
      if (src) frameSources.push(src);
    }
  } catch (e) {}

  const docs = [];
  const queue = [window];
  const seen = [];
  while (queue.length > 0) {
    const win = queue.shift();
    if (!win || seen.includes(win)) continue;
    seen.push(win);
    try {
      if (win.document) docs.push(win.document);
      const frames = win.frames || [];
      for (let i = 0; i < frames.length; i += 1) {
        try { queue.push(frames[i]); } catch (e) {}
      }
    } catch (e) {}
  }

  const isVisible = (element) => {
    if (!element || element.disabled) return false;
    try {
      const style = element.ownerDocument.defaultView.getComputedStyle(element);
      if (!style) return true;
      if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
    } catch (e) {}
    return true;
  };

  const pickFirst = (root, selectors) => {
    if (!root) return null;
    for (const selector of selectors) {
      let nodes = [];
      try { nodes = Array.from(root.querySelectorAll(selector)); } catch (e) { nodes = []; }
      for (const node of nodes) {
        if (isVisible(node)) return node;
      }
    }
    return null;
  };

  const findLoginOpenButton = (doc) => {
    if (!doc) return null;
    const selectors = [
      'button[mat-raised-button]',
      'button.mat-raised-button',
      'button',
      'a'
    ];
    for (const selector of selectors) {
      let nodes = [];
      try { nodes = Array.from(doc.querySelectorAll(selector)); } catch (e) { nodes = []; }
      for (const node of nodes) {
        const text = String(
          node.innerText
          || node.textContent
          || node.getAttribute('aria-label')
          || node.getAttribute('title')
          || node.value
          || ''
        ).trim();
        if (!text) continue;
        if (loginOpenTextPattern.test(text)) {
          return node;
        }
      }
    }
    return null;
  };

  const clickLoginOpenButton = (doc) => {
    const loginButton = findLoginOpenButton(doc);
    if (loginButton) {
      loginButton.click();
      return true;
    }
    return false;
  };

  const hasLogoutMarker = docs.some((doc) => {
    try {
      const links = Array.from(doc.querySelectorAll('a[href], button, [role="button"]'));
      return links.some((item) => {
        const text = String(item.innerText || item.textContent || '').trim();
        const href = String(item.getAttribute('href') || '').trim();
        return /выйти|logout|log\\s*out|sign\\s*out/i.test(text) || /logout|signout/i.test(href);
      });
    } catch (e) {
      return false;
    }
  });

  const hasAccountMarker = docs.some((doc) => {
    try {
      const nodes = Array.from(doc.querySelectorAll('a[href], button, [role="button"], [aria-label], [data-testid]'));
      return nodes.some((item) => {
        const text = String(item.innerText || item.textContent || item.getAttribute('aria-label') || '').trim();
        const href = String(item.getAttribute('href') || '').trim();
        if (text && accountTextPattern.test(text) && !loginEntryPattern.test(text)) {
          return true;
        }
        if (href && accountHrefPattern.test(href) && !loginEntryPattern.test(text)) {
          return true;
        }
        return false;
      });
    } catch (e) {
      return false;
    }
  });

  const hasLoginDialog = docs.some((doc) => {
    try {
      return Boolean(doc.querySelector('mat-dialog-container form input[formcontrolname="password"]'));
    } catch (e) {
      return false;
    }
  });
  const hasLoginEntryButton = docs.some((doc) => Boolean(findLoginOpenButton(doc)));
  const loginUiPresent = hasLoginDialog || hasLoginEntryButton;
  const sessionMarkerPresent = hasLogoutMarker || (hasAccountMarker && !loginUiPresent);

  if (sessionMarkerPresent) {
    return {
      ok: true,
      found_fields: false,
      submitted: false,
      already_authorized: true,
      session_marker_present: true,
      login_ui_present: loginUiPresent,
      frame_sources: frameSources,
      message: hasLogoutMarker ? 'Вход уже выполнен' : 'Обнаружены признаки активной сессии'
    };
  }

  if (!hasLoginDialog) {
    for (const doc of docs) {
      if (clickLoginOpenButton(doc)) {
        return {
          ok: true,
          found_fields: false,
          submitted: false,
          already_authorized: false,
          dialog_opened: true,
          captcha_required: false,
          submit_disabled: false,
          login_ui_present: true,
          frame_sources: frameSources,
          message: 'Открыто окно входа'
        };
      }
    }
  }

  const loginSelectors = [
    'input[formcontrolname="login"]',
    'input[name="username"]',
    'input[name="user"]',
    'input[name="login"]',
    'input[name="email"]',
    'input[id*="user" i]',
    'input[id*="login" i]',
    'input[id*="email" i]',
    'input[placeholder*="логин" i]',
    'input[placeholder*="email" i]',
    'input[autocomplete="username"]',
    'input[type="email"]',
    'input[type="text"]',
    'input:not([type])'
  ];
  const passwordSelectors = [
    'input[formcontrolname="password"]',
    'input[name="password"]',
    'input[name="pass"]',
    'input[id*="pass" i]',
    'input[placeholder*="парол" i]',
    'input[autocomplete="current-password"]',
    'input[type="password"]'
  ];

  let loginInput = null;
  let passwordInput = null;
  let sourceDoc = null;
  for (const doc of docs) {
    const pass = pickFirst(doc, passwordSelectors);
    if (!pass) continue;
    let login = pickFirst(doc, loginSelectors);
    if (!login && pass.form) login = pickFirst(pass.form, loginSelectors);
    if (!login) {
      const root = pass.form || doc;
      login = pickFirst(root, ['input[type="text"]', 'input[type="email"]', 'input:not([type])']);
    }
    if (login) {
      loginInput = login;
      passwordInput = pass;
      sourceDoc = doc;
      break;
    }
  }

  if (!loginInput || !passwordInput) {
    return {
      ok: false,
      found_fields: false,
      submitted: false,
      already_authorized: false,
      dialog_opened: false,
      captcha_required: false,
      submit_disabled: false,
      login_ui_present: loginUiPresent,
      frame_sources: frameSources,
      message: `Поля входа не найдены (проверено документов: ${docs.length})`
    };
  }

  const setNativeValue = (input, value) => {
    try {
      const descriptor = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(input), 'value');
      if (descriptor && typeof descriptor.set === 'function') {
        descriptor.set.call(input, value);
      } else {
        input.value = value;
      }
    } catch (e) {
      input.value = value;
    }
    input.focus();
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    input.dispatchEvent(new Event('blur', { bubbles: true }));
  };

  setNativeValue(loginInput, loginValue);
  setNativeValue(passwordInput, passwordValue);

  const findSubmitControl = (root) => {
    if (!root) return null;
    const selectors = [
      'button.mat-raised-button.mat-primary',
      'button[type="submit"]',
      'input[type="submit"]',
      'button[name*="login" i]',
      'button[id*="login" i]',
      'button[id*="submit" i]',
      'input[name*="login" i]',
      'input[id*="login" i]',
      'button',
      'input[type="button"]'
    ];
    for (const selector of selectors) {
      let nodes = [];
      try { nodes = Array.from(root.querySelectorAll(selector)); } catch (e) { nodes = []; }
      for (const node of nodes) {
        if (!isVisible(node)) continue;
        const text = String(node.innerText || node.textContent || node.value || node.getAttribute('aria-label') || '').trim();
        if (selector === 'button.mat-raised-button.mat-primary') {
          if (node.classList.contains('alt-auth-button')) continue;
          if (!submitTextPattern.test(text) && !nextButtonPattern.test(text)) continue;
        } else if (selector === 'button' || selector === 'input[type="button"]') {
          if (!submitTextPattern.test(text) && !nextButtonPattern.test(text)) continue;
        }
        return node;
      }
    }
    return null;
  };

  const tokenInput = sourceDoc
    ? sourceDoc.querySelector('input[name="smart-token"]')
    : null;
  const smartToken = String((tokenInput && tokenInput.value) || '').trim();
  const hasSmartCaptcha = sourceDoc
    ? Boolean(sourceDoc.querySelector('um-smart-captcha, iframe[src*="smartcaptcha"], iframe[title*="SmartCaptcha"]'))
    : false;
  const captchaRequired = hasSmartCaptcha && smartToken.length === 0;

  const form = passwordInput.form || loginInput.form || null;
  const submitControl = findSubmitControl(form) || findSubmitControl(sourceDoc);
  if (submitControl && submitControl.disabled) {
    return {
      ok: false,
      found_fields: true,
      submitted: false,
      already_authorized: false,
      dialog_opened: false,
      captcha_required: captchaRequired,
      submit_disabled: true,
      login_ui_present: true,
      frame_sources: frameSources,
      message: captchaRequired
        ? 'Кнопка входа неактивна: ожидается SmartCaptcha'
        : 'Кнопка входа неактивна'
    };
  }

  if (captchaRequired && !submitControl) {
    return {
      ok: false,
      found_fields: true,
      submitted: false,
      already_authorized: false,
      dialog_opened: false,
      captcha_required: true,
      submit_disabled: true,
      login_ui_present: true,
      frame_sources: frameSources,
      message: 'Ожидание SmartCaptcha для продолжения входа'
    };
  }

  if (submitControl) {
    submitControl.click();
    return {
      ok: true,
      found_fields: true,
      submitted: true,
      already_authorized: false,
      dialog_opened: false,
      captcha_required: false,
      submit_disabled: false,
      login_ui_present: true,
      frame_sources: frameSources,
      message: 'Форма входа отправлена кнопкой'
    };
  }

  if (form) {
    if (typeof form.requestSubmit === 'function') {
      form.requestSubmit();
      return {
        ok: true,
        found_fields: true,
        submitted: true,
        already_authorized: false,
        dialog_opened: false,
        captcha_required: false,
        submit_disabled: false,
        login_ui_present: true,
        frame_sources: frameSources,
        message: 'Форма входа отправлена через requestSubmit()'
      };
    }
    if (typeof form.submit === 'function') {
      form.submit();
      return {
        ok: true,
        found_fields: true,
        submitted: true,
        already_authorized: false,
        dialog_opened: false,
        captcha_required: false,
        submit_disabled: false,
        login_ui_present: true,
        frame_sources: frameSources,
        message: 'Форма входа отправлена через submit()'
      };
    }
  }

  passwordInput.focus();
  const enterEventData = { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true };
  passwordInput.dispatchEvent(new KeyboardEvent('keydown', enterEventData));
  passwordInput.dispatchEvent(new KeyboardEvent('keypress', enterEventData));
  passwordInput.dispatchEvent(new KeyboardEvent('keyup', enterEventData));
  return {
    ok: true,
    found_fields: true,
    submitted: true,
    already_authorized: false,
    dialog_opened: false,
    captcha_required: false,
    submit_disabled: false,
    login_ui_present: true,
    frame_sources: frameSources,
    message: 'Форма входа отправлена через Enter'
  };
})();
"""
        script = script.replace("__LOGIN__", json.dumps(login))
        script = script.replace("__PASSWORD__", json.dumps(password))
        return script

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
        script = self._build_web_auth_script(self._web_auth_login, self._web_auth_password)
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

        self._stop_web_authorization()
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

    @staticmethod
    def _compact_web_text(value):
        return re.sub(r"\s+", " ", str(value or "")).strip()

    def _extract_web_payload(self, html_text):
        try:
            document = lxml_html.fromstring(html_text)
        except (ParserError, ValueError) as e:
            raise ValueError("Не удалось разобрать HTML страницы") from e

        title = self._compact_web_text(document.xpath("string(//title)"))
        heading_nodes = document.xpath("//h1|//h2|//h3|//h4|//h5|//h6")
        headings = []
        for node in heading_nodes:
            text = self._compact_web_text(node.text_content())
            if text:
                headings.append(text)

        form_nodes = document.xpath("//form")
        forms = []
        for index, form in enumerate(form_nodes, start=1):
            fields = []
            for field in form.xpath(".//input|.//select|.//textarea"):
                field_name = self._compact_web_text(field.get("name") or field.get("id") or "—")
                field_type = self._compact_web_text(field.get("type") or field.tag or "field")
                fields.append({"name": field_name, "type": field_type})
            forms.append(
                {
                    "index": index,
                    "method": self._compact_web_text(form.get("method") or "GET").upper(),
                    "action": self._compact_web_text(form.get("action") or ""),
                    "fields": fields[:30],
                }
            )

        table_nodes = document.xpath("//table")
        tables = []
        for index, table in enumerate(table_nodes, start=1):
            row_nodes = table.xpath(".//tr")
            preview_rows = []
            for row_node in row_nodes[:8]:
                row_values = [
                    self._compact_web_text(cell.text_content()) for cell in row_node.xpath("./th|./td")
                ]
                if any(value for value in row_values):
                    preview_rows.append(row_values)
            tables.append(
                {
                    "index": index,
                    "rows_total": len(row_nodes),
                    "preview_rows": preview_rows[:5],
                }
            )

        link_nodes = document.xpath("//a[@href]")
        links_preview = []
        for link in link_nodes[:100]:
            href = self._compact_web_text(link.get("href"))
            if not href:
                continue
            text = self._compact_web_text(link.text_content()) or "—"
            links_preview.append({"text": text, "href": href})

        frame_nodes = document.xpath("//frame|//iframe")
        frames = []
        for frame in frame_nodes:
            src = self._compact_web_text(frame.get("src"))
            name = self._compact_web_text(frame.get("name") or frame.get("id") or "—")
            frames.append({"name": name, "src": src})

        return {
            "url": self.ui.webView.url().toString(),
            "title": title,
            "html_size": len(html_text),
            "headings": headings[:30],
            "forms_count": len(form_nodes),
            "forms": forms,
            "tables_count": len(table_nodes),
            "tables": tables,
            "links_count": len(link_nodes),
            "links_preview": links_preview,
            "frames_count": len(frame_nodes),
            "frames": frames,
        }

    def _on_web_html_ready(self, html_text):
        self.ui.webParseButton.setEnabled(True)
        html_text = str(html_text or "")
        if not html_text.strip():
            self.ui.webParserOutput.setPlainText("HTML пустой, парсинг не выполнен.")
            self._set_web_status("HTML пустой, парсинг не выполнен")
            return

        try:
            payload = self._extract_web_payload(html_text)
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

    def _setup_history_tab_table(self):
        if not hasattr(self.ui, "historyTable"):
            return

        table = self.ui.historyTable
        table.setColumnCount(len(self.HISTORY_HEADERS))
        table.setHorizontalHeaderLabels(self.HISTORY_HEADERS)
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
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

    @staticmethod
    def _history_event_name(event_type: str) -> str:
        mapping = {
            "docx": "КП (DOCX)",
            "excel": "Таблица (Excel)",
        }
        key = str(event_type or "").strip().lower()
        return mapping.get(key, key or "Событие")

    def _format_history_total(self, total_amount, currency: str) -> str:
        if total_amount in (None, ""):
            return "—"
        try:
            value = float(total_amount)
        except (TypeError, ValueError):
            return "—"
        return Tool.formatPrice(self._fmt_number(value), str(currency or ""))

    def _history_row_meta(self, row: int) -> dict:
        if row < 0:
            return {}
        item = self.ui.historyTable.item(row, self.HISTORY_META_COLUMN)
        if item is None:
            return {}
        meta = item.data(Qt.ItemDataRole.UserRole)
        return meta if isinstance(meta, dict) else {}

    def _open_history_file_path(self, file_path: str):
        value = str(file_path or "").strip()
        if not value:
            return
        path = Path(value)
        if not path.exists():
            self.error("Ошибка", f"Файл не найден:\n{value}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_history_file_dir(self, file_path: str):
        value = str(file_path or "").strip()
        if not value:
            return
        path = Path(value)
        directory = path.parent
        if not directory.exists():
            self.error("Ошибка", f"Папка не найдена:\n{directory}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))

    def _copy_history_file_path(self, file_path: str):
        value = str(file_path or "").strip()
        if not value:
            return
        QApplication.clipboard().setText(value)
        if self.statusBar() is not None:
            self.statusBar().showMessage("Путь к файлу скопирован", 2500)

    def _repeat_history_doc(self, row: int):
        meta = self._history_row_meta(row)
        if str(meta.get("event_type", "")).strip().lower() != "docx":
            self.error("Ошибка", "Повторить можно только создание КП (DOCX)")
            return

        payload_text = str(meta.get("payload_json", "") or "").strip()
        if not payload_text:
            self.error("Ошибка", "Для этой записи не сохранена исходная таблица")
            return

        try:
            payload = json.loads(payload_text)
        except Exception as e:
            Tool.log_exception(
                "Не удалось прочитать payload истории",
                e,
                include_traceback=False,
            )
            self.error("Ошибка", "Не удалось прочитать данные таблицы из истории")
            return

        rows = payload.get("table_data", [])
        if not isinstance(rows, list) or not rows:
            self.error("Ошибка", "В истории нет валидной таблицы для повторного создания")
            return

        normalized_rows = []
        for row_data in rows:
            if not isinstance(row_data, list):
                continue
            normalized_rows.append([str(value) for value in row_data[: len(self.SUMMARY_HEADERS)]])

        if not normalized_rows:
            self.error("Ошибка", "В истории нет валидной таблицы для повторного создания")
            return

        self.openCreateDocWindow((len(normalized_rows), normalized_rows))

    def _delete_history_event(self, row: int):
        meta = self._history_row_meta(row)
        event_id = meta.get("id")
        if not event_id:
            return

        confirm = QMessageBox.question(
            self,
            "Удаление записи",
            "Удалить выбранную запись из истории?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.deleteHistoryEvent(int(event_id))
            self.db.save()
            self.updateHistoryTable()
        except Exception as e:
            self.error("Ошибка", f"Не удалось удалить запись:\n{e}")

    def _show_history_context_menu(self, pos):
        table = self.ui.historyTable
        clicked_item = table.itemAt(pos)
        row = clicked_item.row() if clicked_item is not None else -1
        meta = self._history_row_meta(row) if row >= 0 else {}
        file_path = str(meta.get("file_path", "") or "").strip()
        event_type = str(meta.get("event_type", "") or "").strip().lower()

        if row >= 0:
            table.selectRow(row)

        menu = QMenu(self)
        refresh_action = menu.addAction("Обновить")

        repeat_action = None
        open_file_action = None
        open_folder_action = None
        copy_path_action = None
        delete_action = None

        if row >= 0:
            menu.addSeparator()
            if event_type == "docx":
                repeat_action = menu.addAction("Повторить создание КП")
            if file_path:
                open_file_action = menu.addAction("Открыть файл")
                open_folder_action = menu.addAction("Открыть папку файла")
                copy_path_action = menu.addAction("Скопировать путь")
            delete_action = menu.addAction("Удалить запись")

        action = menu.exec(table.viewport().mapToGlobal(pos))
        if action is None:
            return
        if action == refresh_action:
            self.updateHistoryTable()
            return
        if action == repeat_action:
            self._repeat_history_doc(row)
            return
        if action == open_file_action:
            self._open_history_file_path(file_path)
            return
        if action == open_folder_action:
            self._open_history_file_dir(file_path)
            return
        if action == copy_path_action:
            self._copy_history_file_path(file_path)
            return
        if action == delete_action:
            self._delete_history_event(row)

    def updateHistoryTable(self):
        if not hasattr(self.ui, "historyTable"):
            return

        try:
            rows = self.db.getOffersHistory(limit=1000)
        except Exception as e:
            Tool.write_log(f"Ошибка загрузки истории: {e}")
            return

        table = self.ui.historyTable
        blocker = QSignalBlocker(table)
        table.clearContents()
        table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            (
                _entry_id,
                offer_number,
                date_value,
                created_at,
                event_type,
                customer_company,
                customer_name,
                items_count,
                total_amount,
                currency,
                file_path,
                _notes,
                payload_json,
            ) = row

            date_text = str(created_at or "").strip() or str(date_value or "").strip()
            event_text = self._history_event_name(event_type)
            offer_text = str(offer_number) if int(offer_number or 0) > 0 else "—"
            company_text = str(customer_company or "").strip() or "—"
            contact_text = str(customer_name or "").strip() or "—"
            items_text = str(max(0, int(items_count or 0)))
            total_text = self._format_history_total(total_amount, str(currency or ""))
            file_path_text = str(file_path or "").strip()
            file_text = Path(file_path_text).name if file_path_text else "—"
            meta = {
                "id": int(_entry_id),
                "event_type": str(event_type or "").strip().lower(),
                "file_path": file_path_text,
                "payload_json": str(payload_json or ""),
            }

            values = [
                date_text,
                event_text,
                offer_text,
                company_text,
                contact_text,
                items_text,
                total_text,
                file_text,
            ]

            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(
                    (item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    & ~Qt.ItemFlag.ItemIsEditable
                )
                if col_idx == self.HISTORY_META_COLUMN:
                    item.setData(Qt.ItemDataRole.UserRole, meta)
                if col_idx == self.HISTORY_FILE_COLUMN and file_path_text:
                    item.setData(Qt.ItemDataRole.UserRole, file_path_text)
                    item.setToolTip(file_path_text)
                table.setItem(row_idx, col_idx, item)

        del blocker
        table.resizeRowsToContents()

    def _openHistoryFile(self, item):
        if item is None or not hasattr(self.ui, "historyTable"):
            return

        row = item.row()
        meta = self._history_row_meta(row)
        file_path = str(meta.get("file_path", "") or "").strip()
        self._open_history_file_path(file_path)

    def _get_formula_for_editor(self, row, col):
        if col not in self.FORMULA_EDITABLE_COLUMNS:
            return None
        formulas = self.formulaExpressions.get(col, [])
        if row < 0 or row >= len(formulas):
            return None
        return formulas[row]

    @staticmethod
    def _default_formula(col):
        defaults = {
            8: "Custom*Logistic",
            9: "Customs/Amount",
            10: "UnitSalePrice*Markup",
            11: "RealPrice*Amount",
            13: "SupplierTerm+TermDelivery",
        }
        return defaults[col]

    def _column_title(self, col):
        if col in self._baseHeaderLabels:
            return self._baseHeaderLabels[col]
        item = self.ui.KpTable.horizontalHeaderItem(col)
        return item.text() if item is not None else str(col)

    def _setup_table_quick_search(self):
        self.tableQuickSearchLine = QLineEdit(self)
        self.tableQuickSearchLine.setPlaceholderText("Быстрый поиск по таблице (Ctrl+F)")
        self.tableQuickSearchClearButton = QPushButton("Сброс", self)
        self.tableQuickSearchClearButton.setMinimumWidth(82)

        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 6)
        search_layout.addWidget(self.tableQuickSearchLine, 1)
        search_layout.addWidget(self.tableQuickSearchClearButton, 0)
        self.ui.verticalLayout_2.insertLayout(0, search_layout)

        self.tableQuickSearchLine.textChanged.connect(self._on_table_quick_search_changed)
        self.tableQuickSearchClearButton.clicked.connect(self.tableQuickSearchLine.clear)

    def _on_table_quick_search_changed(self, text):
        self.quickSearchText = str(text or "").strip().casefold()
        self._apply_table_filters()

    def _focus_table_quick_search(self):
        self.ui.tabWidget.setCurrentWidget(self.ui.tab)
        self.tableQuickSearchLine.setFocus()
        self.tableQuickSearchLine.selectAll()

    def _setup_shortcuts(self):
        self.ui.openTableMenuButton.setShortcut(QKeySequence("Ctrl+O"))
        self.ui.helpMenuButton.setShortcut(QKeySequence("F1"))
        self.ui.createDocMenuButton.setShortcut(QKeySequence("Ctrl+Shift+E"))

        def _bind(shortcut_text, callback, parent=None, context=None):
            shortcut = QShortcut(QKeySequence(shortcut_text), parent or self)
            if context is not None:
                shortcut.setContext(context)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)
            return shortcut

        _bind("F1", self.show_help)
        _bind("Ctrl+O", self.openTable)
        _bind("Ctrl+Shift+E", self.exportDocs)
        _bind("Ctrl+F", self._focus_table_quick_search)
        _bind(
            "Ctrl+D",
            self._duplicate_selected_rows,
            parent=self.ui.KpTable,
            context=Qt.ShortcutContext.WidgetWithChildrenShortcut,
        )
        _bind(
            "Delete",
            self._delete_selected_rows,
            parent=self.ui.KpTable,
            context=Qt.ShortcutContext.WidgetWithChildrenShortcut,
        )
        undo_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Undo), self.ui.KpTable)
        undo_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        undo_shortcut.activated.connect(self._undo_last_table_change)
        self._shortcuts.append(undo_shortcut)

    def _selected_table_rows(self):
        table = self.ui.KpTable
        rows = set()
        selection_model = table.selectionModel()
        if selection_model is not None:
            rows.update(index.row() for index in selection_model.selectedRows())
            if not rows:
                rows.update(index.row() for index in selection_model.selectedIndexes())
        current_row = table.currentRow()
        if current_row >= 0:
            rows.add(current_row)
        return sorted(row for row in rows if 0 <= row < table.rowCount())

    def _capture_table_state(self):
        table = self.ui.KpTable
        table_rows = []
        for row in range(table.rowCount()):
            row_values = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                row_values.append(item.text() if item is not None else "")
            table_rows.append(row_values)

        return {
            "table_rows": table_rows,
            "table_data": {key: list(values) for key, values in self.tableData.items()},
            "formula_expressions": {
                col: list(self.formulaExpressions.get(col, [])) for col in self.FORMULA_EDITABLE_COLUMNS
            },
            "mixed_currency_warning": bool(self.mixedCurrencyWarningShown),
        }

    def _push_undo_state(self):
        if not Config.isTableOpened or self._is_restoring_undo:
            return
        self._pending_edit_undo_state = None
        self._undo_stack.append(self._capture_table_state())
        if len(self._undo_stack) > self.MAX_UNDO_STATES:
            self._undo_stack.pop(0)

    def _restore_table_state(self, state):
        self._pending_edit_undo_state = None
        table_rows = state.get("table_rows", [])
        table = self.ui.KpTable
        self._is_restoring_undo = True
        try:
            blocker = QSignalBlocker(table)
            table.setRowCount(len(table_rows))
            for row, row_values in enumerate(table_rows):
                for col in range(table.columnCount()):
                    value = row_values[col] if col < len(row_values) else ""
                    self._set_table_item(row, col, value, editable=(col in self.EDITABLE_COLUMNS))
            del blocker
        finally:
            self._is_restoring_undo = False

        table_data_state = state.get("table_data", {})
        self.tableData = {
            "amount": list(table_data_state.get("amount", [])),
            "currency": list(table_data_state.get("currency", [])),
            "unitPrice": list(table_data_state.get("unitPrice", [])),
            "totalPrice": list(table_data_state.get("totalPrice", [])),
            "termDelivery": list(table_data_state.get("termDelivery", [])),
            "logistic": list(table_data_state.get("logistic", [])),
        }
        formula_state = state.get("formula_expressions", {})
        self.formulaExpressions = {
            col: list(formula_state.get(col, [])) for col in self.FORMULA_EDITABLE_COLUMNS
        }
        self.rows = len(table_rows)
        self.mixedCurrencyWarningShown = bool(state.get("mixed_currency_warning", False))
        Config.isTableOpened = self.rows > 0
        self._apply_table_filters()
        self._update_total_tab_table()

    def _undo_last_table_change(self):
        if not self._undo_stack:
            return
        state = self._undo_stack.pop()
        self._restore_table_state(state)

    def _clear_undo_history(self):
        self._undo_stack.clear()
        self._pending_edit_undo_state = None

    def _capture_state_before_cell_edit(self, row, col):
        if not Config.isTableOpened or self._is_restoring_undo:
            return
        if row < 0 or col not in self.EDITABLE_COLUMNS:
            return
        self._pending_edit_undo_state = self._capture_table_state()

    def _push_pending_edit_undo_state(self):
        if self._pending_edit_undo_state is None:
            return
        self._undo_stack.append(self._pending_edit_undo_state)
        self._pending_edit_undo_state = None
        if len(self._undo_stack) > self.MAX_UNDO_STATES:
            self._undo_stack.pop(0)

    def _duplicate_selected_rows(self):
        if not Config.isTableOpened or self.ui.KpTable.rowCount() == 0:
            return

        selected_rows = self._selected_table_rows()
        if not selected_rows:
            return

        self._push_undo_state()

        table = self.ui.KpTable
        blocker = QSignalBlocker(table)
        offset = 0
        for source_row in selected_rows:
            source_index = source_row + offset
            insert_index = source_index + 1
            table.insertRow(insert_index)

            for col in range(table.columnCount()):
                src_item = table.item(source_index, col)
                src_text = src_item.text() if src_item is not None else ""
                self._set_table_item(insert_index, col, src_text, editable=(col in self.EDITABLE_COLUMNS))

            for key in ("amount", "currency", "unitPrice", "totalPrice", "termDelivery", "logistic"):
                self.tableData[key].insert(insert_index, self.tableData[key][source_index])
            for col in self.FORMULA_EDITABLE_COLUMNS:
                self.formulaExpressions[col].insert(insert_index, self.formulaExpressions[col][source_index])

            offset += 1
        del blocker

        self.rows = table.rowCount()
        self.mixedCurrencyWarningShown = False
        self.logisticCalculate()
        self.calculating()
        self._apply_table_filters()
        self._update_total_tab_table()

    def _delete_selected_rows(self):
        if not Config.isTableOpened or self.ui.KpTable.rowCount() == 0:
            return

        selected_rows = self._selected_table_rows()
        if not selected_rows:
            return

        self._push_undo_state()

        table = self.ui.KpTable
        blocker = QSignalBlocker(table)
        for row in sorted(selected_rows, reverse=True):
            if 0 <= row < table.rowCount():
                table.removeRow(row)
            for key in ("amount", "currency", "unitPrice", "totalPrice", "termDelivery", "logistic"):
                if 0 <= row < len(self.tableData[key]):
                    del self.tableData[key][row]
            for col in self.FORMULA_EDITABLE_COLUMNS:
                formulas = self.formulaExpressions.get(col, [])
                if 0 <= row < len(formulas):
                    del formulas[row]
        del blocker

        self.rows = table.rowCount()
        self.mixedCurrencyWarningShown = False
        if self.rows == 0:
            self.closeTable(clear_undo=False)
            return

        self.logisticCalculate()
        self.calculating()
        self._apply_table_filters()
        self._update_total_tab_table()

    def _init_table_filters(self):
        table = self.ui.KpTable
        self._baseHeaderLabels = {}
        for col in range(table.columnCount()):
            item = table.horizontalHeaderItem(col)
            self._baseHeaderLabels[col] = item.text() if item is not None else str(col + 1)

        header = table.horizontalHeader()
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_filter_menu)
        self._refresh_filter_headers()

    def _column_values(self, col):
        values = set()
        for row in range(self.ui.KpTable.rowCount()):
            item = self.ui.KpTable.item(row, col)
            values.add((item.text() if item is not None else "").strip())
        return sorted((value for value in values if value != ""), key=lambda value: value.casefold())

    def _refresh_filter_headers(self):
        for col, base_label in self._baseHeaderLabels.items():
            item = self.ui.KpTable.horizontalHeaderItem(col)
            if item is None:
                continue
            if col in self.columnFilters:
                item.setText(f"{base_label} [Ф]")
            else:
                item.setText(base_label)

    @staticmethod
    def _match_filter_value(row_value, filter_spec):
        mode = filter_spec.get("mode", "equals")
        filter_value = str(filter_spec.get("value", "")).strip()
        row_text = str(row_value or "").strip()
        row_norm = row_text.casefold()
        filter_norm = filter_value.casefold()

        if mode == "equals":
            return row_norm == filter_norm
        if mode == "contains":
            return filter_norm in row_norm
        if mode == "starts_with":
            return row_norm.startswith(filter_norm)
        if mode == "ends_with":
            return row_norm.endswith(filter_norm)
        if mode == "empty":
            return row_text == ""
        return True

    def _set_text_filter(self, col, mode, prompt):
        current_filter = self.columnFilters.get(col, {})
        current_value = ""
        if current_filter.get("mode") == mode:
            current_value = str(current_filter.get("value", ""))

        value, ok = QInputDialog.getText(self, "Текстовый фильтр", prompt, text=current_value)
        if not ok:
            return False

        value = value.strip()
        if not value:
            self.error("Ошибка", "Введите текст для фильтра")
            return False

        self.columnFilters[col] = {"mode": mode, "value": value}
        return True

    def _apply_table_filters(self):
        table = self.ui.KpTable
        for row in range(table.rowCount()):
            is_visible = True
            for col, filter_spec in self.columnFilters.items():
                item = table.item(row, col)
                row_value = (item.text() if item is not None else "").strip()
                if not self._match_filter_value(row_value, filter_spec):
                    is_visible = False
                    break
            if is_visible and self.quickSearchText:
                row_has_match = False
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    row_text = (item.text() if item is not None else "").casefold()
                    if self.quickSearchText in row_text:
                        row_has_match = True
                        break
                is_visible = row_has_match
            table.setRowHidden(row, not is_visible)

    def _clear_all_filters(self):
        self.columnFilters.clear()
        self._refresh_filter_headers()
        self._apply_table_filters()

    def _show_filter_menu(self, pos):
        header = self.ui.KpTable.horizontalHeader()
        col = header.logicalIndexAt(pos)
        if col < 0:
            return

        menu = QMenu(self)
        column_name = self._baseHeaderLabels.get(col, self._column_title(col))
        title_action = menu.addAction(f"Фильтр: {column_name}")
        title_action.setEnabled(False)
        menu.addSeparator()

        clear_column_action = menu.addAction("Сбросить фильтр по столбцу")
        clear_column_action.setEnabled(col in self.columnFilters)
        clear_all_action = menu.addAction("Сбросить все фильтры")
        clear_all_action.setEnabled(bool(self.columnFilters))
        menu.addSeparator()

        contains_action = menu.addAction("Текстовый фильтр: содержит...")
        starts_with_action = menu.addAction("Текстовый фильтр: начинается с...")
        ends_with_action = menu.addAction("Текстовый фильтр: заканчивается на...")
        equals_text_action = menu.addAction("Текстовый фильтр: равно...")
        menu.addSeparator()

        all_values_action = menu.addAction("Все значения")
        empty_value_action = menu.addAction("(Пустые)")
        menu.addSeparator()

        value_actions = {}
        values = self._column_values(col)
        current_filter = self.columnFilters.get(col, {})
        current_mode = current_filter.get("mode")
        current_value = str(current_filter.get("value", "")).strip()
        current_value_norm = current_value.casefold()
        visible_limit = 150
        for value in values[:visible_limit]:
            action = menu.addAction(value)
            if current_mode == "equals" and value.casefold() == current_value_norm:
                action.setCheckable(True)
                action.setChecked(True)
            value_actions[action] = value

        if current_mode == "empty":
            empty_value_action.setCheckable(True)
            empty_value_action.setChecked(True)

        if len(values) > visible_limit:
            menu.addSeparator()
            extra_action = menu.addAction(f"Показано {visible_limit} из {len(values)} значений")
            extra_action.setEnabled(False)

        selected_action = menu.exec(header.mapToGlobal(pos))
        if selected_action is None:
            return
        if selected_action == clear_column_action:
            self.columnFilters.pop(col, None)
        elif selected_action == clear_all_action:
            self.columnFilters.clear()
        elif selected_action == contains_action:
            if not self._set_text_filter(col, "contains", f'{column_name}: содержит текст'):
                return
        elif selected_action == starts_with_action:
            if not self._set_text_filter(col, "starts_with", f'{column_name}: начинается с'):
                return
        elif selected_action == ends_with_action:
            if not self._set_text_filter(col, "ends_with", f'{column_name}: заканчивается на'):
                return
        elif selected_action == equals_text_action:
            if not self._set_text_filter(col, "equals", f'{column_name}: равно тексту'):
                return
        elif selected_action == all_values_action:
            self.columnFilters.pop(col, None)
        elif selected_action == empty_value_action:
            self.columnFilters[col] = {"mode": "empty", "value": ""}
        elif selected_action in value_actions:
            self.columnFilters[col] = {"mode": "equals", "value": value_actions[selected_action]}
        else:
            return

        self._refresh_filter_headers()
        self._apply_table_filters()

    @staticmethod
    def _normalize_param_name(value):
        return str(value or "").strip().casefold()

    def _load_formula_parameters(self):
        params_data = Tool.load_json(Config.vars_path)
        parameters = {}
        for values in params_data.get("parameters", {}).values():
            if len(values) < 3:
                continue
            variable, value, calc_type = values[0], values[1], values[2]
            key = self._normalize_param_name(variable)
            if not key:
                continue
            parameters[key] = (str(value).replace(",", "."), str(calc_type))
        return parameters

    def _eval_formula(self, formula, context, row, col, parameters):
        expression = str(formula or "").strip().replace(",", ".")
        if expression.startswith("="):
            expression = expression[1:].strip()
        if not expression:
            raise ValueError(
                f'Строка {row + 1}, столбец "{self._column_title(col)}": формула не может быть пустой'
            )

        def _replace_named_variable(match):
            token = match.group(1).strip()
            key = self._normalize_param_name(token)
            if key not in parameters:
                raise ValueError(
                    f'Строка {row + 1}, столбец "{self._column_title(col)}": '
                    f'неизвестная переменная "${token}$"'
                )
            value, calc_type = parameters[key]
            if calc_type == "percents":
                return f"({value})/100"
            if calc_type == "multiply":
                return f"*({value})"
            if calc_type == "division":
                return f"/({value})"
            return f"({value})"

        expression = re.sub(r"\$([^$]+)\$", _replace_named_variable, expression).strip()
        while expression and expression[0] in "+*/":
            expression = expression[1:].strip()
        if not expression:
            raise ValueError(
                f'Строка {row + 1}, столбец "{self._column_title(col)}": формула не может быть пустой'
            )

        def _replace_token(match):
            token = match.group(0)
            key = token.lower()
            if key not in context:
                key = key.replace("_", "")
            if key not in context:
                raise ValueError(
                    f'Строка {row + 1}, столбец "{self._column_title(col)}": неизвестная переменная "{token}"'
                )
            return str(context[key])

        token_pattern = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
        math_expression = token_pattern.sub(_replace_token, expression)
        try:
            return float(Tool._safe_eval(math_expression))
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(
                f'Строка {row + 1}, столбец "{self._column_title(col)}": некорректная формула'
            ) from e

    def _init_formula_expressions(self):
        self.formulaExpressions = {col: [] for col in self.FORMULA_EDITABLE_COLUMNS}
        for _ in range(self.rows):
            for col in self.FORMULA_EDITABLE_COLUMNS:
                self.formulaExpressions[col].append(self._default_formula(col))

    def _update_total_price_cell(self, row):
        amount = self.tableData["amount"][row]
        unit_price = self.tableData["unitPrice"][row]
        currency = self.tableData["currency"][row]
        total_price = round(amount * unit_price, 2)
        self.tableData["totalPrice"][row] = total_price
        self._set_table_item(row, 6, Tool.formatPrice(str(total_price), currency), editable=False)

    def _restore_edited_cell(self, row, col):
        if col == 4:
            self._set_table_item(row, col, self.tableData["amount"][row], editable=True)
            return
        if col == 5:
            self._set_table_item(
                row,
                col,
                Tool.formatPrice(
                    str(self.tableData["unitPrice"][row]),
                    self.tableData["currency"][row],
                ),
                editable=True,
            )
            return
        if col == 14:
            self._set_table_item(
                row,
                col,
                f"{self.tableData['termDelivery'][row]} дней",
                editable=True,
            )

    def tableItemChanged(self, item):
        if not Config.isTableOpened or item is None:
            return

        row = item.row()
        col = item.column()
        if row < 0 or row >= self.rows or col not in self.EDITABLE_COLUMNS:
            return

        self._push_pending_edit_undo_state()

        text = item.text().strip()
        needs_manual_summary_refresh = col in {0, 1, 2, 3}
        if col in self.FORMULA_EDITABLE_COLUMNS:
            old_formula = self.formulaExpressions[col][row]
            try:
                if not text:
                    raise ValueError(
                        f'Строка {row + 1}, столбец "{self._column_title(col)}": формула не может быть пустой'
                    )
                self.formulaExpressions[col][row] = text
                self.calculating()
            except ValueError as e:
                self.formulaExpressions[col][row] = old_formula
                self.calculating()
                self.error("Ошибка", str(e))
            self._apply_table_filters()
            return

        try:
            if col == 4:
                parsed_amount = Tool.parse_int(text, f"Кол-во (строка {row + 1})", allow_zero=False)
                self.tableData["amount"][row] = parsed_amount
                blocker = QSignalBlocker(self.ui.KpTable)
                self._set_table_item(row, 4, parsed_amount, editable=True)
                self._update_total_price_cell(row)
                del blocker
                self.logisticCalculate()
                self.calculating()
            elif col == 5:
                currency, price_text = Tool.parsePrice(text)
                if not currency:
                    currency = self.tableData["currency"][row]
                    price_text = text
                parsed_price = Tool.parse_float(price_text, f"Цена (строка {row + 1})", allow_zero=True)
                self.tableData["currency"][row] = currency
                self.tableData["unitPrice"][row] = parsed_price
                blocker = QSignalBlocker(self.ui.KpTable)
                self._set_table_item(row, 5, Tool.formatPrice(str(parsed_price), currency), editable=True)
                self._update_total_price_cell(row)
                del blocker
                self.logisticCalculate()
                self.calculating()
            elif col == 14:
                parsed_term = Tool.parse_delivery_days(text)
                self.tableData["termDelivery"][row] = parsed_term
                blocker = QSignalBlocker(self.ui.KpTable)
                self._set_table_item(row, 14, f"{parsed_term} дней", editable=True)
                del blocker
                self.calculating()
            else:
                blocker = QSignalBlocker(self.ui.KpTable)
                self._set_table_item(row, col, text, editable=True)
                del blocker
        except ValueError as e:
            self.error("Ошибка", str(e))
            blocker = QSignalBlocker(self.ui.KpTable)
            self._restore_edited_cell(row, col)
            del blocker
        self._apply_table_filters()
        if needs_manual_summary_refresh:
            self._update_total_tab_table()

    def testFeature(self, checked):
        QMessageBox.about(
            self,
            "ВНИМАНИЕ",
            "Для включения тестовой функции, необходимо перезапустить приложение"
            "<br>*Возможны неточности в склонении слов</br>",
        )

        Config.settings["testFeature"] = checked
        self.saveConfig()

    def clear_cache(self):
        dst_dir = Tool.user_data_dir("MyApp")
        dst_dir.mkdir(parents=True, exist_ok=True)

        dst = dst_dir / "config.json"
        src = Tool.resourcePath("utilities/config.json")
        shutil.copy2(src, dst)

        self.loadConfig()
        self.ensureOutputDirs()
        if Config.settings["autoFill"]:
            self.ui.logisticNum.setText(Config.config["logisticNum"])
            self.ui.customLine.setText(Config.config["customNum"])
            self.ui.termDeliveryLine.setText(Config.config["termDelivery"])
            self.ui.markupLine.setText(Config.config["markup"])
            self.ui.logisticVar.setCurrentIndex(int(Config.config["logisticVar"]))
        self.processFormula()

    def open_url(self, url):
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            Tool.log_exception(f"Не удалось открыть URL: {url}", e, include_traceback=False)

    def show_help(self):
        help_text = """
        <html>
        <head>
        <style>
            h2 { color: #2c3e50; }
            h3 { color: #34495e; }
            .hotkey { background: #ecf0f1; padding: 2px 6px; border-radius: 3px; }
        </style>
        </head>
        <body>
        <h2>📖 Справка по программе</h2>

        <h3>Основные функции</h3>
        <ul>
            <li><b>Настройки → Импортировать БД</b> - импортировать БД с заказчиками</li>
            <li><b>Настройки → Экспортировать БД</b> - сохранить текущую БД с заказчиками</li>
        </ul>

        <h3>Переменные</h3>
        <p>Для заполнения переменных, необходимо перейти в <b>Редактировать -> редактировать переменные</b>. Далее для использования переменных
        необходимо соблюдать формат: $название переменной$</p>

        <h3>Логистика</h3>
        <li><b>Распределение</b> - распределяет указанную сумму на столбцы</li>
            <li><b>Коэффициент</b> - умножает указанную сумму на столбцы</li>

        <h3>Горячие клавиши</h3>
        <ul>
            <li><span class="hotkey">F1</span> - открыть справку</li>
            <li><span class="hotkey">Ctrl+O</span> - открыть таблицу</li>
            <li><span class="hotkey">Ctrl+F</span> - поиск по таблице</li>
            <li><span class="hotkey">Ctrl+D</span> - дублировать выбранные строки</li>
            <li><span class="hotkey">Ctrl+Z / Cmd+Z</span> - отменить последнее изменение таблицы</li>
            <li><span class="hotkey">Delete</span> - удалить выбранные строки</li>
            <li><span class="hotkey">Ctrl+Shift+E</span> - скачать КП</li>
        </ul>

        <h3>Поддержка</h3>
        <p>При возникновении проблем:</p>
        <ol>
            <li>Перезапустите программу</li>
            <li>Проверьте наличие обновлений</li>
            <li>Обратитесь в техподдержку: zemtsovpast@yandex.ru</li>
            <li>Телеграм: @p4strick</li>
        </ol>
        </body>
        </html>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Справка")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def show_about(self):
        QMessageBox.about(
            self,
            "О программе",
            "<b>Автоматизация подгтовки коммерческих приложений</b><br>"
            "Версия 1.0.5<br><br>"
            "Создано с использованием PySide6<br>"
            "<br>Лицензия MIT</br>"
            "Автор: https://github.com/p4st1",
        )

    def exportDatabase(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить файл",
            f"database_{datetime.now().strftime('%d.%m.%Y')}.db",
            "База данных (*.db);;Все файлы (*)",
        )
        if not file_path:
            return

        status = self.db.export(Config.db_path, file_path)
        if status == -1:
            self.error("Ошибка", "Не удалось экспортировать базу данных")
        else:
            QMessageBox.information(self, "Готово", "База данных экспортирована")

    def importDatabase(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть файл",
            "",
            "База данных (*.db);;Все файлы (*)",
        )
        if not file_path:
            return

        status = self.db.import_(file_path, Config.db_path)
        if status == -1:
            self.error("Ошибка", "Не удалось импортировать базу данных")
        else:
            self.db.close()
            self.db.open(Config.db_path)
            QMessageBox.information(self, "Готово", "База данных импортирована")

    @staticmethod
    def _fmt_number(value: float) -> str:
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.6f}".rstrip("0").rstrip(".")

    def _parse_input_parameters(self, show_error=True):
        try:
            custom = float(Tool.evalWithVars(self.ui.customLine.text().replace(",", ".")))
            markup = float(Tool.evalWithVars(self.ui.markupLine.text().replace(",", ".")))
            logistic = float(Tool.evalWithVars(self.ui.logisticNum.text().replace(",", ".")))
            term_delivery = Tool.parse_int(self.ui.termDeliveryLine.text(), "Срок поставки", allow_zero=True)
            if custom <= 0:
                raise ValueError('Поле "Таможня" должно быть положительным')
            if markup <= 0:
                raise ValueError('Поле "Наценка" должно быть положительным')
            if logistic < 0:
                raise ValueError('Поле "Логистика" должно быть неотрицательным')
        except Exception as e:
            if show_error:
                self.error("Ошибка", str(e))
            return None

        self.formulaCustom = custom
        self.formulaMarkup = markup
        self.formulaLogistic = logistic
        self.termDeliveryDays = term_delivery

        self.ui.customLine.setText(self._fmt_number(custom))
        self.ui.markupLine.setText(self._fmt_number(markup))
        self.ui.logisticNum.setText(self._fmt_number(logistic))
        self.ui.termDeliveryLine.setText(str(term_delivery))

        return {
            "custom": custom,
            "markup": markup,
            "logistic": logistic,
            "termDelivery": term_delivery,
        }

    def processFormula(self):
        parsed = self._parse_input_parameters(show_error=True)
        if parsed is None:
            return

        if Config.isTableOpened:
            try:
                self.logisticCalculate()
                self.calculating()
            except ValueError as e:
                self.error("Ошибка", str(e))

    @staticmethod
    def _normalize_header(text):
        value = str(text or "").strip().lower().replace("ё", "е")
        value = re.sub(r"[^a-zа-я0-9]+", "", value)
        return value

    def _read_source_table(self, filename):
        ext = Path(filename).suffix.lower()
        if ext in {".xls", ".xlsx"}:
            return pd.read_excel(filename, header=None, dtype=str).fillna("")

        errors = []
        for encoding in ("utf-8-sig", "utf-16", "cp1251", "utf-8"):
            try:
                return pd.read_csv(
                    filename,
                    header=None,
                    sep=";",
                    dtype=str,
                    encoding=encoding,
                    engine="python",
                    on_bad_lines="skip",
                ).fillna("")
            except Exception as e:
                errors.append(str(e))
        raise ValueError("Не удалось прочитать файл. Проверьте кодировку и формат CSV")

    def _detect_columns(self, df):
        header_row = None
        max_rows = min(len(df.index), 50)
        max_cols = min(len(df.columns), 20)
        for row_idx in range(max_rows):
            row_values = [self._normalize_header(df.iat[row_idx, col]) for col in range(max_cols)]
            has_name = any("наименование" in value for value in row_values)
            has_qty = any("колво" in value or ("кол" in value and "во" in value) for value in row_values)
            has_price = any("цена" in value for value in row_values)
            if has_name and has_qty and has_price:
                header_row = row_idx
                break

        if header_row is None:
            header_row = 0

        mapping = {
            "number": None,
            "name": None,
            "sku": None,
            "unit": None,
            "qty": None,
            "price": None,
            "term": None,
        }

        for col in range(len(df.columns)):
            value = self._normalize_header(df.iat[header_row, col])
            if "наименование" in value:
                if mapping["name"] is None:
                    mapping["name"] = col
            elif "каталож" in value and "номер" in value:
                if mapping["sku"] is None:
                    mapping["sku"] = col
            elif value.startswith("ед") or "едизм" in value:
                if mapping["unit"] is None:
                    mapping["unit"] = col
            elif "колво" in value or ("кол" in value and "во" in value):
                if mapping["qty"] is None:
                    mapping["qty"] = col
            elif (
                "ценазаедбезндс" in value
                or ("цена" in value and "заед" in value)
                or ("цена" in value and mapping["price"] is None)
            ):
                if mapping["price"] is None:
                    mapping["price"] = col
            elif "срок" in value:
                if mapping["term"] is None:
                    mapping["term"] = col
            elif value in {"n", "no", "номер"} or "№" in str(df.iat[header_row, col]):
                if mapping["number"] is None:
                    mapping["number"] = col

        defaults = {
            "number": 0,
            "name": 1,
            "sku": 2,
            "unit": 3,
            "qty": 4,
            "price": 5,
            "term": 6,
        }
        for key, default_col in defaults.items():
            if mapping[key] is None:
                mapping[key] = default_col

        if max(mapping.values()) >= len(df.columns):
            raise ValueError("В таблице не хватает необходимых столбцов")
        return header_row, mapping

    def _parse_source_rows(self, df):
        header_row, mapping = self._detect_columns(df)
        parsed_rows = []
        warnings = []
        blank_streak = 0

        for row_idx in range(header_row + 1, len(df.index)):
            number_text = str(df.iat[row_idx, mapping["number"]]).strip()
            name = str(df.iat[row_idx, mapping["name"]]).strip()
            sku = str(df.iat[row_idx, mapping["sku"]]).strip()
            unit = str(df.iat[row_idx, mapping["unit"]]).strip()
            qty_text = str(df.iat[row_idx, mapping["qty"]]).strip()
            price_text = str(df.iat[row_idx, mapping["price"]]).strip()
            term_text = str(df.iat[row_idx, mapping["term"]]).strip()

            if not any([name, sku, unit, qty_text, price_text, term_text]):
                blank_streak += 1
                if parsed_rows and blank_streak >= 2:
                    break
                continue
            blank_streak = 0

            if not name:
                warnings.append(f"Строка {row_idx + 1}: пропущено наименование, строка пропущена")
                continue

            try:
                qty = Tool.parse_int(qty_text, f"Кол-во (строка {row_idx + 1})", allow_zero=False)
            except ValueError as e:
                warnings.append(str(e))
                continue

            try:
                currency, price_value = Tool.parsePrice(price_text)
                if not currency:
                    match = re.search(r"[¥$₽€]", price_text)
                    if match:
                        currency = match.group(0)
                        price_value = price_text.replace(currency, "").strip()
                if not currency:
                    raise ValueError("Не указана валюта")
                unit_price = Tool.parse_float(price_value, f"Цена (строка {row_idx + 1})", allow_zero=True)
            except ValueError as e:
                warnings.append(f"Строка {row_idx + 1}: {e}")
                continue

            try:
                supplier_term_days = Tool.parse_delivery_days(term_text)
            except ValueError as e:
                warnings.append(f"Строка {row_idx + 1}: {e}. Установлено 0 дней")
                supplier_term_days = 0

            row_number = number_text if number_text else str(len(parsed_rows) + 1)
            parsed_rows.append(
                {
                    "number": row_number,
                    "name": name,
                    "sku": sku,
                    "unit": unit if unit else "шт.",
                    "qty": qty,
                    "currency": currency,
                    "unitPrice": unit_price,
                    "supplierTermDays": supplier_term_days,
                }
            )

        if not parsed_rows:
            raise ValueError("В файле не найдено ни одной валидной строки товара")

        return parsed_rows, warnings

    def openTable(self, file=None):
        filename = file
        if not filename:
            filename = QFileDialog.getOpenFileName(
                self,
                "Открыть файл",
                "",
                "csv (*.csv);; Excel Files (*.xls *.xlsx)",
            )[0]
        if not filename:
            return

        if not Path(filename).exists():
            self.error("Ошибка", f"Файл не найден: {filename}")
            return

        params = self._parse_input_parameters(show_error=True)
        if params is None:
            return

        self.closeTable()
        try:
            df = self._read_source_table(filename)
            parsed_rows, warnings = self._parse_source_rows(df)
        except Exception as e:
            self.error("Ошибка", f"Невозможно прочитать таблицу\n{e}")
            return

        self.ui.KpTable.setRowCount(len(parsed_rows))
        self.tableData = {
            "amount": [],
            "currency": [],
            "unitPrice": [],
            "totalPrice": [],
            "termDelivery": [],
            "logistic": [],
        }

        blocker = QSignalBlocker(self.ui.KpTable)
        for row_num, row in enumerate(parsed_rows):
            total_price = round(row["qty"] * row["unitPrice"], 2)
            self._set_table_item(row_num, 0, row["number"], editable=True)
            self._set_table_item(row_num, 1, row["name"], editable=True)
            self._set_table_item(row_num, 2, row["sku"], editable=True)
            self._set_table_item(row_num, 3, row["unit"], editable=True)
            self._set_table_item(row_num, 4, row["qty"], editable=True)
            self._set_table_item(
                row_num,
                5,
                Tool.formatPrice(str(row["unitPrice"]), row["currency"]),
                editable=True,
            )
            self._set_table_item(
                row_num,
                6,
                Tool.formatPrice(str(total_price), row["currency"]),
                editable=False,
            )
            self._set_table_item(row_num, 14, f"{row['supplierTermDays']} дней", editable=True)

            self.tableData["amount"].append(row["qty"])
            self.tableData["currency"].append(row["currency"])
            self.tableData["unitPrice"].append(row["unitPrice"])
            self.tableData["totalPrice"].append(total_price)
            self.tableData["termDelivery"].append(row["supplierTermDays"])
        del blocker

        self.rows = len(parsed_rows)
        self._init_formula_expressions()
        self._clear_undo_history()
        self.mixedCurrencyWarningShown = False
        self.logisticCalculate()
        self.calculating()
        self.ui.KpTable.resizeColumnsToContents()
        self._apply_table_filters()

        Config.config["lastTable"] = filename
        self.saveConfig()
        Config.isTableOpened = True
        self.ui.tabWidget.setCurrentIndex(1)

        if warnings:
            trimmed = warnings[:10]
            message = "Найдены проблемы в таблице:\n- " + "\n- ".join(trimmed)
            if len(warnings) > 10:
                message += f"\n... и еще {len(warnings) - 10}"
            QMessageBox.warning(self, "Внимание", message)

    def error(self, title, text):
        error = QMessageBox(self)
        error.setWindowTitle(title)
        error.setText(text)
        error.exec()

    def openCreateDocWindow(self, tableData):
        window = createDocWindow(self, tableData=tableData)
        window.show()
        window.windowClosed.connect(self.updateHistoryTable)
        if Config.settings["closeTable"]:
            window.windowClosed.connect(self.closeTable)
            self.ui.KpTable.setRowCount(0)

    def openParamsWindow(self):
        window = paramsWindow(self)
        window.paramsSaved.connect(self._recalculate_after_params_save)
        window.show()

    def _recalculate_after_params_save(self):
        if not Config.isTableOpened:
            return
        try:
            self.calculating()
        except ValueError as e:
            self.error("Ошибка", str(e))

    def openSettingsWindow(self):
        window = settingsWindow(self)
        window.show()

    def openSuppliersWindow(self):
        window = customersWindow(self)
        window.show()

    def closeTable(self, _checked=False, clear_undo=True):
        Config.isTableOpened = False
        blocker = QSignalBlocker(self.ui.KpTable)
        self.ui.KpTable.clearContents()
        self.ui.KpTable.setRowCount(0)
        del blocker
        self.tableData = {
            "amount": [],
            "currency": [],
            "unitPrice": [],
            "totalPrice": [],
            "termDelivery": [],
            "logistic": [],
        }
        self.formulaExpressions = {col: [] for col in self.FORMULA_EDITABLE_COLUMNS}
        self.rows = 0
        self.quickSearchText = ""
        if hasattr(self, "tableQuickSearchLine"):
            blocker_search = QSignalBlocker(self.tableQuickSearchLine)
            self.tableQuickSearchLine.clear()
            del blocker_search
        if clear_undo:
            self._clear_undo_history()
        self._clear_all_filters()
        self._update_total_tab_table()

    def _vat_multiplier(self):
        params_data = Tool.load_json(Config.vars_path)
        for values in params_data.get("parameters", {}).values():
            if len(values) < 3:
                continue
            name, value, calc_type = values[0], values[1], values[2]
            if name == "НДС":
                try:
                    rate = float(str(value).replace(",", "."))
                except ValueError as e:
                    Tool.log_exception(
                        f"Некорректное значение НДС: {value}",
                        e,
                        include_traceback=False,
                    )
                    return 1.0
                if calc_type == "percents":
                    return 1 + rate / 100
                return 1 + rate
        return 1.0

    def calculating(self):
        if not self.tableData["amount"] or not self.tableData["logistic"]:
            return

        for col in self.FORMULA_EDITABLE_COLUMNS:
            if len(self.formulaExpressions.get(col, [])) != self.rows:
                self._init_formula_expressions()
                break

        named_parameters = self._load_formula_parameters()
        vat_multiplier = self._vat_multiplier()
        blocker = QSignalBlocker(self.ui.KpTable)
        for row_num in range(self.rows):
            amount = self.tableData["amount"][row_num]
            unit_price = self.tableData["unitPrice"][row_num]
            total_price = self.tableData["totalPrice"][row_num]
            currency = self.tableData["currency"][row_num]
            logistic_value = self.tableData["logistic"][row_num]
            supplier_term = self.tableData["termDelivery"][row_num]
            context = {
                "amount": float(amount),
                "qty": float(amount),
                "unitprice": float(unit_price),
                "price": float(unit_price),
                "totalprice": float(total_price),
                "logistic": float(logistic_value),
                "custom": float(self.formulaCustom),
                "markup": float(self.formulaMarkup),
                "vat": float(vat_multiplier),
                "supplierterm": float(supplier_term),
                "termdelivery": float(self.termDeliveryDays),
            }

            customs_sum = round(
                self._eval_formula(self.formulaExpressions[8][row_num], context, row_num, 8, named_parameters),
                2,
            )
            if customs_sum < 0:
                raise ValueError(
                    f'Строка {row_num + 1}, столбец "{self._column_title(8)}": '
                    "результат формулы не может быть отрицательным"
                )
            context["customs"] = float(customs_sum)

            unit_sale_price = round(
                self._eval_formula(self.formulaExpressions[9][row_num], context, row_num, 9, named_parameters),
                2,
            )
            if unit_sale_price < 0:
                raise ValueError(
                    f'Строка {row_num + 1}, столбец "{self._column_title(9)}": '
                    "результат формулы не может быть отрицательным"
                )
            context["unitsaleprice"] = float(unit_sale_price)

            real_price = round(
                self._eval_formula(self.formulaExpressions[10][row_num], context, row_num, 10, named_parameters),
                2,
            )
            if real_price < 0:
                raise ValueError(
                    f'Строка {row_num + 1}, столбец "{self._column_title(10)}": '
                    "результат формулы не может быть отрицательным"
                )
            context["realprice"] = float(real_price)

            total_without_vat = round(
                self._eval_formula(self.formulaExpressions[11][row_num], context, row_num, 11, named_parameters),
                2,
            )
            if total_without_vat < 0:
                raise ValueError(
                    f'Строка {row_num + 1}, столбец "{self._column_title(11)}": '
                    "результат формулы не может быть отрицательным"
                )
            context["totalwithoutvat"] = float(total_without_vat)

            total_with_vat = round(total_without_vat * vat_multiplier, 2)
            if total_with_vat < 0:
                raise ValueError(
                    f'Строка {row_num + 1}, столбец "{self._column_title(12)}": '
                    "результат формулы не может быть отрицательным"
                )
            context["totalwithvat"] = float(total_with_vat)

            total_delivery_days = int(
                round(
                    self._eval_formula(
                        self.formulaExpressions[13][row_num], context, row_num, 13, named_parameters
                    )
                )
            )
            if total_delivery_days < 0:
                raise ValueError(
                    f'Строка {row_num + 1}, столбец "{self._column_title(13)}": '
                    "результат формулы не может быть отрицательным"
                )

            self._set_table_item(
                row_num,
                8,
                Tool.formatPrice(str(customs_sum), currency),
                editable=True,
            )
            self._set_table_item(
                row_num,
                9,
                Tool.formatPrice(str(unit_sale_price), currency),
                editable=True,
            )
            self._set_table_item(
                row_num,
                10,
                Tool.formatPrice(str(real_price), currency),
                editable=True,
            )
            self._set_table_item(
                row_num,
                11,
                Tool.formatPrice(str(total_without_vat), currency),
                editable=True,
            )
            self._set_table_item(
                row_num,
                12,
                Tool.formatPrice(str(total_with_vat), currency),
                editable=False,
            )
            self._set_table_item(
                row_num,
                13,
                f"{total_delivery_days} дней",
                editable=True,
            )
        del blocker
        self._apply_table_filters()
        self._update_total_tab_table()

    def logisticVarChanged(self, _):
        if Config.isTableOpened:
            try:
                self.logisticCalculate()
                self.calculating()
            except ValueError as e:
                self.error("Ошибка", str(e))

    def logisticCalculate(self):
        if not self.tableData["totalPrice"]:
            return

        logistic_var = self.ui.logisticVar.currentIndex()
        currencies = set(self.tableData["currency"])
        if logistic_var == 1 and len(currencies) > 1:
            if not self.mixedCurrencyWarningShown:
                QMessageBox.warning(
                    self,
                    "Внимание",
                    "Режим 'распределение' недоступен при смешанной валюте. "
                    "Переключено на режим 'коэффициент'.",
                )
                self.mixedCurrencyWarningShown = True
            self.ui.logisticVar.blockSignals(True)
            self.ui.logisticVar.setCurrentIndex(0)
            self.ui.logisticVar.blockSignals(False)
            logistic_var = 0

        logistic_num = self.formulaLogistic
        total_sum = sum(self.tableData["totalPrice"])
        self.tableData["logistic"] = []

        blocker = QSignalBlocker(self.ui.KpTable)
        for row_num in range(self.rows):
            base_total = self.tableData["totalPrice"][row_num]
            if logistic_var == 1:
                if total_sum <= 0:
                    f = 0
                else:
                    f = round(base_total + logistic_num / total_sum * base_total, 2)
            else:
                f = round(base_total * logistic_num, 2)
            currency = self.tableData["currency"][row_num]
            self._set_table_item(
                row_num,
                7,
                Tool.formatPrice(str(f), currency),
                editable=False,
            )
            self.tableData["logistic"].append(f)
        del blocker
        self._apply_table_filters()

    def getTableData(self):
        table_data = []
        row_count = self.ui.KpTable.rowCount()
        for row in range(row_count):
            row_data = []
            for col in self.SUMMARY_SOURCE_COLUMNS:
                item = self.ui.KpTable.item(row, col)
                row_data.append(item.text() if item is not None else "")
            table_data.append(row_data)
        return table_data

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

    def _has_mixed_currencies(self):
        return len(set(self.tableData.get("currency", []))) > 1

    def _table_column_total(self, col: int):
        total = 0.0
        currency = ""
        for row in range(self.ui.KpTable.rowCount()):
            item = self.ui.KpTable.item(row, col)
            if item is None:
                continue
            symb, amount_text = Tool.parsePrice(item.text())
            if symb and not currency:
                currency = symb
            try:
                total += float(str(amount_text).replace(" ", "").replace(",", "."))
            except ValueError as e:
                Tool.log_exception(
                    f"Не удалось распарсить сумму в строке {row + 1}: {amount_text}",
                    e,
                    include_traceback=False,
                )
                continue
        return round(total, 2), currency

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

        tableData = []
        row_count = self.ui.KpTable.rowCount()

        for row in range(row_count):
            row_data = []
            for col in range(6):
                item = self.ui.KpTable.item(row, col)
                row_data.append(item.text() if item is not None else "")
            for col in range(13, 15):
                item = self.ui.KpTable.item(row, col)
                row_data.append(item.text() if item is not None else "")
            tableData.append(row_data)

        export_result = exportExcelFile(
            (
                tableData,
                (
                    self.ui.logisticVar.currentIndex(),
                    self.ui.logisticNum.text(),
                    self.ui.markupLine.text(),
                ),
                self.ui.customLine.text(),
                sum(self.tableData["totalPrice"]),
            )
        )
        if not getattr(export_result, "success", False):
            error_text = getattr(export_result, "error_message", "") or "Не удалось создать Excel"
            self.error("Ошибка", error_text)
            return

        total_amount, currency = self._table_column_total(12)
        self.db.addHistoryEvent(
            event_type="excel",
            items_count=row_count,
            total_amount=total_amount,
            currency=currency,
            file_path=getattr(export_result, "output_path", ""),
            notes="Экспорт расчетной таблицы",
        )
        self.db.save()
        self.updateHistoryTable()

    def resourcePath(self, relativePath):
        return Tool.resourcePath(relativePath)

    def closeEvent(self, event):
        Config.config["logisticNum"] = self.ui.logisticNum.text()
        Config.config["customNum"] = self.ui.customLine.text()
        Config.config["termDelivery"] = self.ui.termDeliveryLine.text()
        Config.config["markup"] = self.ui.markupLine.text()
        Config.config["logisticVar"] = str(self.ui.logisticVar.currentIndex())
        self.ensureOutputDirs()
        self.saveConfig()
        self.db.close()
        super().closeEvent(event)

    def funcExitSystem(self):
        self.close()
