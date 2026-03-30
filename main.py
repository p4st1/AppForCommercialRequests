from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QStyledItemDelegate,
    QHeaderView,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
)
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtCore import Qt, QUrl, QSignalBlocker, QTimer
from createDocument import mainWindow as createDocWindow
from create import createExcelFile as exportExcelFile
from customers import mainWindow as customersWindow
from settings import mainWindow as settingsWindow
from app.models.calculation_models import CalculationRowInput, CalculationSettings
from app.repositories.offer_repository import OfferRepository
from app.services.calculation_service import CalculationService
from app.services.history_service import HistoryService
from app.services.proposal_import_service import ProposalImportService
from app.ui.formula_config_mixin import FormulaConfigMixin
from app.ui.formula_editing_mixin import FormulaEditingMixin
from app.ui.table_cell_edit_mixin import TableCellEditMixin
from app.ui.shortcut_mixin import ShortcutMixin
from app.ui.table_row_actions_mixin import TableRowActionsMixin
from app.ui.table_undo_mixin import TableUndoMixin
from app.ui.table_search_mixin import TableSearchMixin
from app.ui.table_filter_mixin import TableFilterMixin
from app.ui.history_flow_mixin import HistoryFlowMixin
from app.services.web_parser_service import WebPageParser
from app.ui.web_flow_mixin import WebFlowMixin
from tools import DatabaseTools as Tool
from params import mainWindow as paramsWindow
from database import Database
from config import Config
from ui_mainGui import Ui_MainWindow
from ui_theme import apply_unified_theme
from datetime import datetime
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
import shutil
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


class mainWindow(
    ShortcutMixin,
    TableUndoMixin,
    FormulaConfigMixin,
    FormulaEditingMixin,
    TableCellEditMixin,
    TableRowActionsMixin,
    TableSearchMixin,
    TableFilterMixin,
    HistoryFlowMixin,
    WebFlowMixin,
    QMainWindow,
):
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
        self.calculation_service = CalculationService()
        self.proposal_import_service = ProposalImportService()
        self.web_page_parser = WebPageParser()
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
        self._web_request_number = ""
        self._web_request_search_pending = False
        self._web_request_search_attempts_left = 0
        self._web_request_search_total_attempts = 0
        self._web_request_search_js_running = False
        self._formula_fill_highlight_cells = []
        self._formula_fill_highlight_timer = QTimer(self)
        self._formula_fill_highlight_timer.setSingleShot(True)
        self._formula_fill_highlight_timer.timeout.connect(self._clear_formula_fill_highlight)

        self.loadConfig()
        self.ensureOutputDirs()

        self.db = Database()
        if self.db.open(Config.db_path) == -1:
            self.error("Ошибка", "Не удалось открыть базу данных")
        self.offer_repository = OfferRepository(self.db)
        self.history_service = HistoryService(self.offer_repository)

        if Config.settings["autoFill"]:
            self.ui.logisticNum.setText(Config.config["logisticNum"])
            self.ui.customLine.setText(Config.config["customNum"])
            self.ui.termDeliveryLine.setText(Config.config["termDelivery"])
            self.ui.markupLine.setText(Config.config["markup"])
            self.ui.requestNumberLine.setText(Config.config.get("requestNumber", ""))
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
        self.ui.KpTable.itemSelectionChanged.connect(self._fill_formula_on_ctrl_selection)
        self.ui.KpTable.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.ui.KpTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.ui.KpTable.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
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
        self._setup_full_table_input_layout()
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

    def _clear_layout_items(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                continue
            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout_items(child_layout)

    @staticmethod
    def _input_block(label_widget, *input_widgets):
        block = QVBoxLayout()
        block.setSpacing(6)
        block.setContentsMargins(0, 0, 0, 0)
        block.addWidget(label_widget)
        for widget in input_widgets:
            block.addWidget(widget)
        return block

    def _setup_full_table_input_layout(self):
        self.ui.verticalLayout.setSpacing(0)
        root_layout = self.ui.funcButtons
        self._clear_layout_items(root_layout)
        root_layout.setContentsMargins(8, 0, 8, 8)
        root_layout.setHorizontalSpacing(14)
        root_layout.setVerticalSpacing(8)

        labels = (
            self.ui.label_5,
            self.ui.label,
            self.ui.label_3,
            self.ui.label_2,
            self.ui.requestNumberLabel,
        )
        for label in labels:
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        inputs = (
            self.ui.logisticNum,
            self.ui.customLine,
            self.ui.markupLine,
            self.ui.termDeliveryLine,
            self.ui.requestNumberLine,
        )
        for field in inputs:
            field.setMinimumHeight(32)
            field.setClearButtonEnabled(True)

        self.ui.logisticVar.setMinimumHeight(32)
        self.ui.logisticVar.setMinimumWidth(170)
        self.ui.logisticNum.setMinimumWidth(120)
        self.ui.customLine.setMinimumWidth(140)
        self.ui.markupLine.setMinimumWidth(140)
        self.ui.termDeliveryLine.setMinimumWidth(140)
        self.ui.requestNumberLine.setMinimumWidth(260)

        logistics_row = QHBoxLayout()
        logistics_row.setSpacing(8)
        logistics_row.setContentsMargins(0, 0, 0, 0)
        logistics_row.addWidget(self.ui.logisticVar, 2)
        logistics_row.addWidget(self.ui.logisticNum, 1)

        logistics_block = QVBoxLayout()
        logistics_block.setSpacing(6)
        logistics_block.setContentsMargins(0, 0, 0, 0)
        logistics_block.addWidget(self.ui.label_5)
        logistics_block.addLayout(logistics_row)

        customs_block = self._input_block(self.ui.label, self.ui.customLine)
        markup_block = self._input_block(self.ui.label_3, self.ui.markupLine)
        term_block = self._input_block(self.ui.label_2, self.ui.termDeliveryLine)
        request_block = self._input_block(self.ui.requestNumberLabel, self.ui.requestNumberLine)

        inputs_layout = QGridLayout()
        inputs_layout.setContentsMargins(0, 0, 0, 0)
        inputs_layout.setHorizontalSpacing(14)
        inputs_layout.setVerticalSpacing(10)
        inputs_layout.addLayout(logistics_block, 0, 0)
        inputs_layout.addLayout(customs_block, 0, 1)
        inputs_layout.addLayout(markup_block, 0, 2)
        inputs_layout.addLayout(term_block, 1, 0)
        inputs_layout.addLayout(request_block, 1, 1, 1, 2)
        inputs_layout.setColumnStretch(0, 3)
        inputs_layout.setColumnStretch(1, 2)
        inputs_layout.setColumnStretch(2, 2)

        actions_layout = QGridLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setHorizontalSpacing(8)
        actions_layout.setVerticalSpacing(8)
        actions_layout.addWidget(self.ui.openTableButton, 0, 0)
        actions_layout.addWidget(self.ui.closeTableButton, 0, 1)
        actions_layout.addWidget(self.ui.createExcelButton, 1, 0)
        actions_layout.addWidget(self.ui.createDocButton, 1, 1)
        actions_layout.addWidget(self.ui.createDocFromExcelButton, 2, 0, 1, 2)

        root_layout.addLayout(inputs_layout, 0, 0)
        root_layout.addLayout(actions_layout, 0, 1, 1, 1, Qt.AlignmentFlag.AlignTop)
        root_layout.setColumnStretch(0, 1)
        root_layout.setColumnStretch(1, 0)

        for widget in (
            self.ui.label_5,
            self.ui.logisticVar,
            self.ui.logisticNum,
            self.ui.label,
            self.ui.customLine,
            self.ui.label_3,
            self.ui.markupLine,
            self.ui.label_2,
            self.ui.termDeliveryLine,
            self.ui.requestNumberLabel,
            self.ui.requestNumberLine,
            self.ui.openTableButton,
            self.ui.closeTableButton,
            self.ui.createExcelButton,
            self.ui.createDocButton,
            self.ui.createDocFromExcelButton,
        ):
            widget.show()

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
            self.ui.requestNumberLine.setText(Config.config.get("requestNumber", ""))
            self.ui.logisticVar.setCurrentIndex(int(Config.config["logisticVar"]))
        if hasattr(self.ui, "webRequestNumberLine"):
            self.ui.webRequestNumberLine.setText(
                str(
                    Config.config.get(
                        "webRequestNumber",
                        Config.config.get("requestNumber", ""),
                    )
                    or ""
                ).strip()
            )
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
            <li><span class="hotkey">Ctrl+Enter</span> - протянуть формулу по выделенным строкам</li>
            <li><span class="hotkey">Ctrl + выделение ячеек</span> - протянуть формулу из активной ячейки</li>
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

    @staticmethod
    def _round_money(value) -> float:
        return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

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
            parsed_rows, warnings = self.proposal_import_service.load_source_rows(filename)
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
            total_price = self._round_money(row["qty"] * row["unitPrice"])
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
        window.ui.numLine.setText(self.ui.requestNumberLine.text().strip())
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
        self._clear_formula_fill_highlight()
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
        return self.calculation_service.vat_multiplier_from_parameters(
            params_data,
            log_exception=Tool.log_exception,
        )

    def calculating(self):
        if not self.tableData["amount"] or not self.tableData["logistic"]:
            return

        for col in self.FORMULA_EDITABLE_COLUMNS:
            if len(self.formulaExpressions.get(col, [])) != self.rows:
                self._init_formula_expressions()
                break

        named_parameters = self._load_formula_parameters()
        vat_multiplier = self._vat_multiplier()
        calculation_settings = CalculationSettings(
            custom=float(self.formulaCustom),
            markup=float(self.formulaMarkup),
            vat_multiplier=float(vat_multiplier),
            term_delivery_days=int(self.termDeliveryDays),
        )
        blocker = QSignalBlocker(self.ui.KpTable)
        for row_num in range(self.rows):
            row_input = CalculationRowInput(
                amount=float(self.tableData["amount"][row_num]),
                unit_price=float(self.tableData["unitPrice"][row_num]),
                total_price=float(self.tableData["totalPrice"][row_num]),
                currency=str(self.tableData["currency"][row_num]),
                logistic_value=float(self.tableData["logistic"][row_num]),
                supplier_term=float(self.tableData["termDelivery"][row_num]),
            )
            row_formulas = {
                8: self.formulaExpressions[8][row_num],
                9: self.formulaExpressions[9][row_num],
                10: self.formulaExpressions[10][row_num],
                11: self.formulaExpressions[11][row_num],
                13: self.formulaExpressions[13][row_num],
            }
            row_result = self.calculation_service.calculate_row(
                row_index=row_num,
                row_input=row_input,
                formulas=row_formulas,
                named_parameters=named_parameters,
                settings=calculation_settings,
                column_title_resolver=self._column_title,
            )
            currency = row_input.currency

            self._set_table_item(
                row_num,
                8,
                Tool.formatPrice(str(row_result.customs_sum), currency),
                editable=True,
            )
            self._set_table_item(
                row_num,
                9,
                Tool.formatPrice(str(row_result.unit_sale_price), currency),
                editable=True,
            )
            self._set_table_item(
                row_num,
                10,
                Tool.formatPrice(str(row_result.real_price), currency),
                editable=True,
            )
            self._set_table_item(
                row_num,
                11,
                Tool.formatPrice(str(row_result.total_without_vat), currency),
                editable=True,
            )
            self._set_table_item(
                row_num,
                12,
                Tool.formatPrice(str(row_result.total_with_vat), currency),
                editable=False,
            )
            self._set_table_item(
                row_num,
                13,
                f"{row_result.total_delivery_days} дней",
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
        logistic_num_text = self._fmt_number(logistic_num)
        total_sum = sum(self.tableData["totalPrice"])
        total_sum_text = self._fmt_number(total_sum)
        self.tableData["logistic"] = []

        blocker = QSignalBlocker(self.ui.KpTable)
        for row_num in range(self.rows):
            base_total = self.tableData["totalPrice"][row_num]
            if logistic_var == 1:
                if total_sum <= 0:
                    f = 0
                    formula_text = "0"
                else:
                    f = self._round_money(base_total + logistic_num / total_sum * base_total)
                    formula_text = f"TotalPrice+{logistic_num_text}/{total_sum_text}*TotalPrice"
            else:
                f = self._round_money(base_total * logistic_num)
                formula_text = f"TotalPrice*{logistic_num_text}"
            currency = self.tableData["currency"][row_num]
            self._set_table_item(
                row_num,
                7,
                Tool.formatPrice(str(f), currency),
                editable=False,
            )
            logistic_item = self.ui.KpTable.item(row_num, 7)
            if logistic_item is not None:
                logistic_item.setData(Qt.ItemDataRole.UserRole, formula_text)
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
        return self._round_money(total), currency

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

        parsed = self._parse_input_parameters(show_error=True)
        if parsed is None:
            return

        tableData = []
        logistic_formulas = []
        row_count = self.ui.KpTable.rowCount()
        column_count = self.ui.KpTable.columnCount()

        for row in range(row_count):
            row_data = []
            for col in range(column_count):
                item = self.ui.KpTable.item(row, col)
                row_data.append(item.text() if item is not None else "")
            tableData.append(row_data)
            logistic_item = self.ui.KpTable.item(row, 7)
            logistic_formula = logistic_item.data(Qt.ItemDataRole.UserRole) if logistic_item is not None else ""
            if isinstance(logistic_formula, dict):
                logistic_formula = logistic_formula.get("formula", "")
            logistic_formulas.append(str(logistic_formula or ""))

        export_result = exportExcelFile(
            {
                "table_rows": tableData,
                "request_number": self.ui.requestNumberLine.text().strip(),
                "logistic_mode": self.ui.logisticVar.currentIndex(),
                "logistic_value": parsed["logistic"],
                "custom_value": parsed["custom"],
                "markup_value": parsed["markup"],
                "term_delivery": parsed["termDelivery"],
                "vat_multiplier": self._vat_multiplier(),
                "named_parameters": self._load_formula_parameters(),
                "logistic_formulas": logistic_formulas,
                "formula_expressions": {
                    col: list(self.formulaExpressions.get(col, [])) for col in self.FORMULA_EDITABLE_COLUMNS
                },
            }
        )
        if not getattr(export_result, "success", False):
            error_text = getattr(export_result, "error_message", "") or "Не удалось создать Excel"
            self.error("Ошибка", error_text)
            return

        total_amount, currency = self._table_column_total(12)
        self.history_service.record_excel_export(
            items_count=row_count,
            total_amount=total_amount,
            currency=currency,
            file_path=getattr(export_result, "output_path", ""),
        )
        self.history_service.save()
        self.updateHistoryTable()

    def resourcePath(self, relativePath):
        return Tool.resourcePath(relativePath)

    def closeEvent(self, event):
        Config.config["logisticNum"] = self.ui.logisticNum.text()
        Config.config["customNum"] = self.ui.customLine.text()
        Config.config["termDelivery"] = self.ui.termDeliveryLine.text()
        Config.config["markup"] = self.ui.markupLine.text()
        Config.config["requestNumber"] = self.ui.requestNumberLine.text().strip()
        if hasattr(self.ui, "webRequestNumberLine"):
            Config.config["webRequestNumber"] = self.ui.webRequestNumberLine.text().strip()
        Config.config["logisticVar"] = str(self.ui.logisticVar.currentIndex())
        self.ensureOutputDirs()
        self.saveConfig()
        self.db.close()
        super().closeEvent(event)

    def funcExitSystem(self):
        self.close()
