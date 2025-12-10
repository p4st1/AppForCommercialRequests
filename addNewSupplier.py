from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QLabel, QLineEdit
from PyQt6 import uic
import json
from utilities.config import Config
from database.database import Database
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
        uic.loadUi(self.resourcePath("ui/addSupplierGui.ui"), self)
        
        self.logoURL = 'None'
        
        self.acceptButton.clicked.connect(self.addNewSupplier)

    def addNewSupplier(self):
        db = Database()
        db.open(self.resourcePath('database/database.db'))
        data = (self.nameLine.text(),
                self.emailLine.text(),
                self.streetLine.text(),
                self.cityLine.text(),
                self.TINLine.text(),
                self.phoneNumLine.text(),
                self.websiteLine.text(),
                self.mailIndexLine.text(),
                self.roomLine.text(),
                self.buildingLine.text(),
                self.RRCLine.text(),
                self.logoURL
                )
        db.createSupplier(data)
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
