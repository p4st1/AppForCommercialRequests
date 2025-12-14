from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox, QLabel, QLineEdit
from ui_paramsGui import Ui_MainWindow
from ui_createParamsGui import Ui_MainWindow as Ui_addNewParamWindow
from tools import DatabaseTools as Tool
import json
from config import Config
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

        self.ui.addButton.clicked.connect(self.addParam)
        self.ui.cancelButton.clicked.connect(self.cancelParam)

    def cancelParam(self):
        self.close()

    def addParam(self):

        with open(
            self.resourcePath("utilities/variables.json"), "r", encoding="utf-8"
        ) as f:
            self.paramsData = json.load(f)
            self.paramsData["parameters"][len(self.paramsData["parameters"]) + 1] = [
                self.ui.nameEdit.text(),
                self.ui.valueEdit.text(),
                Config.types[self.typeEdit.currentText()],
            ]
        with open(
            self.resourcePath("utilities/variables.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(self.paramsData, f, indent=4)
        self.close()
    
    def resourcePath(self, relativePath):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relativePath)

    def closeEvent(self, event):
        self.close()

    def funcExitSystem(self):
        self.close()


class mainWindow(QMainWindow):
    windowClosed = Signal()

    def __init__(self, parent=None):
        super(mainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.parameters = {}
        self.hasChanges = False

        with open(
            self.resourcePath("utilities/variables.json"), "r", encoding="utf-8"
        ) as f:
            self.paramsData = json.load(f)

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
        for key, item in self.parameters.items():
            value = item.text().split("%")[0]
            if value.isdigit():
                self.paramsData["parameters"][key] = [
                    self.paramsData["parameters"][key][0],
                    value,
                    "percents",
                ]
            else:
                error = QMessageBox(self)
                error.setWindowTitle("Ошибка")
                error.setText(f"Введены некорректные данные: {value}")
                error.exec()
        with open(self.resourcePath("utilities/variables.json"), "w", encoding='utf-8') as f:
            json.dump(self.paramsData, f, indent=4)
        self.saveButton.setDisabled(True)
        self.saveAndCloseButton.setDisabled(True)
        self.hasChanges = False

    def saveChangesAndClose(self):
        for key, item in self.parameters.items():
            value = item.text().split("%")[0]
            if value.isdigit():
                self.paramsData["parameters"][key] = [
                    self.paramsData["parameters"][key][0],
                    value,
                    "percents",
                ]
            else:
                error = QMessageBox(self)
                error.setWindowTitle("Ошибка")
                error.setText(f"Введены некорректные данные: {value}")
                error.exec()
        with open(self.resourcePath("utilities/variables.json"), "w", encoding='utf-8') as f:
            json.dump(self.paramsData, f, indent=4)
        self.saveButton.setDisabled(True)
        self.saveAndCloseButton.setDisabled(True)
        self.hasChanges = False
        self.close()

    def onTextValueChanged(self, arg):
        self.hasChanges = True
        self.saveButton.setDisabled(False)
        self.saveAndCloseButton.setDisabled(False)

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
        self.close()

    def funcExitSystem(self):
        self.close()
