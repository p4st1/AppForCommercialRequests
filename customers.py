from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QMessageBox, QListWidgetItem, QLineEdit
from app.repositories.customer_repository import CustomerRepository
from app.services.customer_service import CustomerService
from config import Config
from database import Database
from addNewCustomer import mainWindow as newSupplierWindow
from tools import DatabaseTools as Tool
from ui_customersGui import Ui_MainWindow
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

    def __init__(self, parent=None):
        super(mainWindow, self).__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        apply_unified_theme(self)

        self.searchLine = QLineEdit(self)
        self.searchLine.setPlaceholderText("Поиск заказчика (Ctrl+F)...")
        self.ui.verticalLayout_4.insertWidget(0, self.searchLine)
        self.searchLine.textChanged.connect(self.filterCustomers)
        self.searchShortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.searchShortcut.activated.connect(self.focusSearch)

        self.db = Database()
        if self.db.open(Config.db_path) == -1:
            QMessageBox.critical(self, "Ошибка", "Не удалось открыть базу данных")
        self.customer_repository = CustomerRepository(self.db)
        self.customer_service = CustomerService(self.customer_repository)

        self.ui.suppliersList.itemClicked.connect(self.customerSelected)
        self.ui.closeButton.clicked.connect(self.close)
        self.ui.addSupplierButton.clicked.connect(self.openNewCustomer)
        self.ui.changeSupplierButton.clicked.connect(self.openExistCustomer)
        self.ui.deleteSupplierButton.clicked.connect(self.delSelectedCustomer)

        self.selectedCustomerData = None
        self.ui.deleteSupplierButton.setEnabled(False)
        self.ui.changeSupplierButton.setEnabled(False)

        self.showSuppliers()

    def showSuppliers(self):
        self.suppliers = self.customer_service.get_all_customers()
        self.ui.suppliersList.clear()
        self.customer_by_id = {}
        for supplier in self.suppliers:
            display_name = supplier[7] if supplier[7] else f"{supplier[2]} {supplier[1]}".strip()
            item = QListWidgetItem(display_name or "Без названия")
            item.setData(Qt.ItemDataRole.UserRole, supplier[0])
            search_blob = " ".join(
                [
                    str(supplier[7] or ""),
                    str(supplier[2] or ""),
                    str(supplier[1] or ""),
                    str(supplier[3] or ""),
                    str(supplier[5] or ""),
                    str(supplier[6] or ""),
                    str(supplier[8] or ""),
                ]
            ).casefold()
            item.setData(Qt.ItemDataRole.UserRole + 1, search_blob)
            self.customer_by_id[supplier[0]] = supplier
            self.ui.suppliersList.addItem(item)
        self.filterCustomers(self.searchLine.text())

    def focusSearch(self):
        self.searchLine.setFocus()
        self.searchLine.selectAll()

    def filterCustomers(self, text):
        value = str(text or "").strip().casefold()
        for i in range(self.ui.suppliersList.count()):
            item = self.ui.suppliersList.item(i)
            search_blob = str(item.data(Qt.ItemDataRole.UserRole + 1) or item.text()).casefold()
            item.setHidden(bool(value and value not in search_blob))

    def customerSelected(self, item):
        customer_id = item.data(Qt.ItemDataRole.UserRole)
        self.selectedCustomerData = self.customer_by_id.get(customer_id)
        is_enabled = self.selectedCustomerData is not None
        self.ui.deleteSupplierButton.setEnabled(is_enabled)
        self.ui.changeSupplierButton.setEnabled(is_enabled)

    def delSelectedCustomer(self):
        if not self.selectedCustomerData:
            return
        self.customer_service.delete_customer_by_id(self.selectedCustomerData[0], commit=True)
        self.showSuppliers()
        self.selectedCustomerData = None
        self.ui.deleteSupplierButton.setEnabled(False)
        self.ui.changeSupplierButton.setEnabled(False)

    def openExistCustomer(self):
        if not self.selectedCustomerData:
            return
        window = newSupplierWindow(self, exist=self.selectedCustomerData)
        window.show()
        window.windowClosed.connect(self.showSuppliers)

    def openNewCustomer(self):
        window = newSupplierWindow(self, exist=None)
        window.show()
        window.windowClosed.connect(self.showSuppliers)

    def resourcePath(self, relativePath):
        return Tool.resourcePath(relativePath)

    def closeEvent(self, event):
        self.db.close()
        self.windowClosed.emit()
        super().closeEvent(event)

    def funcExitSystem(self):
        self.close()
