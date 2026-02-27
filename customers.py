from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QMainWindow, QMessageBox, QListWidgetItem
from config import Config
from database import Database
from addNewCustomer import mainWindow as newSupplierWindow
from ui_customersGui import Ui_MainWindow
import sys
import os

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
        
        self.db = Database()
        if self.db.open(Config.db_path) == -1:
            QMessageBox.critical(self, "Ошибка", "Не удалось открыть базу данных")
        
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
        self.suppliers = self.db.getAllCustomers()
        self.ui.suppliersList.clear()
        self.customer_by_id = {}
        for supplier in self.suppliers:
            display_name = supplier[7] if supplier[7] else f"{supplier[2]} {supplier[1]}".strip()
            item = QListWidgetItem(display_name or "Без названия")
            item.setData(Qt.ItemDataRole.UserRole, supplier[0])
            self.customer_by_id[supplier[0]] = supplier
            self.ui.suppliersList.addItem(item)
    
    def customerSelected(self, item):
        customer_id = item.data(Qt.ItemDataRole.UserRole)
        self.selectedCustomerData = self.customer_by_id.get(customer_id)
        is_enabled = self.selectedCustomerData is not None
        self.ui.deleteSupplierButton.setEnabled(is_enabled)
        self.ui.changeSupplierButton.setEnabled(is_enabled)

    def delSelectedCustomer(self):
        if not self.selectedCustomerData:
            return
        self.db.delCustomerById(self.selectedCustomerData[0])
        self.db.save()
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
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relativePath)

    def closeEvent(self, event):
        self.db.close()
        self.windowClosed.emit()
        super().closeEvent(event)

    def funcExitSystem(self):
        self.close()
