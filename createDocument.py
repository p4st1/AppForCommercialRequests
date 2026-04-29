from PySide6.QtCore import Signal, Qt, QSignalBlocker
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QListWidgetItem,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QPushButton,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QCheckBox,
    QWidget,
)
from app.repositories.offer_repository import OfferRepository
from app.repositories.customer_repository import CustomerRepository
from app.services.customer_service import CustomerService
from app.services.history_service import HistoryService
from app.ui.table_autosize import configure_table_autosize, resize_table_to_contents
from database import Database
from config import Config
from create import createTextFile as exportTextFile
from tools import DatabaseTools as Tool
from ui_createDocGui import Ui_MainWindow
from ui_theme import apply_unified_theme

class Dialog:
    def myDialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Подтверждение")
        dlg.setText("Есть не сохраненные изменения. Продолжить?")
        dlg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dlg.setIcon(QMessageBox.Icon.Question)
        button = dlg.exec()

        if button == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

class mainWindow(QMainWindow):
    windowClosed = Signal()
    SUMMARY_COLUMNS = 9

    def __init__(self, parent=None, tableData=None):
        super(mainWindow, self).__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        apply_unified_theme(self)

        self.ui.createDocButton.clicked.connect(self.confirmDoc)
        self.ui.payComboBox.currentIndexChanged.connect(self.indChanged)
        self.ui.payLineEdit.textChanged.connect(self.payUpd)

        self.tableData = tableData if tableData is not None else (0, [])
        self._setup_window_ergonomics()
        self._fill_summary_table()

        self.db = Database()
        self.db.open(Config.db_path)
        self.customer_repository = CustomerRepository(self.db)
        self.customer_service = CustomerService(self.customer_repository)
        self.offer_repository = OfferRepository(self.db)
        self.history_service = HistoryService(self.offer_repository)
        self.suppliers = self.customer_service.get_all_customers()
        self.setupSuppliersItems()

        self._setup_field_placeholders()
        self._setup_participation_checkbox()
        self.payInd = 0
        self.payTemplates = self._load_payment_templates()
        self.payCustomValue = ""
        self._fill_payment_templates()
        self.ui.payLineEdit.setEnabled(False)

    def _setup_window_ergonomics(self):
        self.setMinimumSize(1180, 820)

        summary = self.ui.summaryTable
        summary.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        summary.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        summary.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        summary.setAlternatingRowColors(True)
        summary.setSortingEnabled(False)
        summary.verticalHeader().setVisible(False)
        configure_table_autosize(summary)

        header = summary.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        summary.setColumnWidth(1, 300)
        for col in range(2, self.SUMMARY_COLUMNS):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        self.supplierSearchLine = QLineEdit(self)
        self.supplierSearchLine.setPlaceholderText("Поиск заказчика...")
        self.ui.verticalLayout_4.insertWidget(1, self.supplierSearchLine)

        controls = QHBoxLayout()
        self.selectAllSuppliersButton = QPushButton("Выбрать всех", self)
        self.clearSuppliersButton = QPushButton("Снять выбор", self)
        self.checkedSuppliersLabel = QLabel("Выбрано: 0", self)
        controls.addWidget(self.selectAllSuppliersButton)
        controls.addWidget(self.clearSuppliersButton)
        controls.addStretch(1)
        controls.addWidget(self.checkedSuppliersLabel)
        self.ui.verticalLayout_4.addLayout(controls)

        self.supplierSearchLine.textChanged.connect(self.filterSuppliers)
        self.selectAllSuppliersButton.clicked.connect(self.selectAllSuppliers)
        self.clearSuppliersButton.clicked.connect(self.clearSuppliersSelection)
        self.ui.suppliersList.itemChanged.connect(self.updateSelectedSuppliersCount)

    def _fill_summary_table(self):
        row_count = int(self.tableData[0]) if self.tableData else 0
        rows = self.tableData[1] if len(self.tableData) > 1 else []

        table = self.ui.summaryTable
        table.setColumnCount(self.SUMMARY_COLUMNS)
        table.setRowCount(row_count)
        blocker = QSignalBlocker(table)
        for row in range(row_count):
            row_data = rows[row] if row < len(rows) else []
            for col in range(self.SUMMARY_COLUMNS):
                value = row_data[col] if col < len(row_data) else ""
                table.setItem(row, col, QTableWidgetItem(str(value)))
        del blocker
        resize_table_to_contents(table)

    def _setup_field_placeholders(self):
        self.ui.numLine.setPlaceholderText("Например: 24-2026")
        self.ui.warrantyPeriod.setPlaceholderText("Например: 12 месяцев")
        self.ui.conditionLine.setPlaceholderText("Например: по договору")
        self.ui.producerLine.setPlaceholderText("Например: завод-изготовитель")
        self.ui.deliveryTimeLine.setPlaceholderText("Например: 45 дней")
        self.ui.payLineEdit.setPlaceholderText("Уточните условие оплаты")

    def _setup_participation_checkbox(self):
        self.checkbox_participate = QCheckBox("Участвовать в приёме заявок", self)
        self.checkbox_participate.setObjectName("checkbox_participate")

        grid_layout = getattr(self.ui, "gridLayout", None)
        num_line = getattr(self.ui, "numLine", None)
        if grid_layout is None or num_line is None:
            return

        number_container = QWidget(self)
        number_layout = QHBoxLayout(number_container)
        number_layout.setContentsMargins(0, 0, 0, 0)
        number_layout.setSpacing(8)
        number_layout.addWidget(num_line)
        number_layout.addWidget(self.checkbox_participate)
        number_layout.setStretch(0, 1)
        number_layout.setStretch(1, 0)

        grid_layout.removeWidget(num_line)
        grid_layout.addWidget(number_container, 3, 3, 1, 1)

    def _load_payment_templates(self):
        templates_raw = Config.config.get("paymentTemplates", Config.DEFAULT_PAYMENT_TEMPLATES)
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

    def _fill_payment_templates(self):
        blocker = QSignalBlocker(self.ui.payComboBox)
        self.ui.payComboBox.clear()
        for template in self.payTemplates:
            self.ui.payComboBox.addItem(template)
        self.ui.payComboBox.addItem("Другое...")
        self.ui.payComboBox.setCurrentIndex(0)
        del blocker
        self.indChanged(0)

    def _custom_payment_index(self):
        return len(self.payTemplates)

    def _current_payment_value(self):
        index = self.ui.payComboBox.currentIndex()
        if 0 <= index < len(self.payTemplates):
            return self.payTemplates[index]
        return self.payCustomValue

    def payUpd(self):
        self.payCustomValue = self.ui.payLineEdit.text().strip()

    def indChanged(self, ind):
        self.payInd = ind
        if self.payInd == self._custom_payment_index():
            self.ui.payLineEdit.setEnabled(True)
        else:
            self.ui.payLineEdit.setEnabled(False)

    def filterSuppliers(self, text):
        value = text.casefold().strip()
        for i in range(self.ui.suppliersList.count()):
            item = self.ui.suppliersList.item(i)
            item.setHidden(value not in item.text().casefold())

    def selectAllSuppliers(self):
        only_visible = bool(self.supplierSearchLine.text().strip())
        blocker = QSignalBlocker(self.ui.suppliersList)
        for i in range(self.ui.suppliersList.count()):
            item = self.ui.suppliersList.item(i)
            if only_visible and item.isHidden():
                continue
            item.setCheckState(Qt.CheckState.Checked)
        del blocker
        self.updateSelectedSuppliersCount()

    def clearSuppliersSelection(self):
        only_visible = bool(self.supplierSearchLine.text().strip())
        blocker = QSignalBlocker(self.ui.suppliersList)
        for i in range(self.ui.suppliersList.count()):
            item = self.ui.suppliersList.item(i)
            if only_visible and item.isHidden():
                continue
            item.setCheckState(Qt.CheckState.Unchecked)
        del blocker
        self.updateSelectedSuppliersCount()

    def updateSelectedSuppliersCount(self):
        checked = 0
        for i in range(self.ui.suppliersList.count()):
            item = self.ui.suppliersList.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                checked += 1
        self.checkedSuppliersLabel.setText(f"Выбрано: {checked}")

    def confirmDoc(self):
        confirmedSuppliers = []
        for i in range(self.ui.suppliersList.count()):
            item = self.ui.suppliersList.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                confirmedSuppliers.append(self.customer_service.get_customers_by_company(item.text())[0])
        extraData = self.getExtraData()
        if not confirmedSuppliers:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одного заказчика")
            return

        parent_window = self.parent()
        set_pipeline_status = getattr(parent_window, "set_pipeline_status", None)
        set_pipeline_success_status = getattr(parent_window, "_set_pipeline_success_status", None)
        set_pipeline_error_status = getattr(parent_window, "_set_pipeline_error_status", None)

        if callable(set_pipeline_status):
            set_pipeline_status("🔄 Создание КП...")

        offer_id = self.offer_repository.get_next_doc_offer_number()
        export_result = exportTextFile(
            (
                self.tableData,
                confirmedSuppliers,
                extraData,
                str(offer_id),
                self.ui.radioButton.isChecked(),
                self._current_payment_value(),
            ),
        )
        if not getattr(export_result, "success", False):
            error_text = getattr(export_result, "error_message", "") or "Не удалось создать файл DOCX"
            if callable(set_pipeline_error_status):
                set_pipeline_error_status()
            elif callable(set_pipeline_status):
                set_pipeline_status("❌ Ошибка")
            QMessageBox.critical(self, "Ошибка", error_text)
            return

        self.history_service.record_docx_offer(
            customer_data=confirmedSuppliers[0],
            table_rows=self.tableData[1] if self.tableData and len(self.tableData) > 1 else [],
            output_path=getattr(export_result, "output_path", ""),
            selected_suppliers_count=len(confirmedSuppliers),
            summary_columns=self.SUMMARY_COLUMNS,
        )
        self.history_service.save()

        if self.checkbox_participate.isChecked():
            try:
                run_web_pipeline = getattr(self.parent(), "run_web_pipeline", None)
                if callable(run_web_pipeline):
                    run_web_pipeline(trade_number=self.ui.numLine.text().strip())
                else:
                    if callable(set_pipeline_success_status):
                        set_pipeline_success_status()
                    elif callable(set_pipeline_status):
                        set_pipeline_status("✅ Готово")
            except Exception as exc:
                if callable(set_pipeline_error_status):
                    set_pipeline_error_status()
                elif callable(set_pipeline_status):
                    set_pipeline_status("❌ Ошибка")
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Ошибка на этапе: запуск pipeline\n{exc}",
                )
        else:
            if callable(set_pipeline_success_status):
                set_pipeline_success_status()
            elif callable(set_pipeline_status):
                set_pipeline_status("✅ Готово")

        self.close()

    def _history_summary(self):
        rows = self.tableData[1] if self.tableData and len(self.tableData) > 1 else []
        return self.history_service.summarize_table_for_history(rows, total_col_index=7)

    def _history_payload_json(self) -> str:
        rows = self.tableData[1] if self.tableData and len(self.tableData) > 1 else []
        return self.history_service.build_payload_json(rows, summary_columns=self.SUMMARY_COLUMNS)

    def getExtraData(self):
        result = []
        result.append(self.ui.numLine.text())
        result.append(self.ui.warrantyPeriod.text())
        result.append(self.ui.conditionLine.text())
        result.append(self.ui.producerLine.text())
        result.append(self.ui.deliveryTimeLine.text())
        return result

    def setupSuppliersItems(self):
        filter_text = self.supplierSearchLine.text() if hasattr(self, "supplierSearchLine") else ""
        blocker = QSignalBlocker(self.ui.suppliersList)
        self.ui.suppliersList.clear()
        for supplier in self.suppliers:
            item = QListWidgetItem(supplier[7])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.ui.suppliersList.addItem(item)
        del blocker
        if filter_text:
            self.filterSuppliers(filter_text)
        self.updateSelectedSuppliersCount()

    def resourcePath(self, relativePath):
        return Tool.resourcePath(relativePath)

    def closeEvent(self, event):
        self.db.close()
        self.windowClosed.emit()
        super().closeEvent(event)

    def funcExitSystem(self):
        self.db.close()
        self.close()
