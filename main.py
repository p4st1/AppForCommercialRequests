from PyQt6.QtCore import Qt, QDate, QDateTime
from PyQt6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QTableWidgetItem,
    QMenu
)
from PyQt6.QtGui import (
    QFont
)
from PyQt6 import QtWidgets, QtCore, QtGui
from os import listdir
from os.path import isfile, join
from PyQt6 import uic
from datetime import datetime
from utilities.config import Config
from params import mainWindow as paramsWindow
from create import createTextFile as exportTextFile
import pandas as pd
import json


class Dialog():
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
        uic.loadUi("ui/mainGui.ui", self)
        
        with open('utilities/config.json', 'r', encoding='utf-8') as f:
            self.configData = json.load(f)
            
        self.logisticNum.setText(self.configData['config']['logisticNum'])
            
        self.openTableButton.clicked.connect(self.openTable)
        self.editParamsButton.triggered.connect(self.openParamsWindow)

        
    def openTable(self):
        self.KpTable.clearContents()
        filename = QFileDialog.getOpenFileName(
            self, 'Открыть файл', '', 'csv (*.csv);; Excel Files (*.xls, *.xlsx)')[0]
        
        try:
            df = pd.read_csv(filename, header=None, sep=';') 
            df.columns = [f'col{i}' for i in range(len(df.columns))]
            df = df.fillna('')
            self.rows = len(df['col0'])
            totalPrices = []

            self.tableData = {
                'amount' : [],
                'currency': [],
                'unitPrice': [],
                'totalPrice': [],
            }

            print(df)

            #read
            for rowNum in range(1, self.rows):
                print(1)
                colNum = 0
                for col in df.columns:
                    print(col, rowNum)
                    if df[col][rowNum]:
                        self.KpTable.setItem(
                            rowNum-1, colNum, QTableWidgetItem(str(df[col][rowNum])))
                    colNum += 1
                    
                self.tableData['amount'].append(int(df['col4'][rowNum][0]))
                self.tableData['currency'].append(str(df['col5'][rowNum][0]))
                self.tableData['unitPrice'].append(float(df['col5'][rowNum][1:].replace(',', '.')))
                self.tableData['totalPrice'].append(self.tableData['amount'][rowNum - 1] * self.tableData['unitPrice'][rowNum - 1])    
                
                self.KpTable.setItem(
                                rowNum-1, 6, QTableWidgetItem(f'{self.tableData['currency'][rowNum - 1]}{str(self.tableData['totalPrice'][rowNum - 1]).replace('.', ',')}'))

            #calc and write
            self.test()

        except Exception as e:
            error = QMessageBox(self)
            error.setWindowTitle("Ошибка")
            error.setText(
                f"Невозможно прочитать таблицу\n{e}")
            print(e)
            error.exec()
            
    def openParamsWindow(self):
        window = paramsWindow(self)
        window.show()
        window.windowClosed.connect(self.test)
    
    def test(self):
        with open('utilities/variables.json', 'r', encoding='utf-8') as f:
                    self.paramsData = json.load(f)

        for rowNum in range(self.rows - 1):
            print(rowNum),
            f = round(60000 + self.tableData['totalPrice'][rowNum] / sum(self.tableData['totalPrice']) * self.tableData['totalPrice'][rowNum], 2)
            price = f/self.tableData['amount'][rowNum]
            realPrice = 0
            self.KpTable.setItem(
                            rowNum, 7, QTableWidgetItem(f'{self.tableData['currency'][rowNum]}{str(f).replace('.', ',')}'))
            self.KpTable.setItem(
                            rowNum, 8, QTableWidgetItem(f'{self.tableData['currency'][rowNum]}{str(f).replace('.', ',')}'))
            self.KpTable.setItem(
                            rowNum, 9, QTableWidgetItem(f'{str(price).replace('.', ',')}'))
            
            priceIncrease = {(0, 13700): 1.25,
                                (13700, 10**10): 1.4}

            for key, value in priceIncrease.items():
                print(key, value, price)
                if key[0] <= price <= key[1]:
                    realPrice = price * value
                    break
            
            print(realPrice)

            self.KpTable.setItem(
                            rowNum, 10, QTableWidgetItem(f'{str(realPrice).replace('.', ',')}'))

            self.KpTable.setItem(
                            rowNum, 11, QTableWidgetItem(f'{str(realPrice * self.tableData['amount'][rowNum]).replace('.', ',')}'))
            
            for key, item in self.paramsData['parameters'].items():
                if item[0] == 'НДС':
                    if item[2]:
                        temp_var = 1 + int(item[1])/100

            self.KpTable.setItem(
                            rowNum, 12, QTableWidgetItem(f'{str(realPrice * self.tableData['amount'][rowNum] * temp_var).replace('.', ',')}'))
            
        print(self.tableData, sep='\n')
        a = self.createTextFile()
        print(a)
        exportTextFile(a)


    def createTextFile(self):
        table_data = []
    
        row_count = self.KpTable.rowCount()
        col_count = self.KpTable.columnCount()
    
        for row in range(row_count):
            row_data = []
            for col in range(col_count):
                item = self.KpTable.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            table_data.append(row_data)
        
        return (len(table_data), len(table_data[0]), table_data)
    
    def closeEvent(self, event):
        self.close()
    
    def funcExitSystem(self):
        self.close()