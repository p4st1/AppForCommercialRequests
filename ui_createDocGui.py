# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'createDocument.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QLayout, QLineEdit, QListView, QListWidget,
    QListWidgetItem, QMainWindow, QPushButton, QRadioButton,
    QSizePolicy, QSpacerItem, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1104, 810)
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
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
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

        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        sizePolicy1.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy1)
        self.label_3.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")

        self.gridLayout.addWidget(self.label_3, 4, 3, 1, 1)

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

        self.radioButton = QRadioButton(self.centralwidget)
        self.radioButton.setObjectName(u"radioButton")
        self.radioButton.setAutoFillBackground(False)
        self.radioButton.setStyleSheet(u"\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"\n"
"")

        self.gridLayout.addWidget(self.radioButton, 1, 3, 1, 1)

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

        self.label_7 = QLabel(self.centralwidget)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")

        self.gridLayout.addWidget(self.label_7, 2, 5, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 0, 3, 1, 1)

        self.label_8 = QLabel(self.centralwidget)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")
        self.label_8.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft)

        self.gridLayout.addWidget(self.label_8, 0, 6, 1, 1)

        self.payComboBox = QComboBox(self.centralwidget)
        self.payComboBox.addItem("")
        self.payComboBox.addItem("")
        self.payComboBox.addItem("")
        self.payComboBox.setObjectName(u"payComboBox")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.payComboBox.sizePolicy().hasHeightForWidth())
        self.payComboBox.setSizePolicy(sizePolicy2)
        self.payComboBox.setStyleSheet(u"QQMainWindow {\n"
"    background-color: #f5f7fa;\n"
"	font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;\n"
"}\n"
"\n"
"/* ===== \u0426\u0415\u041d\u0422\u0420\u0410\u041b\u042c\u041d\u042b\u0419 \u0412\u0418\u0414\u0416\u0415\u0422 ===== */\n"
"QWidget#centralWidget {\n"
"    background-color: #f5f7fa;\n"
"    padding: 15px;\n"
"}\n"
"\n"
"/* ===== \u0422\u0410\u0411\u041b\u0418\u0426\u0410 (\u041e\u0441\u043d\u043e\u0432\u043d\u043e\u0439 \u0432\u0438\u0434\u0436\u0435\u0442) ===== */\n"
"QTableWidget {\n"
"    background-color: #ffffff;\n"
"    gridline-color: #dee2e6;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 10px;\n"
"    font-family: 'Inter';\n"
"    font-size: 12px;\n"
"    selection-background-color: #e3f2fd;\n"
"    selection-color: #1565c0;\n"
"    alternate-background-color: #f8f9fa;\n"
"    padding: 2px;\n"
"}\n"
"\n"
"/* \u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u0438 \u0441\u0442\u043e\u043b\u0431\u0446\u043e\u0432 \u0442\u0430\u0431\u043b\u0438"
                        "\u0446\u044b */\n"
"QHeaderView::section {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    padding: 12px 15px;\n"
"    border: none;\n"
"    font-weight: 600;\n"
"    font-size: 13px;\n"
"    border-right: 1px solid #34495e;\n"
"    border-bottom: 2px solid #1a252f;\n"
"    text-align: left;\n"
"}\n"
"\n"
"QHeaderView::section:first {\n"
"    border-top-left-radius: 9px;\n"
"    padding-left: 20px;\n"
"}\n"
"\n"
"QHeaderView::section:last {\n"
"    border-top-right-radius: 9px;\n"
"    border-right: none;\n"
"}\n"
"\n"
"/* \u042f\u0447\u0435\u0439\u043a\u0438 \u0442\u0430\u0431\u043b\u0438\u0446\u044b */\n"
"QTableWidget::item {\n"
"    padding: 10px 15px;\n"
"    border-bottom: 1px solid #f1f3f5;\n"
"}\n"
"\n"
"/* \u0427\u0435\u0440\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u0435 \u0441\u0442\u0440\u043e\u043a \u0442\u0430\u0431\u043b\u0438\u0446\u044b */\n"
"QTableWidget::item:nth-child(even) {\n"
"    background-color: #f8f9fa;\n"
"}\n"
"\n"
"QTableWidget::item:nth-child(odd) {\n"
"    back"
                        "ground-color: #ffffff;\n"
"}\n"
"\n"
"/* \u0412\u044b\u0434\u0435\u043b\u0435\u043d\u043d\u0430\u044f \u0441\u0442\u0440\u043e\u043a\u0430 */\n"
"QTableWidget::item:selected {\n"
"    background-color: #e3f2fd;\n"
"    color: #1565c0;\n"
"    font-weight: 500;\n"
"    border-left: 3px solid #2196f3;\n"
"}\n"
"\n"
"\n"
"\n"
"/* \u041a\u043d\u043e\u043f\u043a\u0438 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0439 */\n"
"QPushButton#addButton {\n"
"    background-color: #27ae60;\n"
"}\n"
"\n"
"QPushButton#addButton:hover {\n"
"    background-color: #2ecc71;\n"
"}\n"
"\n"
"QPushButton#deleteButton {\n"
"    background-color: #e74c3c;\n"
"}\n"
"\n"
"QPushButton#deleteButton:hover {\n"
"    background-color: #c0392b;\n"
"}\n"
"\n"
"QPushButton#editButton {\n"
"    background-color: #3498db;\n"
"}\n"
"\n"
"QPushButton#editButton:hover {\n"
"    background-color: #2980b9;\n"
"}\n"
"\n"
"QPushButton#exportButton {\n"
"    background-color: #9b59b6;\n"
"}\n"
"\n"
"QPushButton#exportButton:hover {\n"
"    background-colo"
                        "r: #8e44ad;\n"
"}\n"
"\n"
"/* ===== \u041f\u0410\u041d\u0415\u041b\u042c \u0418\u041d\u0421\u0422\u0420\u0423\u041c\u0415\u041d\u0422\u041e\u0412 ===== */\n"
"QToolBar {\n"
"    background-color: #2c3e50;\n"
"    border: none;\n"
"    padding: 5px;\n"
"    spacing: 10px;\n"
"    border-bottom: 2px solid #1a252f;\n"
"}\n"
"\n"
"QToolBar QToolButton {\n"
"    background-color: transparent;\n"
"    color: white;\n"
"    padding: 8px;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QToolBar QToolButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QToolBar QToolButton:pressed {\n"
"    background-color: rgba(255, 255, 255, 0.2);\n"
"}\n"
"\n"
"/* ===== \u0421\u0422\u0410\u0422\u0423\u0421 \u0411\u0410\u0420 ===== */\n"
"QStatusBar {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    font-size: 11px;\n"
"    padding: 8px 15px;\n"
"    border-top: 1px solid #34495e;\n"
"}\n"
"\n"
"QStatusBar QLabel {\n"
"    color: white;\n"
"    padding: 0 10px;\n"
"}\n"
"\n"
"/* ===== \u041c\u0415"
                        "\u041d\u042e \u0411\u0410\u0420 ===== */\n"
"QMenuBar {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    border-bottom: 2px solid #1a252f;\n"
"}\n"
"\n"
"QMenuBar::item {\n"
"    background-color: transparent;\n"
"    padding: 8px 15px;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QMenuBar::item:selected {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QMenuBar::item:pressed {\n"
"    background-color: rgba(255, 255, 255, 0.2);\n"
"}\n"
"\n"
"QMenu {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    border: 1px solid #34495e;\n"
"    border-radius: 6px;\n"
"    padding: 5px;\n"
"}\n"
"\n"
"QMenu::item {\n"
"    padding: 8px 30px 8px 20px;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QMenu::item:selected {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QMenu::separator {\n"
"    height: 1px;\n"
"    background-color: #34495e;\n"
"    margin: 5px 10px;\n"
"}\n"
"\n"
"/* ===== \u041f\u0410\u041d\u0415\u041b\u042c \u0418\u041d\u0421\u0422\u0420\u0423"
                        "\u041c\u0415\u041d\u0422\u041e\u0412 \u0421\u041b\u0415\u0412\u0410/\u0421\u041f\u0420\u0410\u0412\u0410 ===== */\n"
"QDockWidget {\n"
"    background-color: #ffffff;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 8px;\n"
"    font-size: 12px;\n"
"    titlebar-close-icon: url(close.png);\n"
"    titlebar-normal-icon: url(float.png);\n"
"}\n"
"\n"
"QDockWidget::title {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    padding: 10px;\n"
"    border-top-left-radius: 7px;\n"
"    border-top-right-radius: 7px;\n"
"    text-align: center;\n"
"    font-weight: 600;\n"
"}\n"
"\n"
"/* ===== \u0413\u0420\u0423\u041f\u041f\u041e\u0412\u042b\u0415 \u0411\u041e\u041a\u0421\u042b ===== */\n"
"QGroupBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 8px;\n"
"    margin-top: 10px;\n"
"    padding-top: 15px;\n"
"    font-weight: 600;\n"
"    font-size: 13px;\n"
"    color: #2c3e50;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"  "
                        "  left: 15px;\n"
"    padding: 0 10px;\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"/* ===== \u041c\u0415\u0422\u041a\u0418 ===== */\n"
"QLabel {\n"
"    color: #2c3e50;\n"
"    font-size: 12px;\n"
"    padding: 2px;\n"
"}\n"
"\n"
"QLabel#titleLabel {\n"
"    font-size: 16px;\n"
"    font-weight: 700;\n"
"    color: #2c3e50;\n"
"}\n"
"\n"
"QLabel#totalLabel {\n"
"    font-size: 14px;\n"
"    font-weight: 600;\n"
"    color: #2c3e50;\n"
"    padding: 10px;\n"
"    background-color: #e8f5e9;\n"
"    border-radius: 6px;\n"
"    border: 1px solid #c8e6c9;\n"
"}\n"
"\n"
"\n"
"\n"
"QLineEdit:focus, QComboBox:focus, QDateEdit:focus {\n"
"    border: 1px solid #3498db;\n"
"    background-color: #f8fdff;\n"
"}\n"
"\n"
"QComboBox::drop-down {\n"
"    border: none;\n"
"    background-color: #2c3e50;\n"
"    border-radius: 0 5px 5px 0;\n"
"    width: 25px;\n"
"}\n"
"\n"
"QComboBox::down-arrow {\n"
"    image: url(down_arrow.png);\n"
"    width: 12px;\n"
"    height: 6"
                        "px;\n"
"}\n"
"\n"
"/* ===== \u041f\u041e\u041b\u041e\u0421\u042b \u041f\u0420\u041e\u041a\u0420\u0423\u0422\u041a\u0418 ===== */\n"
"QScrollBar:vertical {\n"
"    border: none;\n"
"    background: #f8f9fa;\n"
"    width: 12px;\n"
"    border-radius: 6px;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical {\n"
"    background: #b0bec5;\n"
"    border-radius: 6px;\n"
"    min-height: 30px;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical:hover {\n"
"    background: #78909c;\n"
"}\n"
"\n"
"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n"
"    height: 0px;\n"
"}\n"
"\n"
"QScrollBar:horizontal {\n"
"    border: none;\n"
"    background: #f8f9fa;\n"
"    height: 12px;\n"
"    border-radius: 6px;\n"
"}\n"
"\n"
"QScrollBar::handle:horizontal {\n"
"    background: #b0bec5;\n"
"    border-radius: 6px;\n"
"    min-width: 30px;\n"
"}\n"
"\n"
"QScrollBar::handle:horizontal:hover {\n"
"    background: #78909c;\n"
"}\n"
"\n"
"/* ===== \u0421\u041f\u0418\u0421\u041e\u041a (QListWidget) ===== */\n"
"QListWidget {\n"
"    ba"
                        "ckground-color: white;\n"
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
"}\n"
"\n"
"/* ===== \u0414\u0415\u0420\u0415\u0412\u041e (QTreeWidget) ===== */\n"
"QTreeWidget {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 8px;\n"
"    font-size: 12px;\n"
"}\n"
"\n"
"QTreeWidget::item {\n"
"    padding: 8px;\n"
"    border-bottom: 1px solid #f1f3f5;\n"
"}\n"
"\n"
"QTreeWidget::item:selected {\n"
"    background-color: #e3f2fd;\n"
"    color: #1565c0;\n"
"}\n"
"\n"
"/* ===== \u0412\u041a\u041b\u0410\u0414\u041a\u0418 (QTabWidget) ===== */\n"
"QTabWidget::pane {\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 8px;\n"
"    background-color: white"
                        ";\n"
"    margin-top: 5px;\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"    background-color: #f8f9fa;\n"
"    color: #2c3e50;\n"
"    padding: 10px 20px;\n"
"    margin-right: 2px;\n"
"    border-top-left-radius: 6px;\n"
"    border-top-right-radius: 6px;\n"
"    font-weight: 600;\n"
"}\n"
"\n"
"QTabBar::tab:selected {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"}\n"
"\n"
"QTabBar::tab:hover:!selected {\n"
"    background-color: #e9ecef;\n"
"}\n"
"\n"
"/* ===== \u041f\u0410\u041d\u0415\u041b\u042c \u0424\u0418\u041b\u042c\u0422\u0420\u041e\u0412 ===== */\n"
"QWidget#filterPanel {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 8px;\n"
"    padding: 15px;\n"
"}\n"
"\n"
"/* ===== \u0421\u0422\u0410\u0422\u0423\u0421\u041d\u042b\u0415 \u0418\u041a\u041e\u041d\u041a\u0418 ===== */\n"
"QLabel[status=\"success\"] {\n"
"    color: #27ae60;\n"
"    font-weight: 600;\n"
"}\n"
"\n"
"QLabel[status=\"warning\"] {\n"
"    color: #f39c12;\n"
"    font-weight: 600;\n"
"}\n"
""
                        "\n"
"QLabel[status=\"error\"] {\n"
"    color: #e74c3c;\n"
"    font-weight: 600;\n"
"}\n"
"\n"
"/* ===== \u0424\u0418\u041d\u0410\u041d\u0421\u041e\u0412\u042b\u0415 \u0421\u0422\u0418\u041b\u0418 (\u0434\u043b\u044f \u0442\u0430\u0431\u043b\u0438\u0446\u044b) ===== */\n"
"QTableWidget::item[positive=\"true\"] {\n"
"    color: #27ae60;\n"
"    background-color: rgba(39, 174, 96, 0.1);\n"
"    font-weight: 600;\n"
"}\n"
"\n"
"QTableWidget::item[negative=\"true\"] {\n"
"    color: #e74c3c;\n"
"    background-color: rgba(231, 76, 60, 0.1);\n"
"    font-weight: 600;\n"
"}\n"
"\n"
"QTableWidget::item[zero=\"true\"] {\n"
"    color: #7f8c8d;\n"
"    font-style: italic;\n"
"}\n"
"\n"
"/* ===== \u0418\u041a\u041e\u041d\u041a\u0418 ===== */\n"
"QToolButton[iconOnly=\"true\"] {\n"
"    border: none;\n"
"    background-color: transparent;\n"
"    padding: 5px;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QToolButton[iconOnly=\"true\"]:hover {\n"
"    background-color: rgba(44, 62, 80, 0.1);\n"
"}\n"
"\n"
"\n"
"/* ===== \u0414"
                        "\u0418\u0410\u041b\u041e\u0413\u041e\u0412\u042b\u0415 \u041e\u041a\u041d\u0410 ===== */\n"
"QDialog {\n"
"    background-color: #f5f7fa;\n"
"}\n"
"\n"
"QDialog QLabel {\n"
"    color: #2c3e50;\n"
"}\n"
"\n"
"QDialog QPushButton {\n"
"    min-width: 80px;\n"
"}")

        self.gridLayout.addWidget(self.payComboBox, 1, 6, 1, 1)

        self.payLineEdit = QLineEdit(self.centralwidget)
        self.payLineEdit.setObjectName(u"payLineEdit")
        self.payLineEdit.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout.addWidget(self.payLineEdit, 2, 6, 1, 1)


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

        self.label.setText(QCoreApplication.translate("MainWindow", u"\u041d\u043e\u043c\u0435\u0440 \u0437\u0430\u044f\u0432\u043a\u0438", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0440\u043e\u043a \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f \u041a\u041f:", None))
        self.radioButton.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0442\u043e\u0431\u0440\u0430\u0436\u0430\u0442\u044c \u0441\u0442\u043e\u043b\u0431\u0435\u0446 \"\u0421\u0440\u043e\u043a \u043f\u043e\u0441\u0442\u0430\u0432\u043a\u0438\"", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u044c", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0440\u043e\u043a \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0440\u043e\u043a \u0433\u0430\u0440\u0430\u043d\u0442\u0438\u0438", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"\u0423\u0441\u043b\u043e\u0432\u0438\u044f \u043e\u043f\u043b\u0430\u0442\u044b", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"\u041e\u043f\u043b\u0430\u0442\u0430", None))
        self.payComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"\u043d\u0430 \u0434\u0430\u0442\u0443 \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043d\u0438\u044f \u0441\u043f\u0435\u0446\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438 \u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u043e\u043c", None))
        self.payComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"\u043d\u0430 \u0434\u0430\u0442\u0443 \u043e\u043f\u043b\u0430\u0442\u044b", None))
        self.payComboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"\u0414\u0440\u0443\u0433\u043e\u0435...", None))

        self.createDocButton.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
    # retranslateUi

