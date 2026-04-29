import platform

from PySide6.QtWidgets import QFrame, QPushButton, QTableWidget, QWidget


PRIMARY_BUTTONS = {
    "acceptButton",
    "addButton",
    "addNewButton",
    "addSupplierButton",
    "createDocButton",
    "createDocFromExcelButton",
    "createExcelButton",
    "saveAndCloseButton",
    "saveButton",
}

DANGER_BUTTONS = {
    "deleteSupplierButton",
}

NEUTRAL_BUTTONS = {
    "cancelButton",
    "cancellButton",
    "changeSupplierButton",
    "closeButton",
    "closeTableButton",
    "dirOpenButton",
    "dirOpenButton_2",
    "openTableButton",
}


UNIFIED_QSS = """
QMainWindow, QWidget {
    background-color: #e7eaee;
    color: #1f2a36;
    font-family: "Segoe UI";
    font-size: 12px;
}

QWidget#centralwidget, QWidget#centralWidget {
    background-color: #e7eaee;
}

QMenuBar {
    background-color: #d8dde4;
    color: #1f2a36;
    border-bottom: 1px solid #afb8c4;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
}

QMenuBar::item:selected {
    background-color: #c2cad5;
}

QMenu {
    background-color: #f2f4f7;
    color: #1f2a36;
    border: 1px solid #afb8c4;
}

QMenu::item {
    padding: 6px 20px 6px 10px;
}

QMenu::item:selected {
    background-color: #d3dae3;
}

QStatusBar {
    background-color: #dde2e8;
    color: #273443;
    border-top: 1px solid #b3bcc7;
}

QTabWidget::pane {
    border: 1px solid #b8c2cd;
    background-color: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background-color: #e3e8ef;
    border: 1px solid #b8c2cd;
    border-bottom: none;
    color: #2a3848;
    padding: 6px 12px;
    min-width: 100px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #172330;
    font-weight: 600;
}

QTabBar::tab:!selected {
    margin-top: 2px;
}

QTableWidget, QListWidget, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #b8c2cd;
    border-radius: 4px;
    color: #1f2a36;
}

QTableWidget {
    gridline-color: #ccd4de;
    alternate-background-color: #f5f7f9;
    selection-background-color: #d1d9e3;
    selection-color: #172330;
}

QHeaderView::section {
    background-color: #d7dee7;
    color: #1f2a36;
    border: 1px solid #b8c2cd;
    border-top: none;
    border-left: none;
    padding: 6px;
    font-weight: 600;
}

QTableCornerButton::section {
    background-color: #d7dee7;
    border: 1px solid #b8c2cd;
}

QListWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #e4e9ef;
}

QListWidget::item:selected {
    background-color: #d1d9e3;
    color: #172330;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: #ffffff;
    border: 1px solid #aeb8c4;
    border-radius: 3px;
    padding: 4px 8px;
    color: #1f2a36;
    min-height: 24px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
    border: 1px solid #5b6777;
    background-color: #fcfdff;
}

QComboBox::drop-down {
    width: 22px;
    border-left: 1px solid #aeb8c4;
    background-color: #e8edf3;
}

QCheckBox, QRadioButton, QLabel {
    color: #243242;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 14px;
    height: 14px;
}

QPushButton {
    background-color: #dde4ec;
    color: #243242;
    border: 1px solid #aeb8c4;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 30px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #d2dbe5;
}

QPushButton:pressed {
    background-color: #c4ceda;
}

QPushButton[variant="primary"] {
    background-color: #425266;
    color: #ffffff;
    border: 1px solid #364556;
}

QPushButton[variant="primary"]:hover {
    background-color: #4c5e74;
}

QPushButton[variant="primary"]:pressed {
    background-color: #38485b;
}

QPushButton[variant="danger"] {
    background-color: #8e4c4c;
    color: #ffffff;
    border: 1px solid #783f3f;
}

QPushButton[variant="danger"]:hover {
    background-color: #9e5858;
}

QPushButton[variant="danger"]:pressed {
    background-color: #7d4444;
}

QPushButton:disabled {
    background-color: #bec8d3;
    color: #edf1f5;
    border-color: #adb7c3;
}

QFrame[separator="true"] {
    background-color: #b8c2cd;
    border: none;
    min-height: 1px;
    max-height: 1px;
}
"""


MAC_QSS = (
    UNIFIED_QSS
    + """
QMainWindow, QWidget {
    background-color: #f5f5f7;
    color: #1d1d1f;
    font-family: "SF Pro Text", "Helvetica Neue", "Arial";
    font-size: 13px;
}

QWidget#centralwidget, QWidget#centralWidget {
    background-color: #f5f5f7;
}

QMenuBar {
    background-color: #f5f5f7;
    color: #1d1d1f;
    border-bottom: 1px solid #d2d2d7;
}

QMenuBar::item {
    padding: 7px 14px;
    border-radius: 6px;
}

QMenuBar::item:selected {
    background-color: #e5e5ea;
}

QMenu {
    background-color: #ffffff;
    color: #1d1d1f;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 7px 24px 7px 12px;
    border-radius: 6px;
}

QMenu::item:selected {
    background-color: #e5e5ea;
}

QStatusBar {
    background-color: #f5f5f7;
    color: #3a3a3c;
    border-top: 1px solid #d2d2d7;
}

QTabWidget::pane {
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #ececf0;
    border: 1px solid #d2d2d7;
    border-bottom: none;
    color: #3a3a3c;
    padding: 8px 16px;
    min-width: 110px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1d1d1f;
    font-weight: 600;
}

QTableWidget, QListWidget, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    color: #1d1d1f;
}

QTableWidget {
    background-color: white;
    gridline-color: #d0d0d0;
    alternate-background-color: #f7f7fa;
    selection-background-color: #d7e9ff;
    selection-color: #1d1d1f;
}

QHeaderView::section {
    background-color: #f2f2f7;
    color: #1d1d1f;
    border: 1px solid #d2d2d7;
    padding: 7px;
    font-weight: 600;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: #ffffff;
    border: 1px solid #d1d1d6;
    border-radius: 8px;
    padding: 6px 10px;
    color: #1d1d1f;
    min-height: 28px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
    border: 1px solid #007aff;
    background-color: #ffffff;
}

QPushButton {
    background-color: #e5e5ea;
    color: #1d1d1f;
    border: 1px solid #d1d1d6;
    border-radius: 8px;
    padding: 6px 12px;
    min-height: 32px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #dcdce0;
}

QPushButton:pressed {
    background-color: #d1d1d6;
}

QPushButton[variant="primary"] {
    background-color: #007aff;
    color: #ffffff;
    border: 1px solid #0071eb;
    border-radius: 8px;
}

QPushButton[variant="primary"]:hover {
    background-color: #0a84ff;
}

QPushButton[variant="danger"] {
    background-color: #ff3b30;
    color: #ffffff;
    border: 1px solid #e7352b;
    border-radius: 8px;
}

QPushButton[variant="danger"]:hover {
    background-color: #ff453a;
}

QFrame[separator="true"] {
    background-color: #d2d2d7;
}
"""
)


WINDOWS_QSS = (
    UNIFIED_QSS
    + """
QMainWindow, QWidget {
    background-color: #ffffff;
    color: #202020;
    font-family: "Segoe UI";
    font-size: 12px;
}

QWidget#centralwidget, QWidget#centralWidget {
    background-color: #ffffff;
}

QMenuBar {
    background-color: #f3f3f3;
    color: #202020;
    border-bottom: 1px solid #c0c0c0;
}

QMenuBar::item {
    padding: 5px 10px;
    border-radius: 2px;
}

QMenuBar::item:selected {
    background-color: #e5e5e5;
}

QMenu {
    background-color: #ffffff;
    color: #202020;
    border: 1px solid #c0c0c0;
    border-radius: 2px;
}

QMenu::item {
    padding: 5px 22px 5px 10px;
}

QMenu::item:selected {
    background-color: #e0e0e0;
}

QStatusBar {
    background-color: #f3f3f3;
    color: #202020;
    border-top: 1px solid #c0c0c0;
}

QTabWidget::pane {
    border: 1px solid #c0c0c0;
    border-radius: 2px;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #f0f0f0;
    border: 1px solid #c0c0c0;
    border-bottom: none;
    color: #202020;
    padding: 5px 12px;
    min-width: 100px;
    border-top-left-radius: 2px;
    border-top-right-radius: 2px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #202020;
    font-weight: 600;
}

QTableWidget, QListWidget, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 2px;
    color: #202020;
}

QTableWidget {
    background-color: white;
    gridline-color: #c0c0c0;
    alternate-background-color: #f7f7f7;
    selection-background-color: #cce8ff;
    selection-color: #202020;
}

QHeaderView::section {
    background-color: #f0f0f0;
    color: #202020;
    border: 1px solid #c0c0c0;
    padding: 5px;
    font-weight: 600;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 2px;
    padding: 4px 8px;
    color: #202020;
    min-height: 24px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
    border: 1px solid #0078d4;
    background-color: #ffffff;
}

QPushButton {
    background-color: #f0f0f0;
    color: #202020;
    border: 1px solid #c0c0c0;
    border-radius: 2px;
    padding: 5px 10px;
    min-height: 28px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #e0e0e0;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QPushButton[variant="primary"] {
    background-color: #0078d4;
    color: #ffffff;
    border: 1px solid #006cbe;
    border-radius: 2px;
}

QPushButton[variant="primary"]:hover {
    background-color: #106ebe;
}

QPushButton[variant="danger"] {
    background-color: #c42b1c;
    color: #ffffff;
    border: 1px solid #a4262c;
    border-radius: 2px;
}

QPushButton[variant="danger"]:hover {
    background-color: #d13438;
}

QFrame[separator="true"] {
    background-color: #c0c0c0;
}
"""
)


def _clear_inline_styles(window: QWidget):
    if window.styleSheet():
        window.setStyleSheet("")
    for child in window.findChildren(QWidget):
        if child.styleSheet():
            child.setStyleSheet("")


def _mark_widget_roles(window: QWidget):
    for table in window.findChildren(QTableWidget):
        table.setAlternatingRowColors(True)

    for frame in window.findChildren(QFrame):
        shape = frame.frameShape()
        if shape in (QFrame.Shape.HLine, QFrame.Shape.VLine):
            frame.setProperty("separator", True)

    for button in window.findChildren(QPushButton):
        name = button.objectName()
        if name in PRIMARY_BUTTONS:
            button.setProperty("variant", "primary")
        elif name in DANGER_BUTTONS:
            button.setProperty("variant", "danger")
        elif name in NEUTRAL_BUTTONS:
            button.setProperty("variant", "neutral")
        else:
            button.setProperty("variant", "neutral")


def get_platform():
    return platform.system()


def apply_mac_style(window):
    window.setStyleSheet(MAC_QSS)


def apply_windows_style(window):
    window.setStyleSheet(WINDOWS_QSS)


def apply_default_style(window):
    window.setStyleSheet(UNIFIED_QSS)


def apply_unified_theme(window: QWidget):
    _clear_inline_styles(window)
    _mark_widget_roles(window)
    platform_name = get_platform()
    if platform_name == "Darwin":
        apply_mac_style(window)
    elif platform_name == "Windows":
        apply_windows_style(window)
    else:
        apply_default_style(window)
