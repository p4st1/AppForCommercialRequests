from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox
from database import Database
from ui_addCustomerGui import Ui_MainWindow
from config import Config
from ui_theme import apply_unified_theme
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

    def __init__(self, parent=None, exist=None):
        super(mainWindow, self).__init__(parent)
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        apply_unified_theme(self)
        
        self.logoURL = 'None'
        self.edit_customer_id = None
        
        self.ui.acceptButton.clicked.connect(self.addNewSupplier)
        
        if exist:
            self.edit_customer_id = exist[0]
            self.ui.nameLine.setText(f'{exist[2]} {exist[1]} {exist[3]}')
            self.ui.emailLine.setText(exist[5])
            self.ui.companyNameLine.setText(exist[7])
            self.ui.phoneNumLine.setText(exist[6])
            self.ui.postLine.setText(exist[8])
            self.ui.condLine.setText(exist[9])
            if exist[10] == 'женский':
                self.ui.sexComboBox.setCurrentIndex(1)

    @staticmethod
    def split_full_name(full_name: str):
        parts = full_name.split()
        surname = parts[0] if len(parts) > 0 else ''
        name = parts[1] if len(parts) > 1 else ''
        patronymic = " ".join(parts[2:]) if len(parts) > 2 else ''
        return surname, name, patronymic

    def addNewSupplier(self):
        db = Database()
        if db.open(Config.db_path) == -1:
            QMessageBox.critical(self, "Ошибка", "Не удалось открыть базу данных")
            return
        
        surname, name, patronymic = self.split_full_name(self.ui.nameLine.text().strip())

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
           
        if self.ui.sexComboBox.currentIndex() == 0:
            sex = 'мужской'
        else:
            sex = 'женский'

        data = (
            name,
            surname,
            patronymic,
            fullAddress,
            email,
            phone,
            companyName,
            post,
            conditions,
            sex
                )

        if not companyName:
            QMessageBox.warning(self, "Ошибка", "Заполните поле \"Название компании\"")
            db.close()
            return

        if self.edit_customer_id is not None:
            db.updateCustomer(self.edit_customer_id, data)
        else:
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

    def funcExitSystem(self):
        self.close()
