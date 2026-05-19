from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox


class InfoDialogsMixin:
    def show_help(self):
        help_text = """
        <html>
        <head>
        <style>
            h2 { color: #2c3e50; }
            h3 { color: #34495e; }
            .hotkey { background: #ecf0f1; padding: 2px 6px; border-radius: 3px; }
        </style>
        </head>
        <body>
        <h2>📖 Справка по программе</h2>

        <h3>Основные функции</h3>
        <ul>
            <li><b>Настройки → Импортировать БД</b> - импортировать БД с заказчиками</li>
            <li><b>Настройки → Экспортировать БД</b> - сохранить текущую БД с заказчиками</li>
        </ul>

        <h3>Переменные</h3>
        <p>Для заполнения переменных, необходимо перейти в <b>Редактировать -> редактировать переменные</b>. Далее для использования переменных
        необходимо соблюдать формат: $название переменной$</p>

        <h3>Логистика</h3>
        <li><b>Распределение</b> - распределяет указанную сумму на столбцы</li>
            <li><b>Коэффициент</b> - умножает указанную сумму на столбцы</li>

        <h3>Горячие клавиши</h3>
        <ul>
            <li><span class="hotkey">F1</span> - открыть справку</li>
            <li><span class="hotkey">Ctrl+O</span> - открыть таблицу</li>
            <li><span class="hotkey">Ctrl+F</span> - поиск по таблице</li>
            <li><span class="hotkey">Ctrl+D</span> - дублировать выбранные строки</li>
            <li><span class="hotkey">Ctrl+Enter</span> - протянуть формулу по выделенным строкам</li>
            <li><span class="hotkey">Ctrl + выделение ячеек</span> - протянуть формулу из активной ячейки</li>
            <li><span class="hotkey">Ctrl+Z / Cmd+Z</span> - отменить последнее изменение таблицы</li>
            <li><span class="hotkey">Delete / Backspace</span> - очистить выделенные ячейки</li>
            <li><span class="hotkey">Ctrl+Delete</span> - удалить выбранные строки</li>
            <li><span class="hotkey">Ctrl+Shift+E</span> - скачать КП</li>
        </ul>

        <h3>Поддержка</h3>
        <p>При возникновении проблем:</p>
        <ol>
            <li>Перезапустите программу</li>
            <li>Проверьте наличие обновлений</li>
            <li>Обратитесь в техподдержку: zemtsovpast@yandex.ru</li>
            <li>Телеграм: @p4strick</li>
        </ol>
        </body>
        </html>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Справка")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def show_about(self):
        QMessageBox.about(
            self,
            "О программе",
            "<b>Автоматизация подгтовки коммерческих приложений</b><br>"
            "Версия 1.0.5<br><br>"
            "Создано с использованием PySide6<br>"
            "<br>Лицензия MIT</br>"
            "Автор: https://github.com/p4st1",
        )
