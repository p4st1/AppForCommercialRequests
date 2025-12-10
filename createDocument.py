from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QLabel, QLineEdit, QListWidgetItem, QTableWidgetItem
from PyQt6 import uic
import json
from utilities.config import Config
from database.database import Database
from addNewSupplier import mainWindow as newSupplierWindow
from create import createTextFile as exportTextFile
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

    def __init__(self, parent=None, tableData=None):
        super(mainWindow, self).__init__(parent)
        uic.loadUi(self.resourcePath("ui/createDocument.ui"), self)
        
        self.createDocButton.clicked.connect(self.confirmDoc)
        
        self.db = Database()
        self.db.open('database/database.db')
        self.suppliers = self.db.getAllSuppliers()
        
        self.setupSuppliersItems()
        
        self.tableData = tableData
        print(self.tableData)
        
        self.summaryTable.setColumnCount(8)
        self.summaryTable.setRowCount(self.tableData[0])
        for row in range(self.tableData[0]):
            for col in range(8):
                self.summaryTable.setItem(
                        row, col, QTableWidgetItem(str(self.tableData[1][row][col]))
                    )
                
        self.summaryTable.resizeColumnsToContents()     
           
    def confirmDoc(self):
        confirmedSuppliers = []
        for i in range(self.suppliersList.count()):
            item = self.suppliersList.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                for supplier in self.suppliers:
                    if supplier[1] == item.text():
                        confirmedSuppliers.append(supplier)
        print(confirmedSuppliers)
        exportTextFile(self.tableData)
                
    def setupSuppliersItems(self):
        self.suppliersList.clear()
        for supplier in self.suppliers:
            item = QListWidgetItem(supplier[1])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.suppliersList.addItem(item)
             
    
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
