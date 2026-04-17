from PySide6.QtWidgets import (
    QMainWindow,
    QTableWidget,
    QAbstractItemView,
    QStyledItemDelegate,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSignalBlocker, QTimer
from app.repositories.offer_repository import OfferRepository
from app.services.calculation_service import CalculationService
from app.services.history_service import HistoryService
from app.services.proposal_import_service import ProposalImportService
from app.ui.app_lifecycle_mixin import AppLifecycleMixin
from app.ui.calculation_flow_mixin import CalculationFlowMixin
from app.ui.config_io_mixin import ConfigIoMixin
from app.ui.database_transfer_mixin import DatabaseTransferMixin
from app.ui.doc_export_flow_mixin import DocExportFlowMixin
from app.ui.doc_from_excel_mixin import DocFromExcelMixin
from app.ui.excel_export_flow_mixin import ExcelExportFlowMixin
from app.ui.formula_config_mixin import FormulaConfigMixin
from app.ui.formula_editing_mixin import FormulaEditingMixin
from app.ui.formula_input_mixin import FormulaInputMixin
from app.ui.formula_metadata_mixin import FormulaMetadataMixin
from app.ui.info_dialogs_mixin import InfoDialogsMixin
from app.ui.number_format_mixin import NumberFormatMixin
from app.ui.table_cell_edit_mixin import TableCellEditMixin
from app.ui.shortcut_mixin import ShortcutMixin
from app.ui.table_row_actions_mixin import TableRowActionsMixin
from app.ui.table_summary_mixin import TableSummaryMixin
from app.ui.table_summary_view_mixin import TableSummaryViewMixin
from app.ui.table_undo_mixin import TableUndoMixin
from app.ui.table_search_mixin import TableSearchMixin
from app.ui.table_filter_mixin import TableFilterMixin
from app.ui.table_import_flow_mixin import TableImportFlowMixin
from app.ui.table_item_mixin import TableItemMixin
from app.ui.vat_mixin import VatMixin
from app.ui.history_flow_mixin import HistoryFlowMixin
from app.ui.maintenance_actions_mixin import MaintenanceActionsMixin
from app.ui.ui_feedback_mixin import UiFeedbackMixin
from app.ui.window_navigation_mixin import WindowNavigationMixin
from ui_mixins.platform_mixin import PlatformMixin
from ui_mixins.upload_mixin import UploadMixin
from tools import DatabaseTools as Tool
from database import Database
from config import Config
from ui_mainGui import Ui_MainWindow
from ui_theme import apply_unified_theme
from pathlib import Path
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
    ConfigIoMixin,
    AppLifecycleMixin,
    CalculationFlowMixin,
    UiFeedbackMixin,
    TableImportFlowMixin,
    TableItemMixin,
    NumberFormatMixin,
    VatMixin,
    FormulaInputMixin,
    DatabaseTransferMixin,
    MaintenanceActionsMixin,
    InfoDialogsMixin,
    DocExportFlowMixin,
    DocFromExcelMixin,
    ExcelExportFlowMixin,
    WindowNavigationMixin,
    ShortcutMixin,
    TableUndoMixin,
    FormulaMetadataMixin,
    FormulaConfigMixin,
    FormulaEditingMixin,
    TableCellEditMixin,
    TableRowActionsMixin,
    TableSummaryMixin,
    TableSummaryViewMixin,
    TableSearchMixin,
    TableFilterMixin,
    HistoryFlowMixin,
    UploadMixin,
    PlatformMixin,
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
        self.mixedCurrencyWarningShown = False
        self.columnFilters = {}
        self._baseHeaderLabels = {}
        self.quickSearchText = ""
        self._shortcuts = []
        self._undo_stack = []
        self._is_restoring_undo = False
        self._pending_edit_undo_state = None
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
        self._setup_history_tab_table()
        self.init_platform_mixin()
        self.init_upload_mixin()
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
