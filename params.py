from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox, QLabel, QLineEdit
from ui_paramsGui import Ui_MainWindow
from ui_createParamsGui import Ui_MainWindow as Ui_addNewParamWindow
from tools import DatabaseTools as Tool
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


class addNewParamGUI(QMainWindow):
    def __init__(self, parent=None):
        super(addNewParamGUI, self).__init__(parent)
        self.ui = Ui_addNewParamWindow()
        self.ui.setupUi(self)
        apply_unified_theme(self)

        self.ui.addButton.clicked.connect(self.addParam)
        self.ui.cancelButton.clicked.connect(self.cancelParam)

    def cancelParam(self):
        self.close()

    def addParam(self):
        name = self.ui.nameEdit.text().strip()
        value_raw = self.ui.valueEdit.text().strip().replace(",", ".")
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название переменной")
            return
        try:
            value = str(float(value_raw))
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите числовое значение")
            return

        self.paramsData = Tool.load_json(Config.vars_path)
        keys = [int(k) for k in self.paramsData.get("parameters", {}).keys() if str(k).isdigit()]
        next_key = str(max(keys, default=0) + 1)
        self.paramsData["parameters"][next_key] = [
            name,
            value,
            Config.types[self.ui.typeEdit.currentText()],
        ]
        Tool.save_json_atomic(Config.vars_path, self.paramsData)
        self.close()
    
    def resourcePath(self, relativePath):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relativePath)

    def closeEvent(self, event):
        super().closeEvent(event)

    def funcExitSystem(self):
        self.close()


class mainWindow(QMainWindow):
    windowClosed = Signal()

    def __init__(self, parent=None):
        super(mainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        apply_unified_theme(self)

        self.parameters = {}
        self.hasChanges = False

        self.paramsData = Tool.load_json(Config.vars_path)  

        self.ui.saveButton.setDisabled(True)
        self.ui.saveAndCloseButton.setDisabled(True)

        for key, item in self.paramsData["parameters"].items():
            label = QLabel()
            label.setText(item[0])
            _name = f"lineEdit{key}"
            self._name = QLineEdit()
            value = str(item[1]) + self.getValueType(item[2])
            self._name.setText(value)
            self._name.textEdited.connect(self.onTextValueChanged)

            self.ui.parametersLabels.addWidget(label)
            self.ui.parametersValues.addWidget(self._name)

            if key not in self.parameters:
                self.parameters[key] = self._name

        self.ui.addNewButton.clicked.connect(self.addNewParamGui)
        self.ui.saveButton.clicked.connect(self.saveChanges)
        self.ui.saveAndCloseButton.clicked.connect(self.saveChangesAndClose)
        self.ui.cancelButton.clicked.connect(self.cancelChanges)

    def saveChanges(self):
        data = Tool.load_json(Config.vars_path)
        for key, item in self.parameters.items():
            raw = item.text().strip().replace(",", ".")
            if not raw:
                QMessageBox.warning(self, "Ошибка", f"Поле {data['parameters'][key][0]} пустое")
                return
            if raw[-1] in Config.types:
                symbol = raw[-1]
                value_part = raw[:-1]
                calc_type = Config.types[symbol]
            else:
                value_part = raw
                calc_type = data["parameters"][key][2]
            try:
                value = str(float(value_part))
            except ValueError:
                error = QMessageBox(self)
                error.setWindowTitle("Ошибка")
                error.setText(f"Введены некорректные данные: {raw}")
                error.exec()
                return

            data["parameters"][key] = [
                data["parameters"][key][0],
                value,
                calc_type,
            ]

        Tool.save_json_atomic(Config.vars_path, data)
        self.ui.saveButton.setDisabled(True)
        self.ui.saveAndCloseButton.setDisabled(True)
        self.hasChanges = False

    def saveChangesAndClose(self):
        data = Tool.load_json(Config.vars_path)
        for key, item in self.parameters.items():
            raw = item.text().strip().replace(",", ".")
            if not raw:
                QMessageBox.warning(self, "Ошибка", f"Поле {data['parameters'][key][0]} пустое")
                return
            if raw[-1] in Config.types:
                symbol = raw[-1]
                value_part = raw[:-1]
                calc_type = Config.types[symbol]
            else:
                value_part = raw
                calc_type = data["parameters"][key][2]
            try:
                value = str(float(value_part))
            except ValueError:
                error = QMessageBox(self)
                error.setWindowTitle("Ошибка")
                error.setText(f"Введены некорректные данные: {raw}")
                error.exec()
                return

            data["parameters"][key] = [
                data["parameters"][key][0],
                value,
                calc_type,
            ]

        Tool.save_json_atomic(Config.vars_path, data)
        self.ui.saveButton.setDisabled(True)
        self.ui.saveAndCloseButton.setDisabled(True)
        self.hasChanges = False
        self.close()

    def onTextValueChanged(self, arg):
        self.hasChanges = True
        self.ui.saveButton.setDisabled(False)
        self.ui.saveAndCloseButton.setDisabled(False)

    def getValueType(self, value):
        if value == "percents":
            return "%"
        if value == 'multiply':
            return '*'
        if value == 'division':
            return '/'

    def addNewParamGui(self):
        window = addNewParamGUI(self)
        window.show()

    def cancelChanges(self):
        if self.hasChanges:
            res = Dialog.myDialog(self)
            if res is True:
                self.close()
        else:
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
