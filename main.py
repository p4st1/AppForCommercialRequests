from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtCore import Qt, QUrl
from createDocument import mainWindow as createDocWindow
from create import createExcelFile as exportExcelFile
from customers import mainWindow as customersWindow
from settings import mainWindow as settingsWindow
from tools import DatabaseTools as Tool
from params import mainWindow as paramsWindow
from database import Database
from config import Config
from ui_mainGui import Ui_MainWindow
from datetime import datetime
from pathlib import Path
import pandas as pd
import shutil
import re
import sys
import os


class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(self.resourcePath("assets/app.ico")))
        self.applyEnterpriseStyle()

        self.tableData = {
            "amount": [],
            "currency": [],
            "unitPrice": [],
            "totalPrice": [],
            "termDelivery": [],
            "logistic": [],
        }
        self.rows = 0
        self.formulaCustom = 1.0
        self.formulaMarkup = 1.0
        self.formulaLogistic = 1.0
        self.termDeliveryDays = 0
        self.mixedCurrencyWarningShown = False

        self.loadConfig()
        self.ensureOutputDirs()

        self.db = Database()
        if self.db.open(Config.db_path) == -1:
            self.error("Ошибка", "Не удалось открыть базу данных")

        if Config.settings["autoFill"]:
            self.ui.logisticNum.setText(Config.config["logisticNum"])
            self.ui.customLine.setText(Config.config["customNum"])
            self.ui.termDeliveryLine.setText(Config.config["termDelivery"])
            self.ui.markupLine.setText(Config.config["markup"])
            self.ui.logisticVar.setCurrentIndex(int(Config.config["logisticVar"]))

        self.ui.openTableButton.clicked.connect(self.openTable)
        self.ui.openTableMenuButton.triggered.connect(self.openTable)
        self.ui.closeTableMenuButton.triggered.connect(self.closeTable)
        self.ui.createDocMenuButton.triggered.connect(self.exportDocs)
        self.ui.createExcelMenuButton.triggered.connect(self.exportExcel)

        self.ui.editParamsButton.triggered.connect(self.openParamsWindow)

        self.ui.suppliersMenuButton.triggered.connect(self.openSuppliersWindow)
        self.ui.settingsMenuButton.triggered.connect(self.openSettingsWindow)
        self.ui.exportMenuButton.triggered.connect(self.exportDatabase)
        self.ui.importMenuButton.triggered.connect(self.importDatabase)
        self.ui.clearCacheMenuButton.triggered.connect(self.clear_cache)
        self.ui.changeFormButton.triggered.connect(self.testFeature)
        self.ui.changeFormButton.setChecked(Config.settings["testFeature"])

        self.ui.helpMenuButton.triggered.connect(self.show_help)
        self.ui.aboutMenuButton.triggered.connect(self.show_about)
        self.ui.GitHubMenuButton.triggered.connect(
            lambda: self.open_url("https://github.com/p4st1/AppForCommercialRequests")
        )
        self.ui.supportMenuButton.triggered.connect(self.show_help)

        self.ui.createDocButton.clicked.connect(self.exportDocs)
        self.ui.createExcelButton.clicked.connect(self.exportExcel)
        self.ui.createDocFromExcelButton.clicked.connect(self.exportDocFromExcel)

        self.ui.logisticVar.currentIndexChanged.connect(self.logisticVarChanged)
        self.ui.logisticNum.editingFinished.connect(self.processFormula)
        self.ui.markupLine.editingFinished.connect(self.processFormula)
        self.ui.customLine.editingFinished.connect(self.processFormula)
        self.ui.termDeliveryLine.editingFinished.connect(self.processFormula)
        self.ui.closeTableButton.clicked.connect(self.closeTable)
        self.ui.KpTable.resizeColumnsToContents()

        if Config.settings["openLastTab"] and Config.config["lastTable"]:
            last_table = Config.config["lastTable"]
            if Path(last_table).exists():
                self.openTable(file=last_table)
            else:
                Config.config["lastTable"] = ""
                self.saveConfig()

        if Config.settings["openUpdateTab"]:
            self.ui.tabWidget.setCurrentIndex(2)
        else:
            self.ui.tabWidget.setCurrentIndex(1)

    def applyEnterpriseStyle(self):
        """Apply a restrained ERP-like style without changing layout structure."""
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #edf1f5;
                color: #24374d;
                font-family: "Segoe UI";
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
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
            }
            QMenu::item:selected {
                background-color: #dce8f6;
            }
            QStatusBar {
                background-color: #e5edf7;
                color: #2d3f54;
                border-top: 1px solid #bccbdd;
            }
            """
        )

        self.ui.centralwidget.setStyleSheet(
            """
            QWidget#centralwidget {
                background-color: #edf1f5;
            }
            """
        )

        self.ui.tabWidget.setStyleSheet(
            """
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
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #1f3653;
                font-weight: 600;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
            """
        )

        self.ui.KpTable.setStyleSheet(
            """
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #c7d4e2;
                border-radius: 4px;
                gridline-color: #d3dde8;
                selection-background-color: #d9e8f7;
                selection-color: #1f3653;
                alternate-background-color: #f7f9fc;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #dde7f2;
                color: #24374d;
                border: 1px solid #c7d4e2;
                border-top: none;
                border-left: none;
                padding: 6px 6px;
                font-weight: 600;
            }
            QTableCornerButton::section {
                background-color: #dde7f2;
                border: 1px solid #c7d4e2;
            }
            QTableWidget::item {
                padding: 4px 6px;
            }
            QTableWidget::item:selected {
                border: 1px solid #89a5c2;
            }
            """
        )
        self.ui.KpTable.setAlternatingRowColors(True)

        input_style = """
            QLineEdit, QComboBox {
                background-color: #ffffff;
                border: 1px solid #b9c8d9;
                border-radius: 3px;
                padding: 4px 8px;
                color: #24374d;
                min-height: 24px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #5b86b1;
                background-color: #fdfefe;
            }
            QComboBox::drop-down {
                width: 22px;
                border-left: 1px solid #b9c8d9;
                background-color: #ecf2f8;
            }
        """
        for widget in (
            self.ui.markupLine,
            self.ui.logisticNum,
            self.ui.customLine,
            self.ui.termDeliveryLine,
            self.ui.logisticVar,
        ):
            widget.setStyleSheet(input_style)

        label_style = """
            QLabel {
                color: #2b3f55;
                font-size: 12px;
                font-weight: 600;
            }
        """
        for widget in (self.ui.label, self.ui.label_2, self.ui.label_3, self.ui.label_5):
            widget.setStyleSheet(label_style)

        neutral_button_style = """
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
        """
        for widget in (self.ui.openTableButton, self.ui.closeTableButton):
            widget.setStyleSheet(neutral_button_style)

        action_button_style = """
            QPushButton {
                background-color: #5f88b3;
                color: #ffffff;
                border: 1px solid #4f769f;
                border-radius: 4px;
                padding: 6px 10px;
                min-height: 30px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #6c96c2;
            }
            QPushButton:pressed {
                background-color: #4d739c;
            }
            QPushButton:disabled {
                background-color: #b7c7d8;
                color: #edf2f7;
                border-color: #aab9c9;
            }
        """
        for widget in (
            self.ui.createDocButton,
            self.ui.createDocFromExcelButton,
            self.ui.createExcelButton,
        ):
            widget.setStyleSheet(action_button_style)

        separator_style = """
            QFrame {
                background-color: #c7d4e2;
                border: none;
                min-height: 1px;
                max-height: 100px;
            }
        """
        for line_name in (
            "line",
            "line1",
            "line_2",
            "line_3",
            "line_4",
            "line_5",
            "line_6",
            "line_7",
            "line_8",
            "line_9",
            "line_10",
        ):
            line_widget = getattr(self.ui, line_name, None)
            if line_widget is not None:
                line_widget.setStyleSheet(separator_style)

        self.ui.textUpdates.setStyleSheet(
            """
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #c7d4e2;
                border-radius: 4px;
                color: #24374d;
                padding: 8px;
            }
            """
        )

    def loadConfig(self):
        try:
            data = Tool.load_json(Config.cfg_path)
        except Exception:
            data = {}
        normalized = Tool.merge_config_with_defaults(data)
        Config.config = normalized["config"]
        Config.settings = normalized["settings"]
        self.saveConfig()

    def saveConfig(self):
        Tool.save_json_atomic(
            Config.cfg_path,
            {"config": Config.config, "settings": Config.settings},
        )

    def ensureOutputDirs(self):
        default_dir = Path.home() / "Documents"
        cp_dir = Tool.ensure_directory(Config.config.get("pathToSaveCP"), default_dir)
        excel_dir = Tool.ensure_directory(Config.config.get("pathToSaveExcel") or cp_dir, cp_dir)
        Config.config["pathToSaveCP"] = str(cp_dir)
        Config.config["pathToSaveExcel"] = str(excel_dir)

    def testFeature(self, checked):
        QMessageBox.about(
            self,
            "ВНИМАНИЕ",
            "Для включения тестовой функции, необходимо перезапустить приложение"
            "<br>*Возможны неточности в склонении слов</br>",
        )

        Config.settings["testFeature"] = checked
        self.saveConfig()

    def clear_cache(self):
        dst_dir = Tool.user_data_dir("MyApp")
        dst_dir.mkdir(parents=True, exist_ok=True)

        dst = dst_dir / "config.json"
        src = Tool.resourcePath("utilities/config.json")
        shutil.copy2(src, dst)

        self.loadConfig()
        self.ensureOutputDirs()
        if Config.settings["autoFill"]:
            self.ui.logisticNum.setText(Config.config["logisticNum"])
            self.ui.customLine.setText(Config.config["customNum"])
            self.ui.termDeliveryLine.setText(Config.config["termDelivery"])
            self.ui.markupLine.setText(Config.config["markup"])
            self.ui.logisticVar.setCurrentIndex(int(Config.config["logisticVar"]))
        self.processFormula()

    def open_url(self, url):
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            Tool.write_log(f"{e}")

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

    @staticmethod
    def _fmt_number(value: float) -> str:
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.6f}".rstrip("0").rstrip(".")

    def _parse_input_parameters(self, show_error=True):
        try:
            custom = float(Tool.evalWithVars(self.ui.customLine.text().replace(",", ".")))
            markup = float(Tool.evalWithVars(self.ui.markupLine.text().replace(",", ".")))
            logistic = float(Tool.evalWithVars(self.ui.logisticNum.text().replace(",", ".")))
            term_delivery = Tool.parse_int(self.ui.termDeliveryLine.text(), "Срок поставки", allow_zero=True)
            if custom <= 0:
                raise ValueError('Поле "Таможня" должно быть положительным')
            if markup <= 0:
                raise ValueError('Поле "Наценка" должно быть положительным')
            if logistic < 0:
                raise ValueError('Поле "Логистика" должно быть неотрицательным')
        except Exception as e:
            if show_error:
                self.error("Ошибка", str(e))
            return None

        self.formulaCustom = custom
        self.formulaMarkup = markup
        self.formulaLogistic = logistic
        self.termDeliveryDays = term_delivery

        self.ui.customLine.setText(self._fmt_number(custom))
        self.ui.markupLine.setText(self._fmt_number(markup))
        self.ui.logisticNum.setText(self._fmt_number(logistic))
        self.ui.termDeliveryLine.setText(str(term_delivery))

        return {
            "custom": custom,
            "markup": markup,
            "logistic": logistic,
            "termDelivery": term_delivery,
        }

    def processFormula(self):
        parsed = self._parse_input_parameters(show_error=True)
        if parsed is None:
            return

        if Config.isTableOpened:
            self.logisticCalculate()
            self.calculating()

    @staticmethod
    def _normalize_header(text):
        value = str(text or "").strip().lower().replace("ё", "е")
        value = re.sub(r"[^a-zа-я0-9]+", "", value)
        return value

    def _read_source_table(self, filename):
        ext = Path(filename).suffix.lower()
        if ext in {".xls", ".xlsx"}:
            return pd.read_excel(filename, header=None, dtype=str).fillna("")

        errors = []
        for encoding in ("utf-8-sig", "utf-16", "cp1251", "utf-8"):
            try:
                return pd.read_csv(
                    filename,
                    header=None,
                    sep=";",
                    dtype=str,
                    encoding=encoding,
                    engine="python",
                    on_bad_lines="skip",
                ).fillna("")
            except Exception as e:
                errors.append(str(e))
        raise ValueError("Не удалось прочитать файл. Проверьте кодировку и формат CSV")

    def _detect_columns(self, df):
        header_row = None
        max_rows = min(len(df.index), 50)
        max_cols = min(len(df.columns), 20)
        for row_idx in range(max_rows):
            row_values = [self._normalize_header(df.iat[row_idx, col]) for col in range(max_cols)]
            has_name = any("наименование" in value for value in row_values)
            has_qty = any("колво" in value or ("кол" in value and "во" in value) for value in row_values)
            has_price = any("цена" in value for value in row_values)
            if has_name and has_qty and has_price:
                header_row = row_idx
                break

        if header_row is None:
            header_row = 0

        mapping = {
            "number": None,
            "name": None,
            "sku": None,
            "unit": None,
            "qty": None,
            "price": None,
            "term": None,
        }

        for col in range(len(df.columns)):
            value = self._normalize_header(df.iat[header_row, col])
            if "наименование" in value:
                if mapping["name"] is None:
                    mapping["name"] = col
            elif "каталож" in value and "номер" in value:
                if mapping["sku"] is None:
                    mapping["sku"] = col
            elif value.startswith("ед") or "едизм" in value:
                if mapping["unit"] is None:
                    mapping["unit"] = col
            elif "колво" in value or ("кол" in value and "во" in value):
                if mapping["qty"] is None:
                    mapping["qty"] = col
            elif (
                "ценазаедбезндс" in value
                or ("цена" in value and "заед" in value)
                or ("цена" in value and mapping["price"] is None)
            ):
                if mapping["price"] is None:
                    mapping["price"] = col
            elif "срок" in value:
                if mapping["term"] is None:
                    mapping["term"] = col
            elif value in {"n", "no", "номер"} or "№" in str(df.iat[header_row, col]):
                if mapping["number"] is None:
                    mapping["number"] = col

        defaults = {
            "number": 0,
            "name": 1,
            "sku": 2,
            "unit": 3,
            "qty": 4,
            "price": 5,
            "term": 6,
        }
        for key, default_col in defaults.items():
            if mapping[key] is None:
                mapping[key] = default_col

        if max(mapping.values()) >= len(df.columns):
            raise ValueError("В таблице не хватает необходимых столбцов")
        return header_row, mapping

    def _parse_source_rows(self, df):
        header_row, mapping = self._detect_columns(df)
        parsed_rows = []
        warnings = []
        blank_streak = 0

        for row_idx in range(header_row + 1, len(df.index)):
            number_text = str(df.iat[row_idx, mapping["number"]]).strip()
            name = str(df.iat[row_idx, mapping["name"]]).strip()
            sku = str(df.iat[row_idx, mapping["sku"]]).strip()
            unit = str(df.iat[row_idx, mapping["unit"]]).strip()
            qty_text = str(df.iat[row_idx, mapping["qty"]]).strip()
            price_text = str(df.iat[row_idx, mapping["price"]]).strip()
            term_text = str(df.iat[row_idx, mapping["term"]]).strip()

            if not any([name, sku, unit, qty_text, price_text, term_text]):
                blank_streak += 1
                if parsed_rows and blank_streak >= 2:
                    break
                continue
            blank_streak = 0

            if not name:
                warnings.append(f"Строка {row_idx + 1}: пропущено наименование, строка пропущена")
                continue

            try:
                qty = Tool.parse_int(qty_text, f"Кол-во (строка {row_idx + 1})", allow_zero=False)
            except ValueError as e:
                warnings.append(str(e))
                continue

            try:
                currency, price_value = Tool.parsePrice(price_text)
                if not currency:
                    match = re.search(r"[¥$₽€]", price_text)
                    if match:
                        currency = match.group(0)
                        price_value = price_text.replace(currency, "").strip()
                if not currency:
                    raise ValueError("Не указана валюта")
                unit_price = Tool.parse_float(price_value, f"Цена (строка {row_idx + 1})", allow_zero=True)
            except ValueError as e:
                warnings.append(f"Строка {row_idx + 1}: {e}")
                continue

            try:
                supplier_term_days = Tool.parse_delivery_days(term_text)
            except ValueError as e:
                warnings.append(f"Строка {row_idx + 1}: {e}. Установлено 0 дней")
                supplier_term_days = 0

            row_number = number_text if number_text else str(len(parsed_rows) + 1)
            parsed_rows.append(
                {
                    "number": row_number,
                    "name": name,
                    "sku": sku,
                    "unit": unit if unit else "шт.",
                    "qty": qty,
                    "currency": currency,
                    "unitPrice": unit_price,
                    "supplierTermDays": supplier_term_days,
                }
            )

        if not parsed_rows:
            raise ValueError("В файле не найдено ни одной валидной строки товара")

        return parsed_rows, warnings

    def openTable(self, file=None):
        filename = file
        if not filename:
            filename = QFileDialog.getOpenFileName(
                self,
                "Открыть файл",
                "",
                "csv (*.csv);; Excel Files (*.xls *.xlsx)",
            )[0]
        if not filename:
            return

        if not Path(filename).exists():
            self.error("Ошибка", f"Файл не найден: {filename}")
            return

        params = self._parse_input_parameters(show_error=True)
        if params is None:
            return

        self.closeTable()
        try:
            df = self._read_source_table(filename)
            parsed_rows, warnings = self._parse_source_rows(df)
        except Exception as e:
            self.error("Ошибка", f"Невозможно прочитать таблицу\n{e}")
            return

        self.ui.KpTable.setRowCount(len(parsed_rows))
        self.tableData = {
            "amount": [],
            "currency": [],
            "unitPrice": [],
            "totalPrice": [],
            "termDelivery": [],
            "logistic": [],
        }

        for row_num, row in enumerate(parsed_rows):
            total_price = round(row["qty"] * row["unitPrice"], 2)
            self.ui.KpTable.setItem(row_num, 0, QTableWidgetItem(str(row["number"])))
            self.ui.KpTable.setItem(row_num, 1, QTableWidgetItem(row["name"]))
            self.ui.KpTable.setItem(row_num, 2, QTableWidgetItem(row["sku"]))
            self.ui.KpTable.setItem(row_num, 3, QTableWidgetItem(row["unit"]))
            self.ui.KpTable.setItem(row_num, 4, QTableWidgetItem(str(row["qty"])))
            self.ui.KpTable.setItem(
                row_num,
                5,
                QTableWidgetItem(Tool.formatPrice(str(row["unitPrice"]), row["currency"])),
            )
            self.ui.KpTable.setItem(
                row_num,
                6,
                QTableWidgetItem(Tool.formatPrice(str(total_price), row["currency"])),
            )
            self.ui.KpTable.setItem(row_num, 14, QTableWidgetItem(f"{row['supplierTermDays']} дней"))

            self.tableData["amount"].append(row["qty"])
            self.tableData["currency"].append(row["currency"])
            self.tableData["unitPrice"].append(row["unitPrice"])
            self.tableData["totalPrice"].append(total_price)
            self.tableData["termDelivery"].append(row["supplierTermDays"])

        self.rows = len(parsed_rows)
        self.mixedCurrencyWarningShown = False
        self.logisticCalculate()
        self.calculating()
        self.ui.KpTable.resizeColumnsToContents()

        Config.config["lastTable"] = filename
        self.saveConfig()
        Config.isTableOpened = True
        self.ui.tabWidget.setCurrentIndex(1)

        if warnings:
            trimmed = warnings[:10]
            message = "Найдены проблемы в таблице:\n- " + "\n- ".join(trimmed)
            if len(warnings) > 10:
                message += f"\n... и еще {len(warnings) - 10}"
            QMessageBox.warning(self, "Внимание", message)

    def error(self, title, text):
        error = QMessageBox(self)
        error.setWindowTitle(title)
        error.setText(text)
        error.exec()

    def openCreateDocWindow(self, tableData):
        window = createDocWindow(self, tableData=tableData)
        window.show()
        if Config.settings["closeTable"]:
            window.windowClosed.connect(self.closeTable)
            self.ui.KpTable.setRowCount(0)

    def openParamsWindow(self):
        window = paramsWindow(self)
        window.show()

    def openSettingsWindow(self):
        window = settingsWindow(self)
        window.show()

    def openSuppliersWindow(self):
        window = customersWindow(self)
        window.show()

    def closeTable(self):
        self.ui.KpTable.clearContents()
        self.ui.KpTable.setRowCount(0)
        self.tableData = {
            "amount": [],
            "currency": [],
            "unitPrice": [],
            "totalPrice": [],
            "termDelivery": [],
            "logistic": [],
        }
        self.rows = 0
        Config.isTableOpened = False

    def _vat_multiplier(self):
        params_data = Tool.load_json(Config.vars_path)
        for values in params_data.get("parameters", {}).values():
            if len(values) < 3:
                continue
            name, value, calc_type = values[0], values[1], values[2]
            if name == "НДС":
                try:
                    rate = float(str(value).replace(",", "."))
                except ValueError:
                    return 1.0
                if calc_type == "percents":
                    return 1 + rate / 100
                return 1 + rate
        return 1.0

    def calculating(self):
        if not self.tableData["amount"] or not self.tableData["logistic"]:
            return

        vat_multiplier = self._vat_multiplier()
        for row_num in range(self.rows):
            amount = self.tableData["amount"][row_num]
            currency = self.tableData["currency"][row_num]
            logistic_value = self.tableData["logistic"][row_num]
            customs_sum = round(logistic_value * self.formulaCustom, 2)
            unit_sale_price = round(customs_sum / amount, 2)
            real_price = round(unit_sale_price * self.formulaMarkup, 2)
            total_without_vat = round(real_price * amount, 2)
            total_with_vat = round(total_without_vat * vat_multiplier, 2)

            self.ui.KpTable.setItem(
                row_num,
                8,
                QTableWidgetItem(Tool.formatPrice(str(customs_sum), currency)),
            )
            self.ui.KpTable.setItem(
                row_num,
                9,
                QTableWidgetItem(Tool.formatPrice(str(unit_sale_price), currency)),
            )
            self.ui.KpTable.setItem(
                row_num,
                10,
                QTableWidgetItem(Tool.formatPrice(str(real_price), currency)),
            )
            self.ui.KpTable.setItem(
                row_num,
                11,
                QTableWidgetItem(Tool.formatPrice(str(total_without_vat), currency)),
            )
            self.ui.KpTable.setItem(
                row_num,
                12,
                QTableWidgetItem(Tool.formatPrice(str(total_with_vat), currency)),
            )
            self.ui.KpTable.setItem(
                row_num,
                13,
                QTableWidgetItem(f"{self.tableData['termDelivery'][row_num] + self.termDeliveryDays} дней"),
            )

    def logisticVarChanged(self, _):
        if Config.isTableOpened:
            self.logisticCalculate()
            self.calculating()

    def logisticCalculate(self):
        if not self.tableData["totalPrice"]:
            return

        logistic_var = self.ui.logisticVar.currentIndex()
        currencies = set(self.tableData["currency"])
        if logistic_var == 1 and len(currencies) > 1:
            if not self.mixedCurrencyWarningShown:
                QMessageBox.warning(
                    self,
                    "Внимание",
                    "Режим 'распределение' недоступен при смешанной валюте. "
                    "Переключено на режим 'коэффициент'.",
                )
                self.mixedCurrencyWarningShown = True
            self.ui.logisticVar.blockSignals(True)
            self.ui.logisticVar.setCurrentIndex(0)
            self.ui.logisticVar.blockSignals(False)
            logistic_var = 0

        logistic_num = self.formulaLogistic
        total_sum = sum(self.tableData["totalPrice"])
        self.tableData["logistic"] = []

        for row_num in range(self.rows):
            base_total = self.tableData["totalPrice"][row_num]
            if logistic_var == 1:
                if total_sum <= 0:
                    f = 0
                else:
                    f = round(base_total + logistic_num / total_sum * base_total, 2)
            else:
                f = round(base_total * logistic_num, 2)
            currency = self.tableData["currency"][row_num]
            self.ui.KpTable.setItem(
                row_num,
                7,
                QTableWidgetItem(Tool.formatPrice(str(f), currency)),
            )
            self.tableData["logistic"].append(f)

    def getTableData(self):
        table_data = []
        row_count = self.ui.KpTable.rowCount()
        for row in range(row_count):
            row_data = []
            for col in range(5):
                item = self.ui.KpTable.item(row, col)
                row_data.append(item.text() if item is not None else "")
            for col in range(10, 14):
                item = self.ui.KpTable.item(row, col)
                row_data.append(item.text() if item is not None else "")
            table_data.append(row_data)
        return table_data

    def exportDocFromExcel(self):
        filename = QFileDialog.getOpenFileName(
            self,
            "Открыть файл",
            "",
            "csv (*.csv);;",
        )[0]
        if not filename:
            return

        df = pd.read_csv(filename, header=None, sep=";").dropna(how="all")
        data = df.values.tolist()
        table_data = []
        for row in data:
            if pd.notna(row[0]):
                table_data.append([*row[:5], *row[10:14]])
            else:
                break

        self.openCreateDocWindow((len(table_data[1:]), table_data[1:]))

    def _has_mixed_currencies(self):
        return len(set(self.tableData.get("currency", []))) > 1

    def exportDocs(self):
        if not Config.isTableOpened:
            self.error("Ошибка", "Загрузите КП поставщика")
            return
        if self._has_mixed_currencies():
            self.error(
                "Ошибка",
                "Создание КП в DOCX для таблицы со смешанной валютой не поддерживается.",
            )
            return

        Tool.write_log("CREATING DOCX")
        table_data = self.getTableData()
        self.openCreateDocWindow((len(table_data), table_data))
        Tool.write_log("CREATING DOCX...")

    def exportExcel(self):
        if not Config.isTableOpened:
            self.error("Ошибка", "Загрузите КП поставщика")
            return
        if self._has_mixed_currencies():
            self.error(
                "Ошибка",
                "Создание Excel для таблицы со смешанной валютой не поддерживается.",
            )
            return

        tableData = []
        row_count = self.ui.KpTable.rowCount()

        for row in range(row_count):
            row_data = []
            for col in range(6):
                item = self.ui.KpTable.item(row, col)
                row_data.append(item.text() if item is not None else "")
            for col in range(13, 15):
                item = self.ui.KpTable.item(row, col)
                row_data.append(item.text() if item is not None else "")
            tableData.append(row_data)

        exportExcelFile(
            (
                tableData,
                (
                    self.ui.logisticVar.currentIndex(),
                    self.ui.logisticNum.text(),
                    self.ui.markupLine.text(),
                ),
                self.ui.customLine.text(),
                sum(self.tableData["totalPrice"]),
            )
        )

    def resourcePath(self, relativePath):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relativePath)

    def closeEvent(self, event):
        Config.config["logisticNum"] = self.ui.logisticNum.text()
        Config.config["customNum"] = self.ui.customLine.text()
        Config.config["termDelivery"] = self.ui.termDeliveryLine.text()
        Config.config["markup"] = self.ui.markupLine.text()
        Config.config["logisticVar"] = str(self.ui.logisticVar.currentIndex())
        self.ensureOutputDirs()
        self.saveConfig()
        self.db.close()
        super().closeEvent(event)

    def funcExitSystem(self):
        self.close()
