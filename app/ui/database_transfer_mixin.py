from datetime import datetime

from PySide6.QtWidgets import QFileDialog, QMessageBox

from config import Config


class DatabaseTransferMixin:
    def exportDatabase(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить файл",
            f"database_{datetime.now().strftime('%d.%m.%Y')}.db",
            "База данных (*.db);;Все файлы (*)",
        )
        if not file_path:
            return

        status = self.db.export(Config.db_path, file_path)
        if status == -1:
            self.error("Ошибка", "Не удалось экспортировать базу данных")
        else:
            QMessageBox.information(self, "Готово", "База данных экспортирована")

    def importDatabase(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть файл",
            "",
            "База данных (*.db);;Все файлы (*)",
        )
        if not file_path:
            return

        status = self.db.import_(file_path, Config.db_path)
        if status == -1:
            self.error("Ошибка", "Не удалось импортировать базу данных")
        else:
            self.db.close()
            self.db.open(Config.db_path)
            QMessageBox.information(self, "Готово", "База данных импортирована")
