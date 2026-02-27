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
    background-color: #edf1f5;
    color: #24374d;
    font-family: "Segoe UI";
    font-size: 12px;
}

QWidget#centralwidget, QWidget#centralWidget {
    background-color: #edf1f5;
}

QMenuBar {
    background-color: #dbe5f1;
    color: #24374d;
    border-bottom: 1px solid #b9c7d8;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
}

QMenuBar::item:selected {
    background-color: #c8d8ea;
}

QMenu {
    background-color: #f6f9fc;
    color: #24374d;
    border: 1px solid #b9c7d8;
}

QMenu::item {
    padding: 6px 20px 6px 10px;
}

QMenu::item:selected {
    background-color: #dce8f6;
}

QStatusBar {
    background-color: #e5edf7;
    color: #2d3f54;
    border-top: 1px solid #bccbdd;
}

QTabWidget::pane {
    border: 1px solid #c7d4e2;
    background-color: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background-color: #eef3f8;
    border: 1px solid #c7d4e2;
    border-bottom: none;
    color: #30465d;
    padding: 6px 12px;
    min-width: 100px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1f3653;
    font-weight: 600;
}

QTabBar::tab:!selected {
    margin-top: 2px;
}

QTableWidget, QListWidget, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #c7d4e2;
    border-radius: 4px;
    color: #24374d;
}

QTableWidget {
    gridline-color: #d3dde8;
    alternate-background-color: #f7f9fc;
    selection-background-color: #d9e8f7;
    selection-color: #1f3653;
}

QHeaderView::section {
    background-color: #dde7f2;
    color: #24374d;
    border: 1px solid #c7d4e2;
    border-top: none;
    border-left: none;
    padding: 6px;
    font-weight: 600;
}

QTableCornerButton::section {
    background-color: #dde7f2;
    border: 1px solid #c7d4e2;
}

QListWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #eef3f8;
}

QListWidget::item:selected {
    background-color: #d9e8f7;
    color: #1f3653;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: #ffffff;
    border: 1px solid #b9c8d9;
    border-radius: 3px;
    padding: 4px 8px;
    color: #24374d;
    min-height: 24px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
    border: 1px solid #5b86b1;
    background-color: #fdfefe;
}

QComboBox::drop-down {
    width: 22px;
    border-left: 1px solid #b9c8d9;
    background-color: #ecf2f8;
}

QCheckBox, QRadioButton, QLabel {
    color: #2b3f55;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 14px;
    height: 14px;
}

QPushButton {
    background-color: #e8eef5;
    color: #2a425d;
    border: 1px solid #bcccdd;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 30px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #dce7f3;
}

QPushButton:pressed {
    background-color: #ccdced;
}

QPushButton[variant="primary"] {
    background-color: #5f88b3;
    color: #ffffff;
    border: 1px solid #4f769f;
}

QPushButton[variant="primary"]:hover {
    background-color: #6c96c2;
}

QPushButton[variant="primary"]:pressed {
    background-color: #4d739c;
}

QPushButton[variant="danger"] {
    background-color: #c85a5a;
    color: #ffffff;
    border: 1px solid #a44747;
}

QPushButton[variant="danger"]:hover {
    background-color: #d26b6b;
}

QPushButton[variant="danger"]:pressed {
    background-color: #b54d4d;
}

QPushButton:disabled {
    background-color: #b7c7d8;
    color: #edf2f7;
    border-color: #aab9c9;
}

QFrame[separator="true"] {
    background-color: #c7d4e2;
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
