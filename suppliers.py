from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QLabel, QLineEdit
from PyQt6 import uic
import json
from utilities.config import Config
from database.database import Database
from addNewSupplier import mainWindow as newSupplierWindow
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
    windowClosed = pyqtSignal()

    def __init__(self, parent=None):
        super(mainWindow, self).__init__(parent)
        uic.loadUi(self.resourcePath("ui/suppliersGui.ui"), self)
        
        db = Database()
        db.open(self.resourcePath("database/database.db"))
        self.suppliers = db.getSuppliers()
        
        for supplier in self.suppliers:
            self.suppliersList.addItem(supplier[1])
        
        self.suppliersList.itemClicked.connect(self.supplierSelected)
        self.closeButton.clicked.connect(self.closeEvent)
        self.addSupplierButton.clicked.connect(self.openNewSupplier)
        print(self.suppliers)
        
    def supplierSelected(self, item):
        print(item.text())
        self.deleteSupplierButton.setEnabled(True)
        self.changeSupplierButton.setEnabled(True)

    def openNewSupplier(self):
        window = newSupplierWindow(self)
        window.show()
        
    def resourcePath(self, relativePath):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relativePath)

    def closeEvent(self, event):
        self.windowClosed.emit()
        super().closeEvent(event)
        self.close()

    def funcExitSystem(self):
        self.close()
