from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

from tools import DatabaseTools as Tool


class UiFeedbackMixin:
    def _show_status_message(self, message, timeout_ms=0):
        status_bar_getter = getattr(self, "statusBar", None)
        status_bar = status_bar_getter() if callable(status_bar_getter) else None
        if status_bar is None or not message:
            return
        try:
            timeout = int(timeout_ms or 0)
        except (TypeError, ValueError):
            timeout = 0
        status_bar.showMessage(str(message), timeout)
        try:
            from PySide6.QtWidgets import QApplication

            QApplication.processEvents()
        except Exception:
            pass

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
