from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

from tools import DatabaseTools as Tool


class UiFeedbackMixin:
    def open_url(self, url):
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            Tool.log_exception(f"Не удалось открыть URL: {url}", e, include_traceback=False)

    def error(self, title, text):
        error = QMessageBox(self)
        error.setWindowTitle(title)
        error.setText(text)
        error.exec()
