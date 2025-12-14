from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem
from PySide6.QtGui import QIcon
from createDocument import mainWindow as createDocWindow
from customers import mainWindow as customersWindow
from settings import mainWindow as settingsWindow
from utilities.tools import DatabaseTools as Tool
from params import mainWindow as paramsWindow
from database.database import Database
from utilities.config import Config
from ui_mainGui import Ui_MainWindow


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

        with open(
            self.resourcePath("utilities/config.json"), "r", encoding="utf-8"
        ) as f:
            self.configData = json.load(f)
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

        # edit menu buttons
        self.ui.editParamsButton.triggered.connect(self.openParamsWindow)

        # # settings menu buttons
        self.ui.suppliersMenuButton.triggered.connect(self.openSuppliersWindow)
        self.ui.settingsMenuButton.triggered.connect(self.openSettingsWindow)
        
        # func buttons 
        self.ui.createDocButton.clicked.connect(self.getTableData)
        self.ui.logisiticVar.currentIndexChanged.connect(self.logisticVarChanged)
        self.ui.customLine.editingFinished.connect(self.processFormula)
        self.ui.termDeliveryLine.editingFinished.connect(self.processFormula)
        self.ui.closeTableButton.clicked.connect(self.closeTable)
        self.ui.KpTable.resizeColumnsToContents()
        
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
            self.ui.KpTable.setRowCount(self.rows)
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
                        f"{df["col6"][rowNum].split()[0]} суток"
                    ),
                )
                                
            self.logisticCalculate()
            self.calculating()

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
        with open(
            self.resourcePath("utilities/variables.json"), "r", encoding="utf-8"
        ) as f:
            self.paramsData = json.load(f)
        
        for rowNum in range(self.rows - 1):
            print(f'tableData:{self.tableData}')
            price =  self.tableData['logistic'][rowNum] / self.tableData["amount"][rowNum]
            realPrice = 0
                         
            self.ui.KpTable.setItem(
                rowNum,
                8,
                QTableWidgetItem(
                    f"{self.tableData['currency'][rowNum]}{str(Tool.evalWithVars(f'{self.tableData['logistic'][rowNum]}*{self.formulaCustom}')).replace('.', ',')}"
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
            for col in range(5):
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

        self.db.open(self.resourcePath('database/database.db'))
        
        self.openCreateDocWindow((
            len(table_data),
            table_data))

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
