from functools import partial

from PySide6.QtCore import QSettings, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QAbstractItemView,
    QCheckBox,
    QColorDialog,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QInputDialog,
    QSpinBox,
    QLineEdit,
)
from tools import DatabaseTools as Tool
from ui_settingsAppGui import Ui_MainWindow
from config import Config
from ui_theme import apply_unified_theme
from pathlib import Path


class mainWindow(QMainWindow):
    windowClosed = Signal()
    AUTO_TRADE_TIMER_MIN_MINUTES = 1
    AUTO_TRADE_TIMER_MAX_MINUTES = 1440
    TABLE_SETTINGS_ORG = "MyApp"
    TABLE_SETTINGS_APP = "TableSettings"
    TABLE_FONT_MIN = 8
    TABLE_FONT_MAX = 24
    TABLE_SETTINGS_DEFAULTS = {
        "font_size": 13,
        "bg_color": "#ffffff",
        "text_color": "#000000",
        "header_color": "#f3f3f3",
        "selection_color": "#cce5ff",
        "alternating": True,
    }

    def __init__(self, parent=None):
        super(mainWindow, self).__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        apply_unified_theme(self)



        self.ui.closeTableCheckBox.setChecked(Config.settings['closeTable'])
        self.ui.autoFillCheckBox.setChecked(Config.settings['autoFill'])
        self.ui.openLastTable.setChecked(Config.settings['openLastTab'])
        self.ui.openUpdateTab.setChecked(Config.settings['openUpdateTab'])
        self._setup_web_auth_autofill_checkbox()
        self.webAuthAutoFillCheckBox.setChecked(
            bool(Config.settings.get('autoFillWebAuth', False))
        )
        self._setup_auto_trade_settings_block()
        self._setup_table_settings_block()
        self._setup_offer_validity_settings_block()
        self._setup_google_drive_settings_block()
        self._setup_tab_visibility_settings_block()
        self.developer_skip_table_fill_errors_checkbox.setChecked(
            bool(Config.settings.get('developer_skip_table_fill_errors', False))
        )
        self.skip_auto_trade_warning_checkbox.setChecked(
            bool(Config.settings.get('skip_auto_trade_warning', False))
        )
        self.use_auto_trade_timer_checkbox.setChecked(
            bool(Config.settings.get('use_auto_trade_timer', False))
        )
        timer_minutes = self._normalize_auto_trade_timer_minutes(
            Config.settings.get('auto_trade_timer_minutes', 30)
        )
        self.auto_trade_timer_minutes_spinbox.setValue(timer_minutes)
        self.auto_trade_timer_minutes_spinbox.setEnabled(
            self.use_auto_trade_timer_checkbox.isChecked()
        )
        Config.settings['auto_trade_timer_minutes'] = timer_minutes
        self._load_table_settings_into_ui()

        self.ui.autoFillCheckBox.toggled.connect(self.autoFillChange)
        self.ui.closeTableCheckBox.toggled.connect(self.closeTableChange)
        self.ui.openLastTable.toggled.connect(self.openLastTableChange)
        self.ui.openUpdateTab.toggled.connect(self.openUpdateTabChange)
        self.webAuthAutoFillCheckBox.toggled.connect(self.webAuthAutoFillChange)
        self.skip_auto_trade_warning_checkbox.toggled.connect(
            self.skipAutoTradeWarningChange
        )
        self.use_auto_trade_timer_checkbox.toggled.connect(self.useAutoTradeTimerChange)
        self.auto_trade_timer_minutes_spinbox.valueChanged.connect(
            self.autoTradeTimerMinutesChange
        )
        self.table_font_size_spinbox.valueChanged.connect(self.tableFontSizeChange)
        self.table_alternating_rows_checkbox.toggled.connect(
            self.tableAlternatingRowsChange
        )
        self.developer_skip_table_fill_errors_checkbox.toggled.connect(
            self.developerSkipTableFillErrorsChange
        )
        self.table_settings_reset_button.clicked.connect(self.resetTableSettings)
        self.offer_validity_days_spinbox.valueChanged.connect(
            self.offerValidityDaysChange
        )
        for key, checkbox in self.tab_visibility_checkboxes.items():
            checkbox.toggled.connect(partial(self.tabVisibilityChange, key))

        default_dir = Path.home() / "Documents"
        cp_dir = Tool.ensure_directory(Config.config.get('pathToSaveCP'), default_dir)
        excel_dir = Tool.ensure_directory(Config.config.get('pathToSaveExcel') or cp_dir, cp_dir)
        Config.config['pathToSaveCP'] = str(cp_dir)
        Config.config['pathToSaveExcel'] = str(excel_dir)

        self.ui.CPdirLine.setText(str(cp_dir))
        self.ui.dirOpenButton.clicked.connect(self.selectDirectory)

        self._setup_payment_templates_editor()
        self._load_payment_templates_from_config()
        self.addPaymentTemplateButton.clicked.connect(self.addPaymentTemplate)
        self.editPaymentTemplateButton.clicked.connect(self.editPaymentTemplate)
        self.deletePaymentTemplateButton.clicked.connect(self.deletePaymentTemplate)
        self.paymentTemplatesList.itemDoubleClicked.connect(self.editPaymentTemplate)

        self.ui.ExcelDirLine.setText(str(excel_dir))
        self.ui.dirOpenButton_2.clicked.connect(self.selectDirectory2)

        self.ui.excelIndent.setValue(int(Config.config['ExcelIndent']))
        self.ui.excelIndent.valueChanged.connect(self.ExcelIndentChange)

    def ExcelIndentChange(self, value):
        Config.config['ExcelIndent'] = str(value)

    def openUpdateTabChange(self, signal):
        Config.settings['openUpdateTab'] = signal

    def openLastTableChange(self, signal):
        Config.settings['openLastTab'] = signal

    def autoFillChange(self, signal):
        Config.settings['autoFill'] = signal

    def closeTableChange(self, signal):
        Config.settings['closeTable'] = signal

    def webAuthAutoFillChange(self, signal):
        Config.settings['autoFillWebAuth'] = bool(signal)

    def skipAutoTradeWarningChange(self, signal):
        Config.settings['skip_auto_trade_warning'] = bool(signal)

    def useAutoTradeTimerChange(self, signal):
        is_enabled = bool(signal)
        Config.settings['use_auto_trade_timer'] = is_enabled
        self.auto_trade_timer_minutes_spinbox.setEnabled(is_enabled)

    def autoTradeTimerMinutesChange(self, value):
        minutes = self._normalize_auto_trade_timer_minutes(value)
        Config.settings['auto_trade_timer_minutes'] = minutes

    def developerSkipTableFillErrorsChange(self, signal):
        Config.settings['developer_skip_table_fill_errors'] = bool(signal)

    def offerValidityDaysChange(self, value):
        Config.config['offerValidityDays'] = str(
            Config.normalize_offer_validity_days(value)
        )

    def tabVisibilityChange(self, key, signal):
        Config.settings[str(key)] = bool(signal)
        parent_window = self.parent()
        apply_visibility = getattr(parent_window, "_apply_main_tab_visibility", None)
        if callable(apply_visibility):
            apply_visibility()

    def _table_settings_store(self):
        return QSettings(self.TABLE_SETTINGS_ORG, self.TABLE_SETTINGS_APP)

    @staticmethod
    def _normalize_bool_setting(raw_value, default):
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, (int, float)):
            return bool(raw_value)
        if isinstance(raw_value, str):
            normalized = raw_value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        return bool(default)

    @staticmethod
    def _normalize_color_setting(raw_value, default):
        color = QColor(str(raw_value or "").strip())
        if color.isValid():
            return color.name()
        fallback = QColor(str(default or "").strip())
        if fallback.isValid():
            return fallback.name()
        return "#ffffff"

    def _read_table_settings(self):
        defaults = self.TABLE_SETTINGS_DEFAULTS
        settings = self._table_settings_store()
        font_size_raw = settings.value("font_size", defaults["font_size"])
        try:
            font_size = int(font_size_raw)
        except (TypeError, ValueError):
            font_size = int(defaults["font_size"])
        font_size = max(self.TABLE_FONT_MIN, min(self.TABLE_FONT_MAX, font_size))

        return {
            "font_size": font_size,
            "bg_color": self._normalize_color_setting(
                settings.value("bg_color", defaults["bg_color"]),
                defaults["bg_color"],
            ),
            "text_color": self._normalize_color_setting(
                settings.value("text_color", defaults["text_color"]),
                defaults["text_color"],
            ),
            "header_color": self._normalize_color_setting(
                settings.value("header_color", defaults["header_color"]),
                defaults["header_color"],
            ),
            "selection_color": self._normalize_color_setting(
                settings.value("selection_color", defaults["selection_color"]),
                defaults["selection_color"],
            ),
            "alternating": self._normalize_bool_setting(
                settings.value("alternating", defaults["alternating"]),
                defaults["alternating"],
            ),
        }

    def _write_table_settings(self):
        settings = self._table_settings_store()
        for key, value in self.table_settings_values.items():
            settings.setValue(key, value)

    def _set_table_color_button_preview(self, key):
        button = self.table_color_buttons.get(key)
        if button is None:
            return
        color_hex = self.table_settings_values.get(
            key,
            self.TABLE_SETTINGS_DEFAULTS.get(key, "#ffffff"),
        )
        color = QColor(color_hex)
        if not color.isValid():
            color_hex = self.TABLE_SETTINGS_DEFAULTS.get(key, "#ffffff")
            color = QColor(color_hex)
        text_color = "#000000" if color.lightnessF() >= 0.55 else "#ffffff"
        button.setText(color_hex)
        button.setStyleSheet(
            f"background-color: {color_hex};"
            f"color: {text_color};"
            "border: 1px solid #9e9e9e;"
            "padding: 4px;"
        )

    def _apply_table_settings_values_to_controls(self):
        font_size = int(self.table_settings_values.get("font_size", self.TABLE_SETTINGS_DEFAULTS["font_size"]))
        self.table_font_size_spinbox.blockSignals(True)
        self.table_font_size_spinbox.setValue(font_size)
        self.table_font_size_spinbox.blockSignals(False)

        alternating = bool(
            self.table_settings_values.get(
                "alternating",
                self.TABLE_SETTINGS_DEFAULTS["alternating"],
            )
        )
        self.table_alternating_rows_checkbox.blockSignals(True)
        self.table_alternating_rows_checkbox.setChecked(alternating)
        self.table_alternating_rows_checkbox.blockSignals(False)

        for key in self.table_color_buttons:
            self._set_table_color_button_preview(key)

    def _load_table_settings_into_ui(self):
        self.table_settings_values = self._read_table_settings()
        self._apply_table_settings_values_to_controls()
        self._apply_table_settings_to_open_tables()

    def _apply_table_settings_to_open_tables(self):
        parent_window = self.parent()
        refresh_method = getattr(parent_window, "refresh_retrade_table_settings", None)
        if callable(refresh_method):
            refresh_method()

    def tableFontSizeChange(self, value):
        font_size = max(self.TABLE_FONT_MIN, min(self.TABLE_FONT_MAX, int(value)))
        self.table_settings_values["font_size"] = font_size
        self._write_table_settings()
        self._apply_table_settings_to_open_tables()

    def tableAlternatingRowsChange(self, signal):
        self.table_settings_values["alternating"] = bool(signal)
        self._write_table_settings()
        self._apply_table_settings_to_open_tables()

    def selectTableColor(self, key):
        current_color = self.table_settings_values.get(
            key,
            self.TABLE_SETTINGS_DEFAULTS.get(key, "#ffffff"),
        )
        selected_color = QColorDialog.getColor(QColor(current_color), self, "Выберите цвет")
        if not selected_color.isValid():
            return

        self.table_settings_values[key] = selected_color.name()
        self._set_table_color_button_preview(key)
        self._write_table_settings()
        self._apply_table_settings_to_open_tables()

    def resetTableSettings(self):
        self.table_settings_values = self.TABLE_SETTINGS_DEFAULTS.copy()
        self._apply_table_settings_values_to_controls()
        self._write_table_settings()
        self._apply_table_settings_to_open_tables()

    @staticmethod
    def _normalize_auto_trade_timer_minutes(raw_value):
        default_minutes = int(Config.DEFAULT_SETTINGS.get('auto_trade_timer_minutes', 30))
        try:
            minutes = int(raw_value)
        except (TypeError, ValueError):
            minutes = default_minutes
        return max(
            mainWindow.AUTO_TRADE_TIMER_MIN_MINUTES,
            min(mainWindow.AUTO_TRADE_TIMER_MAX_MINUTES, minutes),
        )

    def _setup_web_auth_autofill_checkbox(self):
        checkbox = QCheckBox(
            "Автоматически заполнять логин и пароль",
            self.ui.scrollAreaWidgetContents,
        )
        checkbox.setObjectName("webAuthAutoFillCheckBox")
        checkbox.setStyleSheet(self.ui.openUpdateTab.styleSheet())
        checkbox.setFont(self.ui.openUpdateTab.font())

        insert_index = self.ui.verticalLayout.indexOf(self.ui.line)
        if insert_index < 0:
            insert_index = self.ui.verticalLayout.count()
        self.ui.verticalLayout.insertWidget(insert_index, checkbox)
        self.webAuthAutoFillCheckBox = checkbox
        self.ui.webAuthAutoFillCheckBox = checkbox

    def _setup_auto_trade_settings_block(self):
        section_label = QLabel(
            "Настройки автоматических торгов",
            self.ui.scrollAreaWidgetContents,
        )
        section_label.setStyleSheet(
            "color: #2c3e50;\n"
            "font-size: 16px;\n"
            "font-weight: 600;\n"
            "padding: 2px;"
        )

        skip_checkbox = QCheckBox(
            "Больше не показывать предупреждение",
            self.ui.scrollAreaWidgetContents,
        )
        skip_checkbox.setObjectName("skipAutoTradeWarningCheckbox")
        skip_checkbox.setStyleSheet(self.ui.openUpdateTab.styleSheet())
        skip_checkbox.setFont(self.ui.openUpdateTab.font())

        timer_checkbox = QCheckBox(
            "Использовать таймер торгов",
            self.ui.scrollAreaWidgetContents,
        )
        timer_checkbox.setObjectName("useAutoTradeTimerCheckbox")
        timer_checkbox.setStyleSheet(self.ui.openUpdateTab.styleSheet())
        timer_checkbox.setFont(self.ui.openUpdateTab.font())

        timer_layout = QHBoxLayout()
        timer_layout.setSpacing(10)
        timer_layout.setContentsMargins(7, 0, -1, -1)

        timer_label = QLabel("Включить на (мин):", self.ui.scrollAreaWidgetContents)
        timer_spinbox = QSpinBox(self.ui.scrollAreaWidgetContents)
        timer_spinbox.setObjectName("autoTradeTimerMinutesSpinBox")
        timer_spinbox.setMinimum(self.AUTO_TRADE_TIMER_MIN_MINUTES)
        timer_spinbox.setMaximum(self.AUTO_TRADE_TIMER_MAX_MINUTES)
        timer_spinbox.setValue(
            int(Config.DEFAULT_SETTINGS.get('auto_trade_timer_minutes', 30))
        )
        timer_spinbox.setSuffix(" мин")

        timer_layout.addWidget(timer_label)
        timer_layout.addWidget(timer_spinbox)
        timer_layout.addStretch(1)

        insert_index = self.ui.verticalLayout.indexOf(self.ui.line)
        if insert_index < 0:
            insert_index = self.ui.verticalLayout.count()

        self.ui.verticalLayout.insertLayout(insert_index, timer_layout)
        self.ui.verticalLayout.insertWidget(insert_index, timer_checkbox)
        self.ui.verticalLayout.insertWidget(insert_index, skip_checkbox)
        self.ui.verticalLayout.insertWidget(insert_index, section_label)

        self.auto_trade_settings_label = section_label
        self.skip_auto_trade_warning_checkbox = skip_checkbox
        self.use_auto_trade_timer_checkbox = timer_checkbox
        self.auto_trade_timer_minutes_spinbox = timer_spinbox
        self.ui.skip_auto_trade_warning_checkbox = skip_checkbox
        self.ui.use_auto_trade_timer_checkbox = timer_checkbox
        self.ui.auto_trade_timer_minutes_spinbox = timer_spinbox

    def _setup_table_settings_block(self):
        section_widget = QLabel("Настройки таблиц", self.ui.scrollAreaWidgetContents)
        section_widget.setStyleSheet(
            "color: #2c3e50;\n"
            "font-size: 16px;\n"
            "font-weight: 600;\n"
            "padding: 2px;"
        )

        container = QVBoxLayout()
        container.setSpacing(8)
        container.setContentsMargins(0, 0, 0, 0)

        font_row = QHBoxLayout()
        font_row.setSpacing(10)
        font_row.setContentsMargins(7, 0, -1, -1)
        font_label = QLabel("Размер шрифта:", self.ui.scrollAreaWidgetContents)
        font_spinbox = QSpinBox(self.ui.scrollAreaWidgetContents)
        font_spinbox.setObjectName("tableFontSizeSpinBox")
        font_spinbox.setMinimum(self.TABLE_FONT_MIN)
        font_spinbox.setMaximum(self.TABLE_FONT_MAX)
        font_spinbox.setValue(int(self.TABLE_SETTINGS_DEFAULTS["font_size"]))
        font_row.addWidget(font_label)
        font_row.addWidget(font_spinbox)
        font_row.addStretch(1)
        container.addLayout(font_row)

        button_style = self.ui.dirOpenButton.styleSheet()
        color_controls = [
            ("Цвет фона ячеек:", "bg_color", "tableBgColorButton"),
            ("Цвет текста:", "text_color", "tableTextColorButton"),
            ("Цвет заголовка:", "header_color", "tableHeaderColorButton"),
            ("Цвет выделения:", "selection_color", "tableSelectionColorButton"),
        ]
        self.table_color_buttons = {}
        for title, key, object_name in color_controls:
            row = QHBoxLayout()
            row.setSpacing(10)
            row.setContentsMargins(7, 0, -1, -1)
            label = QLabel(title, self.ui.scrollAreaWidgetContents)
            button = QPushButton(self.ui.scrollAreaWidgetContents)
            button.setObjectName(object_name)
            button.setMinimumSize(120, 32)
            button.setStyleSheet(button_style)
            button.clicked.connect(partial(self.selectTableColor, key))
            row.addWidget(label)
            row.addWidget(button)
            row.addStretch(1)
            container.addLayout(row)
            self.table_color_buttons[key] = button

        alternating_checkbox = QCheckBox(
            "Чередование строк",
            self.ui.scrollAreaWidgetContents,
        )
        alternating_checkbox.setObjectName("tableAlternatingRowsCheckBox")
        alternating_checkbox.setStyleSheet(self.ui.openUpdateTab.styleSheet())
        alternating_checkbox.setFont(self.ui.openUpdateTab.font())
        container.addWidget(alternating_checkbox)

        developer_skip_checkbox = QCheckBox(
            "Для разработчика: пропускать ошибки заполнения таблиц",
            self.ui.scrollAreaWidgetContents,
        )
        developer_skip_checkbox.setObjectName("developerSkipTableFillErrorsCheckBox")
        developer_skip_checkbox.setStyleSheet(self.ui.openUpdateTab.styleSheet())
        developer_skip_checkbox.setFont(self.ui.openUpdateTab.font())
        developer_skip_checkbox.setToolTip(
            "Если включено, ошибки автозаполнения и проверки таблиц будут "
            "записаны в лог, но не остановят workflow."
        )
        container.addWidget(developer_skip_checkbox)

        reset_button = QPushButton("Сбросить настройки", self.ui.scrollAreaWidgetContents)
        reset_button.setObjectName("resetTableSettingsButton")
        reset_button.setMinimumSize(180, 32)
        reset_button.setStyleSheet(button_style)
        container.addWidget(reset_button)

        insert_index = self.ui.verticalLayout.indexOf(self.ui.line_2)
        if insert_index < 0:
            insert_index = self.ui.verticalLayout.count()
        self.ui.verticalLayout.insertLayout(insert_index, container)
        self.ui.verticalLayout.insertWidget(insert_index, section_widget)

        self.table_settings_label = section_widget
        self.table_settings_layout = container
        self.table_font_size_spinbox = font_spinbox
        self.table_alternating_rows_checkbox = alternating_checkbox
        self.developer_skip_table_fill_errors_checkbox = developer_skip_checkbox
        self.table_settings_reset_button = reset_button
        self.table_settings_values = self.TABLE_SETTINGS_DEFAULTS.copy()
        self.ui.table_settings_label = section_widget
        self.ui.table_font_size_spinbox = font_spinbox
        self.ui.table_alternating_rows_checkbox = alternating_checkbox
        self.ui.developer_skip_table_fill_errors_checkbox = developer_skip_checkbox
        self.ui.table_settings_reset_button = reset_button

    def _setup_offer_validity_settings_block(self):
        section_label = QLabel("Настройки КП", self.ui.scrollAreaWidgetContents)
        section_label.setStyleSheet(
            "color: #2c3e50;\n"
            "font-size: 16px;\n"
            "font-weight: 600;\n"
            "padding: 2px;"
        )

        row = QHBoxLayout()
        row.setSpacing(10)
        row.setContentsMargins(7, 0, -1, -1)

        label = QLabel("Срок действия КП, дней:", self.ui.scrollAreaWidgetContents)
        spinbox = QSpinBox(self.ui.scrollAreaWidgetContents)
        spinbox.setObjectName("offerValidityDaysSpinBox")
        spinbox.setMinimum(Config.OFFER_VALIDITY_MIN_DAYS)
        spinbox.setMaximum(Config.OFFER_VALIDITY_MAX_DAYS)
        spinbox.setValue(Config.get_offer_validity_days())
        spinbox.setSuffix(" дн.")

        row.addWidget(label)
        row.addWidget(spinbox)
        row.addStretch(1)

        insert_index = self.ui.verticalLayout.indexOf(self.ui.line_2)
        if insert_index < 0:
            insert_index = self.ui.verticalLayout.count()
        self.ui.verticalLayout.insertLayout(insert_index, row)
        self.ui.verticalLayout.insertWidget(insert_index, section_label)

        self.offer_validity_settings_label = section_label
        self.offer_validity_days_spinbox = spinbox
        self.ui.offer_validity_settings_label = section_label
        self.ui.offer_validity_days_spinbox = spinbox

    def _setup_google_drive_settings_block(self):
        section_label = QLabel("Google Drive", self.ui.scrollAreaWidgetContents)
        section_label.setStyleSheet(
            "color: #2c3e50;\n"
            "font-size: 16px;\n"
            "font-weight: 600;\n"
            "padding: 2px;"
        )

        controls = QVBoxLayout()
        controls.setSpacing(8)
        controls.setContentsMargins(0, 0, 0, 0)

        credentials_row = QHBoxLayout()
        credentials_row.setSpacing(10)
        credentials_row.setContentsMargins(7, 0, -1, -1)
        credentials_label = QLabel("OAuth JSON:", self.ui.scrollAreaWidgetContents)
        self.googleDriveCredentialsLine = QLineEdit(self.ui.scrollAreaWidgetContents)
        self.googleDriveCredentialsLine.setObjectName("googleDriveCredentialsLine")
        self.googleDriveCredentialsLine.setText(
            str(Config.config.get("googleDriveCredentialsPath", "") or "")
        )
        self.googleDriveCredentialsLine.setPlaceholderText("Путь к OAuth client JSON")
        self.googleDriveCredentialsBrowseButton = QPushButton(
            "Выбрать",
            self.ui.scrollAreaWidgetContents,
        )
        self.googleDriveCredentialsBrowseButton.setMinimumSize(108, 32)
        self.googleDriveCredentialsBrowseButton.setStyleSheet(
            self.ui.dirOpenButton.styleSheet()
        )
        credentials_row.addWidget(credentials_label)
        credentials_row.addWidget(self.googleDriveCredentialsLine, 1)
        credentials_row.addWidget(self.googleDriveCredentialsBrowseButton)
        controls.addLayout(credentials_row)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(10)
        folder_row.setContentsMargins(7, 0, -1, -1)
        folder_label = QLabel("ID папки:", self.ui.scrollAreaWidgetContents)
        self.googleDriveFolderIdLine = QLineEdit(self.ui.scrollAreaWidgetContents)
        self.googleDriveFolderIdLine.setObjectName("googleDriveFolderIdLine")
        self.googleDriveFolderIdLine.setText(
            str(Config.config.get("googleDriveFolderId", "") or "")
        )
        self.googleDriveFolderIdLine.setPlaceholderText(
            "Необязательно: оставить пустым для корня My Drive"
        )
        folder_row.addWidget(folder_label)
        folder_row.addWidget(self.googleDriveFolderIdLine, 1)
        controls.addLayout(folder_row)

        self.googleDriveCredentialsLine.textChanged.connect(
            self.googleDriveCredentialsPathChange
        )
        self.googleDriveFolderIdLine.textChanged.connect(self.googleDriveFolderIdChange)
        self.googleDriveCredentialsBrowseButton.clicked.connect(
            self.selectGoogleDriveCredentialsFile
        )

        insert_index = self.ui.verticalLayout.indexOf(self.ui.line_2)
        if insert_index < 0:
            insert_index = self.ui.verticalLayout.count()
        self.ui.verticalLayout.insertLayout(insert_index, controls)
        self.ui.verticalLayout.insertWidget(insert_index, section_label)

        self.google_drive_settings_label = section_label
        self.ui.google_drive_settings_label = section_label
        self.ui.googleDriveCredentialsLine = self.googleDriveCredentialsLine
        self.ui.googleDriveFolderIdLine = self.googleDriveFolderIdLine
        self.ui.googleDriveCredentialsBrowseButton = self.googleDriveCredentialsBrowseButton

    def googleDriveCredentialsPathChange(self, value):
        Config.config["googleDriveCredentialsPath"] = str(value or "").strip()

    def googleDriveFolderIdChange(self, value):
        Config.config["googleDriveFolderId"] = str(value or "").strip()

    def selectGoogleDriveCredentialsFile(self):
        current_path = str(Config.config.get("googleDriveCredentialsPath", "") or "").strip()
        start_dir = str(Path(current_path).expanduser().parent) if current_path else str(Path.home())
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите OAuth JSON Google Drive",
            start_dir,
            "JSON (*.json)",
        )
        if not file_path:
            return
        self.googleDriveCredentialsLine.setText(file_path)

    def _setup_tab_visibility_settings_block(self):
        section_label = QLabel("Видимость вкладок", self.ui.scrollAreaWidgetContents)
        section_label.setStyleSheet(
            "color: #2c3e50;\n"
            "font-size: 16px;\n"
            "font-weight: 600;\n"
            "padding: 2px;"
        )

        controls = QVBoxLayout()
        controls.setSpacing(6)
        controls.setContentsMargins(7, 0, -1, -1)

        items = (
            ("show_retrade_tab", "Показывать вкладку «Переторжка»"),
            ("show_platform_tab", "Показывать вкладку «Прием заявок»"),
            ("show_submission_tab", "Показывать вкладку «Подача заявки»"),
            ("show_history_tab", "Показывать вкладку «История»"),
            ("show_updates_tab", "Показывать вкладку «Обновления»"),
        )
        self.tab_visibility_checkboxes = {}
        for key, caption in items:
            checkbox = QCheckBox(caption, self.ui.scrollAreaWidgetContents)
            checkbox.setObjectName(f"{key}CheckBox")
            checkbox.setStyleSheet(self.ui.openUpdateTab.styleSheet())
            checkbox.setFont(self.ui.openUpdateTab.font())
            checkbox.setChecked(bool(Config.settings.get(key, True)))
            controls.addWidget(checkbox)
            self.tab_visibility_checkboxes[key] = checkbox
            setattr(self.ui, f"{key}_checkbox", checkbox)

        insert_index = self.ui.verticalLayout.indexOf(self.ui.line_2)
        if insert_index < 0:
            insert_index = self.ui.verticalLayout.count()
        self.ui.verticalLayout.insertLayout(insert_index, controls)
        self.ui.verticalLayout.insertWidget(insert_index, section_label)

        self.tab_visibility_settings_label = section_label
        self.ui.tab_visibility_settings_label = section_label

    def _setup_payment_templates_editor(self):
        self.paymentTemplatesLabel = QLabel("Шаблоны оплаты", self.ui.scrollAreaWidgetContents)
        self.paymentTemplatesLabel.setStyleSheet(
            "color: #2c3e50;\n"
            "font-size: 16px;\n"
            "padding: 2px;"
        )

        self.paymentTemplatesList = QListWidget(self.ui.scrollAreaWidgetContents)
        self.paymentTemplatesList.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.paymentTemplatesList.setMinimumHeight(120)

        self.paymentTemplatesButtonsLayout = QHBoxLayout()
        self.paymentTemplatesButtonsLayout.setSpacing(10)
        self.paymentTemplatesButtonsLayout.setContentsMargins(7, 0, -1, -1)

        button_style = self.ui.dirOpenButton.styleSheet()
        self.addPaymentTemplateButton = QPushButton("Добавить", self.ui.scrollAreaWidgetContents)
        self.editPaymentTemplateButton = QPushButton("Изменить", self.ui.scrollAreaWidgetContents)
        self.deletePaymentTemplateButton = QPushButton("Удалить", self.ui.scrollAreaWidgetContents)
        for button in (
            self.addPaymentTemplateButton,
            self.editPaymentTemplateButton,
            self.deletePaymentTemplateButton,
        ):
            button.setMinimumSize(108, 32)
            button.setStyleSheet(button_style)
            self.paymentTemplatesButtonsLayout.addWidget(button)
        self.paymentTemplatesButtonsLayout.addStretch(1)

        insert_index = self.ui.verticalLayout.indexOf(self.ui.line_2)
        if insert_index < 0:
            insert_index = self.ui.verticalLayout.count()

        self.ui.verticalLayout.insertLayout(insert_index, self.paymentTemplatesButtonsLayout)
        self.ui.verticalLayout.insertWidget(insert_index, self.paymentTemplatesList)
        self.ui.verticalLayout.insertWidget(insert_index, self.paymentTemplatesLabel)

    def _normalize_payment_templates(self, templates_raw):
        if isinstance(templates_raw, str):
            values = [templates_raw]
        elif isinstance(templates_raw, (list, tuple)):
            values = list(templates_raw)
        else:
            values = []

        templates = []
        for value in values:
            text = str(value or "").strip()
            if not text or text in templates:
                continue
            templates.append(text)
        return templates

    def _load_payment_templates_from_config(self):
        has_key = 'paymentTemplates' in Config.config
        templates = self._normalize_payment_templates(Config.config.get('paymentTemplates'))
        if not templates and not has_key:
            templates = Config.DEFAULT_PAYMENT_TEMPLATES.copy()
        Config.config['paymentTemplates'] = templates

        self.paymentTemplatesList.clear()
        for template in templates:
            self.paymentTemplatesList.addItem(template)
        if self.paymentTemplatesList.count() > 0:
            self.paymentTemplatesList.setCurrentRow(0)

    def _collect_payment_templates(self):
        templates = []
        for row in range(self.paymentTemplatesList.count()):
            item = self.paymentTemplatesList.item(row)
            if item is None:
                continue
            text = item.text().strip()
            if not text or text in templates:
                continue
            templates.append(text)
        return templates

    def _save_payment_templates_to_config(self):
        Config.config['paymentTemplates'] = self._collect_payment_templates()

    def _template_exists(self, candidate_text, *, skip_row=None):
        normalized_candidate = str(candidate_text or "").strip().casefold()
        if not normalized_candidate:
            return False
        for row in range(self.paymentTemplatesList.count()):
            if row == skip_row:
                continue
            item = self.paymentTemplatesList.item(row)
            if item is None:
                continue
            if item.text().strip().casefold() == normalized_candidate:
                return True
        return False

    def addPaymentTemplate(self):
        text, ok = QInputDialog.getText(
            self,
            "Добавление шаблона",
            "Введите текст шаблона оплаты:",
        )
        if not ok:
            return
        normalized = str(text or "").strip()
        if not normalized:
            QMessageBox.warning(self, "Ошибка", "Шаблон оплаты не может быть пустым.")
            return
        if self._template_exists(normalized):
            QMessageBox.warning(self, "Ошибка", "Такой шаблон уже существует.")
            return
        self.paymentTemplatesList.addItem(normalized)
        self.paymentTemplatesList.setCurrentRow(self.paymentTemplatesList.count() - 1)
        self._save_payment_templates_to_config()

    def editPaymentTemplate(self, _item=None):
        row = self.paymentTemplatesList.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон для редактирования.")
            return

        current_item = self.paymentTemplatesList.item(row)
        current_text = current_item.text() if current_item is not None else ""
        text, ok = QInputDialog.getText(
            self,
            "Редактирование шаблона",
            "Измените текст шаблона оплаты:",
            text=current_text,
        )
        if not ok:
            return

        normalized = str(text or "").strip()
        if not normalized:
            QMessageBox.warning(self, "Ошибка", "Шаблон оплаты не может быть пустым.")
            return
        if self._template_exists(normalized, skip_row=row):
            QMessageBox.warning(self, "Ошибка", "Такой шаблон уже существует.")
            return

        if current_item is not None:
            current_item.setText(normalized)
        self._save_payment_templates_to_config()

    def deletePaymentTemplate(self):
        row = self.paymentTemplatesList.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон для удаления.")
            return

        current_item = self.paymentTemplatesList.item(row)
        template_text = current_item.text().strip() if current_item else ""
        button = QMessageBox.question(
            self,
            "Удаление шаблона",
            f'Удалить шаблон "{template_text}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if button != QMessageBox.StandardButton.Yes:
            return

        self.paymentTemplatesList.takeItem(row)
        if self.paymentTemplatesList.count() > 0:
            self.paymentTemplatesList.setCurrentRow(min(row, self.paymentTemplatesList.count() - 1))
        self._save_payment_templates_to_config()

    def selectDirectory(self):
        current_dir = Config.config.get('pathToSaveCP', str(Path.home()))
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите директорию",
            current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if directory:
            Config.config['pathToSaveCP'] = directory
            if not Config.config.get('pathToSaveExcel'):
                Config.config['pathToSaveExcel'] = directory
                self.ui.ExcelDirLine.setText(directory)
            self.ui.CPdirLine.setText(directory)

    def selectDirectory2(self):
        current_dir = Config.config.get('pathToSaveExcel', Config.config.get('pathToSaveCP', str(Path.home())))
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите директорию",
            current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if directory:
            Config.config['pathToSaveExcel'] = directory
            self.ui.ExcelDirLine.setText(directory)

    def resourcePath(self, relativePath):
        return Tool.resourcePath(relativePath)

    def closeEvent(self, event):
        default_dir = Path.home() / "Documents"
        cp_dir = Tool.ensure_directory(Config.config.get('pathToSaveCP'), default_dir)
        excel_dir = Tool.ensure_directory(Config.config.get('pathToSaveExcel') or cp_dir, cp_dir)
        Config.config['pathToSaveCP'] = str(cp_dir)
        Config.config['pathToSaveExcel'] = str(excel_dir)
        self._save_payment_templates_to_config()

        data = {'config' : Config.config,
                'settings' : Config.settings}
        cookies_raw = Config.config.get("cookies")
        if isinstance(cookies_raw, dict):
            cookies = {
                str(key): str(value)
                for key, value in cookies_raw.items()
                if str(key).strip() and str(value).strip()
            }
            if cookies:
                data["cookies"] = cookies

        Tool.save_json_atomic(Config.cfg_path, data)
        self.windowClosed.emit()
        super().closeEvent(event)

    def funcExitSystem(self):
        self.close()
