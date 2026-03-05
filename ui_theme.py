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


def apply_unified_theme(window: QWidget):
    _clear_inline_styles(window)
    _mark_widget_roles(window)
    window.setStyleSheet(UNIFIED_QSS)
