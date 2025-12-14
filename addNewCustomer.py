from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox, QLabel, QLineEdit
from utilities.tools import DatabaseTools as Tool
import json
from utilities.config import Config
from database.database import Database
from ui_addCustomerGui import Ui_MainWindow
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

    def __init__(self, parent=None, exist=[]):
        super(mainWindow, self).__init__(parent)
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.logoURL = 'None'
        
        self.ui.acceptButton.clicked.connect(self.addNewSupplier)
        
        if exist:
            print(exist)
            self.ui.nameLine.setText(f'{exist[2]} {exist[1]} {exist[3]}')
            self.ui.emailLine.setText(exist[5])
            self.ui.companyNameLine.setText(exist[7])
            self.ui.phoneNumLine.setText(exist[6])
            self.ui.postLine.setText(exist[8])
            self.ui.condLine.setText(exist[9])


    def addNewSupplier(self):
        db = Database()
        db.open(self.resourcePath('database/database.db'))
        
        if self.ui.nameLine.text():
            surname, name, patronymic = self.ui.nameLine.text().split()
        else:
            surname, name, patronymic = '', '', ''

        fullAddress = ''
        if self.ui.mailIndexLine.text():
            fullAddress += self.ui.mailIndexLine.text()
        
        if self.ui.cityLine.text():
            fullAddress += f' {self.ui.cityLine.text()}'
        
        if self.ui.streetLine.text():
            fullAddress += f' {self.ui.streetLine.text()}'
        
        if self.ui.buildingLine.text():
            fullAddress += f' {self.ui.buildingLine.text()}'
        
        if self.ui.roomLine.text():
            fullAddress += f" {self.ui.roomLine.text()}"
            
        if self.ui.emailLine.text():
            email = self.ui.emailLine.text()
        else:
            email = ''
            
        if self.ui.phoneNumLine.text():
            phone = self.ui.phoneNumLine.text()
        else:
            phone = ''
            
        if self.ui.companyNameLine.text():
            companyName = self.ui.companyNameLine.text()
        else:
            companyName = ''
        
        if self.ui.postLine.text():
            post = self.ui.postLine.text()
        else:
            post = ''
            
        if self.ui.condLine.text():
            conditions = self.ui.condLine.text()
        else:
            conditions = ''

        data = (
            name,
            surname,
            patronymic,
            fullAddress,
            email,
            phone,
            companyName,
            post,
            conditions
                )
        
        print(data)
        db.createCustomer(data)
        db.save()
        db.close()
        self.close()
    
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
