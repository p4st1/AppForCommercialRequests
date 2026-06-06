from datetime import datetime, timedelta

from PySide6.QtCore import QSize, Signal, Qt, QSignalBlocker
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
    QComboBox,
    QLabel,
    QCheckBox,
    QButtonGroup,
    QRadioButton,
    QWidget,
)
from app.repositories.offer_repository import OfferRepository
from app.repositories.customer_repository import CustomerRepository
from app.services.customer_service import CustomerService
from app.services.history_service import HistoryService
from services.google_drive_service import GoogleDriveService
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
    documentCreated = Signal(dict)
    SUMMARY_COLUMNS = 9
    FORMAT_DOCX = "docx"
    FORMAT_PDF = "pdf"
    FORMAT_GOOGLE_DOCX = "google_docx"
    MANUFACTURER_HISTORY_KEY = "manufacturerHistory"
    MANUFACTURER_HISTORY_LIMIT = 30

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
        self._restore_last_create_doc_fields()

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
        self._append_supplier_list_checkbox_style()
        self._rebuild_details_layout()

    def _append_supplier_list_checkbox_style(self):
        self.ui.suppliersList.setStyleSheet(
            self.ui.suppliersList.styleSheet()
            + """
QListWidget::indicator {
    width: 20px;
    height: 20px;
}
QListWidget::item {
    min-height: 38px;
}
"""
        )

    def _rebuild_details_layout(self):
        grid = getattr(self.ui, "gridLayout", None)
        if grid is None:
            return

        controls = (
            self.ui.label,
            self.ui.numLine,
            self.ui.label_5,
            self.ui.deliveryTimeLine,
            self.ui.label_6,
            self.ui.producerLine,
            self.ui.label_4,
            self.ui.warrantyPeriod,
            self.ui.label_7,
            self.ui.conditionLine,
            self.ui.label_8,
            self.ui.payComboBox,
            self.ui.payLineEdit,
            self.ui.radioButton,
            self.ui.label_3,
        )
        for widget in controls:
            grid.removeWidget(widget)
        self.ui.label_3.hide()

        self.ui.label.setText("Номер заявки")
        self.ui.label_5.setText("Срок доставки")
        self.ui.label_6.setText("Производитель")
        self.ui.label_4.setText("Срок гарантии")
        self.ui.label_7.setText("Условия оплаты")
        self.ui.label_8.setText("Оплата")
        self.ui.radioButton.setText('Показывать столбец "Срок поставки" в КП')
        self.ui.radioButton.setAutoExclusive(False)

        self.producerComboBox = QComboBox(self)
        self.producerComboBox.setObjectName("producerComboBox")
        self.producerComboBox.setEditable(True)
        self.producerComboBox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.producerComboBox.setStyleSheet(self.ui.producerLine.styleSheet())
        self.ui.producerComboBox = self.producerComboBox
        self.ui.producerLine.hide()
        self._refresh_manufacturer_history_combo()

        self.deliveryOrderLabel = QLabel("Порядок доставки", self)
        self.deliveryOrderLabel.setObjectName("deliveryOrderLabel")
        self.deliveryOrderLabel.setStyleSheet(self.ui.label_7.styleSheet())
        self.deliveryOrderLine = QLineEdit(self)
        self.deliveryOrderLine.setObjectName("deliveryOrderLine")
        self.deliveryOrderLine.setStyleSheet(self.ui.conditionLine.styleSheet())
        self.ui.deliveryOrderLabel = self.deliveryOrderLabel
        self.ui.deliveryOrderLine = self.deliveryOrderLine

        self.offerValidityPreviewLabel = QLabel(self._offer_validity_preview_text(), self)
        self.offerValidityPreviewLabel.setObjectName("offerValidityPreviewLabel")
        self.offerValidityPreviewLabel.setStyleSheet(
            "color: #475467; font-weight: 600; padding: 4px 0;"
        )
        self.ui.offerValidityPreviewLabel = self.offerValidityPreviewLabel

        self.outputFormatLabel = QLabel("Формат файла", self)
        self.outputFormatLabel.setObjectName("outputFormatLabel")
        self.outputFormatLabel.setStyleSheet(self.ui.label_7.styleSheet())
        self.docxFormatRadio = QRadioButton("Docx", self)
        self.pdfFormatRadio = QRadioButton("PDF", self)
        self.googleDocxFormatRadio = QRadioButton("Google Docx", self)
        self.googleDocxFormatRadio.setToolTip(
            "Сохранить DOCX локально и загрузить копию на Google Drive"
        )

        self.outputFormatGroup = QButtonGroup(self)
        self.outputFormatGroup.addButton(self.docxFormatRadio)
        self.outputFormatGroup.addButton(self.pdfFormatRadio)
        self.outputFormatGroup.addButton(self.googleDocxFormatRadio)
        self.docxFormatRadio.setChecked(True)
        self.ui.outputFormatLabel = self.outputFormatLabel
        self.ui.docxFormatRadio = self.docxFormatRadio
        self.ui.pdfFormatRadio = self.pdfFormatRadio
        self.ui.googleDocxFormatRadio = self.googleDocxFormatRadio

        self.submissionSupplierStatusCheckBox = QCheckBox(
            'Заполнять "Статус поставщика"',
            self,
        )
        self.submissionSupplierStatusCheckBox.setObjectName(
            "submissionSupplierStatusCheckBox"
        )
        self.submissionSupplierStatusLine = QLineEdit(self)
        self.submissionSupplierStatusLine.setObjectName("submissionSupplierStatusLine")

        self.ui.submissionSupplierStatusCheckBox = self.submissionSupplierStatusCheckBox
        self.ui.submissionSupplierStatusLine = self.submissionSupplierStatusLine

        checkbox_style = """
QCheckBox, QRadioButton {
    color: #2c3e50;
    font-weight: 600;
    font-size: 12px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 20px;
    height: 20px;
}
"""
        self.ui.radioButton.setStyleSheet(checkbox_style)
        self.submissionSupplierStatusCheckBox.setStyleSheet(checkbox_style)
        for radio in (self.docxFormatRadio, self.pdfFormatRadio, self.googleDocxFormatRadio):
            radio.setStyleSheet(checkbox_style)

        def add_pair(row, column, label, widget):
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            widget.setMinimumHeight(32)
            if isinstance(widget, QLineEdit):
                widget.setClearButtonEnabled(True)
            elif isinstance(widget, QComboBox):
                line_edit = widget.lineEdit()
                if line_edit is not None:
                    line_edit.setClearButtonEnabled(True)
            grid.addWidget(label, row, column, 1, 1)
            grid.addWidget(widget, row + 1, column, 1, 1)

        add_pair(0, 0, self.ui.label, self.ui.numLine)
        add_pair(0, 1, self.ui.label_5, self.ui.deliveryTimeLine)
        add_pair(0, 2, self.ui.label_6, self.producerComboBox)
        add_pair(2, 0, self.ui.label_4, self.ui.warrantyPeriod)
        add_pair(2, 1, self.ui.label_7, self.ui.conditionLine)
        add_pair(2, 2, self.ui.label_8, self.ui.payComboBox)

        grid.addWidget(self.ui.payLineEdit, 4, 2, 1, 1)
        grid.addWidget(self.deliveryOrderLabel, 4, 0, 1, 1)
        grid.addWidget(self.deliveryOrderLine, 5, 0, 1, 2)
        grid.addWidget(self.submissionSupplierStatusCheckBox, 6, 0, 1, 2)
        grid.addWidget(self.submissionSupplierStatusLine, 7, 0, 1, 2)
        grid.addWidget(self.offerValidityPreviewLabel, 8, 0, 1, 3)
        grid.addWidget(self.outputFormatLabel, 9, 0, 1, 1)

        format_row = QHBoxLayout()
        format_row.setSpacing(14)
        format_row.setContentsMargins(0, 0, 0, 0)
        format_row.addWidget(self.pdfFormatRadio)
        format_row.addWidget(self.docxFormatRadio)
        format_row.addWidget(self.googleDocxFormatRadio)
        format_row.addStretch(1)
        grid.addLayout(format_row, 10, 0, 1, 3)
        grid.addWidget(self.ui.radioButton, 11, 0, 1, 3)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        self.submissionSupplierStatusCheckBox.toggled.connect(
            self._sync_submission_extra_fields_enabled
        )
        self._sync_submission_extra_fields_enabled()

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
        self.ui.numLine.setPlaceholderText("")
        self.ui.warrantyPeriod.setPlaceholderText("")
        self.ui.conditionLine.setPlaceholderText("")
        self._set_producer_placeholder("")
        self.ui.deliveryTimeLine.setPlaceholderText("")
        if hasattr(self, "deliveryOrderLine"):
            self.deliveryOrderLine.setPlaceholderText("")
        self.ui.payLineEdit.setPlaceholderText("Уточните условие оплаты")
        if hasattr(self, "submissionSupplierStatusLine"):
            self.submissionSupplierStatusLine.setPlaceholderText("Например: Посредник")

    @classmethod
    def _normalize_manufacturer_history(cls, values) -> list[str]:
        if isinstance(values, str):
            source_values = [values]
        elif isinstance(values, (list, tuple)):
            source_values = list(values)
        else:
            source_values = []

        result = []
        seen = set()
        for value in source_values:
            text = str(value or "").strip()
            if not text:
                continue
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(text)
            if len(result) >= cls.MANUFACTURER_HISTORY_LIMIT:
                break
        return result

    def _manufacturer_history(self) -> list[str]:
        return self._normalize_manufacturer_history(
            Config.config.get(self.MANUFACTURER_HISTORY_KEY, [])
        )

    def _refresh_manufacturer_history_combo(self) -> None:
        combo = getattr(self, "producerComboBox", None)
        if not isinstance(combo, QComboBox):
            return

        current_text = combo.currentText().strip()
        blocker = QSignalBlocker(combo)
        combo.clear()
        combo.addItems(self._manufacturer_history())
        combo.setEditText(current_text)
        del blocker

        completer = combo.completer()
        if completer is not None:
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            try:
                completer.setFilterMode(Qt.MatchFlag.MatchContains)
            except Exception:
                pass

    def _producer_text(self) -> str:
        combo = getattr(self, "producerComboBox", None)
        if isinstance(combo, QComboBox):
            return combo.currentText().strip()
        return self.ui.producerLine.text().strip()

    def _set_producer_text(self, value: str) -> None:
        text = str(value or "")
        combo = getattr(self, "producerComboBox", None)
        if isinstance(combo, QComboBox):
            combo.setEditText(text)
            return
        self.ui.producerLine.setText(text)

    def _set_producer_placeholder(self, value: str) -> None:
        combo = getattr(self, "producerComboBox", None)
        if isinstance(combo, QComboBox):
            line_edit = combo.lineEdit()
            if line_edit is not None:
                line_edit.setPlaceholderText(value)
            return
        self.ui.producerLine.setPlaceholderText(value)

    def _remember_manufacturer(self, value: str) -> None:
        text = str(value or "").strip()
        if not text:
            return

        history = [text]
        history.extend(self._manufacturer_history())
        Config.config[self.MANUFACTURER_HISTORY_KEY] = self._normalize_manufacturer_history(
            history
        )
        self._refresh_manufacturer_history_combo()

    def _sync_submission_extra_fields_enabled(self, *_args):
        if hasattr(self, "submissionSupplierStatusLine") and hasattr(
            self,
            "submissionSupplierStatusCheckBox",
        ):
            self.submissionSupplierStatusLine.setEnabled(
                self.submissionSupplierStatusCheckBox.isChecked()
            )

    def _setup_participation_checkbox(self):
        self.checkbox_participate = QCheckBox("Участвовать в приёме заявок", self)
        self.checkbox_participate.setObjectName("checkbox_participate")
        self.checkbox_participate.setStyleSheet(self.ui.radioButton.styleSheet())

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
        grid_layout.addWidget(number_container, 1, 0, 1, 1)

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

    @staticmethod
    def _config_payload_with_cookies() -> dict:
        data = {'config': Config.config, 'settings': Config.settings}
        cookies_raw = Config.config.get("cookies")
        if isinstance(cookies_raw, dict):
            cookies = {
                str(key): str(value)
                for key, value in cookies_raw.items()
                if str(key).strip() and str(value).strip()
            }
            if cookies:
                data["cookies"] = cookies
        return data

    def _save_config_snapshot(self):
        if str(getattr(Config, "cfg_path", "") or "").strip():
            Tool.save_json_atomic(Config.cfg_path, self._config_payload_with_cookies())

    def _last_fields(self) -> dict:
        raw = Config.config.get("lastCreateDocFields")
        return raw if isinstance(raw, dict) else {}

    def _selected_output_format(self) -> str:
        if getattr(self, "pdfFormatRadio", None) is not None and self.pdfFormatRadio.isChecked():
            return self.FORMAT_PDF
        if getattr(self, "googleDocxFormatRadio", None) is not None and self.googleDocxFormatRadio.isChecked():
            return self.FORMAT_GOOGLE_DOCX
        return self.FORMAT_DOCX

    def _set_output_format(self, value: str):
        normalized = str(value or "").strip().lower()
        if normalized == self.FORMAT_PDF:
            self.pdfFormatRadio.setChecked(True)
        elif normalized == self.FORMAT_GOOGLE_DOCX and self.googleDocxFormatRadio.isEnabled():
            self.googleDocxFormatRadio.setChecked(True)
        else:
            self.docxFormatRadio.setChecked(True)

    def _restore_last_create_doc_fields(self):
        fields = self._last_fields()
        if not fields:
            self.ui.payLineEdit.setEnabled(False)
            return

        warranty_period = str(
            fields.get("warranty_period", "")
            or fields.get("submission_warranty", "")
            or ""
        )
        if warranty_period:
            self.ui.warrantyPeriod.setText(warranty_period)

        for widget, key in (
            (self.ui.conditionLine, "payment_terms"),
            (self.ui.deliveryTimeLine, "delivery_time"),
            (getattr(self, "deliveryOrderLine", None), "delivery_order"),
            (
                getattr(self, "submissionSupplierStatusLine", None),
                "submission_supplier_status",
            ),
        ):
            if widget is None:
                continue
            value = str(fields.get(key, "") or "")
            if value:
                widget.setText(value)

        producer_value = str(fields.get("producer", "") or "")
        if producer_value:
            self._set_producer_text(producer_value)

        self.ui.radioButton.setChecked(bool(fields.get("show_delivery_column", False)))
        if hasattr(self, "checkbox_participate"):
            self.checkbox_participate.setChecked(bool(fields.get("participate", False)))
        if hasattr(self, "submissionSupplierStatusCheckBox"):
            self.submissionSupplierStatusCheckBox.setChecked(
                bool(fields.get("fill_submission_supplier_status", False))
            )
        self._set_output_format(str(fields.get("output_format", self.FORMAT_DOCX)))

        payment_template = str(fields.get("payment_template", "") or "").strip()
        custom_payment = str(fields.get("custom_payment", "") or "").strip()
        selected_index = -1
        if payment_template:
            for index in range(self.ui.payComboBox.count()):
                if self.ui.payComboBox.itemText(index).strip() == payment_template:
                    selected_index = index
                    break
        if selected_index >= 0:
            self.ui.payComboBox.setCurrentIndex(selected_index)
        elif custom_payment:
            self.ui.payComboBox.setCurrentIndex(self._custom_payment_index())
            self.ui.payLineEdit.setText(custom_payment)
        self.indChanged(self.ui.payComboBox.currentIndex())
        self._sync_submission_extra_fields_enabled()

    def _save_last_create_doc_fields(self):
        warranty_period = self.ui.warrantyPeriod.text().strip()
        fields = {
            "warranty_period": warranty_period,
            "payment_terms": self.ui.conditionLine.text().strip(),
            "producer": self._producer_text(),
            "delivery_time": self.ui.deliveryTimeLine.text().strip(),
            "delivery_order": self.deliveryOrderLine.text().strip()
            if hasattr(self, "deliveryOrderLine")
            else "",
            "submission_supplier_status": self.submissionSupplierStatusLine.text().strip()
            if hasattr(self, "submissionSupplierStatusLine")
            else "",
            "submission_warranty": warranty_period,
            "fill_submission_supplier_status": self.submissionSupplierStatusCheckBox.isChecked()
            if hasattr(self, "submissionSupplierStatusCheckBox")
            else False,
            "fill_submission_warranty": bool(warranty_period),
            "payment_template": self._current_payment_value(),
            "custom_payment": self.ui.payLineEdit.text().strip(),
            "show_delivery_column": self.ui.radioButton.isChecked(),
            "participate": self.checkbox_participate.isChecked()
            if hasattr(self, "checkbox_participate")
            else False,
            "output_format": self._selected_output_format(),
        }
        Config.config["lastCreateDocFields"] = fields
        self._remember_manufacturer(fields["producer"])
        self._save_config_snapshot()

    def filterSuppliers(self, text):
        value = text.casefold().strip()
        for i in range(self.ui.suppliersList.count()):
            item = self.ui.suppliersList.item(i)
            payload = item.data(Qt.ItemDataRole.UserRole)
            search_text = ""
            if isinstance(payload, dict):
                search_text = str(payload.get("search", "") or "")
            if not search_text:
                search_text = item.text()
            item.setHidden(value not in search_text.casefold())

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
                payload = item.data(Qt.ItemDataRole.UserRole)
                customer_id = payload.get("id") if isinstance(payload, dict) else None
                customer = self.customer_by_id.get(customer_id) if customer_id is not None else None
                if customer is None:
                    company = payload.get("company", "") if isinstance(payload, dict) else item.text().splitlines()[0]
                    matches = self.customer_service.get_customers_by_company(company)
                    customer = matches[0] if matches else None
                if customer is not None:
                    confirmedSuppliers.append(customer)
        if not confirmedSuppliers:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одного заказчика")
            return

        delivery_order = self._customer_delivery_order(confirmedSuppliers[0])
        if hasattr(self, "deliveryOrderLine"):
            self.deliveryOrderLine.setText(delivery_order)

        extraData = self.getExtraData()
        self._save_last_create_doc_fields()

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
                self._selected_output_format(),
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

        remote_url = ""
        if self._selected_output_format() == self.FORMAT_GOOGLE_DOCX:
            if callable(set_pipeline_status):
                set_pipeline_status("☁ Загрузка КП на Google Drive...")
            try:
                upload_result = GoogleDriveService().upload_docx(
                    getattr(export_result, "output_path", "")
                )
                remote_url = upload_result.web_view_link
            except Exception as exc:
                if callable(set_pipeline_error_status):
                    set_pipeline_error_status()
                elif callable(set_pipeline_status):
                    set_pipeline_status("❌ Ошибка")
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    "Локальный DOCX сохранен, но не удалось загрузить его на Google Drive:\n"
                    f"{exc}",
                )
                return

        self.history_service.record_docx_offer(
            customer_data=confirmedSuppliers[0],
            table_rows=self.tableData[1] if self.tableData and len(self.tableData) > 1 else [],
            output_path=getattr(export_result, "output_path", ""),
            selected_suppliers_count=len(confirmedSuppliers),
            summary_columns=self.SUMMARY_COLUMNS,
            remote_url=remote_url,
        )
        self.history_service.save()
        self.documentCreated.emit(
            {
                "output_path": str(getattr(export_result, "output_path", "") or ""),
                "remote_url": remote_url,
                "customer_data": confirmedSuppliers[0],
            }
        )

        if self.checkbox_participate.isChecked():
            try:
                run_web_pipeline = getattr(self.parent(), "run_web_pipeline", None)
                if callable(run_web_pipeline):
                    run_web_pipeline(
                        trade_number=self.ui.numLine.text().strip(),
                        submission_context=self._submission_context(
                            confirmedSuppliers,
                            extraData,
                        ),
                    )
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

    @classmethod
    def _default_offer_validity_period(cls) -> str:
        return (
            datetime.now() + timedelta(days=Config.get_offer_validity_days())
        ).strftime("%d.%m.%Y")

    @classmethod
    def _offer_validity_preview_text(cls) -> str:
        days = Config.get_offer_validity_days()
        date_text = cls._default_offer_validity_period()
        return f"Срок действия КП: до {date_text} (+{days} дн.)"

    @staticmethod
    def _customer_company_name(customer_data) -> str:
        if isinstance(customer_data, (list, tuple)) and len(customer_data) > 7:
            return str(customer_data[7] or "").strip()
        return ""

    @staticmethod
    def _customer_full_name(customer_data) -> str:
        if not isinstance(customer_data, (list, tuple)):
            return ""
        parts = []
        for index in (2, 1, 3):
            if len(customer_data) > index:
                value = str(customer_data[index] or "").strip()
                if value:
                    parts.append(value)
        return " ".join(parts)

    @staticmethod
    def _customer_delivery_order(customer_data) -> str:
        if isinstance(customer_data, (list, tuple)) and len(customer_data) > 9:
            return str(customer_data[9] or "").strip()
        return ""

    def _submission_context(self, confirmed_suppliers, extra_data):
        first_supplier = confirmed_suppliers[0] if confirmed_suppliers else None
        producer = str(
            extra_data[3]
            if len(extra_data) > 3 and extra_data[3] is not None
            else ""
        ).strip()
        fill_supplier_status = (
            hasattr(self, "submissionSupplierStatusCheckBox")
            and self.submissionSupplierStatusCheckBox.isChecked()
        )
        submission_warranty = self.ui.warrantyPeriod.text().strip()
        if not submission_warranty:
            submission_warranty = str(
                extra_data[1] if len(extra_data) > 1 and extra_data[1] is not None else ""
            ).strip()
        return {
            "customer": self._customer_company_name(first_supplier),
            "producer": producer,
            "offer_validity_period": self._default_offer_validity_period(),
            "delivery_order": str(
                extra_data[5] if len(extra_data) > 5 and extra_data[5] is not None else ""
            ).strip(),
            "payment_terms": str(
                extra_data[2] if len(extra_data) > 2 and extra_data[2] is not None else ""
            ).strip(),
            "payment_condition": self._current_payment_value(),
            "supplier_status": self.submissionSupplierStatusLine.text().strip()
            if fill_supplier_status and hasattr(self, "submissionSupplierStatusLine")
            else "",
            "warranty": submission_warranty,
        }

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
        result.append(self._producer_text())
        result.append(self.ui.deliveryTimeLine.text())
        result.append(self.deliveryOrderLine.text() if hasattr(self, "deliveryOrderLine") else "")
        return result

    def setupSuppliersItems(self):
        filter_text = self.supplierSearchLine.text() if hasattr(self, "supplierSearchLine") else ""
        self.customer_by_id = {}
        blocker = QSignalBlocker(self.ui.suppliersList)
        self.ui.suppliersList.clear()
        for supplier in self.suppliers:
            customer_id = supplier[0]
            company = str(supplier[7] or "").strip()
            full_name = self._customer_full_name(supplier)
            display = company
            if full_name:
                display = f"{company}\nФИО: {full_name}"
            item = QListWidgetItem(display)
            item.setSizeHint(QSize(220, 48 if full_name else 34))
            item.setToolTip(display)
            item.setData(
                Qt.ItemDataRole.UserRole,
                {
                    "id": customer_id,
                    "company": company,
                    "full_name": full_name,
                    "search": f"{company} {full_name}",
                },
            )
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.ui.suppliersList.addItem(item)
            self.customer_by_id[customer_id] = supplier
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
