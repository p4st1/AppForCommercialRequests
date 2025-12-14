# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'addSupplierGui.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(747, 568)
        font = QFont()
        font.setFamilies([u"Inter"])
        MainWindow.setFont(font)
        MainWindow.setStyleSheet(u"QQMainWindow {\n"
"    background-color: #f5f7fa;\n"
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
"/* \u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u0438 \u0441\u0442\u043e\u043b\u0431\u0446\u043e\u0432 \u0442\u0430\u0431\u043b\u0438\u0446\u044b */\n"
"QHeaderView::section {\n"
"    background-color: #2c3e50;\n"
"  "
                        "  color: white;\n"
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
"    background-color: #ffffff;\n"
"}\n"
"\n"
"/* \u0412\u044b\u0434\u0435\u043b\u0435\u043d\u043d"
                        "\u0430\u044f \u0441\u0442\u0440\u043e\u043a\u0430 */\n"
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
"    background-color: #8e44ad;\n"
"}\n"
"\n"
"/* ===== \u041f\u0410\u041d\u0415\u041b\u042c \u0418\u041d\u0421"
                        "\u0422\u0420\u0423\u041c\u0415\u041d\u0422\u041e\u0412 ===== */\n"
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
"/* ===== \u041c\u0415\u041d\u042e \u0411\u0410\u0420 ===== */\n"
"QMenuBar {\n"
"    background-color: #2c3e"
                        "50;\n"
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
"/* ===== \u041f\u0410\u041d\u0415\u041b\u042c \u0418\u041d\u0421\u0422\u0420\u0423\u041c\u0415\u041d\u0422\u041e\u0412 \u0421\u041b\u0415\u0412\u0410/\u0421\u041f\u0420"
                        "\u0410\u0412\u0410 ===== */\n"
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
"    left: 15px;\n"
"    padding: 0 10px;\n"
"    background-color: #2c3e50;\n"
"    colo"
                        "r: white;\n"
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
"    height: 6px;\n"
"}\n"
"\n"
"/* ===== \u041f\u041e\u041b\u041e\u0421\u042b \u041f\u0420\u041e\u041a"
                        "\u0420\u0423\u0422\u041a\u0418 ===== */\n"
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
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 8px;\n"
""
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
"    background-color: white;\n"
"    margin-top: 5px;\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"    background-color: #f8f9fa"
                        ";\n"
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
"\n"
"QLabel[status=\"error\"] {\n"
"    color: #e74c3c;\n"
"    font-weight: 600;\n"
"}\n"
""
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
"/* ===== \u0420\u0410\u0417\u0414\u0415\u041b\u0418\u0422\u0415\u041b\u0418 ===== */\n"
"QFrame#line {\n"
" "
                        "   background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 1px;\n"
"}\n"
"\n"
"/* ===== \u0414\u0418\u0410\u041b\u041e\u0413\u041e\u0412\u042b\u0415 \u041e\u041a\u041d\u0410 ===== */\n"
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
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setFont(font)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(12, 12, 12, 12)
        self.label_10 = QLabel(self.centralwidget)
        self.label_10.setObjectName(u"label_10")
        font1 = QFont()
        self.label_10.setFont(font1)
        self.label_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label_10)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, 10, -1, -1)
        self.postLine = QLineEdit(self.centralwidget)
        self.postLine.setObjectName(u"postLine")
        self.postLine.setFont(font1)
        self.postLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout.addWidget(self.postLine, 2, 3, 1, 1)

        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font1)

        self.gridLayout.addWidget(self.label_2, 1, 3, 1, 1)

        self.nameLine = QLineEdit(self.centralwidget)
        self.nameLine.setObjectName(u"nameLine")
        self.nameLine.setFont(font1)
        self.nameLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout.addWidget(self.nameLine, 2, 1, 1, 1)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setFont(font1)

        self.gridLayout.addWidget(self.label, 1, 1, 1, 1)

        self.emailLine = QLineEdit(self.centralwidget)
        self.emailLine.setObjectName(u"emailLine")
        self.emailLine.setFont(font1)
        self.emailLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout.addWidget(self.emailLine, 2, 0, 1, 1)

        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font1)

        self.gridLayout.addWidget(self.label_4, 1, 0, 1, 1)


        self.horizontalLayout_2.addLayout(self.gridLayout)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName(u"line")
        font2 = QFont()
        font2.setFamilies([u"Segoe UI"])
        font2.setPointSize(9)
        font2.setBold(False)
        self.line.setFont(font2)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font1)
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label_3)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(-1, 10, -1, -1)
        self.label_7 = QLabel(self.centralwidget)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font1)

        self.gridLayout_3.addWidget(self.label_7, 0, 1, 1, 1)

        self.label_9 = QLabel(self.centralwidget)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font1)

        self.gridLayout_3.addWidget(self.label_9, 2, 1, 1, 1)

        self.streetLine = QLineEdit(self.centralwidget)
        self.streetLine.setObjectName(u"streetLine")
        self.streetLine.setFont(font1)
        self.streetLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout_3.addWidget(self.streetLine, 1, 1, 1, 1)

        self.label_8 = QLabel(self.centralwidget)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font1)

        self.gridLayout_3.addWidget(self.label_8, 2, 0, 1, 1)

        self.label_5 = QLabel(self.centralwidget)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font1)

        self.gridLayout_3.addWidget(self.label_5, 0, 0, 1, 1)

        self.buildingLine = QLineEdit(self.centralwidget)
        self.buildingLine.setObjectName(u"buildingLine")
        self.buildingLine.setFont(font1)
        self.buildingLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout_3.addWidget(self.buildingLine, 1, 2, 1, 1)

        self.label_6 = QLabel(self.centralwidget)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font1)

        self.gridLayout_3.addWidget(self.label_6, 0, 2, 1, 1)

        self.cityLine = QLineEdit(self.centralwidget)
        self.cityLine.setObjectName(u"cityLine")
        self.cityLine.setFont(font1)
        self.cityLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout_3.addWidget(self.cityLine, 1, 0, 1, 1)

        self.mailIndexLine = QLineEdit(self.centralwidget)
        self.mailIndexLine.setObjectName(u"mailIndexLine")
        self.mailIndexLine.setFont(font1)
        self.mailIndexLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout_3.addWidget(self.mailIndexLine, 3, 0, 1, 1)

        self.roomLine = QLineEdit(self.centralwidget)
        self.roomLine.setObjectName(u"roomLine")
        self.roomLine.setFont(font1)
        self.roomLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout_3.addWidget(self.roomLine, 3, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_3)

        self.line_2 = QFrame(self.centralwidget)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFont(font2)
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_2)

        self.label_11 = QLabel(self.centralwidget)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font1)
        self.label_11.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label_11)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(-1, 10, -1, -1)
        self.phoneNumLine = QLineEdit(self.centralwidget)
        self.phoneNumLine.setObjectName(u"phoneNumLine")
        self.phoneNumLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout_2.addWidget(self.phoneNumLine, 1, 1, 1, 1)

        self.label_13 = QLabel(self.centralwidget)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout_2.addWidget(self.label_13, 0, 1, 1, 1)

        self.label_12 = QLabel(self.centralwidget)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setFont(font1)

        self.gridLayout_2.addWidget(self.label_12, 0, 0, 1, 1)

        self.companyNameLine = QLineEdit(self.centralwidget)
        self.companyNameLine.setObjectName(u"companyNameLine")
        self.companyNameLine.setFont(font1)
        self.companyNameLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout_2.addWidget(self.companyNameLine, 1, 0, 1, 1)

        self.label_14 = QLabel(self.centralwidget)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_2.addWidget(self.label_14, 0, 2, 1, 1)

        self.condLine = QLineEdit(self.centralwidget)
        self.condLine.setObjectName(u"condLine")
        self.condLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.gridLayout_2.addWidget(self.condLine, 1, 2, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_2)

        self.line_3 = QFrame(self.centralwidget)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFont(font2)
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_3)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.horizontalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.acceptButton = QPushButton(self.centralwidget)
        self.acceptButton.setObjectName(u"acceptButton")
        font3 = QFont()
        font3.setWeight(QFont.DemiBold)
        self.acceptButton.setFont(font3)
        self.acceptButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    border: none;\n"
"    padding: 4px 4px;\n"
"    border-radius: 6px;\n"
"    font-weight: 600;\n"
"    font-size: 12px;\n"
"    min-height: 35px;\n"
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

        self.horizontalLayout.addWidget(self.acceptButton)

        self.cancellButton = QPushButton(self.centralwidget)
        self.cancellButton.setObjectName(u"cancellButton")
        self.cancellButton.setFont(font3)
        self.cancellButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    border: none;\n"
"    padding: 4px 4px;\n"
"    border-radius: 6px;\n"
"    font-weight: 600;\n"
"    font-size: 12px;\n"
"    min-height: 35px;\n"
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

        self.horizontalLayout.addWidget(self.cancellButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437\u0447\u0438\u043a\u0430", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0441\u043d\u043e\u0432\u043d\u0430\u044f \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f", None))
        self.postLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u0413\u0435\u043d\u0435\u0440\u0430\u043b\u044c\u043d\u044b\u0439 \u0434\u0438\u0440\u0435\u043a\u0442\u043e\u0440", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"\u0414\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u044c", None))
        self.nameLine.setText("")
        self.nameLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u0418\u0432\u0430\u043d\u043e\u0432 \u0418\u0432\u0430\u043d \u0418\u0432\u0430\u043d\u043e\u0432\u0438\u0447", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u0424\u0418\u041e", None))
        self.emailLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"supplier@mail.com", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"\u0410\u0434\u0440\u0435\u0441 \u042d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u043e\u0439 \u043f\u043e\u0447\u0442\u044b", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"\u0410\u0434\u0440\u0435\u0441", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"\u0423\u043b\u0438\u0446\u0430", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u043c\u0435\u0449\u0435\u043d\u0438\u0435", None))
        self.streetLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u0443\u043b. \u0410\u0440\u0431\u0430\u0442", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u0447\u0442\u043e\u0432\u044b\u0439 \u0438\u043d\u0434\u0435\u043a\u0441", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"\u0413\u043e\u0440\u043e\u0434", None))
        self.buildingLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u0441\u0442\u0440. 1", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0442\u0440\u043e\u0435\u043d\u0438\u0435", None))
        self.cityLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u0433. \u041c\u043e\u0441\u043a\u0432\u0430", None))
        self.mailIndexLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"00000", None))
        self.roomLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"1", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435", None))
        self.phoneNumLine.setText("")
        self.phoneNumLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"788834451212", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"\u041d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438", None))
        self.companyNameLine.setText("")
        self.companyNameLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u041e\u041e\u041e \"\u0418\u0432\u0430\u043d\u0417\u043e\u043b\u043e\u0442\u043e\"", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"\u0423\u0441\u043b\u043e\u0432\u0438\u044f \u043f\u043e\u0441\u0442\u0430\u0432\u043a\u0438", None))
        self.condLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"DDP", None))
        self.acceptButton.setText(QCoreApplication.translate("MainWindow", u"\u0413\u043e\u0442\u043e\u0432\u043e", None))
        self.cancellButton.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c", None))
    # retranslateUi

