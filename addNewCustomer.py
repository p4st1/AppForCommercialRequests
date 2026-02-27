from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox
from database import Database
from tools import DatabaseTools as Tool
from ui_addCustomerGui import Ui_MainWindow
from config import Config
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

    def _confirm_duplicate_resolution(self, duplicate_row):
        duplicate_name = " ".join(
            part for part in [duplicate_row[2], duplicate_row[1], duplicate_row[3]] if str(part).strip()
        ).strip() or "—"
        duplicate_email = str(duplicate_row[5] or "").strip() or "—"
        duplicate_phone = str(duplicate_row[6] or "").strip() or "—"
        duplicate_company = str(duplicate_row[7] or "").strip() or "—"

        msg = QMessageBox(self)
        msg.setWindowTitle("Возможный дубликат заказчика")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(
            "Найдена похожая запись.\n\n"
            f"Компания: {duplicate_company}\n"
            f"Контакт: {duplicate_name}\n"
            f"Email: {duplicate_email}\n"
            f"Телефон: {duplicate_phone}\n\n"
            "Обновить существующего заказчика?"
        )
        update_button = msg.addButton("Обновить существующего", QMessageBox.ButtonRole.AcceptRole)
        create_button = msg.addButton("Создать нового", QMessageBox.ButtonRole.ActionRole)
        cancel_button = msg.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(update_button)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == update_button:
            return "update"
        if clicked == create_button:
            return "create"
        if clicked == cancel_button:
            return "cancel"
        return "cancel"

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

        full_name = " ".join(part for part in [surname, name, patronymic] if str(part).strip())
        duplicate_row = db.findPotentialCustomerDuplicate(
            company_name=companyName,
            email=email,
            phone=phone,
            full_name=full_name,
            exclude_customer_id=self.edit_customer_id,
        )

        if self.edit_customer_id is None and duplicate_row is not None:
            resolution = self._confirm_duplicate_resolution(duplicate_row)
            if resolution == "cancel":
                db.close()
                return
            if resolution == "update":
                db.updateCustomer(int(duplicate_row[0]), data)
                db.save()
                db.close()
                self.close()
                return

        if self.edit_customer_id is not None:
            db.updateCustomer(self.edit_customer_id, data)
        else:
            db.createCustomer(data)
        db.save()
        db.close()
        self.close()

    def resourcePath(self, relativePath):
        return Tool.resourcePath(relativePath)

    def closeEvent(self, event):
        self.windowClosed.emit()
        super().closeEvent(event)

    def funcExitSystem(self):
        self.close()
