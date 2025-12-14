from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QMainWindow, QFileDialog
from tools import DatabaseTools as Tool
from ui_settingsAppGui import Ui_MainWindow
import json
from config import Config
import sys
import os


class mainWindow(QMainWindow):
    windowClosed = Signal()

    def __init__(self, parent=None):
        super(mainWindow, self).__init__(parent)
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        

        
        self.ui.closeTableCheckBox.setChecked(Config.settings['closeTable'])
        self.ui.autoFillCheckBox.setChecked(Config.settings['autoFill'])
        
        self.ui.autoFillCheckBox.toggled.connect(self.autoFillChange)
        self.ui.closeTableCheckBox.toggled.connect(self.closeTableChange)
        
        self.ui.CPdirLine.setText(self.resourcePath(Config.config['pathToSaveCP']))
        self.ui.dirOpenButton.clicked.connect(self.selectDirectory)
    
    def autoFillChange(self, signal):
        Config.settings['autoFill'] = signal
        
    def closeTableChange(self, signal):
        Config.settings['closeTable'] = signal
            
    def selectDirectory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите директорию",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            Config.config['pathToSaveCP'] = directory
            self.ui.CPdirLine.setText(directory)
            
    def resourcePath(self, relativePath):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relativePath)

    def closeEvent(self, event):
        data = {'config' : Config.config,
                'settings' : Config.settings}
        Tool.save_json_atomic(Config.cfg_path, data)
        self.windowClosed.emit()
        super().closeEvent(event)
        self.close()

    def funcExitSystem(self):
        self.close()
