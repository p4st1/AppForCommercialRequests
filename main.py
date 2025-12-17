from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtCore import Qt, QUrl
from createDocument import mainWindow as createDocWindow
from create import createExcelFile as exportExcelFile
from customers import mainWindow as customersWindow
from settings import mainWindow as settingsWindow
from tools import DatabaseTools as Tool
from params import mainWindow as paramsWindow
from database import Database
from config import Config
from ui_mainGui import Ui_MainWindow
from datetime import datetime


import pandas as pd
import json
import sys
import os

class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.setWindowIcon(QIcon(self.resourcePath("logo.ico")))

        self.configData = Tool.load_json(Config.cfg_path)
        for setting, value in self.configData['settings'].items():
            Config.settings[setting] = bool(value)
        for setting, value in self.configData['config'].items():
            Config.config[setting] = value
                
        print(Config.settings)
                
        self.db = Database()
        
        if Config.settings['autoFill']:
            self.ui.logisticNum.setText(Config.config["logisticNum"])
            self.ui.customLine.setText(Config.config["customNum"])
            self.ui.termDeliveryLine.setText(Config.config["termDelivery"])

        self.ui.openTableButton.clicked.connect(self.openTable)

        self.ui.openTableMenuButton.triggered.connect(self.openTable)
        self.ui.closeTableMenuButton.triggered.connect(self.closeTable)
        self.ui.createDocMenuButton.triggered.connect(self.exportDocs)
        self.ui.createExcelMenuButton.triggered.connect(self.exportExcel)
        
        self.ui.editParamsButton.triggered.connect(self.openParamsWindow)
        
        self.ui.suppliersMenuButton.triggered.connect(self.openSuppliersWindow)
        self.ui.settingsMenuButton.triggered.connect(self.openSettingsWindow)
        self.ui.exportMenuButton.triggered.connect(self.exportDatabase)
        self.ui.importMenuButton.triggered.connect(self.importDatabase)
        
        self.ui.helpMenuButton.triggered.connect(self.show_help)
        self.ui.aboutMenuButton.triggered.connect(self.show_about)
        self.ui.GitHubMenuButton.triggered.connect(lambda: self.open_url("https://github.com/p4st1/AppForCommercialRequests"))
        self.ui.supportMenuButton.triggered.connect(self.show_help)
        
        self.ui.createDocButton.clicked.connect(self.exportDocs)
        self.ui.createExcelButton.clicked.connect(self.exportExcel)
        
        self.ui.logisiticVar.currentIndexChanged.connect(self.logisticVarChanged)
        self.ui.customLine.editingFinished.connect(self.processFormula)
        self.ui.termDeliveryLine.editingFinished.connect(self.processFormula)
        self.ui.closeTableButton.clicked.connect(self.closeTable)
        self.ui.KpTable.resizeColumnsToContents()

    def open_url(self, url):
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            print(f"{e}")
            
    def show_help(self):
        help_text = """
        <html>
        <head>
        <style>
            h2 { color: #2c3e50; }
            h3 { color: #34495e; }
            .hotkey { background: #ecf0f1; padding: 2px 6px; border-radius: 3px; }
        </style>
        </head>
        <body>
        <h2>📖 Справка по программе</h2>
        
        <h3>Основные функции</h3>
        <ul>
            <li><b>Настройки → Импортировать БД</b> - импортировать БД с заказчиками</li>
            <li><b>Настройки → Экспортировать БД</b> - сохранить текущую БД с заказчиками</li>
        </ul>
        
        <h3>Переменные</h3>
        <p>Для заполнения переменных, необходимо перейти в <b>Редактировать -> редактировать переменные</b>. Далее для использования переменных 
        необходимо соблюдать формат: $название переменной$</p>
        
        <h3>Логистика</h3>
        <li><b>Распределение</b> - распределяет указанную сумму на столбцы</li>
            <li><b>Коэффициент</b> - умножает указанную сумму на столбцы</li>
        
        <h3>Горячие клавиши</h3>
        <ul>
            <li><span class="hotkey">F1</span> - открыть справку</li>
            <li><span class="hotkey">Ctrl+O</span> - открыть таблицу</li>
        </ul>
        
        <h3>Поддержка</h3>
        <p>При возникновении проблем:</p>
        <ol>
            <li>Перезапустите программу</li>
            <li>Проверьте наличие обновлений</li>
            <li>Обратитесь в техподдержку: zemtsovpast@yandex.ru</li>
            <li>Телеграм: @p4strick</li>
        </ol>
        </body>
        </html>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Справка")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def show_about(self):
        """Показать информацию о программе"""
        QMessageBox.about(
            self,
            "О программе",
            "<b>Автоматизация подгтовки коммерческих приложений</b><br>"
            "Версия 1.0.0<br><br>"
            "Создано с использованием PySide6<br>"
            "© 2024 Все права защищены<br>"
            "Автор: https://github.com/p4st1"
        )
        
    def exportDatabase(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,                    
            "Сохранить файл",
            f"database_{datetime.now().strftime('%d.%m.%Y')}.db",
            "База данных (*.db);;Все файлы (*)"
        )
        self.db.export(Config.db_path, file_path)
        
    def importDatabase(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,                    
            "Открыть файл",
            "",
            "База данных (*.db);;Все файлы (*)"
        )
        print(file_path)
        self.db.import_(file_path, Config.db_path)
        
    def processFormula(self):
        self.formulaCustom = str(Tool.evalWithVars(f'{self.ui.customLine.text()}'))
        self.ui.customLine.setText(self.formulaCustom)
        
        if Config.isTableOpened:
            self.calculating()

    def openTable(self):
        self.ui.KpTable.clearContents()
        self.processFormula()
        
        Config.isTableOpened = True
        filename = QFileDialog.getOpenFileName(
            self, "Открыть файл", "", "csv (*.csv);; Excel Files (*.xls, *.xlsx)"
        )[0]

        if not self.ui.customLine.text():
            self.error('Ошибка', 'Заполните поле "Таможня"')
            return
        
        if not self.ui.termDeliveryLine.text():
            self.error('Ошибка', 'Заполните поле "Срок поставки"')
            return
        
        if not Tool.validNum(self.ui.termDeliveryLine.text()):
            self.error('Ошибка', '"Срок поставки" - не является числом')
            return
        
        try:
            df = pd.read_csv(filename, header=None, sep=";")
            df.columns = [f"col{i}" for i in range(len(df.columns))]
            print(df)
            df = df.fillna("")
            self.rows = len(df["col0"])
            totalPrices = []

            self.tableData = {
                "amount": [],
                "currency": [],
                "unitPrice": [],
                "totalPrice": [],
                'termDelivery': []
            }
            self.ui.KpTable.setRowCount(self.rows - 1)
            for rowNum in range(1, self.rows):
                colNum = 0
                for col in df.columns:
                    if df[col][rowNum]:
                        self.ui.KpTable.setItem(
                            rowNum - 1, colNum, QTableWidgetItem(str(df[col][rowNum]))
                        )
                    colNum += 1

                self.tableData["amount"].append(int(df["col4"][rowNum][0]))
                self.tableData["currency"].append(str(df["col5"][rowNum][0]))
                self.tableData["unitPrice"].append(
                    float(df["col5"][rowNum][1:].replace(",", "."))
                )
                self.tableData["totalPrice"].append(
                    self.tableData["amount"][rowNum - 1]
                    * self.tableData["unitPrice"][rowNum - 1]
                )
                self.tableData['termDelivery'].append(int(df['col6'][rowNum].split()[0]))

                self.ui.KpTable.setItem(
                    rowNum - 1,
                    6,
                    QTableWidgetItem(
                        f"{self.tableData['currency'][rowNum - 1]}{str(self.tableData['totalPrice'][rowNum - 1]).replace('.', ',')}"
                    ),
                )
                
                self.ui.KpTable.setItem(
                    rowNum - 1,
                    14,
                    QTableWidgetItem(
                        f"{df['col6'][rowNum].split()[0]} суток"
                    ),
                )
                                
            self.logisticCalculate()
            self.calculating()
        
            self.ui.tabWidget.setCurrentIndex(1)
            
        except Exception as e:
            self.error('Ошибка', f"Невозможно прочитать таблицу\n{e}")

    def error(self, title, text):
        error = QMessageBox(self)
        error.setWindowTitle(title)
        error.setText(text)
        error.exec()
            
    def openCreateDocWindow(self, tableData):
        window = createDocWindow(self, tableData=tableData)
        window.show()
        if Config.settings['closeTable']:
            window.windowClosed.connect(self.closeTable)
            self.ui.KpTable.setRowCount(0)
    
    def openParamsWindow(self):
        window = paramsWindow(self)
        window.show()
    
    def openSettingsWindow(self):
        window = settingsWindow(self)
        window.show()

    def openSuppliersWindow(self):
        window = customersWindow(self)
        window.show()

    def closeTable(self):
        self.ui.KpTable.clearContents()
        self.ui.KpTable.setRowCount(0)
        
    def calculating(self):
        self.paramsData = Tool.load_json(Config.vars_path)
            
        for rowNum in range(self.rows - 1):
            print(f'tableData:{self.tableData}')
            price =  self.tableData['logistic'][rowNum] / self.tableData["amount"][rowNum]
            realPrice = 0
                         
            self.ui.KpTable.setItem(
                rowNum,
                8,
                QTableWidgetItem(
                    f"{self.tableData['currency'][rowNum]}" + str(Tool.evalWithVars(f"{self.tableData['logistic'][rowNum]}*{self.formulaCustom}")).replace('.', ',')
                ),
            )
            self.ui.KpTable.setItem(
                rowNum, 9, QTableWidgetItem(f"{str(price).replace('.', ',')}")
            )

            priceIncrease = {(0, 13700): 1.25, (13700, 10**10): 1.4}

            for key, value in priceIncrease.items():
                if key[0] <= price <= key[1]:
                    realPrice = price * value
                    break

            self.ui.KpTable.setItem(
                rowNum, 10, QTableWidgetItem(f"{str(realPrice).replace('.', ',')}")
            )

            self.ui.KpTable.setItem(
                rowNum,
                11,
                QTableWidgetItem(
                    f"{str(realPrice * self.tableData['amount'][rowNum]).replace('.', ',')}"
                ),
            )

            for key, item in self.paramsData["parameters"].items():
                if item[0] == "НДС":
                    if item[2]:
                        temp_var = 1 + int(item[1]) / 100

            self.ui.KpTable.setItem(
                rowNum,
                12,
                QTableWidgetItem(
                    f"{str(realPrice * self.tableData['amount'][rowNum] * temp_var).replace('.', ',')}"
                ),
            )
            
            self.ui.KpTable.setItem(
                    rowNum,
                    13,
                    QTableWidgetItem(
                        f"{self.tableData['termDelivery'][rowNum] + int(self.ui.termDeliveryLine.text())} суток"
                    ),
                )
        
    def logisticVarChanged(self, ind):
        self.logisticCalculate()
        self.calculating()
        
    def logisticCalculate(self):
        logisticVarInd = self.ui.logisiticVar.currentIndex()
        self.tableData['logistic'] = []
        for rowNum in range(self.rows - 1):
            if logisticVarInd == 1:
                f = round(
                        self.tableData["totalPrice"][rowNum] + 60000/sum(self.tableData["totalPrice"]) * self.tableData["totalPrice"][rowNum],
                        2,
                    )
            else:
                f = round(
                        self.tableData["totalPrice"][rowNum] * float(self.ui.logisticNum.text()),
                        2
                )
            self.ui.KpTable.setItem(
            rowNum,
            7,
            QTableWidgetItem(
                f"{self.tableData['currency'][rowNum]}{str(f).replace('.', ',')}"
            ),
            )
            self.tableData['logistic'].append(f)
            
        
    def getTableData(self):
        table_data = []

        row_count = self.ui.KpTable.rowCount()
        col_count = self.ui.KpTable.columnCount()

        for row in range(row_count):
            row_data = []
            for col in range(6):
                item = self.ui.KpTable.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
                    
            for col in range(10, 15):
                item = self.ui.KpTable.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            table_data.append(row_data)

        self.db.open(Config.db_path)
        
        return table_data
    
    def exportDocs(self):
        tableData = self.getTableData()
        self.openCreateDocWindow((
            len(tableData),
            tableData))
     
    def exportExcel(self):
        tableData = []

        row_count = self.ui.KpTable.rowCount()
        col_count = self.ui.KpTable.columnCount()
        
        for row in range(row_count):
            row_data = []
            for col in range(6):
                item = self.ui.KpTable.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            
            for col in range(13, 15):
                item = self.ui.KpTable.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            tableData.append(row_data)

        print(f'logistic var: {self.ui.logisiticVar.currentIndex()}')
        print(f'logistic num: {self.ui.logisticNum.text()}')
        print(f'custom num: {self.ui.customLine.text()}')
        
        for row in tableData:
            print(' | '.join(list(map(str, row))))
        exportExcelFile((tableData, 
                         (self.ui.logisiticVar.currentIndex(), self.ui.logisticNum.text()),
                         self.ui.customLine.text(),
                         sum(self.tableData['totalPrice'])))
        
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
