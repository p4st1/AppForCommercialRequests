from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QInputDialog,
)
from tools import DatabaseTools as Tool
from ui_settingsAppGui import Ui_MainWindow
from config import Config
from ui_theme import apply_unified_theme
from pathlib import Path


class mainWindow(QMainWindow):
    windowClosed = Signal()

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

        self.ui.autoFillCheckBox.toggled.connect(self.autoFillChange)
        self.ui.closeTableCheckBox.toggled.connect(self.closeTableChange)
        self.ui.openLastTable.toggled.connect(self.openLastTableChange)
        self.ui.openUpdateTab.toggled.connect(self.openUpdateTabChange)
        self.webAuthAutoFillCheckBox.toggled.connect(self.webAuthAutoFillChange)

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
