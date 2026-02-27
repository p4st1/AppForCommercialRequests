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
)
from database import Database
from config import Config
from create import createTextFile as exportTextFile
from tools import DatabaseTools as Tool
from ui_createDocGui import Ui_MainWindow
from ui_theme import apply_unified_theme
import json

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
        self.suppliers = self.db.getAllCustomers()
        self.setupSuppliersItems()

        self._setup_field_placeholders()
        self.payInd = 0
        self.pay = [
            "на дату подписания спецификации Поставщиком",
            "на дату оплаты",
            "",
        ]
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

        header = summary.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
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
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

    def _setup_field_placeholders(self):
        self.ui.numLine.setPlaceholderText("Например: 24-2026")
        self.ui.warrantyPeriod.setPlaceholderText("Например: 12 месяцев")
        self.ui.conditionLine.setPlaceholderText("Например: по договору")
        self.ui.producerLine.setPlaceholderText("Например: завод-изготовитель")
        self.ui.deliveryTimeLine.setPlaceholderText("Например: 45 дней")
        self.ui.payLineEdit.setPlaceholderText("Уточните условие оплаты")

    def payUpd(self):
        self.pay[2] = self.ui.payLineEdit.text()

    def indChanged(self, ind):
        self.payInd = ind
        if self.payInd == 2:
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
                confirmedSuppliers.append(self.db.getCustomer(item.text())[0])
        extraData = self.getExtraData()
        if not confirmedSuppliers:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одного заказчика")
            return

        offer_id = self.db.getNextOfferNumber()
        export_result = exportTextFile(
            (
                self.tableData,
                confirmedSuppliers,
                extraData,
                str(offer_id),
                self.ui.radioButton.isChecked(),
                self.pay[self.payInd],
            ),
        )
        if not getattr(export_result, "success", False):
            error_text = getattr(export_result, "error_message", "") or "Не удалось создать файл DOCX"
            QMessageBox.critical(self, "Ошибка", error_text)
            return

        customer_data = confirmedSuppliers[0]
        total_amount, currency, items_count = self._history_summary()
        customer_name = " ".join(
            part for part in [customer_data[2], customer_data[1], customer_data[3]] if str(part).strip()
        ).strip()
        notes = ""
        if len(confirmedSuppliers) > 1:
            notes = f"Выбрано заказчиков: {len(confirmedSuppliers)}"

        self.db.createOffer(
            customer_company=customer_data[7],
            customer_name=customer_name,
            items_count=items_count,
            total_amount=total_amount,
            currency=currency,
            file_path=getattr(export_result, "output_path", ""),
            notes=notes,
            payload_json=self._history_payload_json(),
        )
        self.db.save()
        self.close()

    def _history_summary(self):
        rows = self.tableData[1] if self.tableData and len(self.tableData) > 1 else []
        total_amount = 0.0
        currency = ""
        for row in rows:
            if len(row) <= 7:
                continue
            symbol, amount_text = Tool.parsePrice(str(row[7]))
            if symbol and not currency:
                currency = symbol
            try:
                total_amount += float(str(amount_text).replace(" ", "").replace(",", "."))
            except ValueError:
                continue
        return round(total_amount, 2), currency, len(rows)

    def _history_payload_json(self) -> str:
        rows = self.tableData[1] if self.tableData and len(self.tableData) > 1 else []
        normalized_rows = []
        for row in rows:
            normalized_rows.append([str(value) for value in row[: self.SUMMARY_COLUMNS]])
        payload = {"table_data": normalized_rows}
        return json.dumps(payload, ensure_ascii=False)

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
