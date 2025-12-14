# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'createDocument.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLayout,
    QLineEdit, QListView, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(893, 612)
        MainWindow.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        MainWindow.setAnimated(True)
        MainWindow.setDocumentMode(True)
        MainWindow.setTabShape(QTabWidget.TabShape.Rounded)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.summaryTable = QTableWidget(self.centralwidget)
        if (self.summaryTable.columnCount() < 9):
            self.summaryTable.setColumnCount(9)
        __qtablewidgetitem = QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(6, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(7, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(8, __qtablewidgetitem8)
        self.summaryTable.setObjectName(u"summaryTable")
        self.summaryTable.setMinimumSize(QSize(891, 358))
        self.summaryTable.setStyleSheet(u"QTableWidget {\n"
"    background-color: #f8f9fa;\n"
"    gridline-color: #dee2e6;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 8px;\n"
"    font-family: 'Segoe UI', Arial, sans-serif;\n"
"    font-size: 12px;\n"
"    selection-background-color: #e3f2fd;\n"
"    selection-color: #1565c0;\n"
"}\n"
"\n"
"QHeaderView::section {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    padding: 10px;\n"
"    border: none;\n"
"    font-weight: bold;\n"
"    font-size: 13px;\n"
"    border-right: 1px solid #34495e;\n"
"    border-bottom: 2px solid #1a252f;\n"
"}\n"
"\n"
"QHeaderView::section:first {\n"
"    border-top-left-radius: 7px;\n"
"}\n"
"\n"
"QHeaderView::section:last {\n"
"    border-top-right-radius: 7px;\n"
"}\n"
"\n"
"QTableWidget::item {\n"
"    padding: 8px;\n"
"    border-bottom: 1px solid #e9ecef;\n"
"}\n"
"\n"
"QTableWidget::item:nth-child(even) {\n"
"    background-color: #f8f9fa;\n"
"}\n"
"\n"
"QTableWidget::item:nth-child(odd) {\n"
"    background-color: white;\n"
"}\n"
"\n"
""
                        "QTableWidget::item:selected {\n"
"    background-color: #e3f2fd;\n"
"    color: #1565c0;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"QTableWidget::item[column=\"amount\"] {\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"QTableWidget::item[positive=\"true\"] {\n"
"    color: #2e7d32;\n"
"    background-color: #e8f5e9;\n"
"}\n"
"\n"
"QTableWidget::item[negative=\"true\"] {\n"
"    color: #c62828;\n"
"    background-color: #ffebee;\n"
"}\n"
"\n"
"QTableWidget::item[zero=\"true\"] {\n"
"    color: #757575;\n"
"    font-style: italic;\n"
"}\n"
"\n"
"QTableWidget QTableCornerButton::section {\n"
"    background-color: #2c3e50;\n"
"    border-top-left-radius: 7px;\n"
"}\n"
"\n"
"QScrollBar:vertical {\n"
"    border: none;\n"
"    background: #f8f9fa;\n"
"    width: 10px;\n"
"    border-radius: 5px;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical {\n"
"    background: #b0bec5;\n"
"    border-radius: 5px;\n"
"    min-height: 20px;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical:hover {\n"
"    background: #78909c;\n"
"}\n"
"\n"
"QScrol"
                        "lBar::add-line:vertical, QScrollBar::sub-line:vertical {\n"
"    height: 0px;\n"
"}")
        self.summaryTable.setWordWrap(True)
        self.summaryTable.horizontalHeader().setCascadingSectionResizes(False)
        self.summaryTable.horizontalHeader().setDefaultSectionSize(32)
        self.summaryTable.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.summaryTable)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.horizontalLayout_2.setContentsMargins(5, 0, 5, -1)
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(-1, -1, 20, -1)
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_4.addWidget(self.label_2)

        self.suppliersList = QListWidget(self.centralwidget)
        QListWidgetItem(self.suppliersList)
        QListWidgetItem(self.suppliersList)
        QListWidgetItem(self.suppliersList)
        QListWidgetItem(self.suppliersList)
        QListWidgetItem(self.suppliersList)
        QListWidgetItem(self.suppliersList)
        QListWidgetItem(self.suppliersList)
        QListWidgetItem(self.suppliersList)
        QListWidgetItem(self.suppliersList)
        self.suppliersList.setObjectName(u"suppliersList")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.suppliersList.sizePolicy().hasHeightForWidth())
        self.suppliersList.setSizePolicy(sizePolicy)
        self.suppliersList.setStyleSheet(u"QListWidget {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 8px;\n"
"    font-size: 12px;\n"
"    padding: 5px;\n"
"}\n"
"\n"
"QListWidget::item {\n"
"    padding: 8px 12px;\n"
"    border-bottom: 1px solid #f1f3f5;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QListWidget::item:selected {\n"
"    background-color: #e3f2fd;\n"
"    color: #1565c0;\n"
"    font-weight: 500;\n"
"}")
        self.suppliersList.setFrameShape(QFrame.Shape.NoFrame)
        self.suppliersList.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.suppliersList.setDragEnabled(False)
        self.suppliersList.setMovement(QListView.Movement.Static)

        self.verticalLayout_4.addWidget(self.suppliersList)


        self.horizontalLayout_2.addLayout(self.verticalLayout_4)

        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(10)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(10, 0, -1, 5)
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy1)
        self.label_3.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")

        self.gridLayout.addWidget(self.label_3, 4, 3, 1, 1)

        self.numLine = QLineEdit(self.centralwidget)
        self.numLine.setObjectName(u"numLine")
        sizePolicy1.setHeightForWidth(self.numLine.sizePolicy().hasHeightForWidth())
        self.numLine.setSizePolicy(sizePolicy1)
        self.numLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout.addWidget(self.numLine, 3, 3, 1, 1)

        self.deliveryTimeLine = QLineEdit(self.centralwidget)
        self.deliveryTimeLine.setObjectName(u"deliveryTimeLine")
        self.deliveryTimeLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout.addWidget(self.deliveryTimeLine, 1, 4, 1, 1)

        self.label_5 = QLabel(self.centralwidget)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")
        self.label_5.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter)

        self.gridLayout.addWidget(self.label_5, 0, 4, 1, 1)

        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter)

        self.gridLayout.addWidget(self.label_4, 2, 4, 1, 1)

        self.warrantyPeriod = QLineEdit(self.centralwidget)
        self.warrantyPeriod.setObjectName(u"warrantyPeriod")
        self.warrantyPeriod.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout.addWidget(self.warrantyPeriod, 3, 4, 1, 1)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label, 2, 3, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 0, 3, 1, 1)

        self.label_6 = QLabel(self.centralwidget)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")
        self.label_6.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft)

        self.gridLayout.addWidget(self.label_6, 0, 5, 1, 1)

        self.producerLine = QLineEdit(self.centralwidget)
        self.producerLine.setObjectName(u"producerLine")
        self.producerLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout.addWidget(self.producerLine, 1, 5, 1, 1)

        self.label_7 = QLabel(self.centralwidget)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")

        self.gridLayout.addWidget(self.label_7, 2, 5, 1, 1)

        self.conditionLine = QLineEdit(self.centralwidget)
        self.conditionLine.setObjectName(u"conditionLine")
        self.conditionLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout.addWidget(self.conditionLine, 3, 5, 1, 1)


        self.horizontalLayout_2.addLayout(self.gridLayout)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.VLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.createDocButton = QPushButton(self.centralwidget)
        self.createDocButton.setObjectName(u"createDocButton")
        self.createDocButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    border: none;\n"
"    padding: 4px 4px;\n"
"    border-radius: 6px;\n"
"    font-weight: 600;\n"
"    font-size: 12px;\n"
"    min-height: 35px;\n"
"    min-width: 32px;\n"
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

        self.horizontalLayout.addWidget(self.createDocButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u0421\u043e\u0437\u0434\u0430\u043d\u0438\u0435 \u043a\u043e\u043c\u043c\u0435\u0440\u0447\u0435\u0441\u043a\u043e\u0433\u043e \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u044f", None))
        ___qtablewidgetitem = self.summaryTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"\u2116", None));
        ___qtablewidgetitem1 = self.summaryTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435", None));
        ___qtablewidgetitem2 = self.summaryTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"\u041a\u0430\u0442\u0430\u043b\u043e\u0436\u043d\u044b\u0439 \u0442\u043e\u0432\u0430\u0440", None));
        ___qtablewidgetitem3 = self.summaryTable.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"\u0415\u0434. \u0438\u0437\u043c.", None));
        ___qtablewidgetitem4 = self.summaryTable.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"\u041a\u043e\u043b-\u0432\u043e", None));
        ___qtablewidgetitem5 = self.summaryTable.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"\u0426\u0435\u043d\u0430 \u0437\u0430 \u0435\u0434. \u0431\u0435\u0437 \u041d\u0414\u0421", None));
        ___qtablewidgetitem6 = self.summaryTable.horizontalHeaderItem(6)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MainWindow", u"\u0418\u0442\u043e\u0433\u043e \u0431\u0435\u0437 \u041d\u0414\u0421", None));
        ___qtablewidgetitem7 = self.summaryTable.horizontalHeaderItem(7)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("MainWindow", u"\u0418\u0442\u043e\u0433\u043e \u0441 \u041d\u0414\u0421", None));
        ___qtablewidgetitem8 = self.summaryTable.horizontalHeaderItem(8)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0440\u043e\u043a \u043f\u043e\u0441\u0442\u0430\u0432\u043a\u0438", None));
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0437\u0430\u043a\u0430\u0437\u0447\u0438\u043a\u0430", None))

        __sortingEnabled = self.suppliersList.isSortingEnabled()
        self.suppliersList.setSortingEnabled(False)
        ___qlistwidgetitem = self.suppliersList.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("MainWindow", u"1", None));
        ___qlistwidgetitem1 = self.suppliersList.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("MainWindow", u"1", None));
        ___qlistwidgetitem2 = self.suppliersList.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("MainWindow", u"2", None));
        ___qlistwidgetitem3 = self.suppliersList.item(3)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("MainWindow", u"\u041d\u043e\u0432\u044b\u0439 \u044d\u043b\u0435\u043c\u0435\u043d\u0442", None));
        ___qlistwidgetitem4 = self.suppliersList.item(4)
        ___qlistwidgetitem4.setText(QCoreApplication.translate("MainWindow", u"3", None));
        ___qlistwidgetitem5 = self.suppliersList.item(5)
        ___qlistwidgetitem5.setText(QCoreApplication.translate("MainWindow", u"4", None));
        ___qlistwidgetitem6 = self.suppliersList.item(6)
        ___qlistwidgetitem6.setText(QCoreApplication.translate("MainWindow", u"5", None));
        ___qlistwidgetitem7 = self.suppliersList.item(7)
        ___qlistwidgetitem7.setText(QCoreApplication.translate("MainWindow", u"6", None));
        ___qlistwidgetitem8 = self.suppliersList.item(8)
        ___qlistwidgetitem8.setText(QCoreApplication.translate("MainWindow", u"\u041d\u043e\u0432\u044b\u0439 \u044d\u043b\u0435\u043c\u0435\u043d\u0442", None));
        self.suppliersList.setSortingEnabled(__sortingEnabled)

        self.label_3.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0440\u043e\u043a \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f \u041a\u041f:", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0440\u043e\u043a \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0440\u043e\u043a \u0433\u0430\u0440\u0430\u043d\u0442\u0438\u0438", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u041d\u043e\u043c\u0435\u0440 \u0437\u0430\u044f\u0432\u043a\u0438", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u044c", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"\u0423\u0441\u043b\u043e\u0432\u0438\u044f \u043e\u043f\u043b\u0430\u0442\u044b", None))
        self.createDocButton.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
    # retranslateUi

