from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QMainWindow, QMessageBox, QListWidgetItem, QTableWidgetItem
from database import Database
from config import Config
from create import createTextFile as exportTextFile
from ui_createDocGui import Ui_MainWindow
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

    def __init__(self, parent=None, tableData=None):
        super(mainWindow, self).__init__(parent)
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.createDocButton.clicked.connect(self.confirmDoc)
        
        self.db = Database()
        self.db.open(Config.db_path)
        self.suppliers = self.db.getAllCustomers()
        
        self.setupSuppliersItems()
        
        self.tableData = tableData
        
        self.ui.summaryTable.setColumnCount(9)
        self.ui.summaryTable.setRowCount(self.tableData[0])
        for row in range(self.tableData[0]):
            for col in range(8):
                self.ui.summaryTable.setItem(
                        row, col, QTableWidgetItem(str(self.tableData[1][row][col]))
                    )
                
        self.ui.payComboBox.currentIndexChanged.connect(self.indChanged)
        self.ui.payLineEdit.textChanged.connect(self.payUpd)
                
        self.ui.summaryTable.resizeColumnsToContents()     
        self.payInd = 0
        self.pay = ['на дату подписания спецификации Поставщиком',
                    'на дату оплаты',
                    '']
        self.ui.payLineEdit.setEnabled(False)
    
    def payUpd(self):
        self.pay[2] =  self.ui.payLineEdit.text()
        
    def indChanged(self, ind):
        self.payInd = ind
        if self.payInd == 2:
            self.ui.payLineEdit.setEnabled(True)
        else:
            self.ui.payLineEdit.setEnabled(False)
            
            
    def confirmDoc(self):
        confirmedSuppliers = []
        for i in range(self.ui.suppliersList.count()):
            item = self.ui.suppliersList.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                confirmedSuppliers.append(self.db.getCustomer(item.text())[0])
        extraData = self.getExtraData()
        if confirmedSuppliers:
            id = self.db.createOffer()
            self.db.save()
            exportTextFile((self.tableData, 
                            confirmedSuppliers, 
                            extraData, 
                            str(id), 
                            self.ui.radioButton.isChecked(),
                            self.pay[self.payInd]),
                           )
            self.close()
        
    def getExtraData(self):
        result = []
        result.append(self.ui.numLine.text())
        result.append(self.ui.warrantyPeriod.text())
        result.append(self.ui.conditionLine.text())
        result.append(self.ui.producerLine.text())
        result.append(self.ui.deliveryTimeLine.text())
        return result
    
    def setupSuppliersItems(self):
        self.ui.suppliersList.clear()
        for supplier in self.suppliers:
            item = QListWidgetItem(supplier[7])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.ui.suppliersList.addItem(item)
             
    
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
        self.db.close()
        self.close()
