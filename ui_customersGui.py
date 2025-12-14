# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'suppliersGui.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(763, 574)
        font = QFont()
        font.setFamilies([u"Inter"])
        MainWindow.setFont(font)
        MainWindow.setWindowTitle(u"\u0417\u0430\u043a\u0430\u0437\u0447\u0438\u043a\u0438")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName(u"scrollArea")
        font1 = QFont()
        font1.setFamilies([u"Segoe UI"])
        font1.setPointSize(9)
        font1.setBold(False)
        self.scrollArea.setFont(font1)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaItems = QWidget()
        self.scrollAreaItems.setObjectName(u"scrollAreaItems")
        self.scrollAreaItems.setGeometry(QRect(0, 0, 743, 505))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaItems)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.scrollArea_2 = QScrollArea(self.scrollAreaItems)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setFont(font1)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 741, 503))
        self.verticalLayout_4 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.suppliersList = QListWidget(self.scrollAreaWidgetContents)
        self.suppliersList.setObjectName(u"suppliersList")
        self.suppliersList.setFont(font1)

        self.verticalLayout_3.addWidget(self.suppliersList)


        self.verticalLayout_4.addLayout(self.verticalLayout_3)

        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_2.addWidget(self.scrollArea_2)

        self.scrollArea.setWidget(self.scrollAreaItems)

        self.verticalLayout.addWidget(self.scrollArea)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(5, 0, 5, 10)
        self.addSupplierButton = QPushButton(self.centralwidget)
        self.addSupplierButton.setObjectName(u"addSupplierButton")
        font2 = QFont()
        font2.setBold(True)
        self.addSupplierButton.setFont(font2)
        self.addSupplierButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    border: none;\n"
"    padding: 4px 4px;\n"
"    border-radius: 6px;\n"
"    font-weight: 600;\n"
"    font-size: 12px;\n"
"    min-height: 24px;\n"
"    min-width: 100px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #34495e;\n"
"    border: 1px solid #2c3e50;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #1a252f;\n"
"}")

        self.horizontalLayout.addWidget(self.addSupplierButton)

        self.deleteSupplierButton = QPushButton(self.centralwidget)
        self.deleteSupplierButton.setObjectName(u"deleteSupplierButton")
        self.deleteSupplierButton.setEnabled(False)
        self.deleteSupplierButton.setFont(font2)
        self.deleteSupplierButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    border: none;\n"
"    padding: 4px 4px;\n"
"    border-radius: 6px;\n"
"    font-weight: 600;\n"
"    font-size: 12px;\n"
"    min-height: 24px;\n"
"    min-width: 100px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #34495e;\n"
"    border: 1px solid #2c3e50;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #1a252f;\n"
"}\n"
"QPushButton:disabled {\n"
"    background-color: #cccccc;\n"
"    color: #666666;\n"
"}\n"
"\n"
"QPushButton:enabled {\n"
"    background-color: #2c3e50;\n"
"}")
        self.deleteSupplierButton.setCheckable(False)
        self.deleteSupplierButton.setChecked(False)
        self.deleteSupplierButton.setAutoRepeat(False)
        self.deleteSupplierButton.setAutoDefault(False)
        self.deleteSupplierButton.setFlat(False)

        self.horizontalLayout.addWidget(self.deleteSupplierButton)

        self.changeSupplierButton = QPushButton(self.centralwidget)
        self.changeSupplierButton.setObjectName(u"changeSupplierButton")
        self.changeSupplierButton.setEnabled(False)
        self.changeSupplierButton.setFont(font2)
        self.changeSupplierButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    border: none;\n"
"    padding: 4px 4px;\n"
"    border-radius: 6px;\n"
"    font-weight: 600;\n"
"    font-size: 12px;\n"
"    min-height: 24px;\n"
"    min-width: 100px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #34495e;\n"
"    border: 1px solid #2c3e50;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #1a252f;\n"
"}\n"
"QPushButton:disabled {\n"
"    background-color: #cccccc;\n"
"    color: #666666;\n"
"}\n"
"\n"
"QPushButton:enabled {\n"
"    background-color: #2c3e50;\n"
"}")
        self.changeSupplierButton.setCheckable(False)
        self.changeSupplierButton.setChecked(False)

        self.horizontalLayout.addWidget(self.changeSupplierButton)

        self.closeButton = QPushButton(self.centralwidget)
        self.closeButton.setObjectName(u"closeButton")
        self.closeButton.setFont(font2)
        self.closeButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    border: none;\n"
"    padding: 4px 4px;\n"
"    border-radius: 6px;\n"
"    font-weight: 600;\n"
"    font-size: 12px;\n"
"    min-height: 24px;\n"
"    min-width: 100px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #34495e;\n"
"    border: 1px solid #2c3e50;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #1a252f;\n"
"}")

        self.horizontalLayout.addWidget(self.closeButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.deleteSupplierButton.setDefault(False)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        self.addSupplierButton.setText(QCoreApplication.translate("MainWindow", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437\u0447\u0438\u043a\u0430", None))
        self.deleteSupplierButton.setText(QCoreApplication.translate("MainWindow", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430", None))
        self.changeSupplierButton.setText(QCoreApplication.translate("MainWindow", u"\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0434\u0430\u043d\u043d\u044b\u0435", None))
        self.closeButton.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c", None))
        pass
    # retranslateUi

