from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox, QLabel, QLineEdit
from tools import DatabaseTools as Tool
import json
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
        self.db.open(Config.db_path)
        
        self.ui.suppliersList.itemClicked.connect(self.customerSelected)
        self.ui.closeButton.clicked.connect(self.close)
        self.ui.addSupplierButton.clicked.connect(self.openNewCustomer)
        self.ui.changeSupplierButton.clicked.connect(self.openExistCustomer)
        self.ui.deleteSupplierButton.clicked.connect(self.delSelectedCustomer)
        
        self.showSuppliers()
    
    def showSuppliers(self):
        self.suppliers = self.db.getAllCustomers()
        self.ui.suppliersList.clear()
        for supplier in self.suppliers:
            self.ui.suppliersList.addItem(supplier[7])
    
    def customerSelected(self, item):
        self.selectedCustomerData = self.db.getCustomer(item.text())
        self.ui.deleteSupplierButton.setEnabled(True)
        self.ui.changeSupplierButton.setEnabled(True)

    def delSelectedCustomer(self):
        self.db.delCustomer(self.selectedCustomerData[0][7])
        self.db.save()
        self.showSuppliers()
        self.ui.deleteSupplierButton.setEnabled(False)
        self.ui.changeSupplierButton.setEnabled(False)
        
    def openExistCustomer(self):
        self.db.delCustomer(self.selectedCustomerData[0][7])
        self.db.save()
        window = newSupplierWindow(self, exist=self.selectedCustomerData[0])
        window.show()
        window.windowClosed.connect(self.showSuppliers)
        
    def openNewCustomer(self):
        window = newSupplierWindow(self, exist=[])
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
        self.close()

    def funcExitSystem(self):
        self.close()
