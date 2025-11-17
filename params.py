from PyQt6.QtCore import Qt, QDate, QDateTime, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QTableWidgetItem,
    QMenu,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QLineEdit
)
from PyQt6.QtGui import (
    QFont
)
from PyQt6 import uic
import json
from utilities.config import Config



class Dialog():
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
        uic.loadUi("ui/createParams.ui", self)

        self.addButton.clicked.connect(self.addParam)
        self.cancelButton.clicked.connect(self.cancelParam)
        
    def cancelParam(self):
        self.close()
        
    def addParam(self):
        
        with open('utilities/variables.json', 'r', encoding='utf-8') as f:
            self.paramsData = json.load(f)
            self.paramsData['parameters'][len(self.paramsData['parameters']) + 1] = [self.nameEdit.text(), 
                                                                                     self.valueEdit.text(), 
                                                                                     Config.types[self.typeEdit.currentText()]]
        with open('utilities/variables.json', 'w', encoding='utf-8') as f:
            json.dump(self.paramsData, f, indent=4)
        self.close()
    
    
    def closeEvent(self, event):
        self.close()
    
    def funcExitSystem(self):
        self.close()


class mainWindow(QMainWindow):
    windowClosed = pyqtSignal()

    def __init__(self, parent=None):
        super(mainWindow, self).__init__(parent)
        uic.loadUi("ui/paramsGui.ui", self)
    
        self.parameters = {}
        self.hasChanges = False
        
        with open('utilities/variables.json', 'r', encoding='utf-8') as f:
            self.paramsData = json.load(f)

        self.saveButton.setDisabled(True)
        self.saveAndCloseButton.setDisabled(True)
        
        for key, item in self.paramsData['parameters'].items():
            print(key, item)
            
            label = QLabel()
            label.setText(item[0])
            _name = f'lineEdit{key}'
            self._name = QLineEdit()
            value = str(item[1]) + self.getValueType(item[2])
            self._name.setText(value)
            self._name.textEdited.connect(self.onTextValueChanged)

            self.parametersLabels.addWidget(label)
            self.parametersValues.addWidget(self._name)

            if key not in self.parameters:
                self.parameters[key] = self._name

        self.addNewButton.clicked.connect(self.addNewParamGui)
        self.saveButton.clicked.connect(self.saveChanges)
        self.saveAndCloseButton.clicked.connect(self.saveChangesAndClose)
        self.cancelButton.clicked.connect(self.cancelChanges)

    def saveChanges(self):
        for key, item in self.parameters.items():
            value = item.text().split('%')[0]
            if value.isdigit():
                self.paramsData['parameters'][key] = [self.paramsData['parameters'][key][0], value, 'percents']
            else:
                error = QMessageBox(self)
                error.setWindowTitle("Ошибка")
                error.setText(
                    f"Введены некорректные данные: {value}")
                error.exec()
        with open('utilities/variables.json', 'w') as f:
            json.dump(self.paramsData, f, indent=4)
        self.saveButton.setDisabled(True)
        self.saveAndCloseButton.setDisabled(True)
        self.hasChanges = False
    
    def saveChangesAndClose(self):
        for key, item in self.parameters.items():
            value = item.text().split('%')[0]
            if value.isdigit():
                self.paramsData['parameters'][key] = [self.paramsData['parameters'][key][0], value, 'percents']
            else:
                error = QMessageBox(self)
                error.setWindowTitle("Ошибка")
                error.setText(
                    f"Введены некорректные данные: {value}")
                error.exec()
        with open('utilities/variables.json', 'w') as f:
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
        if value == 'percents':
            return '%'
          
    def addNewParamGui(self):
        window = addNewParamGUI(self)
        window.show()
        print(window)
        
    def cancelChanges(self):
        if self.hasChanges:
            res = Dialog.myDialog(self)
            if res is True:
                self.close()
        else:
            self.close()
        
    def closeEvent(self, event):
        self.windowClosed.emit()
        super().closeEvent(event)
        self.close()
    
    def funcExitSystem(self):
        self.close()