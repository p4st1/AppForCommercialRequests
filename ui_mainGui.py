# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainGui.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QComboBox, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1440, 830)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setAutoFillBackground(False)
        MainWindow.setStyleSheet(u"QQMainWindow {\n"
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
        MainWindow.setAnimated(False)
        self.openTableMenuButton = QAction(MainWindow)
        self.openTableMenuButton.setObjectName(u"openTableMenuButton")
        font = QFont()
        font.setFamilies([u"Inter"])
        self.openTableMenuButton.setFont(font)
        self.createDocMenuButton = QAction(MainWindow)
        self.createDocMenuButton.setObjectName(u"createDocMenuButton")
        self.editTableButton = QAction(MainWindow)
        self.editTableButton.setObjectName(u"editTableButton")
        font1 = QFont()
        self.editTableButton.setFont(font1)
        self.editParamsButton = QAction(MainWindow)
        self.editParamsButton.setObjectName(u"editParamsButton")
        self.action_3 = QAction(MainWindow)
        self.action_3.setObjectName(u"action_3")
        self.suppliersMenu = QAction(MainWindow)
        self.suppliersMenu.setObjectName(u"suppliersMenu")
        self.suppliersMenuButton = QAction(MainWindow)
        self.suppliersMenuButton.setObjectName(u"suppliersMenuButton")
        self.suppliersMenuButton.setFont(font1)
        self.helpMenuButton = QAction(MainWindow)
        self.helpMenuButton.setObjectName(u"helpMenuButton")
        self.helpMenuButton.setFont(font1)
        self.settingsMenuButton = QAction(MainWindow)
        self.settingsMenuButton.setObjectName(u"settingsMenuButton")
        self.settingsMenuButton.setFont(font)
        self.exportMenuButton = QAction(MainWindow)
        self.exportMenuButton.setObjectName(u"exportMenuButton")
        self.importMenuButton = QAction(MainWindow)
        self.importMenuButton.setObjectName(u"importMenuButton")
        self.closeTableMenuButton = QAction(MainWindow)
        self.closeTableMenuButton.setObjectName(u"closeTableMenuButton")
        self.createExcelMenuButton = QAction(MainWindow)
        self.createExcelMenuButton.setObjectName(u"createExcelMenuButton")
        self.GitHubMenuButton = QAction(MainWindow)
        self.GitHubMenuButton.setObjectName(u"GitHubMenuButton")
        self.supportMenuButton = QAction(MainWindow)
        self.supportMenuButton.setObjectName(u"supportMenuButton")
        self.aboutMenuButton = QAction(MainWindow)
        self.aboutMenuButton.setObjectName(u"aboutMenuButton")
        self.clearCacheMenuButton = QAction(MainWindow)
        self.clearCacheMenuButton.setObjectName(u"clearCacheMenuButton")
        self.changeFormButton = QAction(MainWindow)
        self.changeFormButton.setObjectName(u"changeFormButton")
        self.changeFormButton.setCheckable(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        font2 = QFont()
        font2.setFamilies([u"Segoe UI"])
        self.centralwidget.setFont(font2)
        self.centralwidget.setStyleSheet(u"QMainWindow {\n"
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
"   "
                        " color: white;\n"
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
"/* ===== \u041f\u041e\u041b\u042f \u0412\u0412\u041e\u0414\u0410 ===== */\n"
"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 8px 12px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 12px;\n"
"    selection-background-color: #e3f2fd;\n"
"}\n"
"\n"
"QLineEdit:focus, QComboBox:focus, QDateEdit:focus {\n"
"    border: 1px solid #3498db;\n"
""
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
"    height: 12px;\n"
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
"QScrollBar:"
                        ":handle:horizontal {\n"
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
""
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
"/* "
                        "===== \u0421\u0422\u0410\u0422\u0423\u0421\u041d\u042b\u0415 \u0418\u041a\u041e\u041d\u041a\u0418 ===== */\n"
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
"/* ===== \u0418\u041a\u041e\u041d\u041a\u0418"
                        " ===== */\n"
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
"    background-color: #dee2e6;\n"
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
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 5)
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setMinimumSize(QSize(0, 200))
        font3 = QFont()
        font3.setFamilies([u"Segoe UI"])
        font3.setPointSize(9)
        font3.setBold(False)
        self.tabWidget.setFont(font3)
        self.tabWidget.setTabsClosable(False)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tab.sizePolicy().hasHeightForWidth())
        self.tab.setSizePolicy(sizePolicy1)
        self.tab.setMaximumSize(QSize(16777215, 493))
        self.verticalLayout_2 = QVBoxLayout(self.tab)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.KpTable = QTableWidget(self.tab)
        if (self.KpTable.columnCount() < 15):
            self.KpTable.setColumnCount(15)
        __qtablewidgetitem = QTableWidgetItem()
        self.KpTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        font4 = QFont()
        font4.setFamilies([u"SF Pro Text"])
        font4.setBold(False)
        __qtablewidgetitem1 = QTableWidgetItem()
        __qtablewidgetitem1.setFont(font4);
        self.KpTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        __qtablewidgetitem2.setFont(font4);
        self.KpTable.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        font5 = QFont()
        font5.setFamilies([u"SF Pro Text"])
        font5.setPointSize(8)
        __qtablewidgetitem3 = QTableWidgetItem()
        __qtablewidgetitem3.setFont(font5);
        self.KpTable.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        __qtablewidgetitem4.setFont(font5);
        self.KpTable.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.KpTable.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.KpTable.setHorizontalHeaderItem(6, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.KpTable.setHorizontalHeaderItem(7, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.KpTable.setHorizontalHeaderItem(8, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.KpTable.setHorizontalHeaderItem(9, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.KpTable.setHorizontalHeaderItem(10, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.KpTable.setHorizontalHeaderItem(11, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.KpTable.setHorizontalHeaderItem(12, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.KpTable.setHorizontalHeaderItem(13, __qtablewidgetitem13)
        __qtablewidgetitem14 = QTableWidgetItem()
        self.KpTable.setHorizontalHeaderItem(14, __qtablewidgetitem14)
        self.KpTable.setObjectName(u"KpTable")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.KpTable.sizePolicy().hasHeightForWidth())
        self.KpTable.setSizePolicy(sizePolicy2)
        self.KpTable.setFont(font)
        self.KpTable.setStyleSheet(u"QTableWidget {\n"
"    background-color: #ffffff;\n"
"    gridline-color: #dee2e6;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 10px;\n"
"	font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;\n"
"    font-size: 12px;\n"
"    selection-background-color: #e3f2fd;\n"
"    selection-color: #1565c0;\n"
"    alternate-background-color: #f8f9fa;\n"
"\n"
"}\n"
"\n"
"/* \u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u0438 \u0441\u0442\u043e\u043b\u0431\u0446\u043e\u0432 \u0442\u0430\u0431\u043b\u0438\u0446\u044b */\n"
"QHeaderView::section {\n"
"    background-color: #2c3e50;\n"
"    color: white;\n"
"    padding: 8px 2px;\n"
"    border: none;\n"
"    font-weight: 600;\n"
"    font-size: 11px;\n"
"    border-right: 1px solid #34495e;\n"
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
""
                        "}\n"
"\n"
"/* \u042f\u0447\u0435\u0439\u043a\u0438 \u0442\u0430\u0431\u043b\u0438\u0446\u044b */\n"
"QTableWidget::item {\n"
"    padding: 10px 5px;\n"
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
"/* \u0412\u044b\u0434\u0435\u043b\u0435\u043d\u043d\u0430\u044f \u0441\u0442\u0440\u043e\u043a\u0430 */\n"
"QTableWidget::item:selected {\n"
"    background-color: #e3f2fd;\n"
"    color: #1565c0;\n"
"    font-weight: 500;\n"
"    border-left: 3px solid #2196f3;\n"
"}")
        self.KpTable.setFrameShape(QFrame.Shape.NoFrame)
        self.KpTable.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        self.KpTable.setTabKeyNavigation(True)
        self.KpTable.setProperty(u"showDropIndicator", True)
        self.KpTable.setShowGrid(True)
        self.KpTable.setGridStyle(Qt.PenStyle.SolidLine)
        self.KpTable.setSortingEnabled(False)
        self.KpTable.setWordWrap(True)
        self.KpTable.setCornerButtonEnabled(True)
        self.KpTable.horizontalHeader().setVisible(True)
        self.KpTable.horizontalHeader().setCascadingSectionResizes(False)
        self.KpTable.horizontalHeader().setHighlightSections(True)
        self.KpTable.verticalHeader().setVisible(False)

        self.verticalLayout_2.addWidget(self.KpTable)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        sizePolicy1.setHeightForWidth(self.tab_2.sizePolicy().hasHeightForWidth())
        self.tab_2.setSizePolicy(sizePolicy1)
        self.verticalLayout_3 = QVBoxLayout(self.tab_2)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.textUpdates = QTextEdit(self.tab_2)
        self.textUpdates.setObjectName(u"textUpdates")
        self.textUpdates.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.textUpdates)

        self.tabWidget.addTab(self.tab_2, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.funcButtons = QGridLayout()
        self.funcButtons.setObjectName(u"funcButtons")
        self.funcButtons.setHorizontalSpacing(12)
        self.funcButtons.setContentsMargins(5, 5, 5, 5)
        self.horizontalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.funcButtons.addItem(self.horizontalSpacer, 0, 13, 1, 1)

        self.line_3 = QFrame(self.centralwidget)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setStyleSheet(u"QFrame {\n"
"    background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 100px;\n"
"}")
        self.line_3.setFrameShape(QFrame.Shape.VLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.funcButtons.addWidget(self.line_3, 2, 2, 1, 1)

        self.line_6 = QFrame(self.centralwidget)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setStyleSheet(u"QFrame {\n"
"    background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 100px;\n"
"}")
        self.line_6.setFrameShape(QFrame.Shape.VLine)
        self.line_6.setFrameShadow(QFrame.Shadow.Sunken)

        self.funcButtons.addWidget(self.line_6, 2, 7, 1, 1)

        self.line_4 = QFrame(self.centralwidget)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setStyleSheet(u"QFrame {\n"
"    background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 100px;\n"
"}")
        self.line_4.setFrameShape(QFrame.Shape.VLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.funcButtons.addWidget(self.line_4, 0, 3, 1, 1)

        self.line_5 = QFrame(self.centralwidget)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setStyleSheet(u"QFrame {\n"
"    background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 100px;\n"
"}")
        self.line_5.setFrameShape(QFrame.Shape.VLine)
        self.line_5.setFrameShadow(QFrame.Shadow.Sunken)

        self.funcButtons.addWidget(self.line_5, 1, 7, 1, 1)

        self.line_8 = QFrame(self.centralwidget)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setStyleSheet(u"QFrame {\n"
"    background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 100px;\n"
"}")
        self.line_8.setFrameShape(QFrame.Shape.VLine)
        self.line_8.setFrameShadow(QFrame.Shadow.Sunken)

        self.funcButtons.addWidget(self.line_8, 1, 9, 1, 1)

        self.line_9 = QFrame(self.centralwidget)
        self.line_9.setObjectName(u"line_9")
        self.line_9.setStyleSheet(u"QFrame {\n"
"    background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 100px;\n"
"}")
        self.line_9.setFrameShape(QFrame.Shape.VLine)
        self.line_9.setFrameShadow(QFrame.Shadow.Sunken)

        self.funcButtons.addWidget(self.line_9, 2, 9, 1, 1)

        self.line_2 = QFrame(self.centralwidget)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setStyleSheet(u"QFrame {\n"
"    background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 100px;\n"
"}")
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.funcButtons.addWidget(self.line_2, 0, 9, 1, 1)

        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(-1, -1, 0, -1)
        self.horizontalLayout_markupRequest = QHBoxLayout()
        self.horizontalLayout_markupRequest.setSpacing(8)
        self.horizontalLayout_markupRequest.setObjectName(u"horizontalLayout_markupRequest")
        self.verticalLayout_markupBlock = QVBoxLayout()
        self.verticalLayout_markupBlock.setObjectName(u"verticalLayout_markupBlock")
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_markupBlock.addWidget(self.label_3)

        self.markupLine = QLineEdit(self.centralwidget)
        self.markupLine.setObjectName(u"markupLine")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.markupLine.sizePolicy().hasHeightForWidth())
        self.markupLine.setSizePolicy(sizePolicy3)
        self.markupLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.verticalLayout_markupBlock.addWidget(self.markupLine)


        self.horizontalLayout_markupRequest.addLayout(self.verticalLayout_markupBlock)

        self.verticalLayout_requestNumberBlock = QVBoxLayout()
        self.verticalLayout_requestNumberBlock.setObjectName(u"verticalLayout_requestNumberBlock")
        self.requestNumberLabel = QLabel(self.centralwidget)
        self.requestNumberLabel.setObjectName(u"requestNumberLabel")
        self.requestNumberLabel.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")
        self.requestNumberLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_requestNumberBlock.addWidget(self.requestNumberLabel)

        self.requestNumberLine = QLineEdit(self.centralwidget)
        self.requestNumberLine.setObjectName(u"requestNumberLine")
        sizePolicy3.setHeightForWidth(self.requestNumberLine.sizePolicy().hasHeightForWidth())
        self.requestNumberLine.setSizePolicy(sizePolicy3)
        self.requestNumberLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.verticalLayout_requestNumberBlock.addWidget(self.requestNumberLine)


        self.horizontalLayout_markupRequest.addLayout(self.verticalLayout_requestNumberBlock)


        self.verticalLayout_10.addLayout(self.horizontalLayout_markupRequest)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.verticalLayout_10.addItem(self.verticalSpacer_3)


        self.funcButtons.addLayout(self.verticalLayout_10, 0, 6, 1, 1)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(-1, 0, 0, -1)
        self.label_5 = QLabel(self.centralwidget)
        self.label_5.setObjectName(u"label_5")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy4)
        font6 = QFont()
        font6.setWeight(QFont.DemiBold)
        self.label_5.setFont(font6)
        self.label_5.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")
        self.label_5.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_5.addWidget(self.label_5)

        self.logisticVar = QComboBox(self.centralwidget)
        self.logisticVar.addItem("")
        self.logisticVar.addItem("")
        self.logisticVar.setObjectName(u"logisticVar")
        sizePolicy2.setHeightForWidth(self.logisticVar.sizePolicy().hasHeightForWidth())
        self.logisticVar.setSizePolicy(sizePolicy2)
        self.logisticVar.setMinimumSize(QSize(0, 30))
        self.logisticVar.setFont(font1)
        self.logisticVar.setStyleSheet(u"QLabel {\n"
"    color: #2c3e50;\n"
"    font-size: 12px;\n"
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
"}")

        self.verticalLayout_5.addWidget(self.logisticVar)

        self.logisticNum = QLineEdit(self.centralwidget)
        self.logisticNum.setObjectName(u"logisticNum")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.logisticNum.sizePolicy().hasHeightForWidth())
        self.logisticNum.setSizePolicy(sizePolicy5)
        self.logisticNum.setMinimumSize(QSize(120, 18))
        self.logisticNum.setFont(font1)
        self.logisticNum.setAutoFillBackground(False)
        self.logisticNum.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")
        self.logisticNum.setClearButtonEnabled(False)

        self.verticalLayout_5.addWidget(self.logisticNum)


        self.funcButtons.addLayout(self.verticalLayout_5, 0, 0, 1, 1)

        self.line_7 = QFrame(self.centralwidget)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setStyleSheet(u"QFrame {\n"
"    background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 100px;\n"
"}")
        self.line_7.setFrameShape(QFrame.Shape.VLine)
        self.line_7.setFrameShadow(QFrame.Shadow.Sunken)

        self.funcButtons.addWidget(self.line_7, 0, 7, 1, 1)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(-1, 0, 0, -1)
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy6)
        self.label.setFont(font6)
        self.label.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_7.addWidget(self.label)

        self.customLine = QLineEdit(self.centralwidget)
        self.customLine.setObjectName(u"customLine")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.customLine.sizePolicy().hasHeightForWidth())
        self.customLine.setSizePolicy(sizePolicy7)
        self.customLine.setFont(font1)
        self.customLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")
        self.customLine.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.verticalLayout_7.addWidget(self.customLine)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.verticalLayout_7.addItem(self.verticalSpacer_2)


        self.funcButtons.addLayout(self.verticalLayout_7, 0, 4, 1, 1)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setSpacing(10)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(-1, -1, 0, -1)
        self.openTableButton = QPushButton(self.centralwidget)
        self.openTableButton.setObjectName(u"openTableButton")
        self.openTableButton.setFont(font6)
        self.openTableButton.setStyleSheet(u"QPushButton {\n"
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

        self.verticalLayout_9.addWidget(self.openTableButton)

        self.closeTableButton = QPushButton(self.centralwidget)
        self.closeTableButton.setObjectName(u"closeTableButton")
        self.closeTableButton.setFont(font6)
        self.closeTableButton.setStyleSheet(u"QPushButton {\n"
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

        self.verticalLayout_9.addWidget(self.closeTableButton)


        self.funcButtons.addLayout(self.verticalLayout_9, 0, 10, 1, 1)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(-1, 0, 0, -1)
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        sizePolicy6.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy6)
        self.label_2.setStyleSheet(u"QLabel {\n"
"	color:  #2c3e50;\n"
"	font-weight: 600;\n"
"	 font-size: 12px;\n"
"}\n"
"")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_6.addWidget(self.label_2)

        self.termDeliveryLine = QLineEdit(self.centralwidget)
        self.termDeliveryLine.setObjectName(u"termDeliveryLine")
        sizePolicy7.setHeightForWidth(self.termDeliveryLine.sizePolicy().hasHeightForWidth())
        self.termDeliveryLine.setSizePolicy(sizePolicy7)
        self.termDeliveryLine.setStyleSheet(u"QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {\n"
"    background-color: white;\n"
"    border: 1px solid #dee2e6;\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"    font-size: 12px;\n"
"    color: #2c3e50;\n"
"    min-height: 8px;\n"
"    selection-background-color: #e3f2fd;\n"
"}")

        self.verticalLayout_6.addWidget(self.termDeliveryLine)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.verticalLayout_6.addItem(self.verticalSpacer)


        self.funcButtons.addLayout(self.verticalLayout_6, 0, 2, 1, 1)

        self.line1 = QFrame(self.centralwidget)
        self.line1.setObjectName(u"line1")
        self.line1.setStyleSheet(u"QFrame {\n"
"    background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 100px;\n"
"}")
        self.line1.setFrameShape(QFrame.Shape.VLine)
        self.line1.setFrameShadow(QFrame.Shadow.Sunken)

        self.funcButtons.addWidget(self.line1, 0, 1, 1, 1)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setSpacing(10)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(-1, -1, 0, -1)
        self.createDocButton = QPushButton(self.centralwidget)
        self.createDocButton.setObjectName(u"createDocButton")
        self.createDocButton.setFont(font6)
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

        self.verticalLayout_8.addWidget(self.createDocButton)

        self.createDocFromExcelButton = QPushButton(self.centralwidget)
        self.createDocFromExcelButton.setObjectName(u"createDocFromExcelButton")
        self.createDocFromExcelButton.setStyleSheet(u"QPushButton {\n"
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

        self.verticalLayout_8.addWidget(self.createDocFromExcelButton)

        self.createExcelButton = QPushButton(self.centralwidget)
        self.createExcelButton.setObjectName(u"createExcelButton")
        self.createExcelButton.setFont(font6)
        self.createExcelButton.setStyleSheet(u"QPushButton {\n"
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

        self.verticalLayout_8.addWidget(self.createExcelButton)


        self.funcButtons.addLayout(self.verticalLayout_8, 0, 8, 1, 1)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName(u"line")
        self.line.setStyleSheet(u"/* ===== \u0420\u0410\u0417\u0414\u0415\u041b\u0418\u0422\u0415\u041b\u0418 ===== */\n"
"QFrame {\n"
"    background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 100px;\n"
"}")
        self.line.setFrameShape(QFrame.Shape.VLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.funcButtons.addWidget(self.line, 1, 2, 1, 1)

        self.line_10 = QFrame(self.centralwidget)
        self.line_10.setObjectName(u"line_10")
        self.line_10.setStyleSheet(u"QFrame {\n"
"    background-color: #dee2e6;\n"
"    border: none;\n"
"    min-height: 1px;\n"
"    max-height: 100px;\n"
"}")
        self.line_10.setFrameShape(QFrame.Shape.VLine)
        self.line_10.setFrameShadow(QFrame.Shadow.Sunken)

        self.funcButtons.addWidget(self.line_10, 0, 5, 1, 1)


        self.verticalLayout.addLayout(self.funcButtons)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1440, 31))
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.menubar.sizePolicy().hasHeightForWidth())
        self.menubar.setSizePolicy(sizePolicy8)
        font7 = QFont()
        font7.setFamilies([u"Inter"])
        font7.setPointSize(8)
        self.menubar.setFont(font7)
        self.menubar.setDefaultUp(False)
        self.FileMenu = QMenu(self.menubar)
        self.FileMenu.setObjectName(u"FileMenu")
        font8 = QFont()
        font8.setPointSize(8)
        self.FileMenu.setFont(font8)
        self.FileMenu.setTearOffEnabled(False)
        self.EditMenu = QMenu(self.menubar)
        self.EditMenu.setObjectName(u"EditMenu")
        self.EditMenu.setFont(font8)
        self.SettingsMenu = QMenu(self.menubar)
        self.SettingsMenu.setObjectName(u"SettingsMenu")
        self.SettingsMenu.setFont(font8)
        self.WindowMenu = QMenu(self.menubar)
        self.WindowMenu.setObjectName(u"WindowMenu")
        self.WindowMenu.setFont(font8)
        self.HelpMenu = QMenu(self.menubar)
        self.HelpMenu.setObjectName(u"HelpMenu")
        self.HelpMenu.setFont(font7)
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.statusbar.setFont(font1)
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.FileMenu.menuAction())
        self.menubar.addAction(self.EditMenu.menuAction())
        self.menubar.addAction(self.SettingsMenu.menuAction())
        self.menubar.addAction(self.WindowMenu.menuAction())
        self.menubar.addAction(self.HelpMenu.menuAction())
        self.FileMenu.addAction(self.openTableMenuButton)
        self.FileMenu.addAction(self.closeTableMenuButton)
        self.FileMenu.addSeparator()
        self.FileMenu.addAction(self.createDocMenuButton)
        self.FileMenu.addAction(self.createExcelMenuButton)
        self.EditMenu.addAction(self.editParamsButton)
        self.EditMenu.addSeparator()
        self.SettingsMenu.addAction(self.suppliersMenuButton)
        self.SettingsMenu.addSeparator()
        self.SettingsMenu.addAction(self.exportMenuButton)
        self.SettingsMenu.addAction(self.importMenuButton)
        self.SettingsMenu.addSeparator()
        self.SettingsMenu.addAction(self.settingsMenuButton)
        self.SettingsMenu.addAction(self.clearCacheMenuButton)
        self.SettingsMenu.addAction(self.changeFormButton)
        self.HelpMenu.addAction(self.helpMenuButton)
        self.HelpMenu.addAction(self.GitHubMenuButton)
        self.HelpMenu.addAction(self.supportMenuButton)
        self.HelpMenu.addAction(self.aboutMenuButton)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0437\u0430\u0446\u0438\u044f \u043f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u043a\u0438 \u043a\u043e\u043c\u043c\u0435\u0440\u0447\u0435\u0441\u043a\u0438\u0445 \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u0439", None))
        self.openTableMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u041e\u043a\u0440\u044b\u0442\u044c \u0442\u0430\u0431\u043b\u0438\u0446\u0443", None))
        self.createDocMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u041a\u041f", None))
        self.editTableButton.setText(QCoreApplication.translate("MainWindow", u"\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0432 \u0442\u0430\u0431\u043b\u0438\u0446\u0435", None))
        self.editParamsButton.setText(QCoreApplication.translate("MainWindow", u"\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u044b\u0435", None))
        self.action_3.setText(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", None))
        self.suppliersMenu.setText(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0438", None))
        self.suppliersMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u043a\u0430\u0437\u0447\u0438\u043a\u0438", None))
        self.helpMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043f\u0440\u0430\u0432\u043a\u0430", None))
        self.settingsMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438...", None))
        self.exportMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u042d\u043a\u0441\u043f\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0411\u0414...", None))
        self.importMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u0418\u043c\u043f\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0411\u0414...", None))
        self.closeTableMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c \u0442\u0430\u0431\u043b\u0438\u0446\u0443", None))
        self.createExcelMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0442\u0430\u0431\u043b\u0438\u0446\u0443 (Excel)", None))
        self.GitHubMenuButton.setText(QCoreApplication.translate("MainWindow", u"GitHub", None))
        self.supportMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", None))
        self.aboutMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u041e \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u0435", None))
        self.clearCacheMenuButton.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0447\u0438\u0441\u0442\u0438\u0442\u044c \u043a\u044d\u0448", None))
        self.changeFormButton.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043a\u043b\u043e\u043d\u0435\u043d\u0438\u0435 \u0441\u043b\u043e\u0432", None))
        ___qtablewidgetitem = self.KpTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"\u2116", None));
        ___qtablewidgetitem1 = self.KpTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435", None));
        ___qtablewidgetitem2 = self.KpTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"\u041a\u0430\u0442\u0430\u043b\u043e\u0436\u043d\u044b\u0439 \u043d\u043e\u043c\u0435\u0440 ", None));
        ___qtablewidgetitem3 = self.KpTable.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"\u0415\u0434. \u0438\u0437\u043c.", None));
        ___qtablewidgetitem4 = self.KpTable.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"\u041a\u043e\u043b-\u0432\u043e", None));
        ___qtablewidgetitem5 = self.KpTable.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"\u0426\u0435\u043d\u0430 \u0437\u0430 \u0435\u0434. \u0431\u0435\u0437 \u041d\u0414\u0421", None));
        ___qtablewidgetitem6 = self.KpTable.horizontalHeaderItem(6)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MainWindow", u"\u0418\u0442\u043e\u0433\u043e \u0431\u0435\u0437 \u041d\u0414\u0421", None));
        ___qtablewidgetitem7 = self.KpTable.horizontalHeaderItem(7)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("MainWindow", u"\u041b\u043e\u0433\u0438\u0441\u0442\u0438\u043a\u0430", None));
        ___qtablewidgetitem8 = self.KpTable.horizontalHeaderItem(8)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("MainWindow", u"\u0422\u0430\u043c\u043e\u0436\u043d\u044f", None));
        ___qtablewidgetitem9 = self.KpTable.horizontalHeaderItem(9)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("MainWindow", u"\u0426\u0435\u043d\u0430 \u0437\u0430 \u0435\u0434 ", None));
        ___qtablewidgetitem10 = self.KpTable.horizontalHeaderItem(10)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("MainWindow", u"\u0426\u0435\u043d\u0430 \u0440\u0435\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u0438 \u0437\u0430 \u0435\u0434. \u0431\u0435\u0437 \u041d\u0414\u0421", None));
        ___qtablewidgetitem11 = self.KpTable.horizontalHeaderItem(11)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("MainWindow", u"\u0418\u0442\u043e\u0433\u043e \u0440\u0435\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u0438 \u0431\u0435\u0437 \u041d\u0414\u0421", None));
        ___qtablewidgetitem12 = self.KpTable.horizontalHeaderItem(12)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("MainWindow", u"\u0418\u0442\u043e\u0433\u043e \u0440\u0435\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u0438 \u0441 \u041d\u0414\u0421", None));
        ___qtablewidgetitem13 = self.KpTable.horizontalHeaderItem(13)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0440\u043e\u043a \u043f\u043e\u0441\u0442\u0430\u0432\u043a\u0438", None));
        ___qtablewidgetitem14 = self.KpTable.horizontalHeaderItem(14)
        ___qtablewidgetitem14.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0440\u043e\u043a \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430", None));
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"\u041f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u043a\u0430 \u041a\u041f", None))
        self.textUpdates.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">AppForCommercialRequests</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt; font-weight:700;\">\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435  </span><a href=\"https://github.com/p4st1/AppForCommercialRequests/releases/tag/v"
                        "1.0.2.30\"><span style=\" font-size:12pt; text-decoration: underline; color:#262524;\">1.0.6</span></a></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:12pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">1. &quot;\u0421\u0440\u043e\u043a \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438&quot; \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u043e \u043d\u0430 &quot;\u0421\u0440\u043e\u043a \u043f\u043e\u0441\u0442\u0430\u0432\u043a\u0438&quot;</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">2. \u041d\u043e\u0432\u0430\u044f \u043b\u043e\u0433\u0438\u043a\u0430 \u0441\u043a\u043b\u043e\u043d\u0435\u043d\u0438\u044f \u0441\u043b\u043e\u0432 \u0441 \u0438\u0441\u043f"
                        "\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u0435\u043c \u0441\u043e\u0431\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e \u0441\u043b\u043e\u0432\u0430\u0440\u044f</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">3. \u041d\u043e\u0432\u0430\u044f \u044f\u0447\u0435\u0439\u043a\u0430 \u0432 \u0448\u0430\u0431\u043b\u043e\u043d\u0435 Excel</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">4. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0430 \u043e\u0448\u0438\u0431\u043a\u0430 \u0441 \u043e\u0442\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435\u043c \u043f\u0435\u0447\u0430\u0442\u0438</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-siz"
                        "e:12pt;\">5. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0435 \u043a\u043e\u043f\u0438\u0439 Excel</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:12pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">09.02.2026</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:12pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt; font-weight:700;\">\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435  </span><a href=\"https://github.com/p4st1/AppForCommercialRequests/rele"
                        "ases/tag/v1.0.2.30\"><span style=\" font-size:12pt; text-decoration: underline; color:#262524;\">1.0.5</span></a></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:12pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">1. \u041f\u0435\u0440\u0435\u0440\u0430\u0431\u043e\u0442\u0430\u043d\u0430 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0430 \u0432\u0430\u043b\u044e\u0442 \u0432 \u0438\u043c\u043f\u043e\u0440\u0442\u0435 \u0438 \u0432\u044b\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u0438 \u0442\u0430\u0431\u043b\u0438\u0446\u044b</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">2. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0432 \u0432"
                        "\u044b\u0432\u043e\u0434\u0435 \u0432\u0430\u043b\u044e\u0442\u044b \u0432 Docx </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:'.AppleSystemUIFont'; font-size:13pt;\">3. \u0421\u0447\u0435\u0442\u0447\u0438\u043a \u041a\u041f \u0442\u0435\u043f\u0435\u0440\u044c \u0441\u0431\u0440\u0430\u0441\u044b\u0432\u0430\u0435\u0442\u0441\u044f \u0441 \u043a\u0430\u0436\u0434\u044b\u043c \u043d\u043e\u0432\u044b\u043c \u0434\u043d\u0435\u043c</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:'.AppleSystemUIFont'; font-size:13pt;\">4. \u0414\u0432\u0430 \u043d\u043e\u0432\u044b\u0445 \u0448\u0430\u0431\u043b\u043e\u043d\u0430 template.docx \u0438 template_short.docx</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px"
                        ";\"><span style=\" font-family:'.AppleSystemUIFont'; font-size:13pt;\">5. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e &quot;\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438&quot; - &quot;\u0417\u0430\u043a\u0430\u0437\u0447\u0438\u043a\u0438&quot; -&gt; &quot;\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438&quot; - &quot;\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0438&quot;</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:'.AppleSystemUIFont'; font-size:13pt;\">6. \u041d\u043e\u0432\u0430\u044f \u043b\u043e\u0433\u0438\u043a\u0430 \u0437\u0430\u043e\u043f\u043b\u043d\u0435\u043d\u0438\u044f Docx</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'.AppleSystemUIFont'; font-size:13pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-botto"
                        "m:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">30.01.2026</span><span style=\" font-size:12pt; font-weight:700;\"><br /><br />\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435  </span><a href=\"https://github.com/p4st1/AppForCommercialRequests/releases/tag/v1.0.2.30\"><span style=\" font-size:12pt; text-decoration: underline; color:#262524;\">1.0.4</span></a></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:12pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">1. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f \u0432 Excel</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12"
                        "pt;\">2. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f \u0432 Docx - &quot;\u0423\u0441\u043b\u043e\u0432\u0438\u044f \u043e\u043f\u043b\u0430\u0442\u044b&quot;</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">3. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0430 \u043e\u0448\u0438\u0431\u043a\u0430 \u0441 \u043e\u0447\u0438\u0441\u0442\u043a\u043e\u0439 \u0444\u0430\u0439\u043b\u043e\u0432 \u043a\u043e\u043d\u0444\u0438\u0433\u0430 \u0438 \u043f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u044b\u0445<br />4. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e \u043f\u0440\u0430\u0432\u0438\u043b\u044c\u043d\u043e\u0435 \u0447\u0442\u0435\u043d\u0438\u0435 \u043f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u044b\u0445</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0;"
                        " text-indent:0px; font-size:12pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">17.01.2026<br /></span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt; font-weight:700;\">\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435  </span><a href=\"https://github.com/p4st1/AppForCommercialRequests/releases/tag/v1.0.2.30\"><span style=\" font-size:12pt; text-decoration: underline; color:#262524;\">1.0.3</span></a></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:12pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">1. \u0414\u043e\u043f\u043e\u043b"
                        "\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u043f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u0430\u044f &quot;\u041d\u0430\u0446\u0435\u043d\u043a\u0430&quot;</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">2. \u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u0432 \u0438\u043d\u0442\u0435\u0440\u0444\u0435\u0439\u0441\u0435:<br />	- \u041d\u043e\u0432\u0430\u044f \u0432\u043a\u043b\u0430\u0434\u043a\u0430 &quot;\u041e\u0431\u0432\u043e\u0432\u043b\u0435\u043d\u0438\u044f&quot; \u0441 \u043f\u043e\u043b\u0435\u0437\u043d\u043e\u0439 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u0435\u0439 \u043e \u043d\u043e\u0432\u044b\u0445 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f\u0445 </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\""
                        ">	- \u041f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u0430\u044f &quot;\u041d\u0430\u0446\u0435\u043d\u043a\u0430&quot; \u0442\u0435\u043f\u0435\u0440\u044c \u0440\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u0443\u0435\u043c\u0430\u044f</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">	- \u041d\u043e\u0432\u0430\u044f \u043a\u043d\u043e\u043f\u043a\u0430 &quot;\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438&quot; -&gt; &quot;\u041e\u0447\u0438\u0441\u0442\u0438\u0442\u044c \u043a\u044d\u0448&quot;</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">3. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e \u0437\u0430\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435 \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0439 \u0442\u0430\u0431\u043b\u0438\u0446\u044b \u0432\u043e"
                        " \u0432\u043a\u043b\u0430\u0434\u043a\u0435 &quot;\u041f\u043e\u043b\u043d\u0430\u044f \u0442\u0430\u0431\u043b\u0438\u0446\u0430&quot;</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">4. \u0418\u0437\u043c\u0435\u043d\u0435\u043d\u043e \u0444\u043e\u0440\u043c\u0430\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u0438\u0442\u043e\u0433\u043e\u0432\u043e\u0433\u043e \u041a\u041f</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">5. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e \u0437\u0430\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435 \u0438\u0442\u043e\u0433\u043e\u0432\u043e\u0439 \u0442\u0430\u0431\u043b\u0438\u0446\u044b \u0432 \u041a\u041f:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-i"
                        "ndent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">6. \u041d\u043e\u0432\u044b\u0435 \u0444\u0443\u043d\u043a\u0446\u0438\u0438 \u0432 \u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430\u0445:<br />	- \u041e\u0442\u043a\u0440\u044b\u0432\u0430\u0442\u044c \u043f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0443\u044e \u0442\u0430\u0431\u043b\u0438\u0446\u0443 - \u043e\u0442\u043a\u0440\u044b\u0432\u0430\u0435\u0442 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u044e\u044e \u0442\u0430\u0431\u043b\u0438\u0446\u0443, \u043e\u0442\u043a\u0440\u044b\u0442\u0443\u044e \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u043c</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">	- \u041f\u0440\u0438 \u043e\u0442\u043a\u0440\u044b\u0442\u0438\u0438 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f, \u043e\u0442\u043a\u0440\u044b\u0432\u0430\u0442\u044c \u0432\u043a"
                        "\u043b\u0430\u0434\u043a\u0443 &quot;\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f&quot; - \u043e\u0442\u043a\u0440\u044b\u0432\u0430\u0435\u0442 \u0432\u043a\u043b\u0430\u0434\u043a\u0443 \u0441 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435\u043c \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f \u043d\u0430 \u0433\u043b\u0430\u0432\u043d\u043e\u043c \u044d\u043a\u0440\u0430\u043d\u0435</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">	- \u0412\u044b\u0431\u043e\u0440 \u043e\u0442\u0441\u0442\u0443\u043f\u0430 \u043f\u0440\u0438 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0438 Excel - \u0438\u0437\u043c\u0435\u043d\u044f\u0435\u0442 \u043e\u0442\u0441\u0442\u0443\u043f \u0443 \u0438\u0442\u043e\u0433\u043e\u0432\u043e\u0439 \u0442\u0430\u0431\u043b\u0438\u0446\u044b \u0432 Excel \u043d\u0430 \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0439 \u043e"
                        "\u0442\u0441\u0442\u0443\u043f</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">7. \u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0435 \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u0438\u0445 \u0444\u0430\u0439\u043b\u043e\u0432 Excel</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">8. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0435 \u043f\u043e\u043b\u0430 \u0437\u0430\u043a\u0430\u0437\u0447\u0438\u043a\u0430</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">9. \u0418\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0430 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0430"
                        " \u043f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u043e\u0439 \u043b\u043e\u0433\u0438\u0441\u0442\u0438\u043a\u0438</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">10. \u0418\u0442\u043e\u0433\u043e\u0432\u0430\u044f \u0441\u0443\u043c\u043c\u0430 \u0432 Docx \u0442\u0435\u043f\u0435\u0440\u044c \u043f\u0440\u043e\u043f\u0438\u0441\u044b\u0432\u0430\u0435\u0442\u0441\u044f \u043f\u0440\u043e\u043f\u0438\u0441\u044c\u044e</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:12pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt; font-weight:700;\">\u0420\u0435\u043b\u0438\u0437  </span><a href=\"https://github.com/p4st1/AppForCommercialRequests/releases/tag/v1."
                        "0.2.30\"><span style=\" font-size:12pt; text-decoration: underline; color:#262524;\">1.0.2</span></a></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:12pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">1. Excel</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">   - \u041f\u043e\u044f\u0432\u0438\u043b\u0430\u0441\u044c \u043a\u043d\u043e\u043f\u043a\u0430, \u043f\u043e\u0437\u0432\u043e\u043b\u044f\u044e\u0449\u0430\u044f \u0441\u0444\u043e\u0440\u043c\u0438\u0432\u0440\u043e\u0432\u0430\u0442\u044c \u0442\u0430\u0431\u043b\u0438\u0446\u0443 \u0441 \u0440\u0430\u0441\u0447\u0435\u0442\u0430\u043c\u0438 \u0438 \u0441\u043a\u0430\u0447\u0430\u0442\u044c \u0444\u0430"
                        "\u0439\u043b \u0441 \u0440\u0430\u0441\u0448\u0438\u0440\u0435\u043d\u0438\u0435\u043c .excel.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">2. \u041d\u043e\u0432\u044b\u0435 \u0432\u0435\u0440\u0441\u0438\u0438 \u0434\u043b\u044f Macos ARM64x \u0438 MacOS x86 (x64)</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">3. \u041d\u043e\u0432\u044b\u0435 \u043f\u0443\u043d\u043a\u0442\u044b \u0432 \u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430\u0445:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">   - \u041f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 \u0432\u043a\u043b\u0430\u0434\u043a\u0438 \u043d\u0430 \u0430\u043a\u0442\u0438"
                        "\u0432\u043d\u0443\u044e, \u043f\u0440\u0438 \u043e\u0442\u043a\u0440\u044b\u0442\u0438\u0438 \u0442\u0430\u0431\u043b\u0438\u0446\u044b</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">   - \u0414\u0438\u0440\u0435\u043a\u0442\u043e\u0440\u0438\u044f \u0434\u043b\u044f \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f Excel \u0442\u0430\u0431\u043b\u0438\u0446</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">4. \u041a\u043d\u043e\u043f\u043a\u0438 \u0432 \u0432\u0435\u0440\u0445\u043d\u0435\u043c \u043c\u0435\u043d\u044e \u0434\u0443\u0431\u043b\u0438\u0440\u0443\u044e\u0442 \u0444\u0443\u043d\u043a\u0446\u0438\u043e\u043d\u0430\u043b \u043d\u0438\u0436\u043d\u0438\u0445 \u0444\u0443\u043d\u043a\u0446\u0438\u043e\u043d\u0430\u043b\u044c\u043d\u044b\u0445 \u043a\u043d"
                        "\u043e\u043f\u043e\u043a</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:12pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">18.12.2025</span></p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0446\u0435\u043d\u043a\u0430", None))
        self.markupLine.setText("")
        self.markupLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u0427\u0438\u0441\u043b\u043e", None))
        self.requestNumberLabel.setText(QCoreApplication.translate("MainWindow", u"\u041d\u043e\u043c\u0435\u0440 \u0437\u0430\u044f\u0432\u043a\u0438", None))
        self.requestNumberLine.setText("")
        self.requestNumberLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440: 24-2026", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"\u041b\u043e\u0433\u0438\u0441\u0442\u0438\u043a\u0430", None))
        self.logisticVar.setItemText(0, QCoreApplication.translate("MainWindow", u"\u043a\u043e\u044d\u0444\u0444\u0438\u0446\u0438\u0435\u043d\u0442", None))
        self.logisticVar.setItemText(1, QCoreApplication.translate("MainWindow", u"\u0440\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0435", None))

        self.logisticNum.setText("")
        self.logisticNum.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u0427\u0438\u0441\u043b\u043e", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u0422\u0430\u043c\u043e\u0436\u043d\u044f", None))
        self.customLine.setText("")
        self.customLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u041a\u043e\u044d\u0444\u0444\u0438\u0446\u0438\u0435\u043d\u0442", None))
        self.openTableButton.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u041a\u041f \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430", None))
        self.closeTableButton.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c \u0442\u0430\u0431\u043b\u0438\u0446\u0443", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0440\u043e\u043a \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438", None))
        self.termDeliveryLine.setText("")
        self.termDeliveryLine.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u0427\u0438\u0441\u043b\u043e (\u0432 \u0441\u0443\u0442\u043a\u0430\u0445)", None))
        self.createDocButton.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043a\u0430\u0447\u0430\u0442\u044c \u041a\u041f", None))
        self.createDocFromExcelButton.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043a\u0430\u0447\u0430\u0442\u044c \u041a\u041f \u0438\u0437 \u0440\u0430\u0441\u0447\u0435\u0442\u043e\u0432", None))
        self.createExcelButton.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043a\u0430\u0447\u0430\u0442\u044c \u0440\u0430\u0441\u0447\u0435\u0442\u044b", None))
        self.FileMenu.setTitle(QCoreApplication.translate("MainWindow", u"\u0424\u0430\u0439\u043b", None))
        self.EditMenu.setTitle(QCoreApplication.translate("MainWindow", u"\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c", None))
        self.SettingsMenu.setTitle(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", None))
        self.WindowMenu.setTitle(QCoreApplication.translate("MainWindow", u"\u041e\u043a\u043d\u043e", None))
        self.HelpMenu.setTitle(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u043c\u043e\u0449\u044c", None))
    # retranslateUi
