from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem
from createDocument import mainWindow as createDocWindow
from suppliers import mainWindow as suppliersWindow
from params import mainWindow as paramsWindow
from database.database import Database
from utilities.tools import DatabaseTools as Tool
from PyQt6 import uic
import pandas as pd
import json
import sys
import os


class Dialog:
    def myDialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Подтверждение")
        dlg.setText("База данных не сохранена. Отменить изменения?")
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
    def __init__(self):
        super().__init__()
        uic.loadUi(self.resourcePath("ui/mainGui.ui"), self)

        with open(
            self.resourcePath("utilities/config.json"), "r", encoding="utf-8"
        ) as f:
            self.configData = json.load(f)

        self.db = Database()

        self.logisticNum.setText(self.configData["config"]["logisticNum"])

        self.openTableButton.clicked.connect(self.openTable)

        # edit menu buttons
        self.editParamsButton.triggered.connect(self.openParamsWindow)

        # settings menu buttons
        self.suppliersMenuButton.triggered.connect(self.openSuppliersWindow)
        
        # func buttons 
        self.createDocButton.clicked.connect(self.getTableData)
        self.logisiticVar.currentIndexChanged.connect(self.logisticVarChanged)
        
        self.KpTable.resizeColumnsToContents()   

    def openTable(self):
        self.KpTable.clearContents()
        
        filename = QFileDialog.getOpenFileName(
            self, "Открыть файл", "", "csv (*.csv);; Excel Files (*.xls, *.xlsx)"
        )[0]

        try:
            df = pd.read_csv(filename, header=None, sep=";")
            df.columns = [f"col{i}" for i in range(len(df.columns))]
            df = df.fillna("")
            self.rows = len(df["col0"])
            totalPrices = []

            self.tableData = {
                "amount": [],
                "currency": [],
                "unitPrice": [],
                "totalPrice": [],
            }
            self.KpTable.setRowCount(self.rows)
            for rowNum in range(1, self.rows):
                colNum = 0
                for col in df.columns:
                    if df[col][rowNum]:
                        self.KpTable.setItem(
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

                self.KpTable.setItem(
                    rowNum - 1,
                    6,
                    QTableWidgetItem(
                        f"{self.tableData['currency'][rowNum - 1]}{str(self.tableData['totalPrice'][rowNum - 1]).replace('.', ',')}"
                    ),
                )

            # calc and write
            self.logisticCalculate()
            self.calculating()

        except Exception as e:
            error = QMessageBox(self)
            error.setWindowTitle("Ошибка")
            error.setText(f"Невозможно прочитать таблицу\n{e}")
            error.exec()

    def openCreateDocWindow(self, tableData):
        window = createDocWindow(self, tableData=tableData)
        window.show()
        
    def openParamsWindow(self):
        window = paramsWindow(self)
        window.show()
        # window.windowClosed.connect(self.test)

    def openSuppliersWindow(self):
        window = suppliersWindow(self)
        window.show()
        # window.windowClosed.connect(self.test)

    def calculating(self):
        with open(
            self.resourcePath("utilities/variables.json"), "r", encoding="utf-8"
        ) as f:
            self.paramsData = json.load(f)
        
        for rowNum in range(self.rows - 1):
            print(f'tableData:{self.tableData}')
            price =  self.tableData['logistic'][rowNum] / self.tableData["amount"][rowNum]
            realPrice = 0
            
            print(rowNum)
            
            
            #Qline edit сделать работу с переменными
            self.KpTable.setItem(
                rowNum,
                8,
                QTableWidgetItem(
                    f"{self.tableData['currency'][rowNum]}{str(Tool.evalWithVars(f'{self.tableData['logistic'][rowNum]}{self.customLine.text()}')).replace('.', ',')}"
                ),
            )
            self.KpTable.setItem(
                rowNum, 9, QTableWidgetItem(f"{str(price).replace('.', ',')}")
            )

            priceIncrease = {(0, 13700): 1.25, (13700, 10**10): 1.4}

            for key, value in priceIncrease.items():
                if key[0] <= price <= key[1]:
                    realPrice = price * value
                    break

            self.KpTable.setItem(
                rowNum, 10, QTableWidgetItem(f"{str(realPrice).replace('.', ',')}")
            )

            self.KpTable.setItem(
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

            self.KpTable.setItem(
                rowNum,
                12,
                QTableWidgetItem(
                    f"{str(realPrice * self.tableData['amount'][rowNum] * temp_var).replace('.', ',')}"
                ),
            )
        
    def logisticVarChanged(self, ind):
        self.logisticCalculate()
        self.calculating()
        
    def logisticCalculate(self):
        logisticVarInd = self.logisiticVar.currentIndex()
        self.tableData['logistic'] = []
        for rowNum in range(self.rows - 1):
            if logisticVarInd == 1:
                f = round(
                        self.tableData["totalPrice"][rowNum] + 60000/sum(self.tableData["totalPrice"]) * self.tableData["totalPrice"][rowNum],
                        2,
                    )
            else:
                f = round(
                        self.tableData["totalPrice"][rowNum] * float(self.logisticNum.text()),
                        2
                )
            self.KpTable.setItem(
            rowNum,
            7,
            QTableWidgetItem(
                f"{self.tableData['currency'][rowNum]}{str(f).replace('.', ',')}"
            ),
            )
            self.tableData['logistic'].append(f)
            
        
    def getTableData(self):
        table_data = []

        row_count = self.KpTable.rowCount()
        col_count = self.KpTable.columnCount()

        for row in range(row_count):
            row_data = []
            for col in range(5):
                item = self.KpTable.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
                    
            for col in range(10, 13):
                item = self.KpTable.item(row, col)
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
