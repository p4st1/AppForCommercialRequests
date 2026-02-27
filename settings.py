from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QFileDialog
from tools import DatabaseTools as Tool
from ui_settingsAppGui import Ui_MainWindow
from config import Config
from pathlib import Path
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
        self.ui.openLastTable.setChecked(Config.settings['openLastTab'])
        self.ui.openUpdateTab.setChecked(Config.settings['openUpdateTab'])
        
        self.ui.autoFillCheckBox.toggled.connect(self.autoFillChange)
        self.ui.closeTableCheckBox.toggled.connect(self.closeTableChange)
        self.ui.openLastTable.toggled.connect(self.openLastTableChange)
        self.ui.openUpdateTab.toggled.connect(self.openUpdateTabChange)

        default_dir = Path.home() / "Documents"
        cp_dir = Tool.ensure_directory(Config.config.get('pathToSaveCP'), default_dir)
        excel_dir = Tool.ensure_directory(Config.config.get('pathToSaveExcel') or cp_dir, cp_dir)
        Config.config['pathToSaveCP'] = str(cp_dir)
        Config.config['pathToSaveExcel'] = str(excel_dir)

        self.ui.CPdirLine.setText(str(cp_dir))
        self.ui.dirOpenButton.clicked.connect(self.selectDirectory)

        self.ui.ExcelDirLine.setText(str(excel_dir))
        self.ui.dirOpenButton_2.clicked.connect(self.selectDirectory2)
        
        self.ui.excelIndent.setValue(int(Config.config['ExcelIndent']))
        self.ui.excelIndent.valueChanged.connect(self.ExcelIndentChange)
    
    def ExcelIndentChange(self, value):
        Config.config['ExcelIndent'] = str(value)
        
    def openUpdateTabChange(self, signal):
        Config.settings['openUpdateTab'] = signal
         
    def openLastTableChange(self, signal):
        Config.settings['openLastTab'] = signal 
    
    def autoFillChange(self, signal):
        Config.settings['autoFill'] = signal
        
    def closeTableChange(self, signal):
        Config.settings['closeTable'] = signal
            
    def selectDirectory(self):
        current_dir = Config.config.get('pathToSaveCP', str(Path.home()))
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите директорию",
            current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            Config.config['pathToSaveCP'] = directory
            if not Config.config.get('pathToSaveExcel'):
                Config.config['pathToSaveExcel'] = directory
                self.ui.ExcelDirLine.setText(directory)
            self.ui.CPdirLine.setText(directory)
    
    def selectDirectory2(self):
        current_dir = Config.config.get('pathToSaveExcel', Config.config.get('pathToSaveCP', str(Path.home())))
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите директорию",
            current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            Config.config['pathToSaveExcel'] = directory
            self.ui.ExcelDirLine.setText(directory)
            
    def resourcePath(self, relativePath):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relativePath)

    def closeEvent(self, event):
        default_dir = Path.home() / "Documents"
        cp_dir = Tool.ensure_directory(Config.config.get('pathToSaveCP'), default_dir)
        excel_dir = Tool.ensure_directory(Config.config.get('pathToSaveExcel') or cp_dir, cp_dir)
        Config.config['pathToSaveCP'] = str(cp_dir)
        Config.config['pathToSaveExcel'] = str(excel_dir)

        data = {'config' : Config.config,
                'settings' : Config.settings}
        Tool.save_json_atomic(Config.cfg_path, data)
        self.windowClosed.emit()
        super().closeEvent(event)

    def funcExitSystem(self):
        self.close()
